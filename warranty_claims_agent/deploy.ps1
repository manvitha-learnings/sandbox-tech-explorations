# ==============================================================================
# Warranty Claims Triage Agent - PowerShell Cloud Run Deploy & Registration Script
# ==============================================================================

$ErrorActionPreference = "Stop"

$GCLOUD = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $GCLOUD)) {
    $GCLOUD = "gcloud"
}

# Determine project & region
$PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
if (-not $PROJECT_ID) {
    $PROJECT_ID = (& $GCLOUD config get-value project 2>$null).Trim()
}

$REGION = $env:GOOGLE_CLOUD_REGION
if (-not $REGION) {
    $REGION = "us-central1"
}

$SERVICE_NAME = "warranty-claims-triage-agent"
$REPO_NAME = "agent-runtime-repo"
$IMAGE_TAG = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/${SERVICE_NAME}:latest"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Agent Runtime Deployment for Gemini Enterprise" -ForegroundColor Cyan
Write-Host " Project: $PROJECT_ID | Region: $REGION" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $PROJECT_ID) {
    Write-Host "ERROR: No GCP Project configured. Run 'gcloud config set project <ID>'" -ForegroundColor Red
    exit 1
}

# 1. Enable Required GCP APIs
Write-Host "--> [Step 1/4] Enabling required GCP APIs..." -ForegroundColor Yellow
& $GCLOUD services enable run.googleapis.com artifactregistry.googleapis.com discoveryengine.googleapis.com aiplatform.googleapis.com --project=$PROJECT_ID

# 2. Create Artifact Registry Repository if it doesn't exist
Write-Host "--> [Step 2/4] Ensuring Artifact Registry repository exists..." -ForegroundColor Yellow
$repoCheck = & $GCLOUD artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID 2>$null
if (-not $repoCheck) {
    & $GCLOUD artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --description="Repository for Agent Runtime containers" --project=$PROJECT_ID
}

# 3. Build & Submit Docker image via Google Cloud Build (no local Docker daemon required)
Write-Host "--> [Step 3/4] Building container in Google Cloud Build..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
& $GCLOUD builds submit --tag $IMAGE_TAG --project=$PROJECT_ID .

# 4. Deploy to Cloud Run (Agent Runtime)
Write-Host "--> [Step 4/4] Deploying to Cloud Run..." -ForegroundColor Yellow
& $GCLOUD run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --region=$REGION `
    --platform=managed `
    --no-allow-unauthenticated `
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=false,MOCK_DATA_MODE=true,MODEL_NAME=gemini-2.5-flash" `
    --project=$PROJECT_ID

$SERVICE_URL = (& $GCLOUD run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" --project=$PROJECT_ID).Trim()

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host " Live Service Endpoint: $SERVICE_URL" -ForegroundColor Green
Write-Host " Health Check: $SERVICE_URL/health" -ForegroundColor Green
Write-Host " Interactive OpenAPI UI: $SERVICE_URL/docs" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
