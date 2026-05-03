#  NimbusCore - AI-Powered Security Monitoring Platform

**Serverless, real-time threat detection and automated response system built on Google Cloud Platform**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![GCP](https://img.shields.io/badge/Platform-Google%20Cloud-orange.svg)](https://cloud.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

##  Overview

NimbusCore is a production-grade serverless security monitoring platform that detects and responds to cybersecurity threats in real-time. Built as a capstone project at Ashesi University, the system processes security logs through a 10-layer event-driven pipeline, employing triple-detection methodology (ML, rule-based, and statistical analysis) to identify attacks and automatically mitigate threats through IP blocking and infrastructure scaling.

**Key Features:**
-  Real-time log ingestion and processing (100+ logs/minute)
-  Triple detection system (ML + Rules + Statistical)
-  Automated threat response (IP blocking, auto-scaling)
-  Interactive dashboards with geolocation mapping
-  Multi-channel alerting (Slack, Email)
-  Cost-effective serverless architecture (~$98/month for 1M logs/day)

---

##  Architecture

### **10-Layer Serverless Pipeline**
```
┌─────────────────────────────────────────────────────────────┐
│                     NIMBUSCORE PIPELINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: HTTP Ingestion (ingest_log)                      │
│      ↓                                                      │
│  Layer 2: Pub/Sub Queue (raw-logs)                         │
│      ↓                                                      │
│  Layer 3: Log Parsing (parse_log)                          │
│      ↓                                                      │
│  Layer 4: Pub/Sub Queue (processed-logs)                   │
│      ↓                                                      │
│  Layer 5: Enrichment + Storage (enrich_log)                │
│      ↓                                                      │
│  Layer 6: Pub/Sub Queue (enriched-logs)                    │
│      ↓                                                      │
│  Layer 7: Triple Detection                                 │
│      ├─ Statistical Detector                               │
│      ├─ Rule-Based Detector                                │
│      └─ ML Detector                                        │
│      ↓                                                      │
│  Layer 8: Pub/Sub Queue (alerts)                           │
│      ↓                                                      │
│  Layer 9: Automated Response                               │
│      ├─ Alert Manager (Slack/Email)                        │
│      ├─ IP Blocker (3-strike threshold)                    │
│      └─ Auto-Scaler (dynamic capacity)                     │
│      ↓                                                      │
│  Layer 10: Dashboard (Real-time Visualization)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

##  Tech Stack

**Backend Infrastructure:**
- Google Cloud Functions (Gen2) - Serverless compute
- Google Cloud Pub/Sub - Asynchronous messaging
- Google Cloud Firestore - NoSQL database
- Python 3.11 - Primary language

**Frontend:**
- HTML5, CSS3, JavaScript
- Chart.js - Data visualization
- Leaflet.js - Interactive mapping
- Firebase Hosting - Static web hosting
- Firebase Authentication - User access control

**External APIs:**
- Slack Webhooks - Real-time notifications
- SendGrid - Email delivery
- ipapi.co - IP geolocation

---

##  Project Structure
```
nimbuscore/
├── cloud-functions/          # Serverless backend
│   ├── ingestion/           # Layer 1: HTTP endpoint
│   ├── processing/
│   │   ├── parser/          # Layer 3: Log parsing
│   │   └── enrichment/      # Layer 5: Data enrichment
│   ├── detection/
│   │   ├── statistical/     # Layer 7a: Statistical detector
│   │   ├── rule-detector/   # Layer 7b: Rule-based detector
│   │   └── ml-detector/     # Layer 7c: ML detector
│   └── alerting/
│       ├── alert-manager/   # Layer 9a: Notifications
│       ├── ip-blocker/      # Layer 9b: IP blocking
│       └── auto-scaler/     # Layer 9c: Auto-scaling
├── dashboard/               # Layer 10: Web interface
│   ├── css/
│   ├── js/
│   ├── admin-dashboard.html
│   └── user-dashboard.html
├── datasets/                # Testing & validation
│   ├── convert_dataset.py  # CIC-IDS-2017 converter
│   └── ingest_dataset.py   # Dataset ingestion script
└── docs/                    # Documentation
```

---

##  Installation & Deployment

### **Prerequisites**
- Google Cloud Platform account
- Firebase project
- Python 3.11+
- Google Cloud SDK

### **1. Clone Repository**
```bash
git clone https://github.com/SallyKalukii/nimbuscore.git
cd nimbuscore
```

### **2. Configure GCP**
```bash
# Set project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
```

### **3. Create Pub/Sub Topics**
```bash
gcloud pubsub topics create raw-logs
gcloud pubsub topics create processed-logs
gcloud pubsub topics create enriched-logs
gcloud pubsub topics create alerts
```

### **4. Deploy Cloud Functions**

**Ingestion Layer:**
```bash
cd cloud-functions/ingestion
gcloud functions deploy ingest_log \
  --gen2 \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --entry-point ingest_log
```

**Detection Layer (repeat for all 3 detectors):**
```bash
cd cloud-functions/detection/statistical
gcloud functions deploy detect-anomalies-statistical \
  --gen2 \
  --runtime python311 \
  --trigger-topic enriched-logs \
  --region us-central1 \
  --entry-point detect_statistical
```

**Response Layer:**
```bash
cd cloud-functions/alerting/alert-manager
gcloud functions deploy alert-manager \
  --gen2 \
  --runtime python311 \
  --trigger-topic alerts \
  --region us-central1 \
  --entry-point manage_alerts \
  --set-env-vars SLACK_WEBHOOK_URL="your-webhook",SENDGRID_API_KEY="your-key"
```

### **5. Deploy Dashboard**
```bash
cd dashboard
firebase deploy --only hosting
```

---

##  Testing

### **Dataset Testing (CIC-IDS-2017)**
```bash
cd datasets

# Convert dataset to NimbusCore format
python convert_dataset.py

# Ingest 100 attack samples
python ingest_dataset.py
```

### **Live Attack Demo**
See [docs/LIVE_DEMO.md](docs/LIVE_DEMO.md) for complete VM setup and attack simulation guide.

---

##  System Requirements

### **Minimum Requirements:**
- **Operating System:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 4GB minimum (8GB recommended)
- **Disk Space:** 2GB free space
- **Internet:** Stable connection (minimum 5 Mbps)
- **Browser:** Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+

### **For Live Demo (Optional):**
- **VirtualBox:** Version 7.0 or higher
- **VM Resources:** 4GB RAM total (2GB per VM)
- **Additional Disk:** 40GB for VM images

### **Developer Requirements:**
- **Python:** 3.11 or higher
- **Node.js:** 16+ (for Firebase CLI)
- **Google Cloud SDK:** Latest version
- **Git:** For version control

---

##  Configuration & Credentials

### **Required API Keys/Credentials:**

1. **Google Cloud Platform:**
   - Create project at https://console.cloud.google.com
   - Enable billing (free tier available)
   - Note your `PROJECT_ID`

2. **Firebase:**
   - Create project at https://console.firebase.google.com
   - Enable Authentication (Email/Password)
   - Enable Firestore Database
   - Enable Hosting
   - Download `firebase-config.js` from project settings

3. **Slack Notifications (Optional):**
   - Create incoming webhook at https://api.slack.com/messaging/webhooks
   - Format: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`

4. **SendGrid Email (Optional):**
   - Sign up at https://sendgrid.com
   - Generate API key from Settings > API Keys
   - Format: `SG.xxxxxxxxxxxxxxxxxxxxx`

### **Environment Variables:**
```bash
# Alert Manager Function
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
SENDGRID_API_KEY="SG.xxxxxxxxxxxxx"
ALERT_EMAIL="your-email@example.com"

# All Functions
GCP_PROJECT="your-project-id"
```

---

##  User Manual

### **Accessing the Dashboard:**
1. Navigate to: `https://your-project-id.web.app`
2. Login with credentials:
   - **Demo Account:** demo@nimbuscore.com / demo123
   - **Create Account:** Click "Sign Up" on login page

### **Dashboard Features:**

**1. Alert Timeline:**
- View recent security alerts in chronological order
- Filter by severity: HIGH, MEDIUM, LOW
- Click alert for detailed information

**2. Threat Map:**
- Red markers = Blocked IP addresses
- Click marker to see IP details, location, block reason
- Map auto-updates every 30 seconds

**3. Metrics Cards:**
- **Total Alerts:** Cumulative detection count
- **Blocked IPs:** Number of banned addresses
- **Active Threats:** HIGH severity alerts in last 24h
- **Detection Rate:** System accuracy percentage

**4. Threat Trends Chart:**
- Shows 7-day alert volume history
- Hover for exact daily counts
- Identifies attack patterns over time

### **Submitting Logs (API):**
```bash
curl -X POST https://your-ingestion-url/ingest_log \
  -H "Content-Type: application/json" \
  -d '{
    "level": "ERROR",
    "source": "web_server",
    "message": "Suspicious activity detected",
    "timestamp": "2026-04-06T10:00:00Z",
    "source_ip": "192.168.1.100",
    "attack_type": "DDoS"
  }'
```

### **Troubleshooting:**

**Problem:** Dashboard shows "No data"
- **Solution:** Check Firestore rules allow read access, verify internet connection

**Problem:** Alerts not appearing
- **Solution:** Verify Cloud Functions are deployed, check function logs with `gcloud functions logs read`

**Problem:** IP blocking not working
- **Solution:** Ensure Firestore composite index created for `alerts` collection (source_ip + timestamp)

---
##  Results

**Dataset Testing (100 attack samples):**
-  100% ingestion success rate
-  150+ alerts generated (3 detectors × 50 attacks)
-  10-20 IPs automatically blocked
-  5-10 scaling events triggered
-  <30 second detection latency

**Live Attack Demonstration:**
-  9 DDoS attacks detected in real-time
-  1 IP automatically blocked after 3 attacks
-  5 auto-scaling events recorded
-  Multi-channel notifications delivered (Slack + Email)

**Cost Efficiency:**
- ~$98/month for 1M logs/day
- 80% cost reduction vs traditional SIEM
- Pay-per-use serverless model

---

##  Key Features Demonstrated

### **Triple Detection System**
- **Statistical Detector** (90% confidence) - Frequency analysis
- **Rule-Based Detector** (95% confidence) - Pattern matching
- **ML Detector** (92% confidence) - Anomaly scoring

### **Automated Response**
- **IP Blocking**: Automatic blocking after 3 attacks within 5 minutes
- **Auto-Scaling**: Dynamic capacity adjustment based on alert volume
- **Multi-Channel Alerts**: Slack + Email notifications

### **Real-Time Dashboard**
- Interactive geolocation map with blocked IP markers
- Threat trend visualization (7-day history)
- Live alert timeline with severity indicators
- System metrics (total alerts, blocked IPs, detection rate)

---

##  Project Highlights

- **Industry-Standard Testing**: Validated with CIC-IDS-2017 benchmark dataset
- **Live Attack Demonstration**: Real-time detection using Kali Linux attacks
- **Production-Grade Architecture**: Serverless, event-driven, fully scalable
- **Cost-Effective**: 80% cheaper than traditional SIEM solutions
- **Comprehensive Documentation**: Full technical documentation and deployment guides

---

##  Team

**Sally Mutemwa** - Backend & Cloud Infrastructure  
**Purity Kinaro** - Frontend & UX Design

**Ashesi University - Computer Science Capstone 2026**

---

##  Contact

- Email: salome.mutemwa@ashesi.edu.gh, purity.moraa@ashesi.edu.gh
- LinkedIn: www.linkedin.com/in/salome-mutemwa
- Project Demo: (https://capstone-log-monitoring.web.app/index.html)

---

##  License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

- Ashesi University CS Department
- Google Cloud Platform (educational credits)
- CIC-IDS-2017 Dataset (Canadian Institute for Cybersecurity)
- Our capstone advisor

