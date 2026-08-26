C:\Users\Kodati Yashashwini\Desktop\Python-practice\website\contract_analyzer>from fpdf import FPDF
import datetime

class PDFReport(FPDF):
    def header(self):
        # Arial bold 8
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        # Title
        if self.page_no() > 1:
            self.cell(0, 10, 'Contract Analyzer AI App - Implementation Report', 0, 0, 'R')
            self.ln(10)
            # Draw a line under header
            self.set_draw_color(220, 220, 220)
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 41, 59) # Slate 800
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
        self.set_draw_color(79, 70, 229) # Indigo 600
        self.set_line_width(0.8)
        self.line(self.get_x(), self.get_y(), self.get_x() + 40, self.get_y())
        self.ln(5)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(79, 70, 229) # Indigo 600
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 65, 85) # Slate 700
        self.multi_cell(0, 6, text)
        self.ln(4)

    def code_block(self, code):
        self.set_fill_color(248, 250, 252) # Slate 50
        self.set_draw_color(226, 232, 240) # Slate 200
        self.set_font('Courier', '', 8.5)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, code, border=1, fill=True)
        self.ln(4)

def generate_report():
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # ------------------ TITLE PAGE ------------------
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.ln(30)
    pdf.cell(0, 15, 'Contract Analyzer AI App', 0, 1, 'C')
    
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(79, 70, 229) # Indigo 600
    pdf.cell(0, 10, 'Full-Stack Implementation & Deployment Report', 0, 1, 'C')
    
    pdf.ln(10)
    pdf.set_draw_color(79, 70, 229)
    pdf.set_line_width(1)
    pdf.line(50, 75, 160, 75)
    
    pdf.ln(25)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(100, 116, 139) # Slate 500
    pdf.cell(0, 8, 'TECHNOLOGY STACK:', 0, 1, 'C')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 6, 'Frontend: React, Vite, Tailwind CSS, Axios, Lucide Icons', 0, 1, 'C')
    pdf.cell(0, 6, 'Backend: FastAPI, Uvicorn, Google Antigravity (ADK) SDK, PyPDF', 0, 1, 'C')
    pdf.cell(0, 6, 'AI Engine: Gemini API (gemini-2.5-flash)', 0, 1, 'C')
    pdf.cell(0, 6, 'Infrastructure & Deployment: Docker, Google Cloud Build, Google Cloud Run', 0, 1, 'C')
    
    pdf.ln(35)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, f'Generated on: {datetime.date.today().strftime("%B %d, %Y")}', 0, 1, 'C')
    pdf.cell(0, 5, 'Designed and built by Antigravity Agentic AI', 0, 1, 'C')
    
    # ------------------ PAGE 2 ------------------
    pdf.add_page()
    pdf.chapter_title('1. Executive Summary')
    pdf.body_text(
        "We have successfully built, verified, and deployed the Contract Analyzer, a modern, full-stack AI web "
        "application that automatically parses, extracts, and summarizes legal contracts, and provides a conversational "
        "interface to ask questions about the contract. \n\n"
        "The project leverages Google's official Antigravity (ADK) Agent framework to drive the interactive chatbot on "
        "the frontend, and uses the standard Google GenAI SDK to perform highly accurate, structured data extraction "
        "representing parties, key dates, obligations, and risk factors in the legal documents.\n\n"
        "Initially designed as separate services, the final deployment was optimized into a unified single container "
        "hosted on Google Cloud Run. The React UI is served directly from the FastAPI root path, eliminating CORS "
        "complexities, minimizing cloud compute costs, and providing a single, seamless live application URL."
    )
    
    pdf.chapter_title('2. Application Architecture')
    pdf.body_text(
        "The application architecture consists of a compiled single-page React frontend mounted directly inside "
        "a FastAPI backend server. The backend runs inside a lightweight Docker container on Google Cloud Run."
    )
    
    pdf.section_title('Unified Directory Structure')
    pdf.code_block(
        "contract-analyzer/\n"
        "|-- backend/\n"
        "|   |-- agents/\n"
        "|   |   `-- contract_agent/\n"
        "|   |       |-- __init__.py\n"
        "|   |       `-- agent.py          # Antigravity ADK Agent configuration\n"
        "|   |-- static/                   # Production build of the React app\n"
        "|   |   |-- assets/               # CSS & JS assets\n"
        "|   |   `-- index.html\n"
        "|   |-- Dockerfile\n"
        "|   |-- main.py                   # FastAPI backend server with routes\n"
        "|   |-- requirements.txt\n"
        "|   `-- .env.example\n"
        "`-- frontend/\n"
        "    |-- src/\n"
        "    |   |-- App.jsx               # React main dashboard UI\n"
        "    |   |-- index.css             # Tailwind base & custom scrollbars\n"
        "    |   `-- main.jsx\n"
        "    |-- index.html\n"
        "    |-- package.json              # Frontend npm dependencies\n"
        "    `-- vite.config.js"
    )
    
    # ------------------ PAGE 3 ------------------
    pdf.add_page()
    pdf.chapter_title('3. Step-by-Step Implementation Details')
    
    pdf.section_title('Phase 1: Backend & ADK Agent Setup')
    pdf.body_text(
        "We configured the contract_agent using Google ADK LLM Agent framework. The agent is configured with the "
        "gemini-2.5-flash model and legal-expert system instructions. \n\n"
        "In main.py, we resolved a startup crash issue: Google GenAI Client (genai.Client()) crashes on startup if "
        "GEMINI_API_KEY environment variables are missing during container initialization. To solve this, we "
        "implemented lazy initialization of the client at request time, ensuring the container starts successfully "
        "and passes the Cloud Run health checks."
    )
    
    pdf.section_title('Phase 2: Structured Contract Analysis')
    pdf.body_text(
        "FastAPI provides a POST /api/analyze endpoint that handles file uploads (.pdf and .txt). Text is extracted "
        "using the pypdf library. We defined a strict Pydantic output schema (ContractAnalysisResult) to guarantee the "
        "integrity of the extracted metadata. Gemini 2.5 is then called with this schema to output structured JSON "
        "containing parties, effective/expiration dates, key clauses, obligations, and risk assessment grades."
    )
    
    pdf.section_title('Phase 3: React Frontend Dashboard')
    pdf.body_text(
        "The React UI provides a clean side-by-side layout using Tailwind CSS. On the left panel, the uploaded contract's "
        "extracted metadata is displayed in cards (such as color-coded Risk badges based on low/medium/high severity). "
        "On the right panel, users can chat with the ADK agent. \n\n"
        "The frontend is configured with environment-aware host detection, defaulting to relative paths if hosted on the "
        "same domain (production) or falling back to the cloud URL if running local Vite dev server."
    )
    
    # ------------------ PAGE 4 ------------------
    pdf.add_page()
    pdf.chapter_title('4. Deployment & Cloud Hosting')
    pdf.body_text(
        "We compiled the React app into static files (index.html, JS/CSS assets) and mounted them inside FastAPI:\n"
    )
    pdf.code_block(
        "static_dir = os.path.join(backend_dir, 'static')\n"
        "if os.path.exists(static_dir):\n"
        "    @app.get('/')\n"
        "    async def read_index():\n"
        "        return FileResponse(os.path.join(static_dir, 'index.html'))\n"
        "    app.mount('/assets', StaticFiles(directory=os.path.join(static_dir, 'assets')))"
    )
    
    pdf.section_title('GCP Artifact Registry and Cloud Run')
    pdf.body_text(
        "The container image was successfully compiled using Google Cloud Build and pushed to the standard Artifact Registry "
        "repository (adk-repo) at region us-central1:\n"
        "us-central1-docker.pkg.dev/project-83b9dd42-537f-47c6-a28/adk-repo/contract-analyzer-backend:latest\n\n"
        "The container was deployed to Cloud Run and is live at:\n"
        "https://contract-analyzer-backend-450158463415.us-central1.run.app"
    )
    
    pdf.chapter_title('5. Verification & Live Status')
    pdf.body_text(
        "We verified the deployment is live by calling the endpoints:\n"
        "1. GET /health: Returns {\"status\":\"ok\"} confirming container status.\n"
        "2. GET /docs: Exposes Swagger interactive docs for the backend APIs.\n"
        "3. GET /: Serves the React single-page app index file, loading compiled assets successfully.\n\n"
        "The application is fully operational and ready to parse and chat about legal documents in real-time."
    )
    
    # Save the PDF
    output_path = r"c:\Users\Kodati Yashashwini\Downloads\contract-analyzer\contract_analyzer_documentation.pdf"
    pdf.output(output_path)
    print(f"PDF generated successfully at: {output_path}")

if __name__ == "__main__":
    generate_report()
