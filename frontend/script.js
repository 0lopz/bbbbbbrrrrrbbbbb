class MalwareAnalyzer {
    constructor() {
        this.apiEndpoint = '/api/analyze';
        this.maxFileSize = 50 * 1024 * 1024; // 50MB limit
        this.supportedTypes = ['.py', '.pyc', '.pyz', '.exe'];
        this.abortController = null;
        this.initEventListeners();
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
        cancelBtn?.addEventListener('click', this.cancelUpload.bind(this));
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
            e.target.value = ''; // Reset input
        }
    }

    async processFile(file) {
        try {
            // Validate file
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. Allowed: ${this.supportedTypes.join(', ')}`);
            }

            if (file.size > this.maxFileSize) {
                throw new Error(`File too large. Max size: ${this.maxFileSize/1024/1024}MB`);
            }

            this.showProgress('Uploading file...', 0);
            this.abortController = new AbortController();

            const results = await this.uploadFile(file);
            
            if (results.error) {
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
                    'X-Filename': encodeURIComponent(file.name)
                }
            });

            // Handle both JSON and text responses
            const textData = await response.text();
            try {
                return JSON.parse(textData);
            } catch {
                throw new Error(textData || 'Invalid server response');
            }
        } catch (error) {
            throw new Error(`Upload failed: ${error.message}`);
        }
    }

    isValidFile(file) {
        return this.supportedTypes.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        );
    }

    showProgress(message, percent) {
        const progressContainer = document.querySelector('.progress-container');
        progressContainer.style.display = 'block';
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressBar').value = percent;
        
        // Show cancel button
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
    }

    hideProgress() {
        document.querySelector('.progress-container').style.display = 'none';
        document.getElementById('progressBar').value = 0;
        
        // Hide cancel button
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) cancelBtn.style.display = 'none';
    }

    showError(message) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <div class="error">${this.escapeHtml(message)}</div>
        `;
    }

    showSuccess(message) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML += `
            <div class="success">${this.escapeHtml(message)}</div>
        `;
    }

    displayResults(results) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h3>Analysis Results</h3>
            <div class="results-container">
                <pre>${this.escapeHtml(JSON.stringify(results, null, 2))}</pre>
            </div>
        `;
    }

    escapeHtml(unsafe) {
        return unsafe.toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MalwareAnalyzer();
});