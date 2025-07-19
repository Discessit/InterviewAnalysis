document.addEventListener('DOMContentLoaded', async () => {
    const quoteElement = document.getElementById('quote');
    const quoteLinkElement = document.getElementById('quote-link');

    if (quoteElement) {
        try {
            console.log('Fetching quote from /quote');
            const response = await fetch('/quote', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API response:', data);

            if (data && data.quote) {
                quoteElement.textContent = `"${data.quote}"`;
                if (quoteLinkElement && data.link) {
                    quoteLinkElement.href = data.link;
                    quoteLinkElement.textContent = 'Source';
                } else if (quoteLinkElement) {
                    quoteLinkElement.style.display = 'none';
                }
            } else {
                throw new Error('Invalid API response: Missing quote field');
            }
        } catch (error) {
            console.error('Error fetching quote:', error);
            quoteElement.textContent = 'Failed to load quote of the day.';
            if (quoteLinkElement) {
                quoteLinkElement.style.display = 'none';
            }
        }
    } else {
        console.error('Quote element not found in DOM');
    }

    const analyzeButton = document.getElementById('analyzeButton');
    const videoFileInput = document.getElementById('videoFile');
    const loadingDiv = document.getElementById('loading');

    if (analyzeButton && videoFileInput) {
        analyzeButton.addEventListener('click', async () => {
            const file = videoFileInput.files[0];
            if (!file) {
                alert('Please select a video file.');
                return;
            }

            if (!file.type.startsWith('video/mp4')) {
                alert('Please upload an MP4 video file.');
                return;
            }

            loadingDiv.classList.remove('hidden');
            analyzeButton.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Analysis failed.');
                }

                const result = await response.json();
                const encodedResult = encodeURIComponent(JSON.stringify(result));
                window.location.href = `/results?report=${encodedResult}`;
            } catch (error) {
                console.error('Error during analysis:', error);
                alert('An error occurred during analysis.');
            } finally {
                loadingDiv.classList.add('hidden');
                analyzeButton.disabled = false;
            }
        });
    }
});