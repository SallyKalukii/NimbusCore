
"""
Log Generator - Simulates applications sending logs to ingestion endpoint

Usage:
    python log_generator.py --count 1000 --rate 100
    
    --count: Total number of logs to send
    --rate: Logs per second
    --anomaly-rate: Percentage of anomalous logs (default: 5%)
"""

import requests
import json
import time
import random
import argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
INGESTION_URL = "https://us-central1-capstone-log-monitoring.cloudfunctions.net/ingest_log"

# Sample data for realistic logs
SOURCES = [
    'api-server',
    'auth-service', 
    'payment-service',
    'user-service',
    'database',
    'cache-server',
    'web-frontend',
    'mobile-api'
]

LOG_LEVELS = {
    'INFO': 70,      # 70% info logs
    'WARN': 20,      # 20% warnings
    'ERROR': 8,      # 8% errors
    'CRITICAL': 2    # 2% critical
}

MESSAGES = {
    'INFO': [
        'Request processed successfully',
        'User logged in',
        'Data retrieved from cache',
        'Transaction completed',
        'API request received',
        'Background job started',
        'Configuration loaded'
    ],
    'WARN': [
        'High memory usage detected',
        'Slow query detected (>500ms)',
        'Rate limit approaching',
        'Deprecated API endpoint used',
        'Connection pool running low'
    ],
    'ERROR': [
        'Database connection failed',
        'API request timeout',
        'Authentication failed',
        'File not found',
        'Invalid input data',
        'Service temporarily unavailable'
    ],
    'CRITICAL': [
        'System out of memory',
        'Database unavailable',
        'Payment processing failed',
        'Security breach detected',
        'Data corruption detected'
    ]
}

# Anomalous patterns (for testing detection later)
ANOMALY_PATTERNS = [
    {
        'type': 'sql_injection',
        'message': "SELECT * FROM users WHERE id='1' OR '1'='1'",
        'level': 'WARN',
        'source': 'api-server'
    },
    {
        'type': 'brute_force',
        'message': 'Failed login attempt',
        'level': 'WARN',
        'source': 'auth-service',
        'user_ip': '192.168.1.100'  # Same IP for brute force
    },
    {
        'type': 'path_traversal',
        'message': 'File access: ../../etc/passwd',
        'level': 'ERROR',
        'source': 'api-server'
    },
    {
        'type': 'suspicious_file',
        'message': 'Attempted access to .env file',
        'level': 'WARN',
        'source': 'web-frontend'
    }
]

