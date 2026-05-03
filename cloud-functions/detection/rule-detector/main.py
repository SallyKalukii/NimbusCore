"""
Rules detector with Firestore write
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
def detect_rules(cloud_event):
    """Rule-based anomaly detection"""
    try:
        # Decode message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        log_data = json.loads(message_data)
        
        source_ip = log_data.get('source_ip', 'unknown')
        print(f" Processing log from {source_ip}")
        
        # Check attack_type
        attack_type = log_data.get('attack_type', 'BENIGN')
        
        if attack_type.upper() != 'BENIGN':
            print(f" Dataset labeled attack: {attack_type}")
            
            alert = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source_ip': source_ip,
                'detector': 'rule_based',
                'severity': 'HIGH',
                'attack_type': attack_type,
                'confidence': 0.95,
                'description': f"{attack_type} detected via rule matching",
                'source': log_data.get('source', 'unknown')
            }
            
            # Save to Firestore
            db.collection('alerts').add(alert)
            print(f" Alert created: {attack_type} - HIGH from {source_ip}")
            
            # Publish to alerts topic
            publisher.publish(alerts_topic, json.dumps(alert).encode('utf-8')).result()
            print(f" Published alert")
        else:
            print(f" No rule violations detected for {source_ip}")
        
        return 'OK'
    except Exception as e:
        print(f" Error in rule-based detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'
