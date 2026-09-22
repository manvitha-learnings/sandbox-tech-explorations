import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from pypdf import PdfReader
from google import genai
from google.genai import types
from google.adk.cli.fast_api import get_fast_api_app
from dotenv import load_dotenv

load_dotenv()

# Define the structured output schema for contract analysis
class DateField(BaseModel):
    date: Optional[str] = Field(description="The date found in YYYY-MM-DD or standard format, or null if not found.")
    explanation: str = Field(description="Explanation of what this date represents (e.g. Effective Date, Expiration Date).")

class ClauseField(BaseModel):
    clause_name: str = Field(description="Name of the clause (e.g. Termination, Indemnification, Governing Law).")
    summary: str = Field(description="Summary of what the clause says.")
    raw_text: str = Field(description="The exact text snippet of this clause from the contract.")

class ObligationField(BaseModel):
    party: str = Field(description="The party responsible for the obligation.")
    obligation: str = Field(description="Description of the obligation or deliverable.")

class RiskField(BaseModel):
    risk_type: str = Field(description="Type of risk (e.g. High Liability, Auto-renewal, Ambiguous terms).")
    severity: str = Field(description="Severity level: Low, Medium, or High.")
    explanation: str = Field(description="Explanation of why this is a risk and how to address it.")

class ContractAnalysisResult(BaseModel):
    parties: List[str] = Field(description="List of all parties involved in the contract.")
    effective_date: Optional[DateField] = Field(description="The effective date of the contract.")
    expiration_date: Optional[DateField] = Field(description="The expiration or termination date of the contract.")
    key_clauses: List[ClauseField] = Field(description="List of key clauses (Termination, Indemnification, Governing Law).")
    obligations: List[ObligationField] = Field(description="List of key obligations and deliverables.")
    risk_assessment: List[RiskField] = Field(description="Assessment of potential risks and liabilities.")
    general_summary: str = Field(description="A general summary of the contract's purpose and scope.")

# Resolve the agents directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.join(backend_dir, "agents")

# Construct the standard ADK FastAPI application
# Allow all origins for the React frontend running separately
app = get_fast_api_app(
    agents_dir=agents_dir,
    web=False,
    allow_origins=["*"]
)

# Serve static files (React frontend)
static_dir = os.path.join(backend_dir, "static")
if os.path.exists(static_dir):
    @app.get("/")
    async def read_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

# Helper to get the GenAI client safely at request time
def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured on the server. Please set it in the environment variables."
        )
    return genai.Client(api_key=api_key)

@app.post("/api/analyze", response_model=ContractAnalysisResult)
async def analyze_contract(file: UploadFile = File(...)):
    """
    Parses an uploaded PDF or Text contract, and uses Gemini to perform structured extraction.
    """
    filename = file.filename or ""
    content_type = file.content_type or ""
    
    # 1. Validate file extension and type
    filename_lower = filename.lower()
    is_pdf = filename_lower.endswith(".pdf") or "application/pdf" in content_type.lower()
    is_txt = filename_lower.endswith(".txt") or "text/plain" in content_type.lower()
    
    if not (is_pdf or is_txt):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF (.pdf) and Text (.txt) files are allowed."
        )

    # 2. Read and validate size (limit to 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the maximum limit of 5 MB."
        )

    # 3. Extract text from the file
    text = ""
    try:
        if is_pdf:
            # Parse PDF
            from io import BytesIO
            reader = PdfReader(BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            text = "\n".join(text_parts)
        else:
            # Parse text
            text = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse contract file: {str(e)}")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail="The contract file is empty or could not be read.")

    # 2. Extract structured analysis from Gemini
    try:
        client = get_genai_client()
        prompt = (
            "You are an expert contract lawyer. Extract the important clauses, dates, parties, obligations, "
            "and risks from this contract. Be precise, cite the exact raw text snippet where applicable, "
            "and categorize risks carefully."
        )
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[prompt, text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ContractAnalysisResult,
            ),
        )
        
        # Parse the JSON response
        import json
        result_dict = json.loads(response.text)
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract analysis failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
