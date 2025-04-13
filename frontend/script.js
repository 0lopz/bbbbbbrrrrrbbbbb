class MalwareAnalyzer {
    constructor() {
        this.apiEndpoint = '/api/analyze';
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
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

        dropZone.addEventListener('drop', e => this.handleDrop(e), false);
        fileInput.addEventListener('change', e => this.handleFileSelect(e));
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
            // Validate file
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. Supported: ${this.supportedTypes.join(', ')}`);
            }

            if (file.size > this.maxFileSize) {
                throw new Error(`File too large (max ${this.maxFileSize/1024/1024}MB)`);
            }

            this.showProgress('Analyzing...', 50);
            const results = await this.uploadFile(file);
            
            if (results.error) {
                throw new Error(results.error);
            }

            this.displayResults(results);
            this.showSuccess('Analysis complete!');
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideProgress();
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                body: formData,
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
        const progress = document.querySelector('.progress-container');
        progress.style.display = 'block';
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressBar').value = percent;
    }

    hideProgress() {
        document.querySelector('.progress-container').style.display = 'none';
    }

    showError(message) {
        document.getElementById('results').innerHTML = `
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
        document.getElementById('results').innerHTML = `
            <h3>Analysis Results</h3>
            <pre>${this.escapeHtml(JSON.stringify(results, null, 2))}</pre>
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new MalwareAnalyzer();
});