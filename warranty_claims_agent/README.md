# Warranty Claims Triage Agent: Complete Architecture & Deployment Guide

> **Enterprise-Grade AI Agent for Automated Automotive Warranty Claims Triage, Defect Spike Detection, TSB Matching, and Quality Engineering Escalation.**  
> *Migrated from Glean No-Code to Google Gemini Enterprise & Vertex AI Agent Runtime.*

---

## Table of Contents
1. [Executive Summary & Background](#1-executive-summary--background)
2. [What the Agent Does & Why](#2-what-the-agent-does--why)
3. [Architecture & Technical Design](#3-architecture--technical-design)
4. [How the Agent Was Created (Code Breakdown)](#4-how-the-agent-was-created-code-breakdown)
   - [A. Data Layer (`data/mock_data.py`)](#a-data-layer-datamock_datapy)
   - [B. Skills Layer (`skills/`)](#b-skills-layer-skills)
   - [C. Tools Layer (`tools/`)](#c-tools-layer-tools)
   - [D. Agent Core (`agent.py` & `gemini_agent.py`)](#d-agent-core-agentpy--gemini_agentpy)
   - [E. API Server (`server.py`)](#e-api-server-serverpy)
5. [Testing & Quality Assurance](#5-testing--quality-assurance)
   - [Automated Test Suite (`run_tests.py`)](#automated-test-suite-run_testspy)
   - [Live Smoke Tests (`smoke_test.py`)](#live-smoke-tests-smoke_testpy)
6. [Deployment to Agent Runtime (What and How)](#6-deployment-to-agent-runtime-what-and-how)
   - [Architecture & Runtime Overview](#architecture--runtime-overview)
   - [Deployment Workflow: deploy_agent.py](#deployment-workflow-deploy_agentpy)
   - [Critical Upstream Fixes & Free Tier Architecture](#critical-upstream-engineering-fixes-applied)
   - [Live Deployment Specifications](#live-deployment-specifications)
7. [Registration in Gemini Enterprise](#7-registration-in-gemini-enterprise)
   - [Direct Access Console Links](#direct-access-links)
   - [Pre-Configured Starter Prompts](#pre-configured-starter-prompts-in-gemini-enterprise)
8. [End-to-End Operational Query Walkthroughs](#8-end-to-end-operational-query-walkthroughs)
9. [Project Directory Reference](#9-project-directory-reference)
10. [Technical FAQ & Architecture Review Questions (Expected Q&A)](#10-technical-faq--architecture-review-questions-expected-qa)
11. [Engineering Journey: Chronological Build Log (How We Actually Built and Deployed It)](#11-engineering-journey-chronological-build-log-how-we-actually-built-and-deployed-it)

---

## 1. Executive Summary & Background

Automotive manufacturing organizations face thousands of warranty claims, dealer repair orders (ROs), and Technical Service Bulletins (TSBs) every month. Manually reading, cross-referencing, and prioritizing these documents is slow, resulting in:
- **Delayed Defect Discovery**: Engineering teams notice recurring component failures weeks or months late.
- **Uncontrolled Financial Liability**: Repeated claims cost millions before root causes are contained.
- **Safety Hazards**: Critical faults (wheel lockups, loss of propulsion, steering failure) risk regulatory recalls (NHTSA) if not escalated within hours.

### Why Migrate from Glean to Gemini Enterprise?
The original agent existed as a **no-code JSON specification in Glean**. While useful for simple searches, moving to **Google Gemini Enterprise & Agent Runtime** provides:
1. **True Agentic Autonomy**: High-speed reasoning with `gemini-2.5-flash` with native function calling and multi-step tool execution.
2. **Standardized Severity Scoring**: Objective, code-based mathematical risk calculation (1–10 scale) rather than loose heuristics.
3. **Enterprise Portability**: Standard OpenAPI 3.0 interfaces, Docker containerization, and native Google Cloud IAM authentication.
4. **Seamless Integration**: Directly accessible to engineers within Google Workspace, Gemini Enterprise Chat, or internal ERP/Jira systems.

---

## 2. What the Agent Does & Why

The **Warranty Claims Triage Agent** acts as an always-on assistant for **Quality Engineering (QE)** and **Warranty Operations** teams:

```
[ Incoming Claims & Repair Orders ]
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│              WARRANTY CLAIMS TRIAGE AGENT               │
│                                                         │
│ 1. Search claims & dealer diagnostic orders             │
│ 2. Cluster recurring failure modes by VIN prefix        │
│ 3. Match against known open TSB bulletins               │
│ 4. Compute standardized 1-10 severity score             │
│ 5. Auto-escalate: Create QE Ticket & Alert #warranty-qe │
└─────────────────────────────────────────────────────────┘
               │
               ▼
[ Structured Triage Report + Jira Ticket + Slack Alert ]
```

### Core Responsibilities:
1. **Multi-Source Ingestion & Search**: Simultaneously searches across warranty claims databases, dealership technician repair orders, Technical Service Bulletins, and internal QE wiki protocols.
2. **Failure Pattern Clustering**: Automatically groups related defect descriptions (e.g. *"whining"*, *"differential grinding"*, *"bearing wear"*) by component and 8-character VIN prefix batch (e.g. `1XYZ4A2X`).
3. **TSB & Diagnostic Trouble Code (DTC) Matching**: Flags whether symptoms correlate with known active manufacturer bulletins (e.g. `TSB-25-03-014`) and diagnostic trouble codes (e.g. `P079A`).
4. **Severity Scoring (1–10)**: Categorizes defects into `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` based on safety severity, recurrence volume, and parts liability.
5. **Automated Escalation**: When critical safety risks or $\ge 3$ recurring claims are detected, it automatically creates a QE Investigation Ticket in Jira/ServiceNow and posts an urgent card to the `#warranty-qe` Slack channel.

---

## 3. Architecture & Technical Design

The system is designed with a clean separation of concerns:

```
+-----------------------------------------------------------------------------------+
|                        GEMINI ENTERPRISE (CLOUD CONSOLE)                          |
|                                                                                   |
|  [Primary Interface] Gemini Enterprise Chat & Agent Studio                       |
|    Engine: warranty-claims-triage_1789741170801                                   |
|    Agent: Warranty Claims Triage Agent (ID: 15381693706825665023)                 |
|    Model: gemini-2.5-flash via Google Gemini API (100% Free Tier, No Vertex AI)   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                     AGENT RUNTIME (Google Cloud Run Service)                      |
|                     https://warranty-claims-triage-agent...                       |
|                                                                                   |
|   ┌───────────────────────────────────────────────────────────────────────────┐   |
|   │               FastAPI + Google ADK Agent Core (server.py)                 │   |
|   │               Model: gemini-2.5-flash | Gemini Developer API              │   |
|   │          Environment: GEMINI_API_KEY (100% Free Tier, Zero Vertex AI)      │   |
|   └───────────────────────────────────────────────────────────────────────────┘   |
|            │                                │                       │             |
|            ▼                                ▼                       ▼             |
|   ┌─────────────────┐             ┌──────────────────┐    ┌─────────────────┐     |
|   │  Search Tools   │             │  Skills Engine   │    │  Action Tools   │     |
|   │ - Claims DB     │             │ - Clustering     │    │ - Create Ticket │     |
|   │ - TSB Repo      │             │ - Severity Score │    │ - Slack Alerts  │     |
|   │ - Dealer ROs    │             └──────────────────┘    └─────────────────┘     |
|   │ - QE Wiki       │                                                             |
|   └─────────────────┘                                                             |
+-----------------------------------------------------------------------------------+
```

---

## 4. How the Agent Was Created (Code Breakdown)

### A. Data Layer (`data/mock_data.py`)
Provides realistic, domain-specific automotive warranty data for testing without needing external databases:
* **`WARRANTY_CLAIMS_DB`**: 6 sample claims highlighting Model X rear axle failures (`1XYZ4A2X8P1098231`), customer complaints, parts costs ($2,450 – $3,400), and mileage.
* **`TSB_REPOSITORY`**: Manufacturer service bulletins (`TSB-25-03-014`) detailing root causes (*pinion bearing metallurgical hardening inconsistency*) and repair procedures.
* **`DEALER_REPAIR_ORDERS`**: Dealership technician road tests, fluid inspections (*metallic flakes*), and DTC codes (`P079A`, `P0730`).
* **`QUALITY_ENGINEERING_WIKI`**: Official SOPs (`WIKI-QE-042` and `WIKI-QE-019`) establishing escalation rules.

### B. Skills Layer (`skills/`)
1. **`pattern_clustering.py`**:
   - Groups claims and repair orders by `(component, vin_prefix, model)`.
   - Aggregates average mileage, total financial cost, and extracts symptom keywords (*whining, grinding, vibration, lockup*).
2. **`severity_scoring.py`**:
   - Implements the 1–10 scoring rubric:
     - Safety hazards (*lockup, seizure, loss of power*): **+4.0**
     - Recurrence ($\ge 4$ claims: **+3.0**; $\ge 2$ claims: **+2.0**)
     - High repair liability ($> \$3,000$): **+2.0**
     - Active Open TSB correlation: **+1.0**
   - Outputs severity tier: `CRITICAL` ($\ge 8.5$), `HIGH` ($\ge 6.5$), `MEDIUM` ($\ge 4.0$), `LOW` ($< 4.0$).

### C. Tools Layer (`tools/`)
Python functions equipped with type hints and docstrings that Gemini invokes via Function Calling:
- `search_warranty_claims(model, vin_prefix, component, keyword)`
- `search_tsb_repository(model, component, symptom_or_dtc, tsb_id)`
- `search_dealer_repair_orders(vin_prefix, model, dtc_code, keyword)`
- `search_quality_engineering_wiki(topic)`
- `create_quality_ticket(...)`: Generates ticket IDs (e.g. `QE-2026-101`) with complete audit trails.
- `notify_warranty_qe_channel(...)`: Builds structured Slack Block Kit alert payloads.

### D. Agent Core (`agent.py` & `gemini_agent.py`)
- Initializes the Google ADK `Agent` instance using `gemini-2.5-flash`.
- Registers all 8 tools and skills.
- Configures `GOOGLE_GENAI_USE_VERTEXAI="false"` to route LLM queries through the **Google Gemini Developer API** (`GEMINI_API_KEY`) for rapid, direct response streaming.

### E. API Server (`server.py`)
- Built with **FastAPI** to serve the agent in web and containerized environments.
- Exposes:
  - `GET /health`: Liveness and readiness probe for Cloud Run / Kubernetes.
  - `POST /api/v1/triage`: Structured REST endpoint for enterprise apps and OpenAPI tools.
  - `POST /chat`: Native compatibility endpoint with Glean's message block format (`{"messages": [...]}`).
  - `GET /openapi.json`: Self-documenting OpenAPI 3.0 specification for Gemini Enterprise registration.

---

## 5. Testing & Quality Assurance

### Automated Test Suite (`run_tests.py`)
17 automated unit and integration tests covering every subsystem:
```bash
python run_tests.py
```
**Results (17/17 Passed)**:
- `[PASS]` Search claims by model
- `[PASS]` Search claims by VIN prefix
- `[PASS]` Search claims by component
- `[PASS]` Search TSB repository
- `[PASS]` Search dealer repair orders
- `[PASS]` Search QE wiki
- `[PASS]` Severity scoring: CRITICAL
- `[PASS]` Severity scoring: LOW
- `[PASS]` Failure pattern clustering
- `[PASS]` Action: Create QE ticket
- `[PASS]` Action: Notify Slack channel
- `[PASS]` Scenario 1: Recurring Model X axle
- `[PASS]` Scenario 2: VIN prefix summary
- `[PASS]` Scenario 3: Open TSB matching
- `[PASS]` Server: Health endpoint
- `[PASS]` Server: Triage API endpoint
- `[PASS]` Server: Glean chat compatibility

### Live Smoke Tests (`smoke_test.py`)
Validates live HTTP request/response payloads:
```bash
python smoke_test.py
```
**Results (4/4 Passed)**:
1. `GET /health` $\rightarrow$ `200 OK` (Service status healthy)
2. `GET /openapi.json` $\rightarrow$ `200 OK` (OpenAPI 3.0 schema complete)
3. `POST /api/v1/triage` $\rightarrow$ `200 OK` (Detected Model X cluster, matched `TSB-25-03-014`, scored CRITICAL 10/10, auto-created ticket `QE-2026-101`, and posted Slack alert)
4. `POST /chat` $\rightarrow$ `200 OK` (Glean message schema fully compatible)

---

## 6. Deployment to Agent Runtime (What and How)

### Architecture & Runtime Overview

The **Warranty Claims Triage Agent** is deployed to the **Agent Runtime on Google Cloud Run**, running containerized Python with Google ADK and FastAPI, powered by **`gemini-2.5-flash`** via the Google Gemini API (`GEMINI_API_KEY`). This architecture provides full agentic autonomy on the **Free Tier** without Vertex AI billing dependencies.

| Layer / Component | Technology / Specification | Purpose |
|---|---|---|
| **Agent Framework** | `google-adk` | Core agent definition, tool binding, and multi-step reasoning. |
| **Agent Runtime Platform** | **Google Cloud Run** | Managed serverless container execution environment. |
| **LLM Model** | **Gemini 2.5 Flash** (`gemini-2.5-flash`) | Fast reasoning, TSB cross-referencing, and triage generation via Google Gemini API. |
| **Container Registry** | **Google Artifact Registry** | `agent-runtime-repo/warranty-claims-triage-agent:latest` |
| **Build Pipeline** | **Google Cloud Build** | Builds and publishes the runtime container from source. |
| **API Server** | **FastAPI + Uvicorn** | Serves REST triage endpoints, health probes, and OpenAPI 3.0 schemas. |
| **Gemini Enterprise Engine** | `warranty-claims-triage_1789741170801` | Intranet engine hosting the registered agent in Google Cloud Console. |
| **Registered Agent** | `Warranty Claims Triage Agent` (`15381693706825665023`) | Native `lowCodeAgentDefinition` with starter prompts and chat capabilities. |

---

### Deployment Workflow: `deploy_agent.py`

To deploy updates to the Cloud Agent Runtime:
```bash
python deploy_agent.py
```

#### What Happens Behind the Scenes:
1. **Container Build**: Google Cloud Build compiles the Docker image and pushes it to:  
   `us-central1-docker.pkg.dev/project-83b9dd42-537f-47c6-a28/agent-runtime-repo/warranty-claims-triage-agent:latest`
2. **Cloud Run Deployment**: Provisions or updates the Cloud Run service with:
   - `GEMINI_API_KEY` (Google Gemini API)
   - `MODEL_NAME=gemini-2.5-flash`
   - `MOCK_DATA_MODE=true`
3. **Health Check & Schema Export**:
   - Queries `GET /health` to confirm liveness (`200 OK`).
   - Exports the live OpenAPI 3.0 specification to [`gemini_enterprise_openapi.json`](gemini_enterprise_openapi.json).

### Critical Upstream Engineering Fixes Applied

During deployment, we encountered and resolved three real-world technical hurdles:

1. **Pydantic Dependency Conflict**:
   - *Problem*: `google-adk 2.6.2` strictly required `pydantic>=2.12.0`, while initial requirements had pinned `pydantic==2.10.6`, causing `pip` resolution to fail.
   - *Fix*: Loosened the range to `pydantic>=2.12.0,<3.0.0` in `requirements.txt`.
2. **Upstream Python 3.10 PEP 613 `TypeAlias` Bug in Vertex AI SDK**:
   - *Problem*: In `vertexai/_genai/_agent_engines_utils.py` (line 310), Google's SDK wrote:
     ```python
     ADKAgent: Optional[TypeAlias] = BaseAgent
     ```
     Under Python 3.10, PEP 613 forbids using `TypeAlias` inside `Optional[...]`, crashing the client with:
     `TypeError: Plain typing.TypeAlias is not valid as type argument`.
   - *Fix*: Patched line 310 to:
     ```python
     ADKAgent: TypeAlias = BaseAgent
     ```
     This completely eliminated the import failure and allowed the Agent Platform client to initialize cleanly.
3. **Windows Terminal Code Page 1252 (`charmap`) Codec Trap**:
   - *Problem*: At the end of deployment, the ADK CLI attempted to print a celebration party popper emoji (`🎉` / `\U0001f389`). On Windows consoles running code page 1252, this raised a harmless `UnicodeEncodeError` after the cloud deployment was already 100% finished.
   - *Verification*: Querying the Google Cloud API confirmed the Reasoning Engine resource `9057024173909475328` was created and active.

---

### Live Deployment Specifications
* **Hosting Platform**: Google Cloud Run
* **Live Service Endpoint**: `https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app`
* **Health Check**: `https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/health`
* **Interactive Docs**: `https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/docs`
* **OpenAPI 3.0 Schema**: `https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/openapi.json`
* **Generated Schema File**: [`gemini_enterprise_openapi.json`](gemini_enterprise_openapi.json)
* **Active LLM**: `gemini-2.5-flash` via Google AI Studio Gemini API (`GEMINI_API_KEY`)
* **Deployment Script**: [`deploy_agent.py`](deploy_agent.py)

---

## 7. Registration in Gemini Enterprise

The agent is registered directly in **Gemini Enterprise** (Google Cloud Vertex AI Agent Builder / Gen App Builder) under Google Cloud Project `project-83b9dd42-537f-47c6-a28`:

* **Gemini Enterprise Engine**: `projects/450158463415/locations/global/collections/default_collection/engines/warranty-claims-triage_1789741170801` (Display Name: `Warranty_claims_Triage`)
* **Registered Agent**: **`Warranty Claims Triage Agent`** (Agent ID: `15381693706825665023`)
* **Architecture Type**: `lowCodeAgentDefinition` (Native Gemini Enterprise Agent)
* **Model**: **`gemini-2.5-flash`**
* **Invocation Mode**: `AUTOMATIC`

### Direct Access Links

| View | Link | Purpose |
|---|---|---|
| **Gemini Enterprise Preview & Chat** | [Open in Cloud Console](https://console.cloud.google.com/gen-app-builder/engines/warranty-claims-triage_1789741170801/preview?project=project-83b9dd42-537f-47c6-a28) | Official Google Cloud Gemini Enterprise chat and triage evaluation |
| **Gemini Enterprise Agent Studio** | [View in Agent Studio](https://console.cloud.google.com/gen-app-builder/engines/warranty-claims-triage_1789741170801/agents/15381693706825665023?project=project-83b9dd42-537f-47c6-a28) | Visual workflow and prompt editor |
| **Cloud Run Agent Runtime** | [https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app](https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app) | Live serverless execution endpoint |
| **OpenAPI Tool Schema** | [https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/openapi.json](https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app/openapi.json) | OpenAPI 3.0 schema for tool binding |

### Pre-Configured Starter Prompts in Gemini Enterprise:
1. *"Any recurring issues with the Model X rear axle claims this month?"*
2. *"Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days."*
3. *"Does this claim match any open TSB for Model X rear axle whine?"*

---

## 8. End-to-End Operational Query Walkthroughs

Once registered, Gemini Enterprise users can execute standard operational inquiries:

### Inquiry 1: Recurring Failure Detection
> **User Prompt**: *"Any recurring issues with the Model X rear axle claims this month?"*
>
> **Agent Execution Flow**:
> 1. Invokes `search_warranty_claims(model="Model X", component="Rear Axle Assembly")` $\rightarrow$ finds 4 claims.
> 2. Invokes `search_dealer_repair_orders` $\rightarrow$ correlates DTC `P079A` and metallic flakes in differential oil.
> 3. Invokes `search_tsb_repository` $\rightarrow$ identifies matching open bulletin `TSB-25-03-014`.
> 4. Invokes `calculate_severity_score` $\rightarrow$ returns **CRITICAL (10.0/10)** due to axle seizure risk.
> 5. Invokes `create_quality_ticket` $\rightarrow$ generates Jira ticket `QE-2026-101`.
> 6. Invokes `notify_warranty_qe_channel` $\rightarrow$ dispatches alert to `#warranty-qe`.
> 7. Returns formatted executive summary to user.

### Inquiry 2: VIN Batch Summary
> **User Prompt**: *"Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days."*
>
> **Agent Execution Flow**:
> 1. Filters claims by `vin_prefix = "1XYZ4A2X"`.
> 2. Calculates total parts liability ($11,630.00), average mileage (13,062 miles), and summarizes primary failure modes (*pinion bearing wear, spline stripping*).

### Inquiry 3: Open TSB Matching
> **User Prompt**: *"Does this claim match any open TSB for rear axle whine?"*
>
> **Agent Execution Flow**:
> 1. Queries TSB repository for symptoms `whine` and `Model X`.
> 2. Confirms match with `TSB-25-03-014` (Status: OPEN).
> 3. Summarizes prescribed repair procedure (*magnetic drain plug inspection and complete rear drive axle subassembly replacement*).

---

## 9. Project Directory Reference

```
warranty_claims_agent/
├── README.md                       # Master Documentation & Architecture Guide (This file)
├── DEPLOYMENT_GUIDE.md             # Operations & deployment runbook
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── Dockerfile                      # Production container image configuration
├── deploy.ps1                      # Windows PowerShell automated deploy script
├── deploy.sh                       # Linux/macOS automated deploy script
│
├── agent.py                        # Google ADK Agent definition (gemini-2.5-flash)
├── gemini_agent.py                 # Standalone Gemini API Agent implementation
├── server.py                       # FastAPI Agent Runtime service
├── test_agent.py                   # Pytest test suite
├── run_tests.py                    # Standalone test runner (17 tests)
├── smoke_test.py                   # Live end-to-end smoke test suite (4 tests)
│
├── data/
│   └── mock_data.py                # Realistic claims DB, TSBs, repair orders, QE wiki
│
├── skills/
│   ├── pattern_clustering.py       # Failure pattern clustering algorithm
│   └── severity_scoring.py         # Standardized 1-10 severity scoring algorithm
│
├── tools/
│   ├── search_tools.py             # Multi-source search tool
│   ├── ticket_tools.py             # QE ticketing tool (Jira / ServiceNow)
│   └── slack_tools.py              # Slack alert tool (#warranty-qe)
│
└── gemini_enterprise_json/         # Declarative Gemini Enterprise Bundle
    ├── agent_manifest.json         # Agent Builder manifest
    ├── examples.json               # Few-shot playbook queries
    ├── register_via_json.py        # Automated registration script
    └── tools/
        ├── qe_ticket_openapi.json  # OpenAPI 3.0 schema for QE ticketing
        ├── slack_notify_openapi.json# OpenAPI 3.0 schema for Slack alerts
        └── search_datastore_tool.json# Vertex AI Search Data Store binding
```

---

## 10. Technical FAQ & Architecture Review Questions (Expected Q&A)

Here are the questions you can expect in technical architecture reviews, stakeholder demos, or engineering interviews, with complete technical answers:

---

### Q1: What is "Agent Runtime", and how does it execute Python agent code?
> **Answer**:  
> In this production architecture, **Agent Runtime** is hosted on **Google Cloud Run** running a containerized Python service (`server.py`) powered by **Google ADK (Agent Development Kit)** and FastAPI.  
> The runtime handles:
> 1. Packaging and lifecycle management of the Python agent classes and multi-step reasoning loops.
> 2. Execution of deterministic triage skills (failure pattern clustering and mathematical 1–10 severity scoring).
> 3. Automatic scaling from 0 to N instances, health monitoring, and OpenAPI 3.0 schema generation.
> 4. Full independence from Vertex AI Reasoning Engine billing restrictions by calling the Google Gemini Developer API directly via `GEMINI_API_KEY`.

---

### Q2: Is the deployment Python-based, container-based, or SDK-driven?
> **Answer**:  
> **It is an SDK-orchestrated containerized Python deployment.**  
> - **Authoring**: Written natively in Python using `google-adk` and FastAPI.
> - **Orchestration**: The `deploy_agent.py` script orchestrates Google Cloud Build and Google Cloud Run deployments.
> - **Packaging**: Google Cloud Build compiles the hardened Docker image into Google Artifact Registry (`agent-runtime-repo/warranty-claims-triage-agent:latest`).
> - **Execution**: Google Cloud Run executes the container with automatic HTTPS TLS, scale-to-zero, and zero Vertex AI billing blockers.

---

### Q3: How is the agent registered into Gemini Enterprise?
> **Answer**:  
> The agent is registered directly in the **Gemini Enterprise Discovery Engine** (`warranty-claims-triage_1789741170801`) as **`Warranty Claims Triage Agent`** (`15381693706825665023`).  
> It is registered as a native `lowCodeAgentDefinition` with pre-configured starter prompts, system triage instructions, and model target **`gemini-2.5-flash`**, allowing users to interact directly via the Google Cloud Console Gemini Enterprise Chat interface.

---


### Q4: How does the agent call the Gemini API instead of Vertex AI foundation model endpoints?
> **Answer**:  
> Under the hood, Google's `google-genai` SDK supports two backends: Vertex AI (GCP enterprise quotas) and the Gemini Developer API (`https://generativelanguage.googleapis.com`).  
> In our code:
> ```python
> os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
> ```
> By explicitly setting `GOOGLE_GENAI_USE_VERTEXAI="false"` and configuring `GEMINI_API_KEY`, the agent directs all model inference calls to the high-speed Gemini Developer API endpoint. This eliminates Vertex AI quota competition and complex GCP project-level model permissions while still running the execution runtime securely on Google Cloud.

---

### Q5: How are the tools and actions passed to Gemini?
> **Answer**:  
> Tools are defined as standard Python functions equipped with explicit PEP 484 type hints and detailed Google-style docstrings (e.g. `search_warranty_claims(model: str, component: str) -> List[Dict]`).  
> During initialization, the Google ADK inspects these callable functions and automatically derives OpenAPI-compatible `FunctionDeclaration` objects. When a user asks a question, Gemini determines which tools to call, generates structured JSON arguments, and ADK executes the corresponding Python functions locally before passing the results back to the LLM for synthesis.

---

### Q6: How does Gemini Enterprise authenticate when invoking this deployed agent?
> **Answer**:  
> Following enterprise zero-trust security principles:
> 1. When registered as an Agent Engine tool or Cloud Run service, the endpoint is protected by **Google Cloud IAM**.
> 2. Gemini Enterprise uses an authorized Service Account with the `roles/aiplatform.user` or `roles/run.invoker` role.
> 3. Every invocation transmits a short-lived **OIDC Bearer Token** in the `Authorization` header.
> 4. Anonymous/unauthenticated public access is strictly disabled (`--no-allow-unauthenticated`).

---

### Q7: Why is severity scoring implemented deterministically in Python rather than asking the LLM to score it?
> **Answer**:  
> **Auditing, repeatability, and safety compliance.**  
> In Quality Engineering and regulatory reporting (e.g. NHTSA safety recalls), severity scoring cannot be subject to generative hallucination or temperature variability.  
> - **Deterministic Skill (`severity_scoring.py`)**: Executes exact mathematical rules based on safety hazards (+4.0 for lockups/stalls), recurrence thresholds (+3.0 for $\ge 4$ claims), and financial liability (+2.0 for $>\$3,000$).
> - **LLM Role**: Extracts and grounds the defect facts, while the deterministic skill computes the verified numerical score (1–10) and criticality tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

---

### Q8: What real-world engineering hurdles were encountered during deployment, and how did you resolve them?
> **Answer**:  
> We resolved three specific enterprise environment issues:
> 1. **Pydantic Version Conflict**: `google-adk 2.6.2` required `pydantic>=2.12.0`, while older project files pinned `2.10.6`. We resolved this by opening the range to `pydantic>=2.12.0,<3.0.0`.
> 2. **Upstream Python 3.10 `TypeAlias` Bug in Vertex AI SDK**: In `vertexai/_genai/_agent_engines_utils.py` (line 310), Google's SDK contained `ADKAgent: Optional[TypeAlias] = BaseAgent`. Under Python 3.10, PEP 613 forbids wrapping `TypeAlias` inside `Optional[...]`, throwing a fatal `TypeError`. We patched this upstream issue to `ADKAgent: TypeAlias = BaseAgent`, enabling clean deployment.
> 3. **Windows Console Charset Trap**: Handled the Windows code page 1252 character mapping limitation where the CLI's celebration emoji (`🎉`) failed to display in standard Windows terminal after the cloud deployment was already complete.

---

### Q9: How do you transition this from mock data to live enterprise databases?
> **Answer**:  
> The agent was built with a **dual-mode architecture**:
> - Set `MOCK_DATA_MODE="false"` in the environment variables.
> - **Database**: Replace the search queries in `tools/search_tools.py` with direct BigQuery SQL queries or Cloud SQL/PostgreSQL ORM calls.
> - **Jira / ServiceNow**: Provide `QE_TICKETING_API_URL` and `QE_TICKETING_API_TOKEN` in `.env`; `create_quality_ticket` will dispatch live REST HTTP POST calls.
> - **Slack**: Provide `SLACK_WEBHOOK_URL`; `notify_warranty_qe_channel` will dispatch live Block Kit JSON payloads to `#warranty-qe`.

---

### Q10: How does this migrated solution compare to the original Glean no-code agent?
> **Answer**:  
> | Metric | Original Glean Agent | Migrated Gemini Enterprise Solution |
> |---|---|---|
> | **Execution Environment** | Proprietary SaaS walled garden | Open, portable Python Google ADK running on Google Cloud Agent Runtime |
> | **Model Flexibility** | Fixed Glean tier | Gemini 2.5 Flash with custom temperature, system prompts, and safety settings |
> | **Custom Business Logic** | Limited to built-in Glean plugins | Full Python support for custom algorithms, numpy, pandas, and custom scoring |
> | **Testability** | Manual UI testing only | 100% automated test suite (`run_tests.py` & `smoke_test.py`) runnable in CI/CD |
> | **Enterprise Access** | Accessible only within Glean UI | Accessible across Google Workspace, Gemini Enterprise Chat, REST APIs, and Jira |

---

## 11. Engineering Journey: Chronological Build Log (How We Actually Built and Deployed It)

This section documents the step-by-step engineering story of how this agent was constructed from a raw JSON snippet, tested, debugged, deployed to Google Cloud Agent Runtime, and registered with Gemini Enterprise.

---

### Stage 1: Deconstructing the Glean No-Code JSON Specification
We began with a raw JSON export of a Glean no-code agent (`wca_4f9c1e2b8a3d`). We analyzed its structure and isolated six core capabilities:
1. **Trigger Prompts**: Three few-shot user inquiries:
   - *"Any recurring issues with the Model X rear axle claims this month?"*
   - *"Summarize warranty claims for VIN prefix XXXX in the last 30 days"*
   - *"Does this claim match any open TSB?"*
2. **Search Data Sources**: Four distinct enterprise repositories:
   - `warranty-claims-db`
   - `tsb-repository`
   - `dealer-repair-orders`
   - `quality-engineering-wiki`
3. **External Write Actions**:
   - `create-quality-ticket` $\rightarrow$ `qe-ticketing-system`
   - `notify-slack-channel` $\rightarrow$ `slack:#warranty-qe`
4. **Autonomous Skills**:
   - `failure-pattern-clustering`
   - `severity-scoring`

---

### Stage 2: Architecture Selection & Workspace Scaffolding
We opted for a **Python-first, production-grade architecture** using **Google ADK (Agent Development Kit)** and **FastAPI** placed in a dedicated, isolated project directory:  
`sandbox-tech-explorations/warranty_claims_agent/`.

We scaffolded the folder structure into modular layers:
- `data/`: Mock datasets representing realistic automotive claims and bulletins.
- `skills/`: Algorithmic modules for clustering and risk scoring.
- `tools/`: Python callable tools for Gemini Function Calling.
- `gemini_enterprise_json/`: OpenAPI 3.0 specs and declarative manifests.

---

### Stage 3: Engineering the Code Components Step-by-Step

#### 1. Creating the Dual-Mode Mock Data Layer (`data/mock_data.py`)
To ensure the agent could be tested immediately without needing live database connections:
- We crafted **`WARRANTY_CLAIMS_DB`** with 6 realistic vehicle records, specifically encoding a progressive failure mode on Model X (`1XYZ4A2X`) rear axles (from mild whining to catastrophic gear teeth shearing).
- We crafted **`TSB_REPOSITORY`** with active bulletin `TSB-25-03-014` covering pinion roller bearing metallurgical spalling.
- We crafted **`DEALER_REPAIR_ORDERS`** with technician observations (DTC `P079A`, metallic shavings in differential fluid).
- We crafted **`QUALITY_ENGINEERING_WIKI`** establishing clear engineering protocols (`WIKI-QE-042` and `WIKI-QE-019`).

#### 2. Implementing the Skills Engine (`skills/`)
- **`pattern_clustering.py`**: Built a clustering function that groups incoming claims by `(component, vin_prefix, model)`, calculates average mileage, computes total parts cost, and extracts symptom keywords.
- **`severity_scoring.py`**: Built a standardized scoring rubric evaluating safety criticality (+4.0 for lockups/stalls), recurrence (+3.0 for $\ge 4$ claims), financial exposure (+2.0 for $>\$3,000$), and open TSB correlation (+1.0), returning a normalized 1–10 score and criticality tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

#### 3. Building the Callable Tools (`tools/`)
- **`search_tools.py`**: Created four search functions (`search_warranty_claims`, `search_tsb_repository`, `search_dealer_repair_orders`, `search_quality_engineering_wiki`) with parameter filters and keyword matching.
- **`ticket_tools.py`**: Created `create_quality_ticket` to generate structured investigation tickets with timestamps and internal tracking.
- **`slack_tools.py`**: Created `notify_warranty_qe_channel` to construct Slack Block Kit message payloads for `#warranty-qe`.

#### 4. Defining the Agent Core (`agent.py` & `gemini_agent.py`)
- Configured Google ADK's `Agent` instance with model `gemini-2.5-flash` and bound all 8 tools.
- Formulated a comprehensive Quality Engineering triage system prompt enforcing fact grounding, TSB cross-referencing, and automatic ticket generation.

#### 5. Exposing the API Server (`server.py`)
- Created a **FastAPI** application exposing `/health`, `/api/v1/triage`, `/chat` (Glean message schema compatibility), and `/openapi.json`.

---

### Stage 4: Testing & Verification Pipeline
We created a 17-test automated test suite in `test_agent.py` and a standalone runner `run_tests.py`:
- Verified all individual search tools against models, VIN prefixes, and components.
- Verified critical vs low severity calculation formulas.
- Tested failure pattern grouping algorithms.
- Validated ticket and Slack action dispatch payloads.
- Executed all 3 Glean prompt trigger scenarios end-to-end.
- **Result**: `Results: 17 passed, 0 failed out of 17 tests. ALL TESTS PASSED SUCCESSFULLY!`

Next, we built `smoke_test.py` to test live HTTP traffic against `/health`, `/openapi.json`, `/api/v1/triage`, and `/chat`.
- **Result**: `ALL 4 SMOKE TESTS COMPLETED SUCCESSFULLY!`

---

### Stage 5: The Real Deployment Journey & Upstream Debugging

This stage involved diagnosing and solving real-world enterprise infrastructure challenges:

#### Hurdle 1: Pydantic Version Conflict in Container Build
When Google Cloud Build attempted to package the container, `pip` failed:
```
ERROR: Cannot install -r requirements.txt (line 1), -r requirements.txt (line 3) and pydantic==2.10.6
The conflict is caused by: google-adk 2.6.2 depends on pydantic<3 and >=2.12
```
*Solution*: We modified `requirements.txt` to `pydantic>=2.12.0,<3.0.0`, resolving the conflict and successfully building and pushing the container to Google Artifact Registry:  
`us-central1-docker.pkg.dev/project-83b9dd42-537f-47c6-a28/agent-runtime-repo/warranty-claims-triage-agent:latest`.

#### Hurdle 2: Python 3.10 `TypeAlias` Upstream Bug in Google's Vertex AI SDK
When deploying to Vertex AI Agent Engine (`adk deploy agent_engine`), the client threw an unexpected fatal error:
```
Deploy failed: Plain typing.TypeAlias is not valid as type argument
```
*Investigation*: We traced the error into `vertexai/_genai/_agent_engines_utils.py`, line 310:
```python
ADKAgent: Optional[TypeAlias] = BaseAgent
```
Under Python 3.10, PEP 613 forbids using `TypeAlias` inside `Optional[...]`. Python's standard `typing.py` raised a `TypeError`.  
*Fix*: We patched line 310 to `ADKAgent: TypeAlias = BaseAgent`. This completely resolved the issue and allowed `vertexai.Client.agent_engines` to load properly.

#### Hurdle 3: Strategic Pivot to Gemini Developer API
To ensure the agent executes inference directly against Google's high-speed **Gemini Developer API** (`gemini-2.5-flash`) without competing for Vertex AI project quotas:
- We set `os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"` in `agent.py`, `server.py`, and runtime deployment variables.
- We passed `GEMINI_API_KEY` directly from the environment.

#### Hurdle 4: Successful Agent Runtime Provisioning & Console Encoding Trap
We re-ran the deployment command:
```bash
python -m google.adk.cli deploy agent_engine \
    --project=project-83b9dd42-537f-47c6-a28 \
    --region=us-central1 \
    --display_name="Warranty Claims Triage Agent" \
    "c:\Users\Kodati Yashashwini\sandbox-tech-explorations\warranty_claims_agent"
```
The cloud infrastructure provisioned successfully:
```
Created a new instance: projects/450158463415/locations/us-central1/reasoningEngines/9057024173909475328
Creating Dockerfile...
Deployed to Agent Platform: projects/450158463415/locations/us-central1/reasoningEngines/9057024173909475328
```
At the very end of deployment, the ADK CLI attempted to print a celebration emoji (`🎉`) which caused a minor Windows code page 1252 (`charmap`) console error. Querying the Vertex AI API confirmed the Agent Engine instance was **live, healthy, and operational**.

#### Hurdle 5: Vertex AI Billing Restrictions & Resolution via Cloud Agent Runtime
When invoking a Vertex AI Reasoning Engine from the Gemini Enterprise console on a Free Tier account, Google Cloud rejected the invocation with `FAILED_PRECONDITION: Reasoning Engine Execution failed` due to missing paid Vertex AI quotas.

*The Architectural Resolution*:
To achieve 100% cloud autonomy with zero billing blockers (following the proven architecture of `product_research_agent`):
1. **Cloud Agent Runtime Deployment (`deploy_agent.py`)**:
   - Automated script using Google Cloud Build and Google Cloud Run.
   - Deployed the container to `https://warranty-claims-triage-agent-5swwqt7jfq-uc.a.run.app`.
   - Configured with `GEMINI_API_KEY`, `MODEL_NAME=gemini-2.5-flash`, and `MOCK_DATA_MODE=true`.
   - Generates the live OpenAPI 3.0 specification [`gemini_enterprise_openapi.json`](gemini_enterprise_openapi.json).
2. **Native Gemini Enterprise Registration**:
   - Created the agent directly in Gemini Enterprise Intranet Engine `warranty-claims-triage_1789741170801` as a native `lowCodeAgentDefinition`.
   - Deleted the broken reasoning engine agent to eliminate any `FAILED_PRECONDITION` triggers.
   - Registered agent: **`Warranty Claims Triage Agent`** (`15381693706825665023`).

---

### Stage 6: Registration & Live Testing in Gemini Enterprise

The agent is live in **Gemini Enterprise**:
1. Open the [Gemini Enterprise Preview Console](https://console.cloud.google.com/gen-app-builder/engines/warranty-claims-triage_1789741170801/preview?project=project-83b9dd42-537f-47c6-a28).
2. Test the triage workflow directly in the chat with:
   > *"Any recurring issues with the Model X rear axle claims this month?"*
3. The agent uses `gemini-2.5-flash`, evaluates the 4 claims on VIN prefix `1XYZ4A2X`, matches `TSB-25-03-014`, calculates severity at CRITICAL 10/10, and renders the complete QE triage summary.

---

*This concludes the complete engineering chronicle from the Glean specification to the fully autonomous Google Cloud Agent Runtime and Gemini Enterprise registration.*

