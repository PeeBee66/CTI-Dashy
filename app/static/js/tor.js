// app/static/js/tor.js
document.addEventListener('DOMContentLoaded', function() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshNodes);
    }

    // Auto refresh every 5 minutes
    setInterval(refreshNodes, 300000);
});

function refreshNodes() {
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.innerHTML = '<span class="refresh-icon">↻</span> Refreshing...';
    }

    fetch('/refresh_tor_nodes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateNodesDisplay(data.nodes);
        } else {
            console.error('Failed to refresh nodes:', data.message);
        }
    })
    .catch(error => {
        console.error('Error refreshing nodes:', error);
    })
    .finally(() => {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.innerHTML = '<span class="refresh-icon">↻</span> Refresh';
        }
    });
}

function updateNodesDisplay(nodes) {
    const container = document.getElementById('tor-nodes');
    if (!container) return;

    container.innerHTML = nodes.map(node => `
        <div class="node-card">
            <div class="node-header">
                <span class="node-name">${node.name}</span>
                ${node.is_exit ? '<span class="exit-badge">Exit Node</span>' : ''}
            </div>
            <div class="node-content">
                <div class="info-row">
                    <span class="label">IP:</span>
                    <span class="value">${node.ip}</span>
                </div>
                <div class="info-row">
                    <span class="label">Ports:</span>
                    <span class="value">${node.onion_port} (Onion) / ${node.dir_port} (Dir)</span>
                </div>
                <div class="info-row">
                    <span class="label">Version:</span>
                    <span class="value">${node.version}</span>
                </div>
                <div class="info-row">
                    <span class="label">Uptime:</span>
                    <span class="value">${node.uptime} seconds</span>
                </div>
                <div class="info-row">
                    <span class="label">Flags:</span>
                    <span class="value">${node.flags.join(', ')}</span>
                </div>
                <div class="info-row">
                    <span class="label">Contact:</span>
                    <span class="value">${node.contact}</span>
                </div>
                <div class="info-row">
                    <span class="label">Collection Date:</span>
                    <span class="value">${node.collection_date}</span>
                </div>
            </div>
        </div>
    `).join('');
}