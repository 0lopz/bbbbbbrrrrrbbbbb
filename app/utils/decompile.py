import os
import subprocess
import tempfile

def unzipJava(jarPath):
    try:
        temp_dir = tempfile.mkdtemp()
        subprocess.run(['unzip', '-q', jarPath, '-d', temp_dir], check=True)
        return temp_dir
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to unzip JAR file: {str(e)}")

def checkUPX(filePath):
    try:
        result = subprocess.run(['upx', '-t', filePath], capture_output=True, text=True)
        return "OK" in result.stdout
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False