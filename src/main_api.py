import os
import json
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader # <--- NUEVO
from typing import List, Optional
from pydantic import BaseModel
from io import BytesIO
from dotenv import load_dotenv

# Imports de tu arquitectura
from src.infrastructure.persistence.sqlalchemy_adapter import SQLAlchemyAdapter
from src.infrastructure.persistence.supabase_report_repository import SupabaseReportRepository
from src.infrastructure.openai.openai_adapter import OpenAIAdapter
from src.infrastructure.pdf.reportlab_adapter import ReportLabAdapter
from src.infrastructure.pdf.xhtml2pdf_adapter import Xhtml2PdfAdapter
from src.application.orchestrator_use_case import OrchestratorUseCase
from src.application.generate_pdf_use_case import GeneratePdfUseCase
from src.application.services.ingestor import TelemetryIngestor
from src.application.services.refinery import DataRefinery
from src.infrastructure.api.schemas import UserUpsert, SessionUpsert, SubjectUpsert, ResponseBase
from src.infrastructure.clients.case_service_client import CaseServiceClient

load_dotenv()

# --- CONFIGURACIÓN DE SEGURIDAD (API KEY) ---
API_KEY_NAME = "X-API-KEY"
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "be_labs_secret_2024") # Pon esto en tu .env
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def validate_api_key(api_key: str = Depends(api_key_header)):
    """Valida que el header X-API-KEY coincida con el secreto del servidor."""
    if api_key != API_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: API Key inválida"
        )
    return api_key

# --- INICIALIZACIÓN APP ---
app = FastAPI(
    title="BE-LABS API & PDF Generator", 
    version="1.2.0",
    description="API para gestión de telemetría y generación de informes psicoprofesionales"
)

# Configurar CORS (Importante si lo usas desde un Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Adaptadores ---
db_url = os.getenv("DATABASE_URL")
db_adapter = SQLAlchemyAdapter(db_url)
ai_adapter = OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
report_repo = SupabaseReportRepository(supabase_url, supabase_key)

# PDF Adapters
pdf_adapter = ReportLabAdapter()
xhtml2pdf_adapter = Xhtml2PdfAdapter()

# Use Cases
orchestrator = OrchestratorUseCase(db_adapter, ai_adapter, pdf_adapter)
generate_pdf_uc = GeneratePdfUseCase(report_repo, ai_adapter, xhtml2pdf_adapter)

# --- MODELOS DE REQUEST/RESPONSE ---
class GeneratePDFRequest(BaseModel):
    session_id: str
    subject_id: str

class GeneratePDFResponse(BaseModel):
    success: bool
    message: str
    report_id: str | None = None
    download_url: str | None = None

# --- ENDPOINTS PROTEGIDOS (Requieren X-API-KEY) ---

@app.post("/generate-pdf", tags=["PDF Generation"], dependencies=[Depends(validate_api_key)])
async def generate_pdf(request: GeneratePDFRequest):
    """
    Genera un PDF y lo retorna como descarga directa.
    Requiere header X-API-KEY.
    """
    try:
        session_uuid = uuid.UUID(request.session_id)
        subject_uuid = uuid.UUID(request.subject_id)
        
        # Obtenemos la ruta del PDF generado por el caso de uso
        pdf_path = generate_pdf_uc.execute(session_uuid, subject_uuid)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="El archivo PDF no pudo ser generado")
            
        filename = os.path.basename(pdf_path)
        
        # Retornamos como FileResponse (más eficiente que StreamingResponse para archivos en disco)
        return FileResponse(
            path=pdf_path, 
            filename=filename,
            media_type="application/pdf"
        )
    except Exception as e:
        print(f"Error en generate_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-pdf-url", response_model=GeneratePDFResponse, tags=["PDF Generation"], dependencies=[Depends(validate_api_key)])
async def generate_pdf_url(request: GeneratePDFRequest):
    """
    Verifica si el reporte existe y construye la URL de descarga.
    Requiere header X-API-KEY.
    """
    try:
        session_uuid = uuid.UUID(request.session_id)
        subject_uuid = uuid.UUID(request.subject_id)
        
        # Verificamos existencia en Supabase usando el puerto del repositorio
        report = report_repo.get_report_content(session_uuid, subject_uuid)
        
        if not report:
            return GeneratePDFResponse(
                success=False,
                message="No se encontró reporte para los IDs proporcionados",
                report_id=None,
                download_url=None
            )
        
        report_id = report.get("report_id")
        # Simulación de URL relativa (el cliente debe llamar luego a /generate-pdf)
        download_url = f"/generate-pdf?session_id={request.session_id}&subject_id={request.subject_id}"
        
        return GeneratePDFResponse(
            success=True,
            message="Reporte encontrado.",
            report_id=str(report_id),
            download_url=download_url
        )
    except Exception as e:
        return GeneratePDFResponse(success=False, message=f"Error: {str(e)}")

# --- ENDPOINTS DE INGESTA (También protegidos) ---

@app.post("/ingest/user", response_model=ResponseBase, dependencies=[Depends(validate_api_key)], tags=["Ingestion"])
async def upsert_user(payload: UserUpsert):
    try:
        user = db_adapter.create_or_update_user(email=payload.email, name=payload.name, role=payload.role, city=payload.city)
        return {"status": "success", "id": str(user.id), "message": "User upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... (Aquí siguen los otros endpoints de ingesta con la dependencia Depends(validate_api_key))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
