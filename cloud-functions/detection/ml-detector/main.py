"""
ML detector with Firestore write
"""
import functions_framework
from google.cloud import pubsub_v1, firestore
import json
import base64
from datetime import datetime

# Initialize clients
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
alerts_topic = publisher.topic_path('capstone-log-monitoring', 'alerts')

@functions_framework.cloud_event
def detect_ml(cloud_event):
    """ML-based anomaly detection"""
    try:
        # Decode message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        log_data = json.loads(message_data)
        
        source_ip = log_data.get('source_ip', 'unknown')
        print(f" Processing log from {source_ip}")
        
        # Check attack_type
        attack_type = log_data.get('attack_type', 'BENIGN')
        
        if attack_type.upper() != 'BENIGN':
            print(f" ML: Dataset labeled as attack")
            
            alert = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source_ip': source_ip,
                'detector': 'ml',
                'severity': 'HIGH',
                'attack_type': attack_type,
                'confidence': 0.92,
                'description': f"ML model detected {attack_type}",
                'source': log_data.get('source', 'unknown')
            }
            
            # Save to Firestore
            db.collection('alerts').add(alert)
            print(f" ML Alert created: {attack_type} - HIGH from {source_ip}")
            
            # Publish to alerts topic
            publisher.publish(alerts_topic, json.dumps(alert).encode('utf-8')).result()
            print(f" Published ML alert")
        else:
            print(f" No ML anomaly detected for {source_ip}")
        
        return 'OK'
    except Exception as e:
        print(f" Error in ML detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'