#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No active gcloud project found. Please run 'gcloud config set project [PROJECT_ID]' first."
    exit 1
fi

echo "=========================================================="
echo "Starting deployment of Product Research Agent to Cloud Run"
echo "Project ID: $PROJECT_ID"
echo "Region:     $REGION"
echo "=========================================================="

# Read GEMINI_API_KEY from backend/.env or ask for it
GEMINI_API_KEY=""
if [ -f "backend/.env" ]; then
    GEMINI_API_KEY=$(grep "GEMINI_API_KEY" backend/.env | cut -d '=' -f2)
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" == "your_gemini_api_key_here" ]; then
    read -sp "Enter your GEMINI_API_KEY: " GEMINI_API_KEY
    echo ""
fi

# Step 1: Build and deploy the MCP Server
echo "----------------------------------------------------------"
echo "Step 1: Building and Deploying Product MCP Server..."
echo "----------------------------------------------------------"

gcloud builds submit --tag gcr.io/$PROJECT_ID/product-mcp-server ./mcp_server

gcloud run deploy product-mcp-server \
    --image gcr.io/$PROJECT_ID/product-mcp-server \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8081 \
    --quiet

# Capture the service URL
MCP_URL=$(gcloud run services describe product-mcp-server --platform managed --region $REGION --format 'value(status.url)')
echo "MCP Server successfully deployed to: $MCP_URL"

# Step 2: Build and deploy the ADK Agent Backend
echo "----------------------------------------------------------"
echo "Step 2: Building and Deploying Product Research Backend..."
echo "----------------------------------------------------------"

gcloud builds submit --tag gcr.io/$PROJECT_ID/product-research-backend ./backend

gcloud run deploy product-research-backend \
    --image gcr.io/$PROJECT_ID/product-research-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "PRODUCT_MCP_URL=${MCP_URL}/sse,GEMINI_API_KEY=${GEMINI_API_KEY},GOOGLE_API_USE_CLIENT_CERTIFICATE=false" \
    --port 8080 \
    --quiet

# Capture the backend URL
BACKEND_URL=$(gcloud run services describe product-research-backend --platform managed --region $REGION --format 'value(status.url)')

echo "=========================================================="
echo "Deployment Complete!"
echo "Product MCP Server:   $MCP_URL"
echo "React Web App & API:  $BACKEND_URL"
echo "=========================================================="
