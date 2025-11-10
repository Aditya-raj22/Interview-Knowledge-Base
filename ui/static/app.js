// Interview KB - URL Finder Frontend
// Clean, focused implementation for URL discovery only

// DOM elements
const elements = {
    companyInput: document.getElementById('company'),
    personInput: document.getElementById('person'),
    maxUrlsInput: document.getElementById('max-urls'),
    pipelineConsole: document.getElementById('pipeline-console'),

    // Simple URL Discovery
    discoverUrlsBtn: document.getElementById('discover-urls-btn'),
    urlDisplay: document.getElementById('url-display'),
    urlTextbox: document.getElementById('url-textbox'),
    urlStats: document.getElementById('url-stats'),
    urlCategories: document.getElementById('url-categories'),
    copyUrlsBtn: document.getElementById('copy-urls-btn'),

    // Advanced URL Finder
    urlFinderBtn: document.getElementById('url-finder-btn'),
    urlFinderDisplay: document.getElementById('url-finder-display'),
    urlFinderTextbox: document.getElementById('url-finder-textbox'),
    urlFinderStats: document.getElementById('url-finder-stats'),
    urlFinderBots: document.getElementById('url-finder-bots'),
    copyFinderUrlsBtn: document.getElementById('copy-finder-urls-btn'),
    exportNotebooklmBtn: document.getElementById('export-notebooklm-btn')
};

//=============================================================================
// CONSOLE LOGGING
//=============================================================================

function logToConsole(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `console-line ${type}`;

    const prompt = document.createElement('span');
    prompt.className = 'console-prompt';
    prompt.textContent = type === 'error' ? '✗' : type === 'success' ? '✓' : '$';

    const text = document.createElement('span');
    text.className = 'console-text';
    text.textContent = message;

    line.appendChild(prompt);
    line.appendChild(text);

    elements.pipelineConsole.appendChild(line);
    elements.pipelineConsole.scrollTop = elements.pipelineConsole.scrollHeight;
}

function clearConsole() {
    elements.pipelineConsole.innerHTML = '';
}

//=============================================================================
// SIMPLE URL DISCOVERY
//=============================================================================

async function discoverUrls() {
    const company = elements.companyInput.value.trim();
    if (!company) {
        alert('Please enter a company name');
        return;
    }

    const person = elements.personInput.value.trim() || null;
    const maxUrls = parseInt(elements.maxUrlsInput.value) || 50;

    elements.discoverUrlsBtn.disabled = true;
    elements.discoverUrlsBtn.innerHTML = '<span class="btn-icon">⏳</span> SEARCHING...';

    clearConsole();
    logToConsole(`Simple search for ${company}...`, 'info');
    elements.urlDisplay.style.display = 'none';
    elements.urlFinderDisplay.style.display = 'none';

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
            logToConsole(`Found ${data.total_urls} URLs`, 'success');
            displayUrlResults(data);
        } else {
            logToConsole(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        logToConsole(`Error: ${error.message}`, 'error');
    } finally {
        elements.discoverUrlsBtn.disabled = false;
        elements.discoverUrlsBtn.innerHTML = '<span class="btn-icon">🔍</span> SIMPLE_SEARCH';
    }
}

function displayUrlResults(data) {
    elements.urlDisplay.style.display = 'block';

    // Build URL list (one per line)
    const urlList = data.urls.map(item => item.url).join('\n');
    elements.urlTextbox.value = urlList;

    // Display stats
    const categoryCount = Object.keys(data.by_category).length;
    elements.urlStats.innerHTML = `
        <div class="stat-item">Total URLs: ${data.total_urls}</div>
        <div class="stat-item">Categories: ${categoryCount}</div>
    `;

    // Display categories
    let categoriesHtml = '<h4>&gt; BY_CATEGORY</h4>';
    for (const [category, urls] of Object.entries(data.by_category)) {
        categoriesHtml += `
            <div class="category-section">
                <div class="category-header">${category.toUpperCase()} (${urls.length})</div>
                <div class="category-urls">
                    ${urls.slice(0, 5).map(item => `
                        <div class="url-item">
                            <div class="url-title">${item.title}</div>
                            <div class="url-link">${item.url}</div>
                        </div>
                    `).join('')}
                    ${urls.length > 5 ? `<div class="url-more">... and ${urls.length - 5} more</div>` : ''}
                </div>
            </div>
        `;
    }
    elements.urlCategories.innerHTML = categoriesHtml;
}

