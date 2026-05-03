
import functions_framework
from google.cloud import pubsub_v1, firestore
import json
import base64
from datetime import datetime
import os

# Initialize clients
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
project_id = os.environ.get('GCP_PROJECT', 'capstone-log-monitoring')
output_topic = f'projects/{project_id}/topics/enriched-logs'

@functions_framework.cloud_event
def enrich_log_event(cloud_event):
    """
    Enrich parsed logs with additional metadata
    Store in Firestore and publish to enriched-logs topic
    """
    try:
        # Decode Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        log_data = json.loads(message_data)
        
        print(f" Enriching log from {log_data.get('source')}")
        
        # Add enrichment metadata
        log_data['enriched_at'] = datetime.utcnow().isoformat() + 'Z'
        log_data['enrichment_version'] = '1.0'
        
        # Add timestamp components for querying
        timestamp = log_data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        log_data['timestamp_day'] = timestamp[:10]  # YYYY-MM-DD
        log_data['timestamp_hour'] = timestamp[:13]  # YYYY-MM-DDTHH
        
        # Add numeric level for sorting
        level_map = {'DEBUG': 0, 'INFO': 1, 'WARN': 2, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
        log_data['level_numeric'] = level_map.get(log_data.get('level', 'INFO'), 1)
        
        # Store in Firestore
        doc_ref = db.collection('logs').add(log_data)
        log_id = doc_ref[1].id
        print(f" Stored in Firestore: {log_id}")
        
        # Publish to enriched-logs topic for detection
        message_bytes = json.dumps(log_data).encode('utf-8')
        future = publisher.publish(output_topic, message_bytes)
        message_id = future.result(timeout=10)
        print(f" Published to enriched-logs: {message_id}")
        
        return 'OK'
        
    except Exception as e:
        print(f" Error enriching log: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
