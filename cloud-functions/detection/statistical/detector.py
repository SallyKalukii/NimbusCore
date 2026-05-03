
"""
Statistical Anomaly Detection
Uses Z-score method to detect unusual patterns in logs
"""

from google.cloud import firestore
from datetime import datetime, timedelta
import statistics
import json

# Initialize Firestore
db = firestore.Client()

class StatisticalDetector:
    def __init__(self):
        self.threshold = 3  # Z-score threshold (3 std deviations)
    
    def get_recent_logs(self, hours=1):
        """Get logs from last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        logs_ref = db.collection('logs')
        query = logs_ref.where('ingested_at', '>=', cutoff_time.isoformat())
        
        logs = []
        for doc in query.stream():
            logs.append(doc.to_dict())
        
        return logs
    
    def detect_error_rate_anomaly(self):
        """Detect unusual error rates"""
        print("Checking error rate anomalies...")
        
        recent_logs = self.get_recent_logs(hours=1)
        
        if not recent_logs:
            print("No recent logs found")
            return None
        
        # Calculate current error rate
        total_logs = len(recent_logs)
        error_logs = len([l for l in recent_logs if l.get('level') == 'ERROR'])
        current_error_rate = (error_logs / total_logs) * 100 if total_logs > 0 else 0
        
        print(f"Current error rate: {current_error_rate:.2f}%")
        print(f"Total logs: {total_logs}, Errors: {error_logs}")
        
        # Baseline (in production, from historical data)
        baseline_mean = 5.0  # 5% error rate is normal
        baseline_std = 2.0   # Standard deviation
        
        # Calculate Z-score
        if baseline_std > 0:
            z_score = (current_error_rate - baseline_mean) / baseline_std
        else:
            z_score = 0
        
        print(f"Z-score: {z_score:.2f}")
        
        # Check if anomaly
        if abs(z_score) > self.threshold:
            anomaly = {
                'type': 'error_rate_anomaly',
                'detected_at': datetime.utcnow().isoformat(),
                'metric': 'error_rate',
                'current_value': current_error_rate,
                'baseline_mean': baseline_mean,
                'baseline_std': baseline_std,
                'z_score': z_score,
                'severity': 'HIGH' if abs(z_score) > 4 else 'MEDIUM',
                'details': f'Error rate ({current_error_rate:.2f}%) is {abs(z_score):.2f} standard deviations from baseline'
            }
            
            print(f" ANOMALY DETECTED: {anomaly['details']}")
            return anomaly
        else:
            print(f" No anomaly - within normal range")
            return None
    
    def detect_volume_anomaly(self):
        """Detect unusual log volumes"""
        print("\nChecking volume anomalies...")
        
        recent_logs = self.get_recent_logs(hours=1)
        current_volume = len(recent_logs)
        
        print(f"Current volume: {current_volume} logs/hour")
        
        # Baseline (in production, from historical data)
        baseline_mean = 5000   # Expected logs per hour
        baseline_std = 1000    # Standard deviation
        
        # Calculate Z-score
        if baseline_std > 0:
            z_score = (current_volume - baseline_mean) / baseline_std
        else:
            z_score = 0
        
        print(f"Z-score: {z_score:.2f}")
        
        if abs(z_score) > self.threshold:
            anomaly = {
                'type': 'volume_anomaly',
                'detected_at': datetime.utcnow().isoformat(),
                'metric': 'log_volume',
                'current_value': current_volume,
                'baseline_mean': baseline_mean,
                'baseline_std': baseline_std,
                'z_score': z_score,
                'severity': 'HIGH' if abs(z_score) > 4 else 'MEDIUM',
                'details': f'Log volume ({current_volume}) is {abs(z_score):.2f} standard deviations from baseline'
            }
            
            print(f" ANOMALY DETECTED: {anomaly['details']}")
            return anomaly
        else:
            print(f" No anomaly - within normal range")
            return None
    
    def run_all_checks(self):
        """Run all statistical checks"""
        print("=" * 60)
        print("STATISTICAL ANOMALY DETECTION")
        print("=" * 60)
        
        anomalies = []
        
        # Check error rate
        error_anomaly = self.detect_error_rate_anomaly()
        if error_anomaly:
            anomalies.append(error_anomaly)
        
        # Check volume
        volume_anomaly = self.detect_volume_anomaly()
        if volume_anomaly:
            anomalies.append(volume_anomaly)
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: {len(anomalies)} anomalies detected")
        print("=" * 60)
        
        return anomalies

def main():
    detector = StatisticalDetector()
    anomalies = detector.run_all_checks()
    
    if anomalies:
        print("\n ANOMALIES DETECTED:")
        for anomaly in anomalies:
            print(json.dumps(anomaly, indent=2))
    else:
        print("\n All metrics within normal range")

if __name__ == '__main__':
    main()


