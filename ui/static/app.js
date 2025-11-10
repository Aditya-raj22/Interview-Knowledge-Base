// Interview KB Frontend Logic
// Handles SSE pipeline streaming, chat interface, and file browsing

// State management
const state = {
    currentCompany: null,
    currentPerson: null,
    pipelineRunning: false,
    chatEnabled: false,
    currentMode: 'rag'  // 'rag' or 'url'
};

// DOM elements
const elements = {
    companyInput: document.getElementById('company'),
    personInput: document.getElementById('person'),
    modeSelect: document.getElementById('mode'),
    modelSelect: document.getElementById('model'),
    skipIngestionCheckbox: document.getElementById('skip-ingestion'),
    skipIndexingCheckbox: document.getElementById('skip-indexing'),
    runPipelineBtn: document.getElementById('run-pipeline-btn'),
    pipelineConsole: document.getElementById('pipeline-console'),
    briefDisplay: document.getElementById('brief-display'),
    briefContent: document.getElementById('brief-content'),
    briefMeta: document.getElementById('brief-meta'),
    clearBriefBtn: document.getElementById('clear-brief-btn'),
    fileList: document.getElementById('file-list'),
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendQueryBtn: document.getElementById('send-query-btn'),

    // Mode toggle
    modeRagBtn: document.getElementById('mode-rag'),
    modeUrlBtn: document.getElementById('mode-url'),
    ragSettings: document.getElementById('rag-settings'),
    urlSettings: document.getElementById('url-settings'),

    // URL Discovery
    discoverUrlsBtn: document.getElementById('discover-urls-btn'),
    maxUrlsInput: document.getElementById('max-urls'),
    urlDisplay: document.getElementById('url-display'),
    urlTextbox: document.getElementById('url-textbox'),
    urlStats: document.getElementById('url-stats'),
    urlCategories: document.getElementById('url-categories'),
    copyUrlsBtn: document.getElementById('copy-urls-btn')
};

// Load saved state from localStorage
function loadSavedState() {
    const saved = localStorage.getItem('interview_kb_state');
    if (saved) {
        const data = JSON.parse(saved);
        elements.companyInput.value = data.company || '';
        elements.personInput.value = data.person || '';
        elements.modeSelect.value = data.mode || 'summary';
        elements.modelSelect.value = data.model || 'gpt-4o';

        if (data.company) {
            state.currentCompany = data.company;
            loadFiles(data.company);
            enableChat();
        }
    }
}

// Save state to localStorage
function saveState() {
    const data = {
        company: elements.companyInput.value,
        person: elements.personInput.value,
        mode: elements.modeSelect.value,
        model: elements.modelSelect.value
    };
    localStorage.setItem('interview_kb_state', JSON.stringify(data));
}

// Console logging
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

// Pipeline execution with SSE
async function runPipeline() {
    const company = elements.companyInput.value.trim();
    if (!company) {
        alert('Please enter a company name');
        return;
    }

    state.pipelineRunning = true;
    state.currentCompany = company;
    state.currentPerson = elements.personInput.value.trim() || null;

    elements.runPipelineBtn.disabled = true;
    elements.runPipelineBtn.innerHTML = '<span class="btn-icon">⏳</span> RUNNING...';

    clearConsole();
    elements.briefDisplay.style.display = 'none';

    saveState();

    // SSE connection
    const payload = {
        company: company,
        person: state.currentPerson,
        mode: elements.modeSelect.value,
        model: elements.modelSelect.value,
        skip_ingestion: elements.skipIngestionCheckbox.checked,
        skip_indexing: elements.skipIndexingCheckbox.checked
    };

    try {
        const response = await fetch('/api/pipeline/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    handlePipelineEvent(data);
                }
            }
        }
    } catch (error) {
        logToConsole(`Error: ${error.message}`, 'error');
    } finally {
        state.pipelineRunning = false;
        elements.runPipelineBtn.disabled = false;
        elements.runPipelineBtn.innerHTML = '<span class="btn-icon">▶</span> RUN_PIPELINE';
    }
}

function handlePipelineEvent(event) {
    const { step, status, message, brief } = event;

    if (status === 'started') {
        logToConsole(`[${step.toUpperCase()}] ${message}`, 'info');
    } else if (status === 'completed') {
        logToConsole(`[${step.toUpperCase()}] ${message}`, 'success');

        if (step === 'ingestion') {
            loadFiles(state.currentCompany);
        }

        if (step === 'generation' && brief) {
            displayBrief(brief);
            enableChat();
        }
    } else if (status === 'skipped') {
        logToConsole(`[${step.toUpperCase()}] ${message}`, 'info');
    } else if (status === 'failed') {
        logToConsole(`[ERROR] ${message}`, 'error');
    }
}

