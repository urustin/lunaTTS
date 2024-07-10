// script.js

const localURL = "http://localhost:5101"
const globalURL = "https://ec2.flaresolution.com"
const currentURL = globalURL;

document.addEventListener('DOMContentLoaded', function() {
    const textInput = document.getElementById('textInput');
    const synthesizeButton = document.getElementById('synthesizeButton');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const statusMessage = document.getElementById('statusMessage');

    synthesizeButton.addEventListener('click', () => {
        const text = textInput.value;
        if (text.trim() === '') {
            alert('Please enter some text before synthesizing.');
            return;
        }
        synthesizeSpeech(text);
    });

    async function synthesizeSpeech(text) {
        try {
            // UI 초기화
            progressBar.style.width = '0%';
            progressText.textContent = '0%';
            statusMessage.textContent = 'Starting synthesis...';
            synthesizeButton.disabled = true;


            // 1. 작업 시작
            const formData = new FormData();
            formData.append('text', text);

            const startResponse = await fetch(currentURL+'/start_synthesis', {
                method: 'POST',
                body: formData,
            });
            const { job_id, total_sentences } = await startResponse.json();

            // 2. 배치 처리
            let processed = 0;
            while (processed < total_sentences) {
                const batchResponse = await fetch(currentURL+`/process_batch?job_id=${job_id}`);
                const batchResult = await batchResponse.json();
                processed = batchResult.processed;
                updateProgress(processed, total_sentences);
                
                // 잠시 대기하여 서버에 과도한 요청을 보내지 않도록 함
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // 3. 결과 가져오기
            statusMessage.textContent = 'Preparing download...';
            const resultResponse = await fetch(currentURL+`/get_result?job_id=${job_id}`);
            if (resultResponse.ok) {
                const blob = await resultResponse.blob();
                downloadZip(blob);
                statusMessage.textContent = 'Download complete!';
            } else {
                const errorData = await resultResponse.json();
                throw new Error(errorData.error || 'Failed to get result');
            }
        } catch (error) {
            console.error('Error during speech synthesis:', error);
            statusMessage.textContent = 'An error occurred. Please try again.';
        } finally {
            synthesizeButton.disabled = false;
        }
    }

    function updateProgress(processed, total) {
        const percentage = (processed / total) * 100;
        const formattedPercentage = percentage.toFixed(2);
        
        // 프로그레스 바 업데이트
        progressBar.style.width = `${formattedPercentage}%`;
        progressText.textContent = `${formattedPercentage}%`;
        
        // 상태 메시지 업데이트
        statusMessage.textContent = `Processing: ${processed} of ${total} sentences`;
    }

    function downloadZip(blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'synthesized_speech.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    }
});