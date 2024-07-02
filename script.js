document.addEventListener('DOMContentLoaded', function() {
    const textbox = document.getElementById('large-textbox');
    const submitButton = document.getElementById('submit-button');
    const downloadLink = document.getElementById('download-link');
    
    submitButton.addEventListener('click', function() {
        const text = textbox.value;
        if (text.trim() === '') {
            alert('Please enter some text before submitting.');
            return;
        }
        
        // Disable submit button and show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'Synthesizing...';
        
        // Create form data
        const formData = new FormData();
        formData.append('text', text);
        
        // Send POST request to the server

        // local
        // fetch('http://localhost:5101/synthesize', {
        // global
        fetch('https://ec2.flaresolution.com/synthesize', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.download = "synthesized_speech.zip";
            downloadLink.style.display = 'block';
            downloadLink.textContent = "Download ZIP";

            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.textContent = 'Synthesize Speech';
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred while synthesizing speech.');
            
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.textContent = 'Synthesize Speech';
        });
    });
});