class LogGenerator:
    def __init__(self, ingestion_url):
        self.ingestion_url = ingestion_url
        self.stats = {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'anomalies_sent': 0
        }
        
    def generate_normal_log(self):
        """Generate a realistic normal log entry"""
        
        # Pick level based on probability distribution
        rand = random.randint(1, 100)
        cumulative = 0
        level = 'INFO'
        
        for lvl, prob in LOG_LEVELS.items():
            cumulative += prob
            if rand <= cumulative:
                level = lvl
                break
        
        log = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'source': random.choice(SOURCES),
            'message': random.choice(MESSAGES[level]),
            'user_ip': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
            'user_id': f'user{random.randint(1000, 9999)}',
            'request_path': f'/api/{random.choice(["users", "products", "orders", "payments"])}/{random.randint(1, 1000)}',
            'response_time_ms': random.randint(50, 500)
        }
        
        return log
    
    def generate_anomalous_log(self):
        """Generate a log with anomalous pattern"""
        
        pattern = random.choice(ANOMALY_PATTERNS)
        
        log = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': pattern['level'],
            'source': pattern['source'],
            'message': pattern['message'],
            'user_ip': pattern.get('user_ip', f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'),
            'user_id': f'user{random.randint(1000, 9999)}',
            'request_path': '/api/admin/users',
            'anomaly_type': pattern['type']  # For testing (real logs won't have this)
        }
        
        return log
    
    def send_log(self, log_data):
        """Send a single log to the ingestion endpoint"""
        
        try:
            response = requests.post(
                self.ingestion_url,
                json=log_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.stats['successful'] += 1
                return True, response.json()
            else:
                self.stats['failed'] += 1
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            self.stats['failed'] += 1
            return False, str(e)
    
    def send_logs_batch(self, count, anomaly_rate=5):
        """Send a batch of logs sequentially"""
        
        results = []
        
        for i in range(count):
            # Decide if this should be an anomaly
            is_anomaly = random.randint(1, 100) <= anomaly_rate
            
            if is_anomaly:
                log = self.generate_anomalous_log()
                self.stats['anomalies_sent'] += 1
            else:
                log = self.generate_normal_log()
            
            success, result = self.send_log(log)
            self.stats['total_sent'] += 1
            
            results.append({
                'log_number': i + 1,
                'success': success,
                'is_anomaly': is_anomaly,
                'result': result
            })
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"Sent {i + 1}/{count} logs...")
        
        return results
    
    def send_logs_parallel(self, count, rate_per_second, anomaly_rate=5):
        """Send logs at a controlled rate (logs per second)"""
        
        print(f"\n🚀 Starting load test: {count} logs at {rate_per_second} logs/second")
        print(f"   Anomaly rate: {anomaly_rate}%")
        print(f"   Expected duration: {count/rate_per_second:.1f} seconds\n")
        
        start_time = time.time()
        batch_size = min(rate_per_second, 100)  # Process in batches
        delay_between_batches = batch_size / rate_per_second
        
        total_sent = 0
        
        while total_sent < count:
            batch_start = time.time()
            
            # Send a batch
            logs_to_send = min(batch_size, count - total_sent)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                
                for _ in range(logs_to_send):
                    is_anomaly = random.randint(1, 100) <= anomaly_rate
                    
                    if is_anomaly:
                        log = self.generate_anomalous_log()
                        self.stats['anomalies_sent'] += 1
                    else:
                        log = self.generate_normal_log()
                    
                    future = executor.submit(self.send_log, log)
                    futures.append(future)
                
                # Wait for batch to complete
                for future in as_completed(futures):
                    self.stats['total_sent'] += 1
                    total_sent += 1
            
            # Progress update
            elapsed = time.time() - start_time
            current_rate = total_sent / elapsed if elapsed > 0 else 0
            print(f"Progress: {total_sent}/{count} logs ({total_sent/count*100:.1f}%) | "
                  f"Rate: {current_rate:.1f} logs/sec | "
                  f"Success: {self.stats['successful']} | "
                  f"Failed: {self.stats['failed']}")
            
            # Rate limiting - wait before next batch
            batch_duration = time.time() - batch_start
            if batch_duration < delay_between_batches:
                time.sleep(delay_between_batches - batch_duration)
        
        total_time = time.time() - start_time
        
        print(f"\n✅ Load test complete!")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Actual rate: {total_sent/total_time:.2f} logs/second")
        print(f"   Total sent: {self.stats['total_sent']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")
        print(f"   Anomalies: {self.stats['anomalies_sent']}")
    
    def print_stats(self):
        """Print summary statistics"""
        
        print("\n" + "="*60)
        print("LOG GENERATOR STATISTICS")
        print("="*60)
        print(f"Total logs sent:     {self.stats['total_sent']}")
        print(f"Successful:          {self.stats['successful']} ({self.stats['successful']/max(self.stats['total_sent'],1)*100:.1f}%)")
        print(f"Failed:              {self.stats['failed']} ({self.stats['failed']/max(self.stats['total_sent'],1)*100:.1f}%)")
        print(f"Anomalies injected:  {self.stats['anomalies_sent']} ({self.stats['anomalies_sent']/max(self.stats['total_sent'],1)*100:.1f}%)")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Generate and send test logs')
    parser.add_argument('--count', type=int, default=100, help='Number of logs to generate')
    parser.add_argument('--rate', type=int, default=10, help='Logs per second')
    parser.add_argument('--anomaly-rate', type=int, default=5, help='Percentage of anomalous logs')
    parser.add_argument('--url', type=str, default=INGESTION_URL, help='Ingestion endpoint URL')
    
    args = parser.parse_args()
    
    generator = LogGenerator(args.url)
    
    # Run load test
    generator.send_logs_parallel(
        count=args.count,
        rate_per_second=args.rate,
        anomaly_rate=args.anomaly_rate
    )
    
    # Print final statistics
    generator.print_stats()


if __name__ == '__main__':
    main()
