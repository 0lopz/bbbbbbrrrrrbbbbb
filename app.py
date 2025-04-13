import os
import subprocess
import yara
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import pefile
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load YARA rules
yara_rules = {
    'python': yara.compile('analysis_tools/yara_rules/python_grabbers.yar'),
    'discord': yara.compile('analysis_tools/yara_rules/discord_rats.yar')
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Perform analysis
        result = {
            'filename': filename,
            'size': os.path.getsize(filepath),
            'analysis': perform_analysis(filepath)
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)

def perform_analysis(filepath):
    """Run various analysis tools on the executable"""
    analysis = {
        'type': 'Unknown',
        'detection': [],
        'risk': 'medium',
        'strings': extract_strings(filepath),
        'urls': [],
        'deobfuscated': None
    }
    
    # Check if it's a PE file
    try:
        pe = pefile.PE(filepath)
        analysis['pe_info'] = {
            'entry_point': pe.OPTIONAL_HEADER.AddressOfEntryPoint,
            'sections': [section.Name.decode().strip('\x00') for section in pe.sections]
        }
    except:
        analysis['pe_info'] = None
    
    # Run YARA rules
    matches = []
    for category, rule in yara_rules.items():
        matches.extend(rule.match(filepath))
    
    if matches:
        analysis['detection'] = [str(m) for m in matches]
        
        # Determine type based on YARA matches
        if any('Python' in m.rule for m in matches):
            analysis['type'] = 'Python-based'
            if any('Grabber' in m.rule for m in matches):
                analysis['type'] += ' Grabber'
                analysis['risk'] = 'high'
            if any('Discord' in m.rule for m in matches):
                analysis['type'] += ' Discord RAT'
                analysis['risk'] = 'critical'
    
    # Extract URLs
    urls = set()
    with open(filepath, 'rb') as f:
        data = f.read()
        # Simple URL regex (would need more sophisticated in production)
        found_urls = re.findall(b'https?://[^\s\x00-\x1f\x7f-\xff]+', data)
        for url in found_urls:
            try:
                urls.add(url.decode('ascii', errors='ignore').split('"')[0].split("'")[0])
            except:
                continue
    
    analysis['urls'] = list(urls)
    
    # Try to deobfuscate Python executables
    if 'Python' in analysis['type']:
        analysis['deobfuscated'] = attempt_deobfuscation(filepath)
    
    return analysis

def extract_strings(filepath, min_length=4):
    """Extract human-readable strings from binary"""
    try:
        result = subprocess.run(
            ['strings', '-n', str(min_length), filepath],
            capture_output=True, text=True
        )
        return result.stdout.splitlines()
    except:
        return ["Failed to extract strings"]

def attempt_deobfuscation(filepath):
    """Try to deobfuscate Python executables"""
    try:
        # First try to extract Python bytecode
        result = subprocess.run(
            ['python', 'analysis_tools/scripts/extract_strings.py', filepath],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return result.stdout
        
        # Fallback to generic deobfuscation
        result = subprocess.run(
            ['python', 'analysis_tools/scripts/deobfuscate.py', filepath],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else "Deobfuscation failed"
    except Exception as e:
        return f"Deobfuscation error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)