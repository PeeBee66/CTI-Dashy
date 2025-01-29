// CTIDashy_Flask/app/static/js/resend.js
document.addEventListener('DOMContentLoaded', function() {
    initializeManifestSelection();
    initializeRefreshButton();

    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});

function initializeRefreshButton() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshManifestList);
    }
}

function refreshManifestList() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.innerHTML = '<span class="refresh-icon">↻</span> Refreshing...';
    }

    fetch('/refresh_resend_manifests', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateManifestList(data.manifests);
        } else {
            console.error('Failed to refresh manifests:', data.message);
        }
    })
    .catch(error => {
        console.error('Error refreshing manifests:', error);
    })
    .finally(() => {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.innerHTML = '<span class="refresh-icon">↻</span> Refresh';
        }
    });
}

function updateManifestList(manifests) {
    const container = document.getElementById('manifest-list');
    if (!container) return;

    container.innerHTML = manifests.map(manifest => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${manifest.name}</div>
                <div class="file-size">${manifest.size} KB</div>
            </div>
        </div>
    `).join('');

    initializeManifestSelection();
}

function initializeManifestSelection() {
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', function() {
            selectManifest(this);
        });
    });
}

function selectManifest(element) {
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
    });
    element.classList.add('selected');
    
    const manifestName = element.querySelector('.file-name').textContent;
    showManifestContent(manifestName);
}

function performSearch() {
    const searchTerm = document.getElementById('search-input').value.trim();
    if (!searchTerm) return;

    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<div class="loading">Searching...</div>';

    fetch('/search_manifest', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ search_term: searchTerm })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsContainer.innerHTML = `<div class="error">${data.error}</div>`;
        } else {
            displayResults(data.results);
        }
    })
    .catch(error => {
        resultsContainer.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
    });
}

function showManifestContent(manifestName) {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<div class="loading">Loading manifest...</div>';

    fetch('/search_manifest', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ manifest_name: manifestName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsContainer.innerHTML = `<div class="error">${data.error}</div>`;
        } else {
            displayResults(data.results);
        }
    })
    .catch(error => {
        resultsContainer.innerHTML = `<div class="error">Failed to load manifest: ${error.message}</div>`;
    });
}

function displayResults(results) {
    const container = document.getElementById('search-results');
    
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="no-results">No results found</div>';
        return;
    }

    container.innerHTML = results.map(result => `
        <div class="result-card">
            <div class="result-header">${result.Filename || ''}</div>
            <div class="result-content">
                <div class="result-field">
                    <span class="field-label">Manifest:</span>
                    <span class="field-value">${result.ManifestFile || ''}</span>
                </div>
                <div class="result-field">
                    <span class="field-label">CTIfeed:</span>
                    <span class="field-value">${result.CTIfeed || ''}</span>
                </div>
                <div class="result-field">
                    <span class="field-label">MD5Hash:</span>
                    <span class="field-value">${result.MD5Hash || ''}</span>
                </div>
                <div class="result-field">
                    <span class="field-label">DateTime:</span>
                    <span class="field-value">${result.DateTime || ''}</span>
                </div>
                <div class="result-field">
                    <span class="field-label">FileSize:</span>
                    <span class="field-value">${result.FileSize || ''}</span>
                </div>
                <div class="result-field">
                    <span class="field-label">FlowUUID:</span>
                    <span class="field-value">${result.FlowUUID || ''}</span>
                </div>
                <button class="resend-button" onclick='initiateResend(${JSON.stringify(result)})'>
                    Resend
                </button>
            </div>
        </div>
    `).join('');
}

function initiateResend(fileData) {
    if (!confirm(`Confirm resend of file: ${fileData.Filename}?`)) {
        return;
    }

    const popup = createPopup('Initiating Transfer...');

    fetch('/initiate_resend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(fileData)
    })
    .then(response => response.json())
    .then(data => {
        let content;
        if (data.status === 'success') {
            content = createTransferDetails(fileData, data);
            popup.setType('success');
        } else {
            content = `<div class="transfer-error">Error: ${data.message}</div>`;
            popup.setType('error');
        }
        popup.setContent(content);
    })
    .catch(error => {
        popup.setType('error');
        popup.setContent(`<div class="transfer-error">Error initiating resend: ${error}</div>`);
    });
}

function createPopup(initialMessage) {
    const popup = document.createElement('div');
    popup.className = 'transfer-popup';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-message">${initialMessage}</div>
            <button class="popup-close" onclick="this.closest('.transfer-popup').remove()">×</button>
        </div>
    `;
    document.body.appendChild(popup);

    return {
        setContent: (content) => {
            popup.querySelector('.popup-content').innerHTML = content +
                '<button class="popup-close" onclick="this.closest(\'.transfer-popup\').remove()">×</button>';
        },
        setType: (type) => {
            popup.className = `transfer-popup ${type}`;
        }
    };
}

function createTransferDetails(fileData, response) {
    // Convert size from bytes to MB
    const sizeMB = (parseInt(fileData.FileSize) / (1024 * 1024)).toFixed(2);
    
    return `
        <div class="transfer-details">
            <h3>Transfer Successful</h3>
            
            <div class="detail-section">
                <h4>File Information</h4>
                <p><strong>Name:</strong> ${fileData.Filename}</p>
                <p><strong>Feed:</strong> ${fileData.CTIfeed}</p>
                <p><strong>Size:</strong> ${sizeMB} MB</p>
                <p><strong>MD5:</strong> ${fileData.MD5Hash}</p>
            </div>

            <div class="detail-section">
                <h4>Transfer Path</h4>
                <p><strong>From:</strong> ${response.details.source_path}</p>
                <p><strong>To:</strong> ${response.details.target_path}</p>
            </div>

            <div class="detail-section">
                <h4>Verification</h4>
                <p>${response.details.verification}</p>
            </div>
            
            <button class="popup-close" onclick="this.closest('.transfer-popup').remove()">×</button>
        </div>
    `;
}