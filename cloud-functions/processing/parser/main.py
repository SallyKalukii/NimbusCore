import functions_framework
from google.cloud import pubsub_v1
import json
from datetime import datetime
import base64
import os

# Initialize publisher OUTSIDE function for reuse
publisher = pubsub_v1.PublisherClient()
project_id = os.environ.get('GCP_PROJECT', 'capstone-log-monitoring')
output_topic = f'projects/{project_id}/topics/processed-logs'

@functions_framework.cloud_event
def parse_log_event(cloud_event):
    """Parse and publish logs"""
    try:
        # Decode message
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        
        print(f"Received message: {pubsub_message[:150]}...")
        
        # Parse JSON
        try:
            log_data = json.loads(pubsub_message)
        except json.JSONDecodeError:
            log_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': 'INFO',
                'source': 'unknown',
                'message': pubsub_message
            }
        
        # Ensure required fields
        if 'level' not in log_data:
            log_data['level'] = 'INFO'
        if 'source' not in log_data:
            log_data['source'] = 'unknown'
        if 'message' not in log_data:
            log_data['message'] = 'Log entry'
        if 'timestamp' not in log_data:
            log_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Normalize level
        log_data['level'] = str(log_data['level']).upper()
        
        # Add metadata
        log_data['parsed_at'] = datetime.utcnow().isoformat() + 'Z'
        log_data['parser_version'] = '2.0'
        
        print(f" Parsed log: level={log_data['level']}, source={log_data['source']}")
        
        # Log important fields for debugging
        if 'attack_type' in log_data:
            print(f"    attack_type={log_data['attack_type']}")
        if 'source_ip' in log_data:
            print(f"    source_ip={log_data['source_ip']}")
        
        # Publish to processed-logs
        message_bytes = json.dumps(log_data).encode('utf-8')
        
        # Publish with error handling
        try:
            future = publisher.publish(output_topic, message_bytes)
            message_id = future.result(timeout=10)
            print(f" Published to processed-logs: {message_id}")
        except Exception as pub_error:
            print(f" Publish error: {str(pub_error)}")
            raise
        
        return 'OK'
        
    except Exception as e:
        print(f" Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
