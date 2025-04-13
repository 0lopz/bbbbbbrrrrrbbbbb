import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DECOMPILER = PyBitDecompiler()

def analyze_file(file_path):
    try:
        return DECOMPILER.analyze_file(file_path)
    except Exception as e:
        return {'error': f"Analysis failed: {str(e)}"}

def lambda_handler(event, context):
    # Check payload size first
    content_length = len(event.get('body', b''))
    if content_length > MAX_FILE_SIZE:
        return {
            'statusCode': HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            'body': json.dumps({'error': f'File exceeds {MAX_FILE_SIZE/1024/1024}MB limit'}),
            'headers': {'Content-Type': 'application/json'}
        }

    temp_path = None
    try:
        file_content = event['body']
        if isinstance(file_content, str):
            file_content = file_content.encode()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        result = analyze_file(temp_path)
        if 'error' in result:
            raise Exception(result['error'])

        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps(result),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)