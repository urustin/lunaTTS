import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from google.cloud import texttospeech
import io
import base64
import zipfile


app = Flask(__name__)
CORS(app)

# Set the path to your service account file
service_account_file = "lunatts-1310b7e6258a.json"
# Set the environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_file

# Create the Text-to-Speech client
client = texttospeech.TextToSpeechClient()

@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    try:
        text = request.form.get('text', 'No text provided')
        sentences = text.split('\n')
        audio_files = []
        sentence_counter = 1

        for sentence in sentences:
            if sentence.strip():  # Skip empty sentences
                input_text = texttospeech.SynthesisInput(text=sentence)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Studio-O",
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1
                )
                
                response = client.synthesize_speech(
                    input=input_text, voice=voice, audio_config=audio_config
                )
                
                audio_files.append((f"sentence_{sentence_counter:03d}.mp3", response.audio_content))
                sentence_counter += 1

        # Create a zip file
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for filename, data in audio_files:
                zf.writestr(filename, data)
        
        memory_file.seek(0)
        
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