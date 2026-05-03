"""
Cloud Function for automatic scaling
Triggered by Pub/Sub messages from alerts topic
"""
import functions_framework
from google.cloud import firestore
import json
import base64
from datetime import datetime, timedelta

# Initialize Firestore
db = firestore.Client()

# Scaling thresholds
SCALE_UP_THRESHOLD = 10  # alerts in time window
SCALE_DOWN_THRESHOLD = 3
TIME_WINDOW_MINUTES = 2

@functions_framework.cloud_event
def auto_scale(cloud_event):
    """
    Automatically scale infrastructure based on alert volume
    Triggered by Pub/Sub messages from alerts topic
    """
    try:
        # Decode Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        alert_data = json.loads(message_data)
        
        print(f" Evaluating scaling decision...")
        
        # Count recent alerts
        alert_count = count_recent_alerts()
        
        print(f" Alert volume: {alert_count} in last {TIME_WINDOW_MINUTES} minutes")
        
        # Determine scaling action
        if alert_count >= SCALE_UP_THRESHOLD:
            scale_up(alert_count)
        elif alert_count <= SCALE_DOWN_THRESHOLD:
            scale_down(alert_count)
        else:
            print(f" Alert volume within normal range, no scaling needed")
        
        return 'OK'
        
    except Exception as e:
        print(f" Error in auto-scaler: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'

def count_recent_alerts():
    """Count total alerts in recent time window"""
    time_threshold = datetime.utcnow() - timedelta(minutes=TIME_WINDOW_MINUTES)
    time_threshold_str = time_threshold.isoformat() + 'Z'
    
    alerts_ref = db.collection('alerts')\
        .where('timestamp', '>=', time_threshold_str)\
        .stream()
    
    count = sum(1 for _ in alerts_ref)
    return count

def scale_up(alert_count):
    """Scale up infrastructure"""
    scale_factor = 2 if alert_count < 20 else 3
    
    scaling_event = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': 'scaled_up',
        'alert_count': alert_count,
        'scale_factor': scale_factor,
        'reason': f'High alert volume detected ({alert_count} alerts in {TIME_WINDOW_MINUTES} min)',
        'threshold': SCALE_UP_THRESHOLD
    }
    
    db.collection('scaling_events').add(scaling_event)
    
    print(f"  SCALED UP: Increasing capacity by {scale_factor}x due to {alert_count} alerts")
    
    # In production, would:
    # - Increase Cloud Run instances
    # - Scale Cloud Functions concurrency
    # - Adjust Cloud Armor rules

def scale_down(alert_count):
    """Scale down infrastructure"""
    scaling_event = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': 'scaled_down',
        'alert_count': alert_count,
        'scale_factor': 1,
        'reason': f'Low alert volume ({alert_count} alerts in {TIME_WINDOW_MINUTES} min)',
        'threshold': SCALE_DOWN_THRESHOLD
    }
    
    db.collection('scaling_events').add(scaling_event)
    
    print(f"  SCALED DOWN: Reducing capacity due to low alert volume ({alert_count} alerts)")