import json
import os
import tempfile
from backend.pybit import PyBitDecompiler

DECOMPILER = PyBitDecompiler()

def analyze_file(file_path):
    """Simplified analysis function"""
    return DECOMPILER.analyze_file(file_path)

def lambda_handler(event, context):
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file_content = event['body']
        if isinstance(file_content, str):
            file_content = file_content.encode()
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # Analyze file
        result = analyze_file(tmp_path)
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)