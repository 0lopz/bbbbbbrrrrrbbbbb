import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler
from backend.pyinstxtractor import extract_exe

DECOMPILER = PyBitDecompiler()

def analyze_file(file_content: bytes, filename: str) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp:
        try:
            temp.write(file_content)
            temp_path = temp.name
            
            if filename.endswith('.exe'):
                extracted_files = extract_exe(temp_path)
                result = {
                    'file_type': 'exe',
                    'python_embedded': bool(extracted_files),
                    'extracted': [],
                    'decompiled': []
                }
                for extracted in extracted_files:
                    decompiled = DECOMPILER.analyze_file(extracted)
                    result['extracted'].append(os.path.basename(extracted))
                    result['decompiled'].append(decompiled)
                return result
            else:
                return DECOMPILER.analyze_file(temp_path)
        finally:
            os.unlink(temp_path)

def lambda_handler(event, context):
    try:
        if not event.get('body'):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({'error': 'No file uploaded'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }

        file_content = event['body'].encode() if isinstance(event['body'], str) else event['body']
        filename = event.get('headers', {}).get('x-filename', 'uploaded_file')

        result = analyze_file(file_content, filename)
        
        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }