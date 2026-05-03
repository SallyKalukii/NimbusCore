#!/bin/bash

echo " Deploying all Cloud Functions..."

cd ~/Documents/capstone-log-monitoring/cloud-functions

# Detection functions
echo "1/5 Deploying statistical detector..."
cd detection/statistical
gcloud functions deploy detect-anomalies-statistical --gen2 --runtime python311 --trigger-topic processed-logs --region us-central1 --entry-point detect_statistical --timeout 540s --memory 256MB --quiet

echo "2/5 Deploying rules detector..."
cd ../rule-detector
gcloud functions deploy detect-anomalies-rules --gen2 --runtime python311 --trigger-topic processed-logs --region us-central1 --entry-point detect_rules --timeout 540s --memory 256MB --quiet

echo "3/5 Deploying ML detector..."
cd ../ml-detector
gcloud functions deploy detect-anomalies-ml --gen2 --runtime python311 --trigger-topic processed-logs --region us-central1 --entry-point detect_ml --timeout 540s --memory 512MB --quiet

# Response functions
echo "4/5 Deploying alert manager..."
cd ../../alerting/alert-manager
gcloud functions deploy alert-manager --gen2 --runtime python311 --trigger-topic alerts --region us-central1 --entry-point manage_alerts --timeout 540s --memory 256MB --quiet

echo "5/5 Deploying IP blocker..."
cd ../ip-blocker
gcloud functions deploy ip-blocker --gen2 --runtime python311 --trigger-topic alerts --region us-central1 --entry-point block_ip --timeout 540s --memory 256MB --quiet

echo "6/6 Deploying auto-scaler..."
cd ../auto-scaler
gcloud functions deploy auto-scaler --gen2 --runtime python311 --trigger-topic alerts --region us-central1 --entry-point auto_scale --timeout 540s --memory 256MB --quiet

echo " All functions deployed!"