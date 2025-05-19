// CTIDashy_Flask/app/static/js/manifest.js
let selectedSource = null;
let selectedTarget = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeFileSelectors();
    initializeRefreshButton();
    initializeCompareAllButton();
});

function initializeFileSelectors() {
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const type = e.target.closest('.manifest-files').querySelector('h3').textContent.toLowerCase().includes('low') ? 'source' : 'target';
            const filename = this.querySelector('.file-name').textContent;
            selectFile(type, filename, this);
        });
    });
}

function initializeRefreshButton() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshFileList);
    }
}

function initializeCompareAllButton() {
    const compareAllButton = document.getElementById('compare-all-btn');
    if (compareAllButton) {
        compareAllButton.addEventListener('click', compareAllManifests);
    }
}

function findMatchingFile(filename, sourceToTarget) {
    const selector = sourceToTarget ? '#high-side-files' : '#low-side-files';
    const container = document.querySelector(selector);
    if (!container) return null;

    const fileItems = container.querySelectorAll('.file-item');
    for (let item of fileItems) {
        if (item.querySelector('.file-name').textContent === filename) {
            return item;
        }
    }
    return null;
}

function selectFile(type, filename, element) {
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    element.classList.add('selected');
    
    if (type === 'source') {
        selectedSource = filename;
        document.getElementById('source-selected').textContent = filename;
        
        const matchingFile = findMatchingFile(filename, true);
        if (matchingFile) {
            matchingFile.classList.add('selected');
            selectedTarget = filename;
            document.getElementById('target-selected').textContent = filename;
        } else {
            selectedTarget = null;
            document.getElementById('target-selected').textContent = 'Select target file';
        }
    } else {
        selectedTarget = filename;
        document.getElementById('target-selected').textContent = filename;
        
        const matchingFile = findMatchingFile(filename, false);
        if (matchingFile) {
            matchingFile.classList.add('selected');
            selectedSource = filename;
            document.getElementById('source-selected').textContent = filename;
        } else {
            selectedSource = null;
            document.getElementById('source-selected').textContent = 'Select source file';
        }
    }
    
    document.getElementById('compare-btn').disabled = !(selectedSource && selectedTarget && selectedSource === selectedTarget);
}

function refreshFileList() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.textContent = 'Refreshing...';
    }

    fetch('/refresh_manifest_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateFileList('low-side-files', data.low_side_files);
            updateFileList('high-side-files', data.high_side_files);
            clearAllSelections();
        } else {
            showError(data.message || 'Failed to refresh file list');
        }
    })
    .catch(error => {
        showError('Failed to refresh file list: ' + error.message);
    })
    .finally(() => {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = '↻ Refresh';
        }
    });
}

function updateFileList(containerId, files) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = files.map(file => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${file.size} KB</div>
            </div>
        </div>
    `).join('');

    initializeFileSelectors();
}

function clearAllSelections() {
    document.querySelectorAll('.file-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    selectedSource = null;
    selectedTarget = null;
    document.getElementById('source-selected').textContent = 'Select source file';
    document.getElementById('target-selected').textContent = 'Select target file';
    document.getElementById('compare-btn').disabled = true;
}

function formatDateTime(dtStr) {
    if (!dtStr) return '';
    return dtStr;
}

function formatFileSize(sizeInBytes) {
    if (!sizeInBytes) return '0.00 KB';
    const kb = parseInt(sizeInBytes) / 1024;
    return `${kb.toFixed(1)} KB`;
}

function formatFlowUUID(uuid) {
    if (!uuid) return '';
    return uuid.trim();
}

function compareAllManifests() {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = '<div class="loading">Comparing all manifests...</div>';
    
    fetch('/compare_all_manifests', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayCompareAllResults(data.results);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        showError('Failed to compare manifests: ' + error.message);
    });
}

function displayCompareAllResults(results) {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = '';
    
    const totalDifferences = results.reduce((total, result) => 
        total + (result.differences ? result.differences.length : 0), 0);
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'comparison-summary';
    summaryDiv.innerHTML = `
        <h3>Complete Comparison Results</h3>
        <p>Found ${totalDifferences} total differences across ${results.length} manifests</p>
    `;
    resultsContainer.appendChild(summaryDiv);
    
    results.forEach((result, index) => {
        const manifestSection = document.createElement('div');
        manifestSection.className = 'manifest-section';
        
        
        if (result.error) {
            manifestSection.innerHTML = `
                <div class="manifest-error">
                    <h4>${result.manifest}</h4>
                    <p class="error">${result.error}</p>
                </div>`;
        } else if (!result.differences || result.differences.length === 0) {
            manifestSection.innerHTML = `
                <div class="no-differences">
                    <h4>${result.manifest}</h4>
                    <p>No differences found</p>
                </div>`;
        } else {
            manifestSection.innerHTML = `
                <h4>${result.manifest}</h4>
                <p>Found ${result.differences.length} differences</p>
            `;
            const table = createDifferencesTable(result.differences);
            manifestSection.appendChild(table);
        }
        
        resultsContainer.appendChild(manifestSection);
    });
}

function createDifferencesTable(differences) {
    const table = document.createElement('table');
    table.className = 'comparison-table';
    
    const headers = ['Filename', 'CTIfeed', 'MD5Hash', 'DateTime', 'FileSize', 'FlowUUID'];
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    differences.forEach(diff => {
        const row = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            switch(header) {
                case 'DateTime':
                    td.textContent = formatDateTime(diff[header]);
                    break;
                case 'FileSize':
                    td.textContent = formatFileSize(diff[header]);
                    break;
                case 'FlowUUID':
                    td.textContent = formatFlowUUID(diff[header]);
                    break;
                default:
                    td.textContent = diff[header] || '';
            }
            if (header === 'MD5Hash') {
                td.className = 'hash-cell';
            }
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    
    return table;
}

function displayResults(differences, manifestName = null) {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = '';
    
    if (!differences || differences.length === 0) {
        resultsContainer.innerHTML = '<div class="no-differences">No differences found between the files</div>';
        return;
    }
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'comparison-summary';
    summaryDiv.innerHTML = `
        <h3>${manifestName ? `Comparison Results for ${manifestName}` : 'Comparison Results'}</h3>
        <p>Found ${differences.length} entries in Low Side missing from High Side</p>
    `;
    resultsContainer.appendChild(summaryDiv);
    
    resultsContainer.appendChild(createDifferencesTable(differences));
}

function showError(message) {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = `<div class="error">${message}</div>`;
}

function compareManifests() {
    if (!selectedSource || !selectedTarget || selectedSource !== selectedTarget) return;
    
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = '<div class="loading">Comparing files...</div>';
    
    fetch('/compare_manifests', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            source_file: selectedSource,
            target_file: selectedTarget
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayResults(data.differences, selectedSource);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        showError(`Error: ${error.message || 'Unknown error occurred'}`);
    });
}