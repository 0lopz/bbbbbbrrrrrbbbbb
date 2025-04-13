import re
import base64
import json
import pefile
import zipfile
import io
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import flask
from flask import Flask, request, render_template, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

class RattersRipAnalyzer:
    def __init__(self):
        # Load detection patterns
        self.patterns = {
            "SUSPICIOUS_CONSTANTS": ["WEBHOOK_URL", "webhook", "discord.com/api/webhooks"],
            "SUSPICIOUS_FUNCTIONS": ["injection", "Inject", "get_passwords", "get_system_info", "grabber", "grabTokens"],
            "SUSPICIOUS_KEYWORDS": ["eval", "exec", "subprocess", "os.system", "import socket", "import requests"],
            "SUSPICIOUS_REG_KEYS": [
                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            ],
            "MALICIOUS_REGISTRY_KEYS": [
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\\DisableTaskMgr",
                "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\"
            ]
        }
        
        self.browser_paths = {
            "paths": {
                "Discord": "AppData\\Roaming\\discord",
                "Chrome": "AppData\\Local\\Google\\Chrome\\User Data\\Default",
                "Firefox": "AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
            },
            "suspicious_directories": [
                "\\Google\\Chrome\\User Data", 
                "\\Discord", 
                "\\Mozilla\\Firefox\\Profiles"
            ]
        }
        
        self.detections = []
        self.webhooks = []
        self.iocs = {
            'urls': [],
            'ips': [],
            'hashes': {
                'md5': '',
                'sha1': '',
                'sha256': ''
            }
        }
    
    def analyze_file(self, file_path: str) -> Dict:
        """Main analysis function"""
        self.detections = []
        self.webhooks = []
        
        # Calculate file hashes
        self._calculate_hashes(file_path)
        
        # Check file type and analyze accordingly
        if file_path.endswith('.exe'):
            self._analyze_pe(file_path)
        elif file_path.endswith('.py') or file_path.endswith('.pyc'):
            self._analyze_python(file_path)
        else:
            self._analyze_generic(file_path)
        
        # Check for packed/obfuscated code
        self._check_obfuscation(file_path)
        
        return {
            'detections': self.detections,
            'webhooks': self.webhooks,
            'iocs': self.iocs,
            'score': self._calculate_malicious_score()
        }
    
    def _calculate_hashes(self, file_path: str) -> None:
        """Calculate file hashes for IOCs"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        self.iocs['hashes']['md5'] = hashlib.md5(data).hexdigest()
        self.iocs['hashes']['sha1'] = hashlib.sha1(data).hexdigest()
        self.iocs['hashes']['sha256'] = hashlib.sha256(data).hexdigest()
    
    def _analyze_pe(self, file_path: str) -> None:
        """Analyze PE (Windows executable) files"""
        try:
            pe = pefile.PE(file_path)
            
            # Check sections for suspicious names
            for section in pe.sections:
                section_name = section.Name.decode('utf-8', 'ignore').strip('\x00')
                if any(s in section_name.lower() for s in ['packed', 'encrypt', 'hidden']):
                    self._add_detection(
                        "Packed/Encrypted Section Found",
                        f"PE section '{section_name}' suggests the file may be packed or encrypted",
                        "warning"
                    )
            
            # Check imports for suspicious functions
            suspicious_imports = set()
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in entry.imports:
                    imp_name = imp.name.decode('utf-8') if imp.name else ''
                    if any(f.lower() in imp_name.lower() for f in self.patterns['SUSPICIOUS_FUNCTIONS']):
                        suspicious_imports.add(imp_name)
            
            if suspicious_imports:
                self._add_detection(
                    "Suspicious Imports Found",
                    f"The following suspicious imports were found: {', '.join(suspicious_imports)}",
                    "critical"
                )
            
            # Check for registry operations in strings
            self._scan_for_registry_operations(pe)
            
        except Exception as e:
            self._add_detection(
                "PE Analysis Error",
                f"Failed to analyze PE file: {str(e)}",
                "info"
            )
        
        # Always scan for strings
        self._scan_file_strings(file_path)
    
    def _analyze_python(self, file_path: str) -> None:
        """Analyze Python files (both .py and compiled .pyc)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for suspicious Python keywords
                found_keywords = []
                for keyword in self.patterns['SUSPICIOUS_KEYWORDS']:
                    if keyword in content:
                        found_keywords.append(keyword)
                
                if found_keywords:
                    self._add_detection(
                        "Suspicious Python Code Found",
                        f"The following suspicious Python constructs were found: {', '.join(found_keywords)}",
                        "critical"
                    )
                
                # Check for webhooks
                self._find_webhooks(content)
                
                # Check for obfuscation
                if any(obf in content for obf in ['eval(', 'exec(', 'base64.b64decode(']):
                    self._add_detection(
                        "Possible Python Obfuscation",
                        "The script contains potential obfuscation techniques (eval, exec, base64)",
                        "warning"
                    )
                
                # Check for stealer-specific patterns
                if any(pattern in content for pattern in ['grabber', 'stealer', 'token', 'password']):
                    self._add_detection(
                        "Possible Stealer Behavior",
                        "The script contains patterns associated with credential stealers",
                        "critical"
                    )
                
        except UnicodeDecodeError:
            # Might be compiled Python, try strings analysis
            self._scan_file_strings(file_path)
    
    def _analyze_generic(self, file_path: str) -> None:
        """Generic analysis for other file types"""
        # Check if it's a zip file (e.g., PyInstaller bundle)
        if zipfile.is_zipfile(file_path):
            self._analyze_zip(file_path)
        else:
            # Fall back to strings analysis
            self._scan_file_strings(file_path)
    
    def _analyze_zip(self, file_path: str) -> None:
        """Analyze zip files (e.g., PyInstaller bundles)"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    # Check for common Python bundled files
                    if file.endswith('.pyz') or file.endswith('.pyc'):
                        self._add_detection(
                            "Python Bundle Detected",
                            f"The file appears to be a bundled Python application containing: {file}",
                            "info"
                        )
                    
                    # Extract and check suspicious files
                    if any(s in file.lower() for s in ['inject', 'grabber', 'steal']):
                        self._add_detection(
                            "Suspicious File in Bundle",
                            f"The bundle contains a potentially malicious file: {file}",
                            "critical"
                        )
        except Exception as e:
            self._add_detection(
                "Zip Analysis Error",
                f"Failed to analyze zip file: {str(e)}",
                "info"
            )
    
    def _scan_file_strings(self, file_path: str) -> None:
        """Scan file for interesting strings"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                
                # Check for webhooks
                self._find_webhooks(content)
                
                # Check for suspicious constants
                for const in self.patterns['SUSPICIOUS_CONSTANTS']:
                    if const in content:
                        self._add_detection(
                            f"Suspicious Constant Found: {const}",
                            f"The file contains a potentially malicious constant: {const}",
                            "warning"
                        )
                
                # Check for registry operations
                self._scan_for_registry_operations(content)
                
                # Check for suspicious functions
                for func in self.patterns['SUSPICIOUS_FUNCTIONS']:
                    if func in content:
                        self._add_detection(
                            f"Suspicious Function Found: {func}",
                            f"The file contains a potentially malicious function reference: {func}",
                            "critical"
                        )
                
                # Check for browser paths (stealer behavior)
                for browser, path in self.browser_paths['paths'].items():
                    if path in content:
                        self._add_detection(
                            "Browser Path Found",
                            f"The file references {browser} data path: {path}",
                            "critical"
                        )
                
                # Check for suspicious directories
                for directory in self.browser_paths['suspicious_directories']:
                    if directory in content:
                        self._add_detection(
                            "Suspicious Directory Reference",
                            f"The file references a sensitive directory: {directory}",
                            "warning"
                        )
                
                # Extract potential URLs
                urls = re.findall(r'https?://[^\s\'"]+', content)
                for url in urls:
                    if 'discord.com/api/webhooks' in url:
                        self.webhooks.append(url)
                    else:
                        self.iocs['urls'].append(url)
                
                # Extract potential IP addresses
                ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
                self.iocs['ips'].extend(ips)
                
        except Exception as e:
            self._add_detection(
                "Strings Analysis Error",
                f"Failed to analyze file strings: {str(e)}",
                "info"
            )
    
    def _find_webhooks(self, content: str) -> None:
        """Find Discord webhooks in content"""
        webhook_patterns = [
            r'discord\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+',
            r'webhook_url\s*=\s*[\'"](https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+)[\'"]',
            r'https://discordapp\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+'
        ]
        
        for pattern in webhook_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in self.webhooks:
                    self.webhooks.append(match)
                    self._add_detection(
                        "Discord Webhook Found",
                        f"Found Discord webhook URL: {match}",
                        "critical"
                    )
    
    def _scan_for_registry_operations(self, content: str) -> None:
        """Scan for registry operations in content"""
        found_keys = []
        
        # Check both suspicious and malicious registry keys
        all_reg_keys = (self.patterns['SUSPICIOUS_REG_KEYS'] + 
                       self.patterns['MALICIOUS_REGISTRY_KEYS'])
        
        for key in all_reg_keys:
            # Clean the key for regex (escape backslashes)
            regex_key = key.replace('\\', '\\\\')
            if re.search(regex_key, content):
                found_keys.append(key)
        
        if found_keys:
            self._add_detection(
                "Registry Operations Detected",
                f"The following registry keys are referenced:\n{'\n'.join(found_keys)}",
                "critical" if any(k in self.patterns['MALICIOUS_REGISTRY_KEYS'] for k in found_keys) else "warning"
            )
    
    def _check_obfuscation(self, file_path: str) -> None:
        """Check for signs of obfuscation"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                
                # Check for common obfuscation patterns
                obfuscation_patterns = [
                    r'eval\(.*\)',
                    r'exec\(.*\)',
                    r'base64\.b64decode\(.*\)',
                    r'[a-zA-Z0-9]{20,}',  # Very long alphanumeric strings
                    r'\\x[0-9a-fA-F]{2}',  # Hex escapes
                    r'[\x80-\xFF]'         # High ASCII characters
                ]
                
                found_patterns = []
                for pattern in obfuscation_patterns:
                    if re.search(pattern, content):
                        found_patterns.append(pattern)
                
                if found_patterns:
                    self._add_detection(
                        "Possible Obfuscation Detected",
                        f"The file shows signs of obfuscation with patterns: {', '.join(found_patterns)}",
                        "warning"
                    )
        except:
            pass
    
    def _add_detection(self, title: str, description: str, severity: str) -> None:
        """Add a detection to the results"""
        self.detections.append({
            'title': title,
            'description': description,
            'severity': severity
        })
    
    def _calculate_malicious_score(self) -> int:
        """Calculate a maliciousness score based on findings"""
        score = 0
        
        for detection in self.detections:
            if detection['severity'] == 'critical':
                score += 30
            elif detection['severity'] == 'warning':
                score += 15
            else:
                score += 5
        
        # Add points for webhooks
        score += len(self.webhooks) * 20
        
        # Cap at 100
        return min(100, score)
    
    def deobfuscate_python(self, code: str) -> str:
        """Attempt to deobfuscate Python code"""
        try:
            # Simple base64 decode if found
            b64_matches = re.findall(r'base64\.b64decode\(([\'"])([a-zA-Z0-9+/=]+)\1\)', code)
            for quote, b64_str in b64_matches:
                try:
                    decoded = base64.b64decode(b64_str).decode('utf-8')
                    self._add_detection(
                        "Base64 Decoded",
                        f"Decoded base64 string: {decoded[:100]}...",
                        "info"
                    )
                    code = code.replace(f'base64.b64decode({quote}{b64_str}{quote})', f'"""DECODED: {decoded}"""')
                except:
                    pass
            
            # Simple hex decode if found
            hex_matches = re.findall(r'\\x[0-9a-fA-F]{2}', code)
            if hex_matches:
                try:
                    decoded = bytes.fromhex(code.replace(r'\x', '')).decode('utf-8')
                    self._add_detection(
                        "Hex Decoded",
                        f"Decoded hex string: {decoded[:100]}...",
                        "info"
                    )
                    code += f'\n\n"""DECODED HEX: {decoded}"""'
                except:
                    pass
            
            return code
        except Exception as e:
            self._add_detection(
                "Deobfuscation Error",
                f"Failed to deobfuscate code: {str(e)}",
                "info"
            )
            return code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    
    # Analyze the file
    analyzer = RattersRipAnalyzer()
    results = analyzer.analyze_file(file_path)
    
    # Clean up
    os.remove(file_path)
    os.rmdir(temp_dir)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)