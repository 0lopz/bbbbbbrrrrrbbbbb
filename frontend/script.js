class MalwareAnalyzer {
    constructor() {
        this.apiEndpoint = '/api/analyze';
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.abortController = null;
        this.supportedTypes = ['.py', '.pyc', '.pyz', '.exe'];
        this.initEventListeners();
    }

    initEventListeners() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

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
            e.target.value = ''; // Reset input to allow same file re-upload
        }
    }

    async processFile(file) {
        try {
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. Allowed: ${this.supportedTypes.join(', ')}`);
            }

            if (file.size > this.maxFileSize) {
                throw new Error(`File too large. Max size: ${this.maxFileSize/1024/1024}MB`);
            }

            this.showProgress('Uploading file...', 0);
            this.abortController = new AbortController();

            const results = await this.uploadFile(file);
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

        const response = await fetch(this.apiEndpoint, {
            method: 'POST',
            body: formData,
            signal: this.abortController?.signal,
            headers: {
                'X-Filename': encodeURIComponent(file.name)
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }

        return await response.json();
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
    }

    hideProgress() {
        document.querySelector('.progress-container').style.display = 'none';
        document.getElementById('progressBar').value = 0;
    }

    showError(message) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <div class="error">Error: ${this.escapeHtml(message)}</div>
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
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const analyzer = new MalwareAnalyzer();
    
    // Add cancel button functionality
    document.body.addEventListener('click', (e) => {
        if (e.target.classList.contains('cancel-btn')) {
            analyzer.abortController?.abort();
        }
    });
});