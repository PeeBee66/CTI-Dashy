// CTIDashy_Flask/app/static/js/manifest.js

let selectedSource = null;
let selectedTarget = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeFileSelectors();
});

function initializeFileSelectors() {
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const type = e.target.closest('.manifest-files').querySelector('h3').textContent.toLowerCase().includes('low') ? 'source' : 'target';
            const filename = this.querySelector('.file-name').textContent;
            clearAllSelections();
            selectFile(type, filename, this);
        });
    });
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

function findMatchingFile(filename) {
    const otherSideSelector = selectedSource ? '.manifest-files:not(:first-child)' : '.manifest-files:first-child';
    const otherSideFiles = document.querySelector(otherSideSelector).querySelectorAll('.file-item');
    
    for (let file of otherSideFiles) {
        if (file.querySelector('.file-name').textContent === filename) {
            return file;
        }
    }
    return null;
}

function selectFile(type, filename, element) {    
    element.classList.add('selected');
    
    if (type === 'source') {
        selectedSource = filename;
        document.getElementById('source-selected').textContent = filename;
        
        const matchingFile = findMatchingFile(filename);
        if (matchingFile) {
            matchingFile.classList.add('selected');
            selectedTarget = filename;
            document.getElementById('target-selected').textContent = filename;
        }
    } else {
        selectedTarget = filename;
        document.getElementById('target-selected').textContent = filename;
        
        const matchingFile = findMatchingFile(filename);
        if (matchingFile) {
            matchingFile.classList.add('selected');
            selectedSource = filename;
            document.getElementById('source-selected').textContent = filename;
        }
    }
    
    document.getElementById('compare-btn').disabled = !(selectedSource && selectedTarget && selectedSource === selectedTarget);
}

function formatDateTime(dtStr) {
    if (!dtStr) return '';
    return dtStr;  // Return as is since it's already in correct format
}

function formatFileSize(bytes) {
    if (!bytes) return '0.00 MB';
    const mb = (parseInt(bytes) / (1024 * 1024)).toFixed(2);
    return `${mb} MB`;
}

function formatFlowUUID(uuid) {
    if (!uuid) return '';
    const cleanUuid = uuid.trim();
    return cleanUuid;  // Return as is since it's already formatted
}

function displayResults(differences) {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = '';
    
    if (!differences || differences.length === 0) {
        resultsContainer.innerHTML = '<div class="no-differences">No differences found between the files</div>';
        return;
    }
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'comparison-summary';
    summaryDiv.innerHTML = `
        <h3>Comparison Results</h3>
        <p>Found ${differences.length} entries in system1 missing from system2</p>
    `;
    resultsContainer.appendChild(summaryDiv);
    
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
                    td.textContent = formatDateTime(diff.DateTime);
                    break;
                case 'FileSize':
                    td.textContent = formatFileSize(diff.FileSize);
                    break;
                case 'FlowUUID':
                    td.textContent = formatFlowUUID(diff.FlowUUID);
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
    
    resultsContainer.appendChild(table);
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
            displayResults(data.differences);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        showError(`Error: ${error.message || 'Unknown error occurred'}`);
    });
}

function showError(message) {
    const resultsContainer = document.getElementById('comparison-results');
    resultsContainer.innerHTML = `<div class="error">${message}</div>`;
}