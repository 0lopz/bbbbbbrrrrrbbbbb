import os
import sys
import struct
import marshal
import zlib
import tempfile
import subprocess
from pathlib import Path

class PyBitDecompiler:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pybit_")
        self.pyinstxtractor_path = os.path.join(os.path.dirname(__file__), "pyinstxtractor.py")
        
    def analyze_file(self, file_path):
        """Main analysis entry point"""
        file_type = self.detect_file_type(file_path)
        
        if file_type == 'py':
            return self.analyze_py(file_path)
        elif file_type == 'pyc':
            return self.analyze_pyc(file_path)
        elif file_type == 'exe':
            return self.analyze_exe(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def detect_file_type(self, file_path):
        """Detect file type by magic numbers"""
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            
        if magic.startswith(b'MZ'):
            return 'exe'
        elif magic.startswith(b'\x03\xf3\x0d\x0a') or magic.startswith(b'\xee\x0c\x0d\x0a'):
            return 'pyc'
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if 'python' in first_line.lower():
                        return 'py'
            except:
                pass
        return 'unknown'

    def analyze_exe(self, file_path):
        """Analyze executable for embedded Python"""
        result = {
            'file_name': os.path.basename(file_path),
            'file_type': 'exe',
            'python_embedded': False,
            'compiler': None,
            'extracted_files': [],
            'decompiled_code': []
        }
        
        # Check for PyInstaller
        if self.is_pyinstaller(file_path):
            result['python_embedded'] = True
            result['compiler'] = 'PyInstaller'
            extracted = self.extract_pyinstaller(file_path)
            for extracted_file in extracted:
                decompiled = self.analyze_pyc(extracted_file)
                result['extracted_files'].append({
                    'name': os.path.basename(extracted_file),
                    'type': 'pyc',
                    'path': extracted_file
                })
                result['decompiled_code'].append(decompiled['decompiled'])
        
        # Check for py2exe
        elif self.is_py2exe(file_path):
            result['python_embedded'] = True
            result['compiler'] = 'py2exe'
            extracted = self.extract_py2exe(file_path)
            for extracted_file in extracted:
                decompiled = self.analyze_pyc(extracted_file)
                result['extracted_files'].append({
                    'name': os.path.basename(extracted_file),
                    'type': 'pyc',
                    'path': extracted_file
                })
                result['decompiled_code'].append(decompiled['decompiled'])
        
        return result

    def extract_pyinstaller(self, exe_path):
        """Extract files using pyinstxtractor"""
        output_dir = os.path.join(self.temp_dir, "extracted")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            subprocess.run([
                sys.executable,
                self.pyinstxtractor_path,
                exe_path,
                "--output",
                output_dir
            ], check=True)
            
            extracted_files = []
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.pyc'):
                        extracted_files.append(os.path.join(root, file))
            
            return extracted_files
        except subprocess.CalledProcessError:
            return []

    # [Rest of the methods from previous implementation]

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)