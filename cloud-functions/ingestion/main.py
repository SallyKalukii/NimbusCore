import functions_framework
from google.cloud import pubsub_v1
import json
from datetime import datetime
import os

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
project_id = os.environ.get('GCP_PROJECT', 'capstone-log-monitoring')
topic_name = f'projects/{project_id}/topics/raw-logs'

@functions_framework.http
def ingest_log(request):
    """
    HTTP Cloud Function to ingest logs
    Accepts logs and publishes to raw-logs Pub/Sub topic
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle preflight
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    if request.method != 'POST':
        return ({'error': 'Method not allowed'}, 405, headers)
    
    try:
        # Parse request
        log_data = request.get_json()
        
        if not log_data:
            return ({'error': 'No JSON body provided'}, 400, headers)
        
        # Validate required fields
        required_fields = ['level', 'source', 'message']
        missing_fields = [field for field in required_fields if field not in log_data]
        
        if missing_fields:
            return ({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, 400, headers)
        
        # Add timestamps
        if 'timestamp' not in log_data:
            log_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        log_data['ingested_at'] = datetime.utcnow().isoformat() + 'Z'
        log_data['ingestion_source'] = 'http-endpoint'
        
        # Publish to Pub/Sub - WAIT for confirmation
        message_data = json.dumps(log_data).encode('utf-8')
        
        try:
            future = publisher.publish(topic_name, message_data)
            message_id = future.result(timeout=5)  # Wait up to 5 seconds
            print(f" Published to raw-logs: {message_id} from {log_data.get('source')}")
            
        except Exception as pub_error:
            print(f" Publish failed: {str(pub_error)}")
            return ({
                'error': 'Failed to publish to Pub/Sub',
                'details': str(pub_error)
            }, 500, headers)
        
        # Return success with message ID
        return ({
            'status': 'accepted',
            'message': 'Log accepted for processing',
            'timestamp': log_data['ingested_at'],
            'message_id': message_id
        }, 202, headers)
        
    except json.JSONDecodeError:
        return ({'error': 'Invalid JSON format'}, 400, headers)
    
    except Exception as e:
        print(f" Error: {str(e)}")
        return ({
            'error': 'Internal server error',
            'details': str(e)
        }, 500, headers)