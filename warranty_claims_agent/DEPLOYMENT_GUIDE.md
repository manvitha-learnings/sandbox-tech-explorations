# Warranty Claims Triage Agent: Deployment & Gemini Enterprise Registration Guide

A complete, step-by-step manual for testing, deploying, and registering the **Warranty Claims Triage Agent** (migrated from Glean) with **Gemini Enterprise (Google Cloud Vertex AI Agent Builder & Agent Runtime)**.

---

## 1. Architecture Overview

```
                  +-------------------------------------------------------------+
                  |                      GEMINI ENTERPRISE                      |
                  |          (Google Cloud Vertex AI Agent Builder UI)          |
                  |   Engine: warranty-claims-triage_1789741170801              |
                  |   Agent: Warranty Claims Triage Agent (15381693706825665023)|
                  +-------------------------------------------------------------+
                                                 │
                                                 │ Native lowCodeAgent / Invocations
                                                 v
   +----------------------------------------------------------------------------+
   |                        AGENT RUNTIME (Google Cloud Run)                    |
   |              https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app  |
   |                                                                            |
   |   +--------------------------------------------------------------------+   |
   |   |   FastAPI Service (server.py) + Google ADK Agent (gemini-2.5-flash) |   |
   |   +--------------------------------------------------------------------+   |
   |          │                          │                          │           |
   |          ▼                          ▼                          ▼           |
   |   [Search Tools]             [Skills Engine]            [Action Tools]     |
   |   - Claims DB                - Pattern Clustering       - Create QE Ticket |
   |   - TSB Repository           - Severity Scoring         - Notify Slack     |
   |   - Dealer ROs                                                             |
   |   - QE Wiki                                                                |
   +----------------------------------------------------------------------------+
```

---

## 2. Project Directory Structure

```
warranty_claims_agent/
├── agent.py                        # Google ADK agent definition (gemini-2.5-flash)
├── server.py                       # FastAPI Agent Runtime service
├── deploy_agent.py                 # Automated Cloud Build + Cloud Run deploy script
├── deploy.ps1                      # PowerShell deployment script
├── deploy.sh                       # Bash deployment script
├── requirements.txt                # Dependencies
├── Dockerfile                      # Container definition for Cloud Run
├── test_agent.py                   # Automated test suite (pytest)
├── smoke_test.py                   # End-to-end HTTP smoke test runner
├── gemini_enterprise_openapi.json  # OpenAPI 3.0 specification for Gemini Enterprise
│
├── static/
│   └── index.html                  # Interactive Quality Engineering web dashboard UI
│
├── data/
│   ├── __init__.py
│   └── mock_data.py                # Realistic sample claims, TSBs, ROs, and QE wiki
│
├── tools/
│   ├── __init__.py
│   ├── search_tools.py             # Replaces glean-search across 4 data sources
│   ├── ticket_tools.py             # Replaces create-quality-ticket
│   └── slack_tools.py              # Replaces notify-slack-channel
│
├── skills/
│   ├── __init__.py
│   ├── pattern_clustering.py       # Failure Pattern Clustering skill
│   └── severity_scoring.py         # Severity Scoring skill (1-10 scale)
│
└── gemini_enterprise_json/         # Declarative Gemini Enterprise Bundle
    ├── agent_manifest.json         # Agent manifest for Gemini Enterprise
    ├── examples.json               # Few-shot playbook triage examples
    └── tools/
        ├── qe_ticket_openapi.json  # OpenAPI 3.0 schema for QE ticketing
        ├── slack_notify_openapi.json# OpenAPI 3.0 schema for Slack alerts
        └── search_datastore_tool.json# Data store search binding
```

---

## 3. Step 1: Testing & Local Validation (Pre-Deployment)

### Prerequisites
- Python 3.10+
- `GEMINI_API_KEY` in `.env` (Google AI Studio Gemini API - Free Tier)

### Run Automated Tests
Execute the comprehensive test suite verifying search tools, clustering algorithms, severity scoring, and all 3 Glean prompt trigger scenarios:

```bash
pytest -v test_agent.py
# Or run standalone runner:
python run_tests.py
python smoke_test.py
```

