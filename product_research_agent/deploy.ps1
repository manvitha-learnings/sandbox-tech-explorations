# Configuration
$Region = "us-central1"
$ProjectId = gcloud config get-value project 2>$null

if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-Error "ERROR: No active gcloud project found. Please run 'gcloud config set project [PROJECT_ID]' first."
    Exit 1
}

Write-Host "=========================================================="
Write-Host "Starting deployment of Product Research Agent to Cloud Run"
Write-Host "Project ID: $ProjectId"
Write-Host "Region:     $Region"
Write-Host "=========================================================="

# Read GEMINI_API_KEY from backend/.env or ask for it
$GeminiApiKey = ""
$EnvPath = Join-Path "backend" ".env"
if (Test-Path $EnvPath) {
    $EnvContent = Get-Content $EnvPath
    foreach ($Line in $EnvContent) {
        if ($Line -match "^GEMINI_API_KEY=(.*)") {
            $GeminiApiKey = $Matches[1].Trim()
        }
    }
}

if ([string]::IsNullOrEmpty($GeminiApiKey) -or $GeminiApiKey -eq "your_gemini_api_key_here") {
    $GeminiApiKey = Read-Host -Prompt "Enter your GEMINI_API_KEY"
}

# Step 1: Build and deploy the MCP Server
Write-Host "----------------------------------------------------------"
Write-Host "Step 1: Building and Deploying Product MCP Server..."
Write-Host "----------------------------------------------------------"

gcloud builds submit --tag "gcr.io/$ProjectId/product-mcp-server" ./mcp_server

gcloud run deploy product-mcp-server `
    --image "gcr.io/$ProjectId/product-mcp-server" `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --port 8081 `
    --quiet

# Capture the service URL
$McpUrl = gcloud run services describe product-mcp-server --platform managed --region $Region --format 'value(status.url)'
Write-Host "MCP Server successfully deployed to: $McpUrl"

# Step 2: Build and deploy the ADK Agent Backend
Write-Host "----------------------------------------------------------"
Write-Host "Step 2: Building and Deploying Product Research Backend..."
Write-Host "----------------------------------------------------------"

gcloud builds submit --tag "gcr.io/$ProjectId/product-research-backend" ./backend

gcloud run deploy product-research-backend `
    --image "gcr.io/$ProjectId/product-research-backend" `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars "PRODUCT_MCP_URL=${McpUrl}/sse,GEMINI_API_KEY=${GeminiApiKey},GOOGLE_API_USE_CLIENT_CERTIFICATE=false" `
    --port 8080 `
    --quiet

# Capture the backend URL
$BackendUrl = gcloud run services describe product-research-backend --platform managed --region $Region --format 'value(status.url)'

Write-Host "=========================================================="
Write-Host "Deployment Complete!"
Write-Host "Product MCP Server:   $McpUrl"
Write-Host "React Web App & API:  $BackendUrl"
Write-Host "=========================================================="
