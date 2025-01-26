// CTIDashy_Flask/app/static/js/resend.js
let selectedManifest = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeManifestSelection();
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});

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
    fetch('/initiate_resend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(fileData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('File successfully queued for resend');
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        alert('Error initiating resend: ' + error);
    });
}