### Start the Local Quality Engineering Dashboard & API
```bash
python server.py
```
- **Interactive Web Dashboard**: [http://localhost:8080/](http://localhost:8080/)
- **Swagger / OpenAPI Documentation**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **Health Check**: [http://localhost:8080/health](http://localhost:8080/health)
- **OpenAPI 3.0 Schema**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)

### Start the Official Google ADK Web UI
```bash
python -m google.adk.cli web --port 8085 .
```
- **Google ADK Dev UI & Execution Trace Graph**: [http://localhost:8085/](http://localhost:8085/)

---

## 4. Step 2: Deploy to Google Cloud Run

### Automated Deployment via `deploy_agent.py`
Runs Google Cloud Build to package the container and deploys to Cloud Run with `GEMINI_API_KEY`:

```bash
python deploy_agent.py
```

### Method B: Manual Step-by-Step Deployment

#### 1. Enable Required Google Cloud APIs
```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    discoveryengine.googleapis.com \
    aiplatform.googleapis.com
```

#### 2. Create Artifact Registry Repository
```bash
gcloud artifacts repositories create agent-runtime-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Repository for Agent Runtime containers"
```

#### 3. Build & Submit Docker Image
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/agent-runtime-repo/warranty-claims-triage-agent:latest .
```

#### 4. Deploy Container to Cloud Run
```bash
gcloud run deploy warranty-claims-triage-agent \
    --image=us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/agent-runtime-repo/warranty-claims-triage-agent:latest \
    --region=us-central1 \
    --platform=managed \
    --no-allow-unauthenticated \
    --set-env-vars="MOCK_DATA_MODE=true,MODEL_NAME=gemini-2.5-flash"
```

After deployment completes, retrieve your live service URL:
```bash
SERVICE_URL=$(gcloud run services describe warranty-claims-triage-agent --region=us-central1 --format='value(status.url)')
echo "Service deployed at: $SERVICE_URL"
```

---

## 5. Step 3: Register with Gemini Enterprise

The agent is registered in **Gemini Enterprise** (Google Cloud Vertex AI Agent Builder / Gen App Builder):

* **Project**: `project-83b9dd42-537f-47c6-a28`
* **Gemini Enterprise Engine**: `warranty-claims-triage_1789741170801`
* **Registered Agent**: **`Warranty Claims Triage Agent`** (`15381693706825665023`)
* **Agent Architecture**: `lowCodeAgentDefinition` (Native Gemini Enterprise Agent)
* **Model**: **`gemini-2.5-flash`**
* **Invocation Mode**: `AUTOMATIC`

### Direct Access Console Links:
- **Gemini Enterprise Preview & Chat**:  
  [Open Gemini Enterprise Preview](https://console.cloud.google.com/gen-app-builder/engines/warranty-claims-triage_1789741170801/preview?project=project-83b9dd42-537f-47c6-a28)
- **Gemini Enterprise Agent Studio**:  
  [Open Agent Studio](https://console.cloud.google.com/gen-app-builder/engines/warranty-claims-triage_1789741170801/agents/15381693706825665023?project=project-83b9dd42-537f-47c6-a28)
- **Cloud Run Agent Runtime**:  
  [https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app](https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app)
- **OpenAPI Tool Schema**:  
  [https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/openapi.json](https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/openapi.json)

---

## 6. Step 4: Verification & Testing in Gemini Enterprise

Once registered, open the **Preview / Test** console in Gemini Enterprise or your enterprise chat window and test the 3 trigger queries:

### Query 1: Recurring Issues Investigation
> **User Prompt**:
> *"Any recurring issues with the Model X rear axle claims this month?"*

**Expected Agent Flow**:
1. Agent queries `search_warranty_claims` for `Model X` / `Rear Axle Assembly`.
2. Agent detects 4 claims matching VIN prefix `1XYZ4A2X`.
3. Agent cross-references `search_dealer_repair_orders` and flags DTC `P079A` and metallic flakes.
4. Agent correlates with `TSB-25-03-014` (*Pinion bearing noise and fluid contamination*).
5. Agent calculates severity score: **CRITICAL (9.0/10)** due to axle lockup risk.
6. Agent invokes `create_quality_ticket` creating ticket `QE-2026-101`.
7. Agent invokes `notify_warranty_qe_channel` dispatching an alert to `#warranty-qe`.
8. Agent outputs formatted executive summary table.

---

### Query 2: VIN Prefix Summary
> **User Prompt**:
> *"Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days"*

**Expected Agent Flow**:
1. Agent filters claims by `vin_prefix = "1XYZ4A2X"`.
2. Returns total count (4), affected mileage range (9,800 - 16,450 miles), total warranty parts liability ($11,630.00), and technician findings.

---

### Query 3: TSB Matching
> **User Prompt**:
> *"Does this claim match any open TSB for Model X rear axle whine?"*

**Expected Agent Flow**:
1. Agent searches TSB repository for symptoms `whine`, `vibration`, `Model X`.
2. Confirms match with **TSB-25-03-014** (Status: OPEN).
3. Displays root cause (sub-supplier metallurgical hardening defect) and repair procedure (magnetic plug inspection and subassembly replacement).

---

## 7. Security & IAM Configuration

To allow Gemini Enterprise / Vertex AI Agent Builder to securely call your Cloud Run service:

```bash
# 1. Create a dedicated service account for Gemini Enterprise
gcloud iam service-accounts create gemini-agent-invoker \
    --display-name="Gemini Enterprise Agent Invoker"

# 2. Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding warranty-claims-triage-agent \
    --region=us-central1 \
    --member="serviceAccount:gemini-agent-invoker@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```