// Display generated brief
function displayBrief(brief) {
    elements.briefDisplay.style.display = 'block';

    // Format summary with markdown-like styling
    const formattedSummary = brief.summary
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    elements.briefContent.innerHTML = `
        <div class="brief-summary">${formattedSummary}</div>

        ${brief.insights && brief.insights.length > 0 ? `
            <div class="brief-section">
                <h4>&gt; KEY_INSIGHTS</h4>
                <ul class="insight-list">
                    ${brief.insights.map(insight => `
                        <li>
                            ${insight.text}
                            ${insight.citations ? `<span class="citations">[${insight.citations.join(', ')}]</span>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}

        ${brief.key_entities && brief.key_entities.length > 0 ? `
            <div class="brief-section">
                <h4>&gt; KEY_ENTITIES</h4>
                <div class="entity-list">
                    ${brief.key_entities.map(entity => `
                        <span class="entity-tag">${entity.text} (${entity.type})</span>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;

    // Display metadata
    if (brief.metadata) {
        const meta = brief.metadata;
        elements.briefMeta.innerHTML = `
            <div class="meta-item">Model: ${meta.model}</div>
            <div class="meta-item">Chunks: ${meta.n_chunks_retrieved || 'N/A'}</div>
            <div class="meta-item">Citations: ${meta.n_citations || 0}</div>
            <div class="meta-item">Time: ${meta.total_time_ms || 'N/A'}ms</div>
        `;
    }
}

// File browser
async function loadFiles(company) {
    try {
        const response = await fetch(`/api/files/${encodeURIComponent(company)}`);
        const data = await response.json();

        if (data.files && data.files.length > 0) {
            elements.fileList.innerHTML = data.files.map(file => `
                <div class="file-item">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">${file.doc_count} docs • ${formatBytes(file.size)}</div>
                </div>
            `).join('');

            // Load preview on hover (future enhancement)
        } else {
            elements.fileList.innerHTML = '<div class="empty-state">No files found</div>';
        }
    } catch (error) {
        elements.fileList.innerHTML = '<div class="empty-state">Error loading files</div>';
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Chat interface
function enableChat() {
    state.chatEnabled = true;
    elements.chatInput.disabled = false;
    elements.sendQueryBtn.disabled = false;
}

async function sendChatQuery() {
    const query = elements.chatInput.value.trim();
    if (!query || !state.currentCompany) return;

    // Add user message
    addChatMessage('user', query);
    elements.chatInput.value = '';

    // Disable input while processing
    elements.chatInput.disabled = true;
    elements.sendQueryBtn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company: state.currentCompany,
                person: state.currentPerson,
                query: query,
                mode: elements.modeSelect.value,
                model: elements.modelSelect.value
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            addChatMessage('assistant', data.response, data.citations);
        } else {
            addChatMessage('system', 'Error: ' + data.detail);
        }
    } catch (error) {
        addChatMessage('system', 'Error: ' + error.message);
    } finally {
        elements.chatInput.disabled = false;
        elements.sendQueryBtn.disabled = false;
        elements.chatInput.focus();
    }
}

function addChatMessage(role, content, citations = null) {
    const message = document.createElement('div');
    message.className = `chat-message ${role}`;

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = role.toUpperCase();

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');

    message.appendChild(header);
    message.appendChild(contentDiv);

    if (citations && citations.length > 0) {
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'message-citations';
        citationsDiv.textContent = `[Citations: ${citations.slice(0, 5).join(', ')}]`;
        message.appendChild(citationsDiv);
    }

    elements.chatMessages.appendChild(message);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Event listeners
elements.runPipelineBtn.addEventListener('click', runPipeline);

elements.clearBriefBtn.addEventListener('click', () => {
    elements.briefDisplay.style.display = 'none';
    clearConsole();
    logToConsole('Waiting for input...', 'info');
});

elements.sendQueryBtn.addEventListener('click', sendChatQuery);

elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !elements.chatInput.disabled) {
        sendChatQuery();
    }
});

// Auto-save on input changes
[elements.companyInput, elements.personInput, elements.modeSelect, elements.modelSelect].forEach(el => {
    el.addEventListener('change', saveState);
});

//=============================================================================
// URL DISCOVERY MODE
//=============================================================================

// Mode toggle
function switchMode(mode) {
    state.currentMode = mode;

    if (mode === 'rag') {
        elements.modeRagBtn.classList.add('active');
        elements.modeUrlBtn.classList.remove('active');
        elements.ragSettings.style.display = 'block';
        elements.urlSettings.style.display = 'none';
        elements.urlDisplay.style.display = 'none';
        elements.briefDisplay.style.display = 'none';
    } else {
        elements.modeUrlBtn.classList.add('active');
        elements.modeRagBtn.classList.remove('active');
        elements.urlSettings.style.display = 'block';
        elements.ragSettings.style.display = 'none';
        elements.briefDisplay.style.display = 'none';
        elements.urlDisplay.style.display = 'none';
    }

    clearConsole();
    logToConsole(`Switched to ${mode.toUpperCase()} mode`, 'info');
}

// URL Discovery
async function discoverUrls() {
    const company = elements.companyInput.value.trim();
    if (!company) {
        alert('Please enter a company name');
        return;
    }

    const person = elements.personInput.value.trim() || null;
    const maxUrls = parseInt(elements.maxUrlsInput.value) || 50;

    elements.discoverUrlsBtn.disabled = true;
    elements.discoverUrlsBtn.innerHTML = '<span class="btn-icon">⏳</span> DISCOVERING...';

    clearConsole();
    logToConsole(`Discovering URLs for ${company}...`, 'info');
    elements.urlDisplay.style.display = 'none';

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
        elements.discoverUrlsBtn.innerHTML = '<span class="btn-icon">🔍</span> DISCOVER_URLS';
    }
}

// Display URL results
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

// Copy URLs to clipboard
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

// Event listeners for URL mode
elements.modeRagBtn.addEventListener('click', () => switchMode('rag'));
elements.modeUrlBtn.addEventListener('click', () => switchMode('url'));
elements.discoverUrlsBtn.addEventListener('click', discoverUrls);
elements.copyUrlsBtn.addEventListener('click', copyUrls);

// Initialize
loadSavedState();
