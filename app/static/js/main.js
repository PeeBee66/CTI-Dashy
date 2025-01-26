// CTIDashy_Flask/app/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsContainer = document.getElementById('search-results');

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    }

    function renderResult(result) {
        const div = document.createElement('div');
        div.className = 'search-result';
        
        const icon = result.type === 'Organization' ? '🔍' : '📄';
        let content = `
            <div class="result-header">
                <span class="entity-icon">${icon}</span>
                <div class="result-title">
                    <h3>${result.name || result.type || 'Unnamed Item'}</h3>
                </div>
            </div>
            <div class="result-details">
                <div class="type-value">
                    <span class="result-type">${result.type || 'Unknown Type'}</span>
                </div>
                <div class="metadata">
                    <span>Created: ${formatDate(result.created)}</span>
                    <span>Updated: ${formatDate(result.updated)}</span>
                </div>
            </div>
            <div class="result-footer">
                <div class="author">Author: ${result.author || 'Unknown'}</div>
                <div class="markings">${result.markings ? 'Markings: ' + result.markings.join(', ') : 'No markings'}</div>
                <div class="labels">${result.labels && result.labels.length ? 'Labels: ' + result.labels.join(', ') : 'No labels'}</div>
            </div>
        `;
        
        div.innerHTML = content;
        return div;
    }

    function performSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        resultsContainer.innerHTML = '<div class="searching">Searching OpenCTI...</div>';

        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                resultsContainer.innerHTML = '';
                
                if (data.error) {
                    resultsContainer.innerHTML = `<div class="error">${data.error}</div>`;
                    return;
                }

                if (!data.results || data.results.length === 0) {
                    resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
                    return;
                }

                data.results.forEach(result => {
                    resultsContainer.appendChild(renderResult(result));
                });
            })
            .catch(error => {
                resultsContainer.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
                console.error('Search error:', error);
            });
    }

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});