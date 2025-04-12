class MalwareAnalyzer {
    constructor() {
        this.apiEndpoint = '/api/analyze';
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.abortController = null;
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
            await this.analyzeFile(files[0]);
        }
    }

    async handleFileSelect(e) {
        if (e.target.files.length > 0) {
            await this.analyzeFile(e.target.files[0]);
        }
    }

    async analyzeFile(file) {
        if (!this.isValidFile(file)) {
            this.showError(`Unsupported file type. Allowed: ${this.getSupportedTypes()}`);
            return;
        }

        if (file.size > this.maxFileSize) {
            this.showError(`File too large. Max size: ${this.maxFileSize/1024/1024}MB`);
            return;
        }

        this.showProgress('Uploading file...', 0);
        this.abortController = new AbortController();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                body: formData,
                signal: this.abortController.signal,
                headers: {
                    'X-Filename': file.name
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Analysis failed');
            }

            const results = await response.json();
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

    isValidFile(file) {
        const validTypes = ['.py', '.pyc', '.pyz', '.exe'];
        return validTypes.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    getSupportedTypes() {
        return ['.py', '.pyc', '.pyz', '.exe'].join(', ');
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
            <div class="error">${message}</div>
        `;
    }

    showSuccess(message) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML += `
            <div class="success">${message}</div>
        `;
    }

    displayResults(results) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h3>Analysis Results</h3>
            <pre>${JSON.stringify(results, null, 2)}</pre>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MalwareAnalyzer();
});