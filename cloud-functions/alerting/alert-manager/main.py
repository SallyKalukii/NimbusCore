"""
Cloud Function for alert management with REAL notifications
Triggered by Pub/Sub messages from alerts topic
"""
import functions_framework
from google.cloud import firestore
import json
import base64
from datetime import datetime
import os
import requests

# Initialize Firestore
db = firestore.Client()

# Get credentials from environment
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'salome.mutemwa@ashesi.edu.gh')

@functions_framework.cloud_event
def manage_alerts(cloud_event):
    """
    Process alerts and send notifications
    Triggered by Pub/Sub messages from alerts topic
    """
    try:
        # Decode Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        alert_data = json.loads(message_data)
        
        print(f" Managing alert: {alert_data.get('attack_type')} from {alert_data.get('source_ip')}")
        
        # Update alert metadata
        alert_data['processed_at'] = datetime.utcnow().isoformat() + 'Z'
        alert_data['notification_sent'] = True
        
        # Send notifications
        notification_success = send_notifications(alert_data)
        alert_data['notification_success'] = notification_success
        
        # Log for auditing
        log_alert(alert_data)
        
        return 'OK'
        
    except Exception as e:
        print(f" Error managing alert: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'

def send_notifications(alert):
    """Send alert notifications via Slack and Email"""
    severity = alert.get('severity', 'MEDIUM')
    attack_type = alert.get('attack_type', 'Unknown')
    source_ip = alert.get('source_ip', 'Unknown')
    detector = alert.get('detector', 'unknown')
    confidence = alert.get('confidence', 0)
    
    # Format message
    message = f""" *{severity} SECURITY ALERT*

*Attack Type:* {attack_type}
*Source IP:* {source_ip}
*Detector:* {detector}
*Confidence:* {confidence:.0%}
*Time:* {alert.get('timestamp', 'Unknown')}

_NimbusCore Security Platform_
"""
    
    success = True
    
    # Send to Slack
    if SLACK_WEBHOOK_URL:
        try:
            slack_payload = {
                'text': message,
                'username': 'NimbusCore Security',
                'icon_emoji': ':shield:'
            }
            response = requests.post(
                SLACK_WEBHOOK_URL,
                json=slack_payload,
                timeout=10
            )
            if response.status_code == 200:
                print(f" Slack notification sent for {attack_type}")
            else:
                print(f"  Slack notification failed: {response.status_code}")
                success = False
        except Exception as e:
            print(f" Slack error: {str(e)}")
            success = False
    else:
        print("  SLACK_WEBHOOK_URL not configured")
    
    # Send Email (if SendGrid configured)
    if SENDGRID_API_KEY and ALERT_EMAIL:
        try:
            email_sent = send_email_notification(alert, message)
            if email_sent:
                print(f" Email notification sent for {attack_type}")
            else:
                print(f"  Email notification failed")
                success = False
        except Exception as e:
            print(f" Email error: {str(e)}")
            success = False
    else:
        print("  SendGrid not configured")
    
    return success

def send_email_notification(alert, message):
    """Send email via SendGrid"""
    try:
        headers = {
            'Authorization': f'Bearer {SENDGRID_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'personalizations': [{
                'to': [{'email': ALERT_EMAIL}],
                'subject': f" {alert.get('severity')} Alert: {alert.get('attack_type')}"
            }],
            'from': {'email': 'salome.mutemwa@ashesi.edu.gh'},
            'content': [{
                'type': 'text/plain',
                'value': message
            }]
        }
        
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers=headers,
            json=data,
            timeout=10
        )
        
        return response.status_code == 202
    except Exception as e:
        print(f" SendGrid error: {str(e)}")
        return False

def log_alert(alert):
    """Log alert for auditing"""
    audit_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'event': 'alert_processed',
        'alert_type': alert.get('attack_type'),
        'severity': alert.get('severity'),
        'source_ip': alert.get('source_ip'),
        'detector': alert.get('detector'),
        'notification_sent': alert.get('notification_success', False)
    }
    
    db.collection('audit_log').add(audit_entry)
    print(f" Alert logged for auditing")
