class MalwareAnalyzer {
    constructor() {
        // Conservative 35MB limit (15MB buffer under backend's 45MB)
        this.maxFileSize = 35 * 1024 * 1024;
        this.supportedTypes = ['.py', '.pyc', '.pyz', '.exe'];
        this.abortController = null;
        
        console.log('Initialized with:', {
            maxSize: `${this.maxFileSize/1024/1024}MB`,
            types: this.supportedTypes
        });

        this.initEventListeners();
    }

    async processFile(file) {
        try {
            // 1. EXTREME size validation
            if (file.size > this.maxFileSize) {
                throw new Error(
                    `🚨 FILE TOO LARGE (${(file.size/1024/1024).toFixed(1)}MB)\n` +
                    `• Our limit: ${this.maxFileSize/1024/1024}MB\n` +
                    `• Vercel's max: 50MB\n` +
                    `• Try smaller files!`
                );
            }

            // 2. Validate file type
            if (!this.isValidFile(file)) {
                throw new Error(`Unsupported file type. We accept: ${this.supportedTypes.join(', ')}`);
            }

            this.showProgress('Uploading...', 0);
            this.abortController = new AbortController();

            // 3. Upload with timeout
            const results = await Promise.race([
                this.uploadFile(file),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Server took too long to respond')), 30000)
                )
            ]);
            
            this.displayResults(results);
            this.showSuccess('Analysis complete!');
        } catch (error) {
            this.showError(
                error.message.includes('Failed to fetch') 
                    ? '🌐 Connection failed - check your network'
                    : error.message
            );
            console.error('ANALYZER ERROR:', error);
        } finally {
            this.hideProgress();
            this.abortController = null;
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
            signal: this.abortController?.signal,
            headers: {
                'X-Filename': encodeURIComponent(file.name),
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || `Server error (${response.status})`);
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
                <div class="error">
                    <strong>Error:</strong> ${this.escapeHtml(message)}
                </div>
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

document.addEventListener('DOMContentLoaded', () => {
    // File name display
    document.getElementById('fileInput').addEventListener('change', function(e) {
        document.getElementById('fileName').textContent = 
            e.target.files[0]?.name || 'No file chosen';
    });

    new MalwareAnalyzer();
});