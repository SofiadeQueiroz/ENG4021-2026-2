(() => {
    const button = document.querySelector('[data-cep-url]');
    if (!button) return;
    const cep = document.getElementById('id_cep');
    const status = document.getElementById('cep-status');
    let activeRequest = null;
    const resetButton = () => {
        button.disabled = false;
        button.textContent = 'Buscar endereço';
    };
    cep.addEventListener('input', () => {
        activeRequest?.abort();
        activeRequest = null;
        resetButton();
        status.textContent = 'Consulte o CEP novamente ou preencha o endereço manualmente.';
    });
    button.addEventListener('click', async () => {
        const value = cep.value.trim();
        if (!/^[0-9]{5}-?[0-9]{3}$/.test(value)) {
            status.textContent = 'Informe um CEP com 8 dígitos, como 01001-000.';
            cep.focus();
            return;
        }
        activeRequest?.abort();
        const controller = new AbortController();
        activeRequest = controller;
        const timer = setTimeout(() => controller.abort(), 8000);
        button.disabled = true;
        button.textContent = 'Buscando…';
        status.textContent = 'Consultando o endereço…';
        try {
            const response = await fetch(`${button.dataset.cepUrl}?cep=${encodeURIComponent(value)}`, {
                signal: controller.signal,
                headers: { Accept: 'application/json' },
            });
            if (response.redirected) throw new Error('Sua sessão expirou. Entre novamente para consultar o CEP.');
            const data = await response.json();
            if (!response.ok) throw new Error(data.erro || 'Não foi possível consultar o CEP. Preencha o endereço manualmente.');
            if (activeRequest !== controller || cep.value.trim() !== value) return;
            for (const field of ['endereco', 'bairro', 'cidade', 'estado']) {
                document.getElementById(`id_${field}`).value = data[field];
            }
            cep.value = `${data.cep.slice(0, 5)}-${data.cep.slice(5)}`;
            status.textContent = 'Endereço encontrado. Confira os dados e informe o número e o complemento.';
            document.getElementById('id_numero').focus();
        } catch (error) {
            if (activeRequest !== controller) return;
            status.textContent = error.name === 'AbortError' || error instanceof TypeError || error instanceof SyntaxError
                ? 'A consulta está indisponível. Preencha o endereço manualmente ou tente novamente.'
                : error.message;
        } finally {
            clearTimeout(timer);
            if (activeRequest === controller) {
                activeRequest = null;
                resetButton();
            }
        }
    });
})();
