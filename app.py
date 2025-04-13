import os
import subprocess
import re
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('temp_extraction', exist_ok=True)

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
        result = analyze_executable(filepath)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

def analyze_executable(filepath):
    """Main analysis function with pycdc integration"""
    result = {
        'filename': os.path.basename(filepath),
        'size': os.path.getsize(filepath),
        'is_python': False,
        'analysis': {
            'strings': [],
            'urls': [],
            'commands': [],
            'behavior': [],
            'decompiled': None,
            'extracted_files': [],
            'warnings': []
        }
    }

    # Check if PyInstaller executable
    if is_pyinstaller_exe(filepath):
        result['is_python'] = True
        extract_pyinstaller(filepath, result)
        decompile_pyc_files(result)  # This is where pycdc gets called
    
    # Always perform these analyses
    extract_strings(filepath, result)
    find_urls_and_commands(result)
    
    return result

def is_pyinstaller_exe(filepath):
    """Check for PyInstaller signature"""
    try:
        output = subprocess.run(['strings', filepath], 
                              capture_output=True, text=True)
        return 'PyInstaller' in output.stdout
    except Exception as e:
        return False

def extract_pyinstaller(filepath, result):
    """Use pyinstxtractor to unpack the executable"""
    try:
        temp_dir = 'temp_extraction'
        subprocess.run(
            ['python', 'tools/pyinstxtractor.py', filepath, '-o', temp_dir],
            check=True,
            timeout=120,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Record extracted files
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(('.pyc', '.py', '.dll', '.pyd', '.json')):
                    rel_path = os.path.join(root, file)
                    result['analysis']['extracted_files'].append(rel_path)
                    
    except subprocess.TimeoutExpired:
        result['analysis']['warnings'].append("Extraction timed out")
    except Exception as e:
        result['analysis']['warnings'].append(f"Extraction failed: {str(e)}")

def decompile_pyc_files(result):
    """Decompile using pycdc with improved error handling"""
    for file in result['analysis']['extracted_files']:
        if not file.endswith('.pyc'):
            continue
            
        try:
            # Windows
            output = subprocess.run(
                ['tools\\pycdc.exe', file],
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            # Linux/macOS alternative:
            # output = subprocess.run(
            #     ['tools/pycdc', file],
            #     capture_output=True,
            #     text=True,
            #     timeout=60
            # )
            
            if output.returncode == 0 and output.stdout.strip():
                result['analysis']['decompiled'] = output.stdout[:10000]  # Limit size
                break
                
        except subprocess.TimeoutExpired:
            result['analysis']['warnings'].append(f"Decompilation timed out for {file}")
        except Exception as e:
            result['analysis']['warnings'].append(f"Failed to decompile {file}: {str(e)}")

def extract_strings(filepath, result, min_length=8):
    """Extract strings from binary with improved filtering"""
    try:
        output = subprocess.run(
            ['strings', '-n', str(min_length), filepath],
            capture_output=True, 
            text=True
        )
        if output.returncode == 0:
            # Filter out common binary strings
            result['analysis']['strings'] = [
                s for s in output.stdout.splitlines() 
                if not re.match(r'^[\d\W_]+$', s)
            ][:2000]  # Limit to 2000 strings
    except Exception as e:
        result['analysis']['warnings'].append(f"Strings extraction failed: {str(e)}")

def find_urls_and_commands(result):
    """Enhanced pattern matching for IOCs"""
    url_pattern = re.compile(
        r'https?://[^\s\x00-\x1f\x7f-\xff]+|'
        r'[a-zA-Z0-9.-]+\.(com|net|org|io|ru|xyz|tk|pw|cc|top|cn|info|biz|online|shop|site|club|fun|me|tv|co|uk|de|fr|ga|gq|ml|cf)[^\s\x00-\x1f\x7f-\xff]*',
        re.IGNORECASE
    )
    
    cmd_pattern = re.compile(
        r'(subprocess\.(run|call|Popen|check_output)|'
        r'(os\.(system|popen|exec|spawn))|'
        r'(WinExec|ShellExecute|CreateProcess)|'
        r'(reg\s+(add|delete|copy|export))',
        re.IGNORECASE
    )
    
    suspicious_patterns = [
        ('keylog', 'Keylogging'),
        ('inject', 'Process injection'),
        ('persist', 'Persistence mechanism'),
        ('webcam', 'Webcam capture'),
        ('screenshot', 'Screen capture'),
        ('clipboard', 'Clipboard monitoring'),
        ('token', 'Credential theft'),
        ('wallet', 'Cryptocurrency theft'),
        ('ransom', 'Ransomware behavior'),
        ('bypass', 'Anti-analysis')
    ]
    
    # Search in strings
    for s in result['analysis']['strings']:
        # URLs
        result['analysis']['urls'].extend(
            url[0] for url in url_pattern.findall(s)
            if not any(d in url[0] for d in ['localhost', 'example.com', '127.0.0.1'])
        )
        
        # Commands
        if cmd_pattern.search(s):
            result['analysis']['commands'].append(s[:300])  # Truncate long strings
            
        # Behaviors
        for pattern, desc in suspicious_patterns:
            if re.search(pattern, s, re.IGNORECASE):
                result['analysis']['behavior'].append(f"{desc}: {s[:300]}")
    
    # Search in decompiled code
    if result['analysis']['decompiled']:
        decompiled = result['analysis']['decompiled']
        result['analysis']['urls'].extend(url_pattern.findall(decompiled))
        result['analysis']['commands'].extend(
            cmd_pattern.findall(decompiled))
        result['analysis']['behavior'].extend(
            f"{desc}: {match}" 
            for pattern, desc in suspicious_patterns 
            for match in re.findall(pattern, decompiled, re.IGNORECASE)
        )
    
    # Deduplicate and clean results
    result['analysis']['urls'] = sorted(list(set(
        url if url.startswith(('http://', 'https://')) else f'http://{url}'
        for url in result['analysis']['urls']
        if len(url) > 8
    )))[:100]
    
    result['analysis']['commands'] = sorted(list(set(
        cmd for cmd in result['analysis']['commands'] 
        if len(cmd) > 10
    )))[:100]
    
    result['analysis']['behavior'] = sorted(list(set(
        result['analysis']['behavior']
    )))[:100]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)