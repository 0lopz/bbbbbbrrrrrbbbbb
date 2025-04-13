class MalwareAnalyzer {
    constructor() {
        // Dynamic API endpoint detection for Vercel
        this.apiEndpoint = window.location.hostname.includes('vercel.app') 
            ? '/api/analyze' 
            : 'http://localhost:3000/api/analyze';
        
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.supportedTypes = ['.py', '.pyc', '.pyz', '.exe'];
        this.abortController = null;
        this.initEventListeners();
        
        // Debug output
        console.log('API Endpoint:', this.apiEndpoint);
    }

    initEventListeners() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const cancelBtn = document.getElementById('cancelBtn');

        // Click handler
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag and drop handlers
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.highlightArea, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.unhighlightArea, false);
        });

        dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', this.cancelUpload.bind(this));
        }
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlightArea() {
        document.getElementById('dropZone').classList.add('highlight');
    }

    unhighlightArea() {
        document.getElementById('dropZone').classList.remove('highlight');
    }

    cancelUpload() {
        if (this.abortController) {
            this.abortController.abort();
            this.showError('Upload cancelled');
            this.hideProgress();
        }
    }

    async handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            await this.processFile(files[0]);
        }
    }

    async handleFileSelect(e) {
        if (e.target.files.length > 0) {
            await this.processFile(e.target.files[0]);
            e.target.value = '';
        }
    }

    async processFile(file) {
        try {
            // Validate file
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. Supported: ${this.supportedTypes.join(', ')}`);
            }

            if (file.size > this.maxFileSize) {
                throw new Error(`File too large. Max size: ${this.maxFileSize/1024/1024}MB`);
            }

            this.showProgress('Uploading file...', 0);
            this.abortController = new AbortController();

            const results = await this.uploadFile(file);
            
            if (results?.error) {
                throw new Error(results.error);
            }

            this.displayResults(results);
            this.showSuccess('Analysis complete!');
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Analysis error:', error);
                this.showError(error.message);
            }
        } finally {
            this.hideProgress();
            this.abortController = null;
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                body: formData,
                signal: this.abortController?.signal,
                headers: {
                    'X-Filename': encodeURIComponent(file.name),
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Server error');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Failed to connect to API: ${error.message}`);
        }
    }

    isValidFile(file) {
        return this.supportedTypes.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        );
    }

    showProgress(message, percent) {
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'block';
            const progressText = document.getElementById('progressText');
            const progressBar = document.getElementById('progressBar');
            if (progressText) progressText.textContent = message;
            if (progressBar) progressBar.value = percent;
        }
    }

    hideProgress() {
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
            const progressBar = document.getElementById('progressBar');
            if (progressBar) progressBar.value = 0;
        }
    }

    showError(message) {
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div class="error">${this.escapeHtml(message)}</div>
            `;
        }
    }

    showSuccess(message) {
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML += `
                <div class="success">${this.escapeHtml(message)}</div>
            `;
        }
    }

    displayResults(results) {
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <h3>Analysis Results</h3>
                <div class="results-container">
                    <pre>${this.escapeHtml(JSON.stringify(results, null, 2))}</pre>
                </div>
            `;
        }
    }

    escapeHtml(unsafe) {
        return unsafe?.toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;") || '';
    }
}

// Initialize when DOM is loadedd
document.addEventListener('DOMContentLoaded', () => {
    new MalwareAnalyzer();
});