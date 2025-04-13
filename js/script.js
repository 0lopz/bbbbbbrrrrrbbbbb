document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const analysisSection = document.getElementById('analysisSection');
    
    // Tab switching functionality
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            const tabId = tab.getAttribute('data-tab') + 'Tab';
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Drag and drop functionality
    dropZone.addEventListener('click', () => fileInput.click());
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            handleFiles(files);
        }
    }
    
    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });
    
    function handleFiles(files) {
        const file = files[0];
        
        // Display file info
        document.getElementById('fileName').textContent = `File: ${file.name}`;
        document.getElementById('fileSize').textContent = `Size: ${formatFileSize(file.size)}`;
        
        // Show loading state
        document.getElementById('malwareType').textContent = 'Analyzing...';
        document.getElementById('detection').textContent = 'Running detection...';
        document.getElementById('summaryText').textContent = 'Please wait while we analyze the file...';
        document.getElementById('riskLevel').textContent = 'Analyzing';
        document.getElementById('riskLevel').className = 'risk-level loading';
        
        // Show analysis section
        analysisSection.classList.remove('hidden');
        
        // Scroll to analysis section
        analysisSection.scrollIntoView({ behavior: 'smooth' });
        
        // Upload and analyze the file
        uploadAndAnalyze(file);
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function uploadAndAnalyze(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Analysis failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayAnalysisResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('malwareType').textContent = 'Analysis Error';
            document.getElementById('detection').textContent = 'Failed to analyze file';
            document.getElementById('summaryText').textContent = error.message;
            document.getElementById('riskLevel').textContent = 'Error';
            document.getElementById('riskLevel').className = 'risk-level';
        });
    }
    
    function displayAnalysisResults(data) {
        const analysis = data.analysis;
        
        // Update basic info
        document.getElementById('malwareType').textContent = analysis.type || 'Unknown';
        document.getElementById('detection').textContent = 
            analysis.detection.length > 0 ? analysis.detection.join(', ') : 'No detection';
        
        // Set risk level
        const risk = analysis.risk || 'medium';
        document.getElementById('riskLevel').textContent = risk.charAt(0).toUpperCase() + risk.slice(1);
        document.getElementById('riskLevel').className = `risk-level ${risk}`;
        
        // Generate summary
        let summary = `This file appears to be ${analysis.type.toLowerCase() || 'an unknown executable'}. `;
        
        if (analysis.detection.length > 0) {
            summary += `Detected as: ${analysis.detection.join(', ')}. `;
        }
        
        if (analysis.urls.length > 0) {
            summary += `Found ${analysis.urls.length} potential URLs. `;
        }
        
        if (analysis.pe_info) {
            summary += `PE file with ${analysis.pe_info.sections.length} sections. `;
        }
        
        document.getElementById('summaryText').textContent = summary;
        
        // Update strings tab
        const stringsContent = document.getElementById('stringsContent');
        stringsContent.textContent = analysis.strings.slice(0, 200).join('\n');
        if (analysis.strings.length > 200) {
            stringsContent.textContent += `\n...and ${analysis.strings.length - 200} more`;
        }
        
        // Update URLs tab
        const urlList = document.getElementById('urlList');
        urlList.innerHTML = '';
        analysis.urls.slice(0, 50).forEach(url => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = url;
            a.textContent = url;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            li.appendChild(a);
            urlList.appendChild(li);
        });
        
        // Update deobfuscated tab
        document.getElementById('deobfuscatedContent').textContent = 
            analysis.deobfuscated || 'No deobfuscated code available';
    }
});