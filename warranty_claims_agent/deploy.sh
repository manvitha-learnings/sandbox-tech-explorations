#!/bin/bash
# ==============================================================================
# Warranty Claims Triage Agent - Cloud Run Deploy & Gemini Enterprise Registration
# ==============================================================================

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME="warranty-claims-triage-agent"
REPO_NAME="agent-runtime-repo"
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"

echo "========================================================"
echo " Starting Agent Runtime Deployment for Gemini Enterprise"
echo " Project: $PROJECT_ID | Region: $REGION"
echo "========================================================"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GOOGLE_CLOUD_PROJECT is not set. Please set it or run 'gcloud config set project <PROJECT_ID>'"
    exit 1
fi

# 1. Enable Required GCP APIs
echo "--> [Step 1/5] Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    discoveryengine.googleapis.com \
    aiplatform.googleapis.com \
    --project="$PROJECT_ID"

# 2. Create Artifact Registry Repository if not exists
echo "--> [Step 2/5] Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1 || \
gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repository for Agent Runtime images" \
    --project="$PROJECT_ID"

# 3. Build & Push Docker Image
echo "--> [Step 3/5] Building and pushing Docker container image..."
gcloud builds submit --tag "$IMAGE_TAG" --project="$PROJECT_ID" .

# 4. Deploy to Cloud Run (Agent Runtime)
echo "--> [Step 4/5] Deploying container to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --region="$REGION" \
    --platform=managed \
    --no-allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=false,MOCK_DATA_MODE=true,MODEL_NAME=gemini-2.5-flash" \
    --project="$PROJECT_ID"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID")
echo " Cloud Run service successfully deployed to: $SERVICE_URL"

# 5. Register with Gemini Enterprise
echo "--> [Step 5/5] Registering agent and OpenAPI tools with Gemini Enterprise..."
python gemini_enterprise_json/register_via_json.py

echo "========================================================"
echo " Deployment & Registration Complete!"
echo " Service Endpoint: $SERVICE_URL"
echo " Gemini Enterprise can now invoke the Warranty Claims Triage Agent."
echo "========================================================"
