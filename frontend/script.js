class PybitAnalyzer {
    constructor() {
        this.config = {};
        this.currentFile = null;
        this.analysisResults = null;
        this.backendUrl = "http://localhost:5000";
        
        // DOM elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.loadingDiv = document.getElementById('loading');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.resultsDiv = document.getElementById('results');
        
        // Initialize
        this.loadConfig().then(() => this.init());
    }
    
    async loadConfig() {
        try {
            const response = await fetch('config.json');
            this.config = await response.json();
            if (this.config.backendUrl) {
                this.backendUrl = this.config.backendUrl;
            }
        } catch (error) {
            console.error('Error loading config:', error);
            this.showError('Failed to load analyzer configuration');
        }
    }
    
    init() {
        this.setupDragAndDrop();
        this.setupFileInput();
    }
    
    setupDragAndDrop() {
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.unhighlight, false);
        });
        
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
    }
    
    setupFileInput() {
        this.fileInput.addEventListener('change', this.handleFiles.bind(this));
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    highlight() {
        this.dropZone.classList.add('highlight');
    }
    
    unhighlight() {
        this.dropZone.classList.remove('highlight');
    }
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles({ target: { files } });
    }
    
    handleFiles(e) {
        const files = e.target.files;
        if (files.length === 0) return;
        
        this.currentFile = files[0];
        
        // Check file type
        const fileExt = this.currentFile.name.split('.').pop().toLowerCase();
        if (!['py', 'pyc', 'exe'].includes(fileExt)) {
            this.showError('Unsupported file type. Please upload .py, .pyc, or .exe files.');
            return;
        }
        
        // Check file size
        if (this.currentFile.size > (this.config.maxFileSize || 10485760)) {
            this.showError('File too large. Maximum size is 10MB.');
            return;
        }
        
        this.startAnalysis();
    }
    
    startAnalysis() {
        this.showLoading();
        this.simulateProgress();
    }
    
    showLoading() {
        this.loadingDiv.style.display = 'block';
        this.resultsDiv.style.display = 'none';
        this.progressBar.value = 0;
        this.progressText.textContent = 'Initializing analyzer...';
    }
    
    simulateProgress() {
        let progress = 0;
        const steps = [
            { percent: 15, message: 'Loading file...' },
            { percent: 30, message: 'Identifying file type...' },
            { percent: 50, message: 'Decompiling bytecode...' },
            { percent: 70, message: 'Deobfuscating code...' },
            { percent: 85, message: 'Analyzing patterns...' },
            { percent: 100, message: 'Finalizing report...' }
        ];
        
        const interval = setInterval(() => {
            const step = steps.find(s => s.percent > progress);
            if (step) {
                progress = step.percent;
                this.progressBar.value = progress;
                this.progressText.textContent = step.message;
            }
            
            if (progress >= 100) {
                clearInterval(interval);
                this.analyzeFile();
            }
        }, 500);
    }
    
    async analyzeFile() {
        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);
            
            const response = await fetch(`${this.backendUrl}/analyze`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            this.analysisResults = await response.json();
            this.displayResults();
        } catch (error) {
            this.showError('Error analyzing file: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults() {
        this.resultsDiv.innerHTML = this.createResultsTemplate();
        this.setupResultsTabs();
        this.populateResults();
    }
    
    createResultsTemplate() {
        const isExe = this.analysisResults.file_type === 'exe';
        
        return `
            <div class="tabs">
                <button class="tab-button active" data-tab="summary">Summary</button>
                ${isExe ? '' : '<button class="tab-button" data-tab="decompiled">Decompiled Code</button>'}
                <button class="tab-button" data-tab="tokens">Discord Tokens</button>
                <button class="tab-button" data-tab="urls">URLs</button>
                <button class="tab-button" data-tab="patterns">Code Patterns</button>
                <button class="tab-button" data-tab="registry">Registry Access</button>
                ${isExe ? '<button class="tab-button" data-tab="exe">EXE Analysis</button>' : ''}
            </div>
            
            <div id="summary" class="tab-content active">
                <h3>Analysis Summary</h3>
                <div id="summaryContent"></div>
            </div>
            
            ${isExe ? '' : `
            <div id="decompiled" class="tab-content">
                <h3>Decompiled Source Code</h3>
                <div class="code-display" id="decompiledCode"></div>
            </div>
            `}
            
            <div id="tokens" class="tab-content">
                <h3>Discord Token Detection</h3>
                <div class="table-container">
                    <table id="tokensTable">
                        <thead>
                            <tr>
                                <th>Token</th>
                                <th>Status</th>
                                <th>Context</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
            
            <div id="urls" class="tab-content">
                <h3>URL Detection</h3>
                <div class="table-container">
                    <table id="urlsTable">
                        <thead>
                            <tr>
                                <th>URL</th>
                                <th>Type</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
            
            <div id="patterns" class="tab-content">
                <h3>Suspicious Code Patterns</h3>
                <div class="table-container">
                    <table id="patternsTable">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Pattern</th>
                                <th>Status</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
            
            <div id="registry" class="tab-content">
                <h3>Registry Access Patterns</h3>
                <div class="table-container">
                    <table id="registryTable">
                        <thead>
                            <tr>
                                <th>Registry Key</th>
                                <th>Status</th>
                                <th>Risk</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
            
            ${isExe ? `
            <div id="exe" class="tab-content">
                <h3>EXE Analysis Results</h3>
                <div id="exeAnalysisContent"></div>
            </div>
            ` : ''}
        `;
    }
    
    populateResults() {
        this.populateSummary();
        
        if (this.analysisResults.file_type !== 'exe') {
            this.populateDecompiledCode();
        } else {
            this.populateExeAnalysis();
        }
        
        this.populateTokens();
        this.populateUrls();
        this.populatePatterns();
        this.populateRegistry();
        
        this.resultsDiv.style.display = 'block';
    }
    
    populateExeAnalysis() {
        const exeContent = document.getElementById('exeAnalysisContent');
        const result = this.analysisResults;
        
        exeContent.innerHTML = `
            <div class="exe-result">
                <div class="exe-header">
                    <h3>${result.file_name}</h3>
                    <span class="badge ${result.python_embedded ? 'badge-danger' : 'badge-success'}">
                        ${result.python_embedded ? 'PYTHON EMBEDDED' : 'NO PYTHON DETECTED'}
                    </span>
                </div>
                
                ${result.python_embedded ? `
                <div class="compiler-info">
                    <p><strong>Compiler:</strong> ${result.compiler || 'Unknown'}</p>
                </div>
                
                <div class="extracted-files">
                    <h4>Extracted Files (${result.extracted_files?.length || 0})</h4>
                    ${result.extracted_files?.map(file => `
                        <div class="file-item">
                            <span>${file.name}</span>
                            <span class="badge">${file.type}</span>
                        </div>
                    `).join('') || '<p>No files extracted</p>'}
                </div>
                
                <div class="decompiled-results">
                    <h4>Decompiled Code</h4>
                    ${result.decompiled_code?.map((code, i) => `
                        <div class="decompiled-container">
                            <button class="toggle-code" data-index="${i}">Show/Hide Code</button>
                            <pre class="code-display" id="exe-code-${i}" style="display:none">${code}</pre>
                        </div>
                    `).join('') || '<p>No code decompiled</p>'}
                </div>
                ` : ''}
            </div>
        `;
    }
    
    // [Previous populateSummary(), populateDecompiledCode(), populateTokens(), 
    // populateUrls(), populatePatterns(), populateRegistry() methods remain the same]
    
    setupResultsTabs() {
        const tabs = this.resultsDiv.querySelectorAll('.tab-button');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const contents = this.resultsDiv.querySelectorAll('.tab-content');
                contents.forEach(c => c.classList.remove('active'));
                
                const tabId = tab.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
            });
        });
    }
    
    hideLoading() {
        this.loadingDiv.style.display = 'none';
    }
    
    showError(message) {
        alert(message);
        this.hideLoading();
    }
    
    // Helper method to apply syntax highlighting
    applySyntaxHighlighting(element) {
        const code = element.textContent;
        let highlighted = code;
        
        // Highlight strings
        highlighted = highlighted.replace(/(['"])(.*?)\1/g, '<span class="string">$1$2$1</span>');
        
        // Highlight keywords
        const keywords = ['def', 'class', 'import', 'from', 'as', 'return', 'if', 'else', 'elif', 
                         'for', 'while', 'try', 'except', 'finally', 'with', 'lambda'];
        
        keywords.forEach(kw => {
            const regex = new RegExp(`\\b${kw}\\b`, 'g');
            highlighted = highlighted.replace(regex, `<span class="keyword">${kw}</span>`);
        });
        
        // Highlight comments
        highlighted = highlighted.replace(/#(.*)$/gm, '<span class="comment">#$1</span>');
        
        element.innerHTML = highlighted;
    }
}

// Initialize analyzer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const analyzer = new PybitAnalyzer();
    
    // Add toggle functionality for EXE code
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('toggle-code')) {
            const index = e.target.getAttribute('data-index');
            const codeElement = document.getElementById(`exe-code-${index}`);
            codeElement.style.display = codeElement.style.display === 'none' ? 'block' : 'none';
        }
    });
});
