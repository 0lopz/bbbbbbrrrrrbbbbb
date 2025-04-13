import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler

# Set to 45MB to stay under Vercel's 50MB limit
MAX_FILE_SIZE = 45 * 1024 * 1024
DECOMPILER = PyBitDecompiler()

def analyze_file(file_path):
    try:
        return DECOMPILER.analyze_file(file_path)
    except Exception as e:
        return {'error': f"Analysis failed: {str(e)}"}

def lambda_handler(event, context):
    # First check payload size
    content_length = len(event.get('body', b''))
    if content_length > MAX_FILE_SIZE:
        return {
            'statusCode': HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            'body': json.dumps({
                'error': f'File exceeds {(MAX_FILE_SIZE/1024/1024):.1f}MB limit'
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    temp_path = None
    try:
        # Handle both base64 and binary
        file_content = event.get('body')
        if not file_content:
            raise ValueError("No file content provided")
            
        if isinstance(file_content, str):
            file_content = file_content.encode()

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        # Analyze file
        result = analyze_file(temp_path)
        if 'error' in result:
            raise Exception(result['error'])

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
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass