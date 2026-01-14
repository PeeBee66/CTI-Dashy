// CTIDashy_Flask/app/static/js/resend.js

// Global variable to track selected files
let selectedFiles = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeManifestSelection();
    initializeRefreshButton();
    initializeSelectionControls();
    initializeBulkControls();

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
    const selectionControls = document.getElementById('selection-controls');

    if (!results || results.length === 0) {
        container.innerHTML = '<div class="no-results">No results found</div>';
        if (selectionControls) selectionControls.style.display = 'none';
        return;
    }

    // Show selection controls when results are displayed
    if (selectionControls) selectionControls.style.display = 'flex';

    container.innerHTML = results.map((result, index) => `
        <div class="result-card">
            <input type="checkbox" class="file-checkbox" data-index="${index}" data-file='${JSON.stringify(result)}'>
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

    // Initialize checkbox event listeners
    initializeCheckboxListeners();

    // Reset selection state
    selectedFiles = [];
    updateSelectionState();
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

// Selection Management Functions

function initializeSelectionControls() {
    const selectAllBtn = document.getElementById('select-all-btn');
    const deselectAllBtn = document.getElementById('deselect-all-btn');
    const resendSelectedBtn = document.getElementById('resend-selected-btn');

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', selectAllResults);
    }
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', deselectAllResults);
    }
    if (resendSelectedBtn) {
        resendSelectedBtn.addEventListener('click', resendSelected);
    }
}

function initializeCheckboxListeners() {
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectionState);
    });
}

function updateSelectionState() {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    selectedFiles = [];

    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            try {
                const fileData = JSON.parse(checkbox.dataset.file);
                selectedFiles.push(fileData);
            } catch (e) {
                console.error('Error parsing file data:', e);
            }
        }
    });

    // Update UI
    const count = selectedFiles.length;
    const countDisplay = document.getElementById('selection-count');
    const resendBtn = document.getElementById('resend-selected-btn');

    if (countDisplay) {
        countDisplay.textContent = `${count} selected`;
    }

    if (resendBtn) {
        resendBtn.disabled = count === 0;
        resendBtn.textContent = `Resend Selected (${count})`;
    }
}

function selectAllResults() {
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
    updateSelectionState();
}

function deselectAllResults() {
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    selectedFiles = [];
    updateSelectionState();
}

function resendSelected() {
    if (selectedFiles.length === 0) return;

    if (!confirm(`Confirm bulk resend of ${selectedFiles.length} file(s)?`)) {
        return;
    }

    const popup = createPopup(`Processing ${selectedFiles.length} file(s)...`);

    fetch('/bulk_resend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ files: selectedFiles })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const summary = data.summary;
            const content = createBulkResultsSummary(summary, data.results);
            popup.setType('success');
            popup.setContent(content);

            // Deselect all after successful bulk resend
            deselectAllResults();
        } else {
            popup.setType('error');
            popup.setContent(`<div class="transfer-error">Error: ${data.message}</div>`);
        }
    })
    .catch(error => {
        popup.setType('error');
        popup.setContent(`<div class="transfer-error">Error: ${error.message}</div>`);
    });
}

function createBulkResultsSummary(summary, results) {
    let html = `
        <div class="transfer-details">
            <h3>Bulk Resend Complete</h3>
            <div class="detail-section">
                <h4>Summary</h4>
                <p><strong>Total Files:</strong> ${summary.total}</p>
                <p><strong>Succeeded:</strong> <span style="color: #2e7d32;">${summary.succeeded}</span></p>
                <p><strong>Failed:</strong> <span style="color: #d32f2f;">${summary.failed}</span></p>
            </div>
    `;

    if (results.failed && results.failed.length > 0) {
        html += `
            <div class="detail-section">
                <h4>Failed Files</h4>
                <ul style="max-height: 200px; overflow-y: auto;">
        `;
        results.failed.forEach(item => {
            html += `<li><strong>${item.file}:</strong> ${item.message}</li>`;
        });
        html += `
                </ul>
            </div>
        `;
    }

    html += `</div>`;
    return html;
}

// Bulk Criteria Functions

let bulkFilteredFiles = [];

function initializeBulkControls() {
    const previewBtn = document.getElementById('preview-bulk-btn');
    const resendAllBtn = document.getElementById('resend-all-btn');

    if (previewBtn) {
        previewBtn.addEventListener('click', previewBulkFiles);
    }
    if (resendAllBtn) {
        resendAllBtn.addEventListener('click', resendAllBulk);
    }
}

function previewBulkFiles() {
    const manifestSelector = document.getElementById('manifest-selector');
    const dateFrom = document.getElementById('date-from').value;
    const dateTo = document.getElementById('date-to').value;
    const feedFilter = document.getElementById('feed-filter').value;

    const selectedManifests = Array.from(manifestSelector.selectedOptions).map(opt => opt.value);

    const previewContainer = document.getElementById('bulk-preview');
    previewContainer.innerHTML = '<div class="loading">Filtering files...</div>';

    fetch('/filter_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            manifest_files: selectedManifests,
            date_from: dateFrom,
            date_to: dateTo,
            feed_filter: feedFilter
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            bulkFilteredFiles = data.files;
            displayBulkPreview(data.files);

            // Enable/disable resend all button
            const resendAllBtn = document.getElementById('resend-all-btn');
            const countSpan = document.getElementById('bulk-count');
            if (resendAllBtn && countSpan) {
                resendAllBtn.disabled = data.files.length === 0;
                countSpan.textContent = data.files.length;
            }
        } else {
            previewContainer.innerHTML = `<div class="error">${data.message}</div>`;
        }
    })
    .catch(error => {
        previewContainer.innerHTML = `<div class="error">Filter failed: ${error.message}</div>`;
    });
}

function displayBulkPreview(files) {
    const container = document.getElementById('bulk-preview');

    if (!files || files.length === 0) {
        container.innerHTML = '<div class="no-results">No files match the criteria</div>';
        return;
    }

    // Group files by feed for better preview
    const feedGroups = {};
    files.forEach(file => {
        const feed = file.CTIfeed || 'Unknown';
        if (!feedGroups[feed]) {
            feedGroups[feed] = [];
        }
        feedGroups[feed].push(file);
    });

    let html = `<div class="preview-summary">Found ${files.length} file(s) matching criteria:</div>`;
    html += '<div class="preview-groups">';

    Object.keys(feedGroups).sort().forEach(feed => {
        const count = feedGroups[feed].length;
        html += `
            <div class="preview-group">
                <strong>${feed}:</strong> ${count} file(s)
            </div>
        `;
    });

    html += '</div>';
    html += `<div class="preview-note">Click "Resend All" to process these ${files.length} file(s)</div>`;
    container.innerHTML = html;
}

function resendAllBulk() {
    if (bulkFilteredFiles.length === 0) return;

    if (!confirm(`Confirm bulk resend of ${bulkFilteredFiles.length} file(s) from filtered criteria?`)) {
        return;
    }

    const popup = createPopup(`Processing ${bulkFilteredFiles.length} file(s)...`);

    fetch('/bulk_resend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ files: bulkFilteredFiles })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const summary = data.summary;
            const content = createBulkResultsSummary(summary, data.results);
            popup.setType('success');
            popup.setContent(content);

            // Clear preview after successful bulk resend
            bulkFilteredFiles = [];
            const previewContainer = document.getElementById('bulk-preview');
            if (previewContainer) {
                previewContainer.innerHTML = '<div class="success">Bulk resend completed. Run preview again to see remaining files.</div>';
            }

            // Disable resend all button
            const resendAllBtn = document.getElementById('resend-all-btn');
            const countSpan = document.getElementById('bulk-count');
            if (resendAllBtn && countSpan) {
                resendAllBtn.disabled = true;
                countSpan.textContent = '0';
            }
        } else {
            popup.setType('error');
            popup.setContent(`<div class="transfer-error">Error: ${data.message}</div>`);
        }
    })
    .catch(error => {
        popup.setType('error');
        popup.setContent(`<div class="transfer-error">Error: ${error.message}</div>`);
    });
}