async function copyUrls() {
    const urls = elements.urlTextbox.value;

    if (!urls) {
        alert('No URLs to copy');
        return;
    }

    try {
        await navigator.clipboard.writeText(urls);

        // Visual feedback
        const originalText = elements.copyUrlsBtn.textContent;
        elements.copyUrlsBtn.textContent = 'COPIED!';
        elements.copyUrlsBtn.style.background = '#00AA00';

        setTimeout(() => {
            elements.copyUrlsBtn.textContent = originalText;
            elements.copyUrlsBtn.style.background = '';
        }, 2000);

        logToConsole(`Copied ${urls.split('\n').length} URLs to clipboard`, 'success');
    } catch (error) {
        alert('Failed to copy URLs. Please select and copy manually.');
    }
}

//=============================================================================
// ADVANCED URL FINDER (5 BOTS)
//=============================================================================

async function runUrlFinder() {
    const company = elements.companyInput.value.trim();
    const person = elements.personInput.value.trim();

    if (!company || !person) {
        alert('Please enter both company name and person name for Advanced Finder');
        return;
    }

    const maxUrls = parseInt(elements.maxUrlsInput.value) || 50;

    elements.urlFinderBtn.disabled = true;
    elements.urlFinderBtn.innerHTML = '<span class="btn-icon">⏳</span> RUNNING...';

    clearConsole();
    logToConsole(`Advanced Finder: ${person} at ${company}`, 'info');
    elements.urlDisplay.style.display = 'none';
    elements.urlFinderDisplay.style.display = 'none';

    logToConsole('Starting 5 bots in parallel...', 'info');
    logToConsole('→ Financial Bot (SEC, transcripts)', 'info');
    logToConsole('→ Interview Bot (videos, podcasts)', 'info');
    logToConsole('→ Science Bot (PubMed, trials, patents)', 'info');
    logToConsole('→ News Bot (articles, press releases)', 'info');
    logToConsole('→ Social Bot (Twitter/X, mentions)', 'info');

    try {
        const response = await fetch('/api/url-finder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                person_name: person,
                company_name: company,
                max_results_per_bot: maxUrls
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            logToConsole(`✓ Found ${data.total_urls} URLs across ${data.metadata.successful_bots} bots`, 'success');
            displayUrlFinderResults(data);
        } else {
            logToConsole(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        logToConsole(`Error: ${error.message}`, 'error');
    } finally {
        elements.urlFinderBtn.disabled = false;
        elements.urlFinderBtn.innerHTML = '<span class="btn-icon">🤖</span> ADVANCED_FINDER';
    }
}

function displayUrlFinderResults(data) {
    elements.urlFinderDisplay.style.display = 'block';

    // Build URL list (one per line)
    const urlList = data.all_urls.map(item => item.url).join('\n');
    elements.urlFinderTextbox.value = urlList;

    // Display stats
    elements.urlFinderStats.innerHTML = `
        <div class="stat-item">Total URLs: ${data.total_urls}</div>
        <div class="stat-item">Successful Bots: ${data.metadata.successful_bots}/5</div>
        <div class="stat-item">Person: ${data.person_name}</div>
        <div class="stat-item">Company: ${data.company_name}</div>
    `;

    // Display bot results with expandable sections
    let botsHtml = '<h4>&gt; RESULTS_BY_BOT</h4>';

    for (const bot of data.bots) {
        const statusIcon = bot.status === 'success' ? '✓' : '✗';
        const statusClass = bot.status === 'success' ? 'success' : 'error';

        botsHtml += `
            <div class="bot-section">
                <div class="bot-header" onclick="toggleBotResults('${bot.name}')">
                    <span class="${statusClass}">${statusIcon}</span>
                    <span class="bot-name">${bot.name.toUpperCase().replace('_', ' ')}</span>
                    <span class="bot-count">${bot.count} URLs</span>
                    <span class="bot-toggle" id="toggle-${bot.name}">▶</span>
                </div>
                <div class="bot-results" id="results-${bot.name}" style="display: none;">
                    ${bot.status === 'success' && bot.results.length > 0 ? `
                        ${bot.results.slice(0, 20).map(url => `
                            <div class="url-item">
                                <div class="url-title">${url.title}</div>
                                <div class="url-meta">
                                    <span class="url-source">${url.source}</span>
                                    <span class="url-date">${url.date}</span>
                                    <span class="url-score">Score: ${(url.relevance_score * 100).toFixed(0)}%</span>
                                </div>
                                <div class="url-link">${url.url}</div>
                                ${url.description ? `<div class="url-description">${url.description}</div>` : ''}
                            </div>
                        `).join('')}
                        ${bot.count > 20 ? `<div class="url-more">... and ${bot.count - 20} more URLs</div>` : ''}
                    ` : `
                        <div class="url-item">
                            ${bot.status === 'error' ? `Error: ${bot.error || 'Unknown error'}` : 'No results found'}
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    elements.urlFinderBots.innerHTML = botsHtml;
}

function toggleBotResults(botName) {
    const resultsDiv = document.getElementById(`results-${botName}`);
    const toggleIcon = document.getElementById(`toggle-${botName}`);

    if (resultsDiv.style.display === 'none') {
        resultsDiv.style.display = 'block';
        toggleIcon.textContent = '▼';
    } else {
        resultsDiv.style.display = 'none';
        toggleIcon.textContent = '▶';
    }
}

async function copyFinderUrls() {
    const urls = elements.urlFinderTextbox.value;

    if (!urls) {
        alert('No URLs to copy');
        return;
    }

    try {
        await navigator.clipboard.writeText(urls);

        // Visual feedback
        const originalText = elements.copyFinderUrlsBtn.textContent;
        elements.copyFinderUrlsBtn.textContent = 'COPIED!';
        elements.copyFinderUrlsBtn.style.background = '#00AA00';

        setTimeout(() => {
            elements.copyFinderUrlsBtn.textContent = originalText;
            elements.copyFinderUrlsBtn.style.background = '';
        }, 2000);

        logToConsole(`Copied ${urls.split('\n').length} URLs to clipboard`, 'success');
    } catch (error) {
        alert('Failed to copy URLs. Please select and copy manually.');
    }
}

function exportToNotebookLM() {
    const urls = elements.urlFinderTextbox.value;

    if (!urls) {
        alert('No URLs to export');
        return;
    }

    // Copy to clipboard first
    navigator.clipboard.writeText(urls).then(() => {
        // Open NotebookLM in new tab
        window.open('https://notebooklm.google.com/', '_blank');

        logToConsole('URLs copied! Opening NotebookLM...', 'success');
        logToConsole('Paste URLs in NotebookLM to create sources', 'info');

        // Visual feedback
        const originalText = elements.exportNotebooklmBtn.innerHTML;
        elements.exportNotebooklmBtn.innerHTML = '<span class="btn-icon">✓</span> COPIED!';
        elements.exportNotebooklmBtn.style.background = '#00AA00';

        setTimeout(() => {
            elements.exportNotebooklmBtn.innerHTML = originalText;
            elements.exportNotebooklmBtn.style.background = '';
        }, 3000);
    }).catch(error => {
        alert('Failed to copy URLs. Please copy manually before opening NotebookLM.');
    });
}

//=============================================================================
// EVENT LISTENERS
//=============================================================================

elements.discoverUrlsBtn.addEventListener('click', discoverUrls);
elements.copyUrlsBtn.addEventListener('click', copyUrls);

elements.urlFinderBtn.addEventListener('click', runUrlFinder);
elements.copyFinderUrlsBtn.addEventListener('click', copyFinderUrls);
elements.exportNotebooklmBtn.addEventListener('click', exportToNotebookLM);

// Initialize
logToConsole('Interview KB URL Finder v2.0 ready', 'success');
