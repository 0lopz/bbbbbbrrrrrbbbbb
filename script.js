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
        
        // Reset UI for new analysis
        resetAnalysisUI();
        
        // Display file info
        document.getElementById('fileName').textContent = `File: ${file.name}`;
        document.getElementById('fileSize').textContent = `Size: ${formatFileSize(file.size)}`;
        
        // Show loading state
        setLoadingState(true);
        
        // Show analysis section
        analysisSection.classList.remove('hidden');
        analysisSection.scrollIntoView({ behavior: 'smooth' });
        
        // Upload and analyze the file
        uploadAndAnalyze(file);
    }
    
    function resetAnalysisUI() {
        document.getElementById('malwareType').textContent = 'Analyzing...';
        document.getElementById('detection').textContent = 'Running detection...';
        document.getElementById('riskLevel').textContent = 'Analyzing';
        document.getElementById('riskLevel').className = 'risk-level loading';
        document.getElementById('summaryText').textContent = 'Please wait while we analyze the file...';
        document.getElementById('stringsContent').textContent = 'Extracting strings...';
        document.getElementById('urlList').innerHTML = '';
        document.getElementById('behaviorContent').textContent = 'Analyzing behavior...';
    }
    
    function setLoadingState(isLoading) {
        const elements = [
            'malwareType',
            'detection',
            'riskLevel',
            'summaryText',
            'stringsContent',
            'behaviorContent'
        ];
        
        elements.forEach(id => {
            const el = document.getElementById(id);
            if (isLoading) {
                el.classList.add('loading');
            } else {
                el.classList.remove('loading');
            }
        });
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
            setLoadingState(false);
        })
        .catch(error => {
            console.error('Error:', error);
            displayError(error.message);
            setLoadingState(false);
        });
    }
    
    function displayAnalysisResults(data) {
        // Basic info
        document.getElementById('fileName').textContent = `File: ${data.filename}`;
        document.getElementById('fileSize').textContent = `Size: ${formatFileSize(data.size)}`;
        
        // Analysis results
        document.getElementById('malwareType').textContent = 
            data.is_python ? 'Python Executable' : 'Unknown Executable';
        
        // Detection status
        let detectionStatus = 'No threats detected';
        if (data.analysis.urls.length > 0 || data.analysis.commands.length > 0) {
            detectionStatus = 'Suspicious activity found';
        }
        document.getElementById('detection').textContent = detectionStatus;
        
        // Risk assessment
        const riskLevel = calculateRiskLevel(data);
        const riskElement = document.getElementById('riskLevel');
        riskElement.textContent = riskLevel;
        riskElement.className = `risk-level ${riskLevel.toLowerCase()}`;
        
        // Summary
        let summaryParts = [];
        if (data.is_python) summaryParts.push('Python-packed executable');
        if (data.analysis.urls.length) summaryParts.push(`${data.analysis.urls.length} suspicious URLs`);
        if (data.analysis.commands.length) summaryParts.push(`${data.analysis.commands.length} dangerous commands`);
        
        document.getElementById('summaryText').textContent = 
            summaryParts.length ? summaryParts.join(' • ') : 'No obvious malicious indicators';
        
        // Strings
        document.getElementById('stringsContent').textContent = 
            data.analysis.strings.slice(0, 500).join('\n') || 'No strings extracted';
        
        // URLs
        const urlList = document.getElementById('urlList');
        urlList.innerHTML = '';
        if (data.analysis.urls.length > 0) {
            data.analysis.urls.slice(0, 50).forEach(url => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.textContent = url;
                a.onclick = (e) => {
                    e.preventDefault();
                    navigator.clipboard.writeText(url);
                    alert('URL copied to clipboard');
                };
                li.appendChild(a);
                urlList.appendChild(li);
            });
        } else {
            urlList.innerHTML = '<li>No URLs found</li>';
        }
        
        // Behavior
        const behaviorContent = document.getElementById('behaviorContent');
        if (data.analysis.behavior.length > 0) {
            behaviorContent.textContent = data.analysis.behavior.slice(0, 100).join('\n');
        } else {
            behaviorContent.textContent = 'No suspicious behavior detected';
        }
    }
    
    function calculateRiskLevel(data) {
        if (data.analysis.urls.length === 0 && data.analysis.commands.length === 0) {
            return 'Low';
        }
        
        const dangerSigns = [
            data.analysis.urls.length > 3,
            data.analysis.commands.length > 2,
            data.analysis.behavior.some(b => b.includes('keylog') || b.includes('inject'))
        ];
        
        return dangerSigns.filter(Boolean).length >= 2 ? 'High' : 'Medium';
    }
    
    function displayError(message) {
        document.getElementById('malwareType').textContent = 'Analysis Error';
        document.getElementById('detection').textContent = 'Failed to analyze';
        document.getElementById('riskLevel').textContent = 'Error';
        document.getElementById('riskLevel').className = 'risk-level';
        document.getElementById('summaryText').textContent = message;
        document.getElementById('stringsContent').textContent = 'Analysis failed';
        document.getElementById('urlList').innerHTML = '<li>Analysis failed</li>';
        document.getElementById('behaviorContent').textContent = 'Analysis failed';
    }
});