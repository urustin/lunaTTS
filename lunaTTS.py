import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from google.cloud import texttospeech
import io
import zipfile
import uuid
import threading
from collections import defaultdict

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "https://luna-tts.vercel.app"}})
CORS(app)

# 메모리 내 저장소
jobs = {}
job_locks = defaultdict(threading.Lock)

# Google Cloud 설정
service_account_file = "lunatts-89b83769231f.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_file
client = texttospeech.TextToSpeechClient()

MAX_SENTENCES_PER_REQUEST = 1  # 한 번에 처리할 최대 문장 수

@app.route('/start_synthesis', methods=['POST'])
def start_synthesis():
    try:

        text = request.form.get('text', 'No text provided')
        voice = request.form.get('voice', 'en-US-Studio-O')
        rate = float(request.form.get('rate', 1.0))


        sentences = text.split('\n')
        job_id = str(uuid.uuid4())
        
        jobs[job_id] = {
            'total': len(sentences),
            'processed': 0,
            'queue': sentences,
            'results': [],
            'voice': voice,
            'rate': rate
        }
        
        return jsonify({"job_id": job_id, "total_sentences": len(sentences)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e), 500

@app.route('/process_batch', methods=['GET'])
def process_batch():
    job_id = request.args.get('job_id')
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    with job_locks[job_id]:
        job = jobs[job_id]
        try:
            batch = job['queue'][:MAX_SENTENCES_PER_REQUEST]
            job['queue'] = job['queue'][MAX_SENTENCES_PER_REQUEST:]
            
            for sentence in batch:
                if sentence.strip():
                    input_text = texttospeech.SynthesisInput(text=sentence)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code="en-US",
                        name=job['voice'],
                        # en-US-Studio-Q
                    )
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        speaking_rate=job['rate']
                        # can be modulate
                    )
                    
                    response = client.synthesize_speech(
                        input=input_text, voice=voice, audio_config=audio_config
                    )
                    
                    job['results'].append(response.audio_content)
            
            job['processed'] += len(batch)
            
            return jsonify({"processed": job['processed'], "total": job['total']})
        except Exception as e:
            print(f"Error: {str(e)}")
            return str(e), 500

@app.route('/get_result', methods=['GET'])
def get_result():
    job_id = request.args.get('job_id')
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    with job_locks[job_id]:
        job = jobs[job_id]
        try:
            if job['processed'] < job['total']:
                return jsonify({"status": "processing", "processed": job['processed'], "total": job['total']})
            
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                for i, audio_data in enumerate(job['results'], 1):
                    zf.writestr(f"sentence_{i:03d}.mp3", audio_data)
            
            memory_file.seek(0)
            
            # 작업 완료 후 메모리에서 데이터 삭제
            del jobs[job_id]
            del job_locks[job_id]
            
            return send_file(
                memory_file,
                mimetype="application/zip",
                as_attachment=True,
                download_name="synthesized_speech.zip"
            )
        except Exception as e:
            print(f"Error: {str(e)}")
            return str(e), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5101, debug=True)