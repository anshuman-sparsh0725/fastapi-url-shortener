document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url-input');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        let longUrl = urlInput.value;

        if (!longUrl.startsWith('http://') && !longUrl.startsWith('https://')) {
            longUrl = `https://${longUrl}`;
        }

        const response = await fetch('/shorten', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: longUrl })
        });

        resultContainer.style.display = 'block';

        if (response.ok) {
            const data = await response.json();
            resultContainer.innerHTML = `
                Shortened URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a>
            `;
            urlInput.value = '';
        } else {
            resultContainer.innerHTML = 'Error: Please enter a valid URL.';
        }
    });
});