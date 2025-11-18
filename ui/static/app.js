// Interview KB - URL Discovery Only
// Simplified frontend for URL discovery

// State
const state = {
    discovering: false,
    lastResults: null
};

// DOM Elements
const elements = {
    companyInput: document.getElementById('company'),
    personInput: document.getElementById('person'),
    maxUrlsInput: document.getElementById('max-urls'),
    discoverBtn: document.getElementById('discover-btn'),
    status: document.getElementById('status'),
    stats: document.getElementById('stats'),
    urlTextbox: document.getElementById('url-textbox'),
    categories: document.getElementById('categories'),
    copyAllBtn: document.getElementById('copy-all-btn'),
    clearBtn: document.getElementById('clear-btn')
};

// Discover URLs
async function discoverUrls() {
    const company = elements.companyInput.value.trim();

    if (!company) {
        showStatus('Please enter a company name', 'error');
        return;
    }

    const person = elements.personInput.value.trim() || null;
    const maxUrls = parseInt(elements.maxUrlsInput.value) || 100;

    state.discovering = true;
    elements.discoverBtn.disabled = true;
    elements.discoverBtn.innerHTML = '<span class="btn-icon">⏳</span> DISCOVERING...';

    showStatus(`Discovering URLs for ${company}${person ? ' / ' + person : ''}...`, 'info');

    try {
        const response = await fetch('/api/discover-urls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company: company,
                person: person,
                max_urls: maxUrls
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            state.lastResults = data;
            displayResults(data);
            showStatus(`✓ Found ${data.total_urls} URLs`, 'success');

            // Enable action buttons
            elements.copyAllBtn.disabled = false;
            elements.clearBtn.disabled = false;
        } else {
            showStatus(`✗ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`✗ Error: ${error.message}`, 'error');
        console.error('Discovery error:', error);
    } finally {
        state.discovering = false;
        elements.discoverBtn.disabled = false;
        elements.discoverBtn.innerHTML = '<span class="btn-icon">🔍</span> DISCOVER_URLS';
    }
}

// Display results
function displayResults(data) {
    // Show stats
    elements.stats.style.display = 'block';
    elements.stats.innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Total URLs:</span>
            <span class="stat-value">${data.total_urls}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Categories:</span>
            <span class="stat-value">${Object.keys(data.by_category).length}</span>
        </div>
    `;

    // Display all URLs (newline-separated for NotebookLM)
    const urlList = data.urls.map(item => item.url).join('\n');
    elements.urlTextbox.value = urlList;

    // Display category breakdown
    let categoriesHtml = '<h3>&gt; BY_CATEGORY</h3>';

    for (const [category, urls] of Object.entries(data.by_category)) {
        categoriesHtml += `
            <div class="category-card">
                <div class="category-header">
                    <span class="category-name">${category.toUpperCase()}</span>
                    <span class="category-count">${urls.length} URLs</span>
                </div>
                <div class="category-urls">
                    ${urls.slice(0, 5).map(item => `
                        <div class="url-item">
                            <div class="url-title">${escapeHtml(item.title)}</div>
                            <a href="${item.url}" target="_blank" class="url-link">${item.url}</a>
                        </div>
                    `).join('')}
                    ${urls.length > 5 ? `
                        <div class="url-more">
                            ... and ${urls.length - 5} more
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    elements.categories.innerHTML = categoriesHtml;
}

// Copy URLs to clipboard
async function copyUrls() {
    const urls = elements.urlTextbox.value;

    if (!urls) {
        showStatus('No URLs to copy', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(urls);

        // Visual feedback
        const originalText = elements.copyAllBtn.textContent;
        elements.copyAllBtn.textContent = 'COPIED!';
        elements.copyAllBtn.style.background = '#00AA00';

        setTimeout(() => {
            elements.copyAllBtn.textContent = originalText;
            elements.copyAllBtn.style.background = '';
        }, 2000);

        showStatus(`✓ Copied ${urls.split('\n').length} URLs to clipboard`, 'success');
    } catch (error) {
        showStatus('Failed to copy. Please select and copy manually.', 'error');
    }
}

// Clear results
function clearResults() {
    state.lastResults = null;
    elements.urlTextbox.value = '';
    elements.categories.innerHTML = '';
    elements.stats.style.display = 'none';
    elements.stats.innerHTML = '';
    elements.copyAllBtn.disabled = true;
    elements.clearBtn.disabled = true;
    showStatus('Results cleared', 'info');
}

// Show status message
function showStatus(message, type = 'info') {
    elements.status.textContent = message;
    elements.status.className = `status-message status-${type}`;

    // Auto-hide info messages after 5 seconds
    if (type === 'info' || type === 'success') {
        setTimeout(() => {
            if (elements.status.textContent === message) {
                elements.status.textContent = '';
                elements.status.className = 'status-message';
            }
        }, 5000);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
elements.discoverBtn.addEventListener('click', discoverUrls);
elements.copyAllBtn.addEventListener('click', copyUrls);
elements.clearBtn.addEventListener('click', clearResults);

// Enter key to discover
elements.companyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') discoverUrls();
});
elements.personInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') discoverUrls();
});

// Load saved state
const savedState = localStorage.getItem('url_discovery_state');
if (savedState) {
    try {
        const data = JSON.parse(savedState);
        if (data.company) elements.companyInput.value = data.company;
        if (data.person) elements.personInput.value = data.person;
        if (data.maxUrls) elements.maxUrlsInput.value = data.maxUrls;
    } catch (e) {
        console.error('Failed to load saved state:', e);
    }
}

// Auto-save state
function saveState() {
    const data = {
        company: elements.companyInput.value,
        person: elements.personInput.value,
        maxUrls: elements.maxUrlsInput.value
    };
    localStorage.setItem('url_discovery_state', JSON.stringify(data));
}

elements.companyInput.addEventListener('input', saveState);
elements.personInput.addEventListener('input', saveState);
elements.maxUrlsInput.addEventListener('change', saveState);
