import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler

DECOMPILER = PyBitDecompiler()

def analyze_file(file_content, filename):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp:
            temp.write(file_content)
            temp_path = temp.name
            return DECOMPILER.analyze_file(temp_path)
    except Exception as e:
        return {'error': str(e)}
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

def lambda_handler(event, context):
    try:
        # Handle both base64 and binary input
        file_content = event['body']
        if isinstance(file_content, str):
            file_content = file_content.encode()
        
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