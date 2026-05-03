"""
Cloud Function for automatic IP blocking
Triggered by Pub/Sub messages from alerts topic
"""
import functions_framework
from google.cloud import firestore
import json
import base64
from datetime import datetime, timedelta

# Initialize Firestore
db = firestore.Client()

# Blocking threshold
ATTACK_THRESHOLD = 3  # Block after 3 attacks within time window
TIME_WINDOW_MINUTES = 5

@functions_framework.cloud_event
def block_ip(cloud_event):
    """
    Automatically block IPs with multiple attacks
    Triggered by Pub/Sub messages from alerts topic
    """
    try:
        # Decode Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        alert_data = json.loads(message_data)
        
        source_ip = alert_data.get('source_ip')
        
        if not source_ip:
            print("  No source IP in alert, skipping")
            return 'OK'
        
        print(f" Checking if {source_ip} should be blocked...")
        
        # Count recent alerts from this IP
        alert_count = count_recent_alerts(source_ip)
        
        print(f" {source_ip} has {alert_count} alerts in last {TIME_WINDOW_MINUTES} minutes")
        
        # Block if threshold exceeded
        if alert_count >= ATTACK_THRESHOLD:
            # Check if already blocked
            if not is_already_blocked(source_ip):
                block_malicious_ip(source_ip, alert_count, alert_data)
                print(f" IP {source_ip} BLOCKED after {alert_count} attacks")
            else:
                print(f"ℹ  IP {source_ip} already blocked")
        else:
            print(f" IP {source_ip} below threshold ({alert_count}/{ATTACK_THRESHOLD})")
        
        return 'OK'
        
    except Exception as e:
        print(f"❌ Error in IP blocker: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'

def count_recent_alerts(source_ip):
    """Count alerts from IP in recent time window"""
    time_threshold = datetime.utcnow() - timedelta(minutes=TIME_WINDOW_MINUTES)
    time_threshold_str = time_threshold.isoformat() + 'Z'
    
    alerts_ref = db.collection('alerts')\
        .where('source_ip', '==', source_ip)\
        .where('timestamp', '>=', time_threshold_str)\
        .stream()
    
    count = sum(1 for _ in alerts_ref)
    return count

def is_already_blocked(source_ip):
    """Check if IP is already in blocked list"""
    blocked_ref = db.collection('blocked_ips')\
        .where('ip_address', '==', source_ip)\
        .where('status', '==', 'blocked')\
        .limit(1)\
        .stream()
    
    return any(True for _ in blocked_ref)

def block_malicious_ip(source_ip, alert_count, alert_data):
    """Add IP to blocked list"""
    blocked_entry = {
        'ip_address': source_ip,
        'blocked_at': datetime.utcnow().isoformat() + 'Z',
        'reason': f'Multiple attacks detected ({alert_count} in {TIME_WINDOW_MINUTES} minutes)',
        'alert_count': alert_count,
        'status': 'blocked',
        'threat_level': alert_data.get('severity', 'MEDIUM'),
        'attack_types': [alert_data.get('attack_type', 'Unknown')],
        'first_detector': alert_data.get('detector', 'unknown')
    }
    
    db.collection('blocked_ips').add(blocked_entry)
    
    # In production, would also:
    # - Update firewall rules
    # - Add to Cloud Armor policy
    # - Notify security team
    
    print(f" Added {source_ip} to blocked_ips collection")