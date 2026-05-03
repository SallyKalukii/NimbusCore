
# Deployment Guide

Complete guide to deploying the log monitoring system.

---

## Prerequisites

- Google Cloud Platform account
- gcloud CLI installed and configured
- Python 3.11+
- Git

---

## Initial Setup

### 1. Create GCP Project
```bash
# Set project ID
export PROJECT_ID="capstone-log-monitoring"

# Create project
gcloud projects create $PROJECT_ID

# Set as default
gcloud config set project $PROJECT_ID

# Enable billing (required)
# Go to: https://console.cloud.google.com/billing
```

### 2. Enable Required APIs
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. Create Pub/Sub Topics
```bash
gcloud pubsub topics create raw-logs
gcloud pubsub topics create processed-logs
gcloud pubsub topics create alerts

gcloud pubsub subscriptions create process-logs-sub --topic=raw-logs
gcloud pubsub subscriptions create detect-anomalies-sub --topic=processed-logs
gcloud pubsub subscriptions create send-alerts-sub --topic=alerts
```

### 4. Initialize Firestore
```bash
gcloud firestore databases create --location=us-east1 --type=firestore-native
```

### 5. Create Storage Buckets
```bash
gsutil mb -l us-east1 gs://${PROJECT_ID}-ml-models
gsutil mb -l us-east1 gs://${PROJECT_ID}-deployments
gsutil mb -l us-east1 gs://${PROJECT_ID}-backups
```

---

## Deploy Functions

### 1. Deploy Ingestion Function
```bash
cd cloud-functions/ingestion

gcloud functions deploy ingest_log \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --region us-east1 \
    --entry-point ingest_log \
    --memory 256MB \
    --timeout 60s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID
```

**Save the URL displayed after deployment!**

### 2. Deploy Parser Function
```bash
cd ../processing/parser

gcloud functions deploy parse_log \
    --runtime python311 \
    --trigger-topic raw-logs \
    --region us-east1 \
    --entry-point parse_log_event \
    --memory 512MB \
    --timeout 60s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID
```

### 3. Deploy Enrichment Function
```bash
cd ../enrichment

gcloud functions deploy enrich_log \
    --runtime python311 \
    --trigger-topic processed-logs \
    --region us-east1 \
    --entry-point enrich_log_event \
    --memory 512MB \
    --timeout 60s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID
```

---

## Verify Deployment

### Test Ingestion
```bash
INGESTION_URL="<your-function-url>"

curl -X POST $INGESTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "source": "deployment-test",
    "message": "Testing deployment"
  }'
```

### Check Logs
```bash
# View function logs
gcloud functions logs read ingest_log --region us-east1 --limit 10
gcloud functions logs read parse_log --region us-east1 --limit 10
gcloud functions logs read enrich_log --region us-east1 --limit 10
```

### Check Firestore
```bash
# Go to Firestore console
https://console.cloud.google.com/firestore/data/logs?project=$PROJECT_ID
```

---

## Monitoring

### Set Up Billing Alerts

1. Go to: https://console.cloud.google.com/billing
2. Select your billing account
3. Click "Budgets & alerts"
4. Create budget: $30/month
5. Set alerts at: 50%, 75%, 90%, 100%

### View Metrics
```bash
# Cloud Functions metrics
https://console.cloud.google.com/functions

# Pub/Sub metrics
https://console.cloud.google.com/cloudpubsub

# Firestore metrics
https://console.cloud.google.com/firestore
```

---

## Troubleshooting

### Function Not Deploying
```bash
# Check build logs
gcloud functions logs read <function-name> --region us-east1 --limit 50

# Common issues:
# - requirements.txt missing dependencies
# - Python indentation errors
# - Missing environment variables
```

### Messages Not Processing
```bash
# Check Pub/Sub backlog
gcloud pubsub subscriptions describe process-logs-sub

# Pull messages manually
gcloud pubsub subscriptions pull process-logs-sub --limit 5

# Check if functions are triggered
gcloud functions logs read parse_log --region us-east1
```

### No Data in Firestore
```bash
# Check enrichment function logs
gcloud functions logs read enrich_log --region us-east1 --limit 20

# Verify Firestore is initialized
gcloud firestore databases list

# Check Firestore rules (shouldn't block Cloud Functions)
```

---

## Update/Redeploy

### Update Function Code
```bash
cd cloud-functions/ingestion

# Edit main.py
# ...

# Redeploy
gcloud functions deploy ingest_log \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --region us-east1
```

### Roll Back
```bash
# List function versions
gcloud functions describe ingest_log --region us-east1

# Deploy previous version (manual)
# Keep previous code in Git, checkout and redeploy
```

---

## Cleanup (When Done)

**⚠️ WARNING: This deletes everything!**
```bash
# Delete functions
gcloud functions delete ingest_log --region us-east1 --quiet
gcloud functions delete parse_log --region us-east1 --quiet
gcloud functions delete enrich_log --region us-east1 --quiet

# Delete Pub/Sub
gcloud pubsub topics delete raw-logs --quiet
gcloud pubsub topics delete processed-logs --quiet
gcloud pubsub topics delete alerts --quiet

# Delete Firestore
# (Manual via console - be careful!)

# Delete storage buckets
gsutil -m rm -r gs://${PROJECT_ID}-ml-models
gsutil -m rm -r gs://${PROJECT_ID}-deployments
gsutil -m rm -r gs://${PROJECT_ID}-backups

# Delete project (removes everything)
gcloud projects delete $PROJECT_ID
```

---

**Last Updated:** January 21, 2025
