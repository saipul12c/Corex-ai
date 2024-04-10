document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('input-form');
    const inputText = document.getElementById('input_text');
    const inputTextDisplay = document.getElementById('input-text');
    const outputTextDisplay = document.getElementById('output-text');
    const errorMessageDisplay = document.getElementById('error-message');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const input = inputText.value.trim();
        if (input === '') {
            errorMessageDisplay.textContent = 'Mohon masukkan pertanyaan Anda.';
            errorMessageDisplay.classList.remove('hidden');
            inputTextDisplay.classList.add('hidden');
            outputTextDisplay.classList.add('hidden');
            return;
        }

        // Menampilkan animasi mengetik
        inputTextDisplay.textContent = 'Mengetik...';
        inputTextDisplay.classList.remove('hidden');
        outputTextDisplay.classList.add('hidden');
        errorMessageDisplay.classList.add('hidden');

        // Simulasi penundaan untuk memberikan efek mengetik
        setTimeout(function() {
            fetch('/api/process_input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input_text: input }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.error_message) {
                    errorMessageDisplay.textContent = data.error_message;
                    errorMessageDisplay.classList.remove('hidden');
                    inputTextDisplay.classList.add('hidden');
                    outputTextDisplay.classList.add('hidden');
                } else {
                    errorMessageDisplay.classList.add('hidden');
                    inputTextDisplay.textContent = `Pertanyaan Anda: ${input}`;
                    inputText.value = ''; // Membersihkan input setelah pengiriman
                    inputTextDisplay.classList.remove('hidden');
                    outputTextDisplay.textContent = `Jawaban Corex: ${data.output_text}`;
                    outputTextDisplay.classList.remove('hidden');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                errorMessageDisplay.textContent = 'Terjadi kesalahan dalam mengirim permintaan. Mohon coba lagi.';
                errorMessageDisplay.classList.remove('hidden');
                inputTextDisplay.classList.add('hidden');
                outputTextDisplay.classList.add('hidden');
            });
        }, 1000); // Mengatur penundaan selama 1 detik (1000 milidetik) untuk memberikan efek mengetik
    });
});
