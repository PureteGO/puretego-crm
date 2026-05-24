// Maps2GO GBP Scan — Extension Popup Logic
document.addEventListener('DOMContentLoaded', function () {
    const loginSection = document.getElementById('loginSection');
    const connectedSection = document.getElementById('connectedSection');
    const tokenInput = document.getElementById('tokenInput');
    const serverInput = document.getElementById('serverInput');
    const saveBtn = document.getElementById('saveBtn');
    const scanBtn = document.getElementById('scanBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const statusMsg = document.getElementById('statusMsg');

    // Load saved config
    chrome.storage.local.get(['scan_token', 'server_url'], function (data) {
        if (data.scan_token && data.server_url) {
            showConnected();
        }
    });

    function showStatus(msg, type) {
        statusMsg.textContent = msg;
        statusMsg.className = 'status ' + type;
    }

    function showConnected() {
        loginSection.style.display = 'none';
        connectedSection.style.display = 'block';
    }

    function showLogin() {
        loginSection.style.display = 'block';
        connectedSection.style.display = 'none';
    }

    // Save config
    saveBtn.addEventListener('click', function () {
        const token = tokenInput.value.trim();
        const server = serverInput.value.trim().replace(/\/$/, '') + '/';

        if (!token) {
            showStatus('Informe o token.', 'error');
            return;
        }
        if (!server || !server.startsWith('http')) {
            showStatus('Informe uma URL válida.', 'error');
            return;
        }

        chrome.storage.local.set({
            scan_token: token,
            server_url: server
        }, function () {
            showStatus('Configuração salva!', 'success');
            showConnected();
        });
    });

    // Logout
    logoutBtn.addEventListener('click', function () {
        chrome.storage.local.remove(['scan_token', 'server_url'], function () {
            showLogin();
            showStatus('Token removido.', 'info');
        });
    });

    // Trigger scan on active tab
    scanBtn.addEventListener('click', function () {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<span>⏳</span> Escaneando...';

        // Send message to content script on active tab
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (!tabs[0]) {
                showStatus('Nenhuma aba ativa encontrada.', 'error');
                resetScanBtn();
                return;
            }

            chrome.tabs.sendMessage(tabs[0].id, { action: 'scan' }, function (response) {
                if (chrome.runtime.lastError) {
                    showStatus('Esta página não é suportada. Abra o Google Search ou Maps.', 'error');
                    resetScanBtn();
                    return;
                }

                if (response && response.success) {
                    showStatus('Score: ' + response.score + '/100 — ' + response.business_name, 'success');
                } else {
                    showStatus(response ? response.error : 'Erro ao escanear.', 'error');
                }
                resetScanBtn();
            });
        });
    });

    function resetScanBtn() {
        scanBtn.disabled = false;
        scanBtn.innerHTML = '<span>🔍</span> Analisar Esta Página';
    }
});
