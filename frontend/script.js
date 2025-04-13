class MalwareAnalyzer {
    constructor() {
        // Dynamic API endpoint configuration
        this.apiEndpoint = window.location.hostname.includes('localhost') 
            ? 'http://localhost:3000/api/analyze'
            : '/api/analyze';
        
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.supportedTypes = ['.py', '.pyc', '.pyz', '.exe'];
        this.abortController = null;
        
        console.log('API Endpoint:', this.apiEndpoint); // Debugging
        this.initEventListeners();
    }

    initEventListeners() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const cancelBtn = document.getElementById('cancelBtn');

        // Click handler
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag and drop setup
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

        // Event handlers
        dropZone.addEventListener('drop', e => this.handleDrop(e), false);
        fileInput.addEventListener('change', e => this.handleFileSelect(e));
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cancelUpload());
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
        const files = e.dataTransfer.files;
        if (files.length > 0) await this.processFile(files[0]);
    }

    async handleFileSelect(e) {
        if (e.target.files.length > 0) {
            await this.processFile(e.target.files[0]);
            e.target.value = ''; // Reset input
        }
    }

    async processFile(file) {
        try {
            // Validation
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. Allowed: ${this.supportedTypes.join(', ')}`);
            }

            if (file.size > this.maxFileSize) {
                throw new Error(`File too large (max ${this.maxFileSize/1024/1024}MB)`);
            }

            this.showProgress('Uploading...', 0);
            this.abortController = new AbortController();

            // Add timeout (30 seconds)
            const timeoutId = setTimeout(() => {
                this.abortController.abort();
            }, 30000);

            const results = await this.uploadFile(file);
            clearTimeout(timeoutId);

            if (results?.error) {
                throw new Error(results.error);
            }

            this.displayResults(results);
            this.showSuccess('Analysis complete!');
        } catch (error) {
            if (error.name !== 'AbortError') {
                const friendlyError = error.message.includes('Failed to fetch')
                    ? 'Server connection failed. Please try again.'
                    : error.message;
                this.showError(friendlyError);
                console.error('Analysis error:', error);
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
                throw new Error(error || `Server error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Network error: ${error.message}`);
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
            const cancelBtn = document.getElementById('cancelBtn');
            
            if (progressText) progressText.textContent = message;
            if (progressBar) progressBar.value = percent;
            if (cancelBtn) cancelBtn.style.display = 'block';
        }
    }

    hideProgress() {
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
            const progressBar = document.getElementById('progressBar');
            const cancelBtn = document.getElementById('cancelBtn');
            
            if (progressBar) progressBar.value = 0;
            if (cancelBtn) cancelBtn.style.display = 'none';
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
        if (!unsafe) return '';
        return unsafe.toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize when ready
document.addEventListener('DOMContentLoaded', () => {
    new MalwareAnalyzer();
});