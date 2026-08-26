# Contract Analyzer

A full-stack web application that uses Google Antigravity (ADK) Agent and Gemini API to parse, analyze, and chat about legal contracts (PDF, Text).

## Project Structure

```text
contract-analyzer/
├── backend/
│   ├── agents/
│   │   └── contract_agent/
│   │       ├── __init__.py
│   │       └── agent.py          # Antigravity ADK Agent definition
│   ├── Dockerfile
│   ├── main.py                   # FastAPI backend server & custom endpoints
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # React main component (side-by-side dashboard)
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
└── README.md
```

## Running Locally

### 1. Run the Backend

1. Navigate to the `backend/` directory.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example and fill in your API key:
   ```bash
   cp .env.example .env
   # Or manually create .env and set GEMINI_API_KEY=your_key
   ```
5. Run the server:
   ```bash
   python main.py
   ```
   The backend will start at `http://localhost:8080`.

### 2. Run the Frontend

1. Navigate to the `frontend/` directory.
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will open at `http://localhost:5173`.

---

## Deployment to Google Cloud Run

To build and deploy the backend to Google Cloud Run:

1. Ensure the Google Cloud CLI (`gcloud`) is installed and authenticated.
2. Navigate to the `backend/` directory.
3. Build the container image using Cloud Builds (replace `YOUR_PROJECT_ID` with your actual GCP project ID):
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/contract-analyzer-backend
   ```
4. Deploy the container to Cloud Run:
   ```bash
   gcloud run deploy contract-analyzer-backend \
     --image gcr.io/YOUR_PROJECT_ID/contract-analyzer-backend \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_api_key_here
   ```
5. Copy the deployed Service URL.
6. Open the React frontend, click the **Config** button in the header, and paste the Cloud Run URL to point the UI to your live cloud backend!
