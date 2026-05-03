# NimbusCore API Documentation

## Log Ingestion Endpoint

**URL:** `https://us-central1-capstone-log-monitoring.cloudfunctions.net/ingest_log`

**Method:** POST

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "level": "ERROR",
  "source": "web_server",
  "message": "Suspicious activity detected",
  "timestamp": "2026-03-13T10:00:00Z",
  "source_ip": "192.168.1.100",
  "attack_type": "DDoS",
  "request_path": "/api/login",
  "status_code": 503
}
```

**Response:**
```json
{
  "status": "accepted",
  "message_id": "18604003053549220",
  "timestamp": "2026-03-13T10:00:01Z"
}
```