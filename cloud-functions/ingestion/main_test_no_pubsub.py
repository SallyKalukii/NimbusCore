
import functions_framework
import json
from datetime import datetime

@functions_framework.http
def ingest_log(request):
    """Test version - NO PUB/SUB - just accepts and returns"""
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    if request.method != 'POST':
        return ({'error': 'Method not allowed'}, 405, headers)
    
    try:
        log_data = request.get_json()
        
        if not log_data:
            return ({'error': 'No JSON body'}, 400, headers)
        
        # Just validate and return - NO PUB/SUB!
        required = ['level', 'source', 'message']
        if not all(k in log_data for k in required):
            return ({'error': 'Missing fields'}, 400, headers)
        
        # Return immediately
        return ({
            'status': 'accepted',
            'message': 'Log received (test mode - no Pub/Sub)',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, 202, headers)
        
    except Exception as e:
        return ({'error': str(e)}, 500, headers)
