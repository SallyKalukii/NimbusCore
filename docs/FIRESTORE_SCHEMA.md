
# Firestore Database Schema

## Collections

### 1. logs (Main collection)

**Document ID:** Auto-generated (unique ID)

**Fields:**
```javascript
{
  // Core fields
  "timestamp": "2025-01-21T10:30:00Z",      // ISO 8601 format
  "level": "INFO|WARN|ERROR|CRITICAL",      // Log level
  "source": "api-server",                    // Source application
  "message": "Log message text",             // Main log message
  
  // Request context
  "user_ip": "192.168.1.100",               // User IP address
  "user_id": "user123",                      // User identifier
  "request_path": "/api/users",              // Request path
  "request_method": "GET",                   // HTTP method
  "status_code": 200,                        // HTTP status
  "response_time_ms": 150,                   // Response time
  
  // Enrichment (added by enrichment function)
  "geo_country": "US",                       // Country from IP
  "geo_city": "San Francisco",               // City from IP
  "geo_latitude": 37.7749,                   // Latitude
  "geo_longitude": -122.4194,                // Longitude
  "user_agent_browser": "Chrome",            // Browser
  "user_agent_os": "Windows",                // Operating system
  
  // Metadata
  "ingested_at": "2025-01-21T10:30:00Z",    // When received
  "parsed_at": "2025-01-21T10:30:01Z",      // When parsed
  "processed_at": "2025-01-21T10:30:02Z",   // When enriched
  "raw_format": "json",                      // Original format
  "parser_version": "1.0",                   // Parser version
  
  // Data quality
  "is_anomaly": false,                       // Flagged by detection
  "anomaly_score": 0.0,                      // ML anomaly score
  "detection_methods": [],                   // Which detectors triggered
  
  // Indexing helpers
  "timestamp_hour": "2025-01-21T10",         // Hour bucket for queries
  "timestamp_day": "2025-01-21",             // Day bucket
  "level_numeric": 3                         // 1=INFO, 2=WARN, 3=ERROR, 4=CRITICAL
}
```

**Indexes:**
- `timestamp` (descending) - for time-range queries
- `source` + `timestamp` (composite) - for per-source queries
- `level` + `timestamp` (composite) - for severity filtering
- `user_id` + `timestamp` (composite) - for user activity
- `is_anomaly` + `timestamp` (composite) - for alerts

---

### 2. metrics (Aggregated statistics)

**Document ID:** `{metric_name}_{time_bucket}`
Example: `error_rate_2025-01-21T10`

**Fields:**
```javascript
{
  "metric_name": "error_rate",
  "time_bucket": "2025-01-21T10:00:00Z",    // Hour bucket
  "source": "api-server",                    // Optional: per-source
  
  // Statistics
  "count": 1234,                             // Total events
  "sum": 5000,                               // Sum of values
  "mean": 4.05,                              // Average
  "stddev": 1.2,                             // Standard deviation
  "min": 1.0,                                // Minimum
  "max": 10.5,                               // Maximum
  
  // For anomaly detection
  "baseline_mean": 3.5,                      // Historical average
  "baseline_stddev": 0.8,                    // Historical std dev
  "is_anomalous": false,                     // Above threshold?
  
  "updated_at": "2025-01-21T10:59:59Z"
}
```

---

### 3. alerts (Detected anomalies)

**Document ID:** Auto-generated

**Fields:**
```javascript
{
  "alert_id": "alert_123456",
  "timestamp": "2025-01-21T10:30:00Z",
  "severity": "HIGH|MEDIUM|LOW",
  "status": "NEW|ACKNOWLEDGED|RESOLVED",
  
  // Detection info
  "detection_method": "statistical|rules|ml",
  "anomaly_type": "sql_injection|brute_force|error_spike",
  "confidence": 0.95,                        // 0-1
  
  // Affected logs
  "affected_source": "api-server",
  "affected_user": "user123",
  "log_count": 50,                           // Logs involved
  "sample_log_ids": ["log1", "log2"],       // Reference logs
  
  // Alert details
  "title": "SQL Injection Detected",
  "description": "Multiple SQL injection attempts",
  "recommendation": "Block IP and review logs",
  
  // Lifecycle
  "acknowledged_by": "admin@email.com",
  "acknowledged_at": "2025-01-21T10:35:00Z",
  "resolved_by": "admin@email.com",
  "resolved_at": "2025-01-21T11:00:00Z",
  "resolution_notes": "False positive, user error"
}
```

---

### 4. rules (Detection rules)

**Document ID:** `rule_{rule_name}`

**Fields:**
```javascript
{
  "rule_id": "sql_injection_001",
  "name": "SQL Injection in URL",
  "description": "Detects SQL injection patterns in request paths",
  "enabled": true,
  "severity": "HIGH",
  
  // Condition
  "field": "message",
  "pattern": "(SELECT|UNION|DROP).*FROM",
  "condition_type": "regex",
  
  // Actions
  "actions": ["alert", "log", "block"],
  
  // Metadata
  "created_at": "2025-01-20T00:00:00Z",
  "updated_at": "2025-01-20T00:00:00Z",
  "created_by": "admin@email.com",
  "trigger_count": 150                       // How many times triggered
}
```

---

## Query Examples

### Get recent errors
```python
db.collection('logs') \
  .where('level', '==', 'ERROR') \
  .order_by('timestamp', direction=firestore.Query.DESCENDING) \
  .limit(100) \
  .stream()
```

### Get logs for specific source in time range
```python
from datetime import datetime, timedelta

start_time = datetime.utcnow() - timedelta(hours=1)

db.collection('logs') \
  .where('source', '==', 'api-server') \
  .where('timestamp', '>=', start_time.isoformat()) \
  .order_by('timestamp') \
  .stream()
```

### Get anomalous logs
```python
db.collection('logs') \
  .where('is_anomaly', '==', True) \
  .order_by('timestamp', direction=firestore.Query.DESCENDING) \
  .limit(50) \
  .stream()
```

### Get active alerts
```python
db.collection('alerts') \
  .where('status', '==', 'NEW') \
  .order_by('timestamp', direction=firestore.Query.DESCENDING) \
  .stream()
```

---

## Data Retention

- **logs:** 90 days (auto-delete via TTL)
- **metrics:** 180 days
- **alerts:** 1 year
- **rules:** Permanent

---

**Last Updated:** January 21, 2025
