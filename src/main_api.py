import os
import json
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Optional

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
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BE-LABS API & Orchestrator", version="1.1.0")

# --- Adaptadores ---
db_url = os.getenv("DATABASE_URL")
db_adapter = SQLAlchemyAdapter(db_url)
ai_adapter = OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase Adapter
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
report_repo = SupabaseReportRepository(supabase_url, supabase_key)

# PDF Adapters
pdf_adapter = ReportLabAdapter() # Existing
xhtml2pdf_adapter = Xhtml2PdfAdapter() # New for this feature

# Use Cases
orchestrator = OrchestratorUseCase(db_adapter, ai_adapter, pdf_adapter)
generate_pdf_uc = GeneratePdfUseCase(report_repo, ai_adapter, xhtml2pdf_adapter)

# --- TASK HU-S3-02-T03: ENDPOINTS DE INGESTA ---

@app.post("/ingest/user", response_model=ResponseBase, tags=["Ingestion"])
async def upsert_user(payload: UserUpsert):
    """
    AC: Dado un payload válido, persiste y retorna 201 con ID.
    Idempotencia: Si se repite, actualiza y retorna el mismo ID.
    """
    try:
        user = db_adapter.create_or_update_user(
            email=payload.email,
            name=payload.name,
            role=payload.role,
            city=payload.city
        )
        return {"status": "success", "id": str(user.id), "message": "User upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User Ingestion Error: {str(e)}")

@app.post("/ingest/session", response_model=ResponseBase, tags=["Ingestion"])
async def upsert_session(payload: SessionUpsert):
    """
    Persistencia de sesiones con lógica de Upsert.
    """
    try:
        session = db_adapter.create_or_update_session(
            app_session_id=payload.app_session_id,
            case_id=payload.case_id,
            status=payload.status,
            created_by=payload.created_by
        )
        return {"status": "success", "id": str(session.session_id), "message": "Session upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session Ingestion Error: {str(e)}")

@app.post("/ingest/participant", response_model=ResponseBase, tags=["Ingestion"])
async def upsert_participant(payload: SubjectUpsert):
    """
    Implementa el CRUD de sujetos/participantes solicitado en la HU.
    """
    db_session = db_adapter.SessionLocal()
    try:
        from src.infrastructure.persistence.models import Subject
        # Lógica de Upsert manual para cumplir con el 'Digest/Idempotencia'
        existing = db_session.query(Subject).filter_by(app_subject_id=payload.app_subject_id).first()
        if existing:
            existing.name = payload.name
            existing.email = payload.email
            existing.city = payload.city
            db_session.commit()
            return {"status": "success", "id": str(existing.subject_id), "message": "Participant updated"}
        
        new_subject = Subject(
            subject_id=uuid.uuid4(),
            app_subject_id=payload.app_subject_id,
            name=payload.name,
            email=payload.email,
            age=payload.age,
            gender=payload.gender,
            city=payload.city
        )
        db_session.add(new_subject)
        db_session.commit()
        return {"status": "success", "id": str(new_subject.subject_id), "message": "Participant created"}
    except Exception as e:
        db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()

# --- AUTOMATION ENDPOINT (EL QUE TE DIO ERROR 500) ---

@app.post("/process/full-json-automation", tags=["Automation"])
async def process_json_automation():
    try:
        json_path = "Data/Sesion_grupal.json"
        
        # Validación de existencia del archivo
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"File not found at {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f) # AQUÍ YA NO DARÁ ERROR PORQUE IMPORTAMOS JSON
            app_session_id = raw_data["json"]["session_meta"]["session_id"]

        # 1. Ingesta Bronze
        ingestor = TelemetryIngestor(db_adapter)
        session_db = db_adapter.get_session_by_app_id(app_session_id)
        if not session_db:
             raise Exception(f"Session {app_session_id} not found. Ingest session first.")
        
        ingestor.ingest_from_file(session_db.session_id, json_path)
        
        # 2. Refinería Silver
        refinery = DataRefinery(db_adapter)
        refinery.run_refinery(session_db.session_id)

        # 3. Orquestación Gold (IA + PDFs)
        results = orchestrator.run_full_session_process(app_session_id, json_path)

        return {
            "status": "success",
            "message": "Full automation sequence completed",
            "reports_created": len(results)
        }
    except Exception as e:
        print(f"Error detallado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/external-case/{case_id}", tags=["Infrastructure Test"])
async def test_case_client(case_id: str):
    client = CaseServiceClient()
    try:
        # Si usas la URL de jsonplaceholder, prueba con case_id "1" (que equivale a /todos/1)
        data = client.fetch_case_data(case_id)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

# --- NEW PDF GENERATOR ENDPOINT ---

class GeneratePDFRequest(BaseModel):
    session_id: str
    subject_id: str

@app.post("/generate-pdf", tags=["PDF Generation"])
async def generate_pdf(request: GeneratePDFRequest):
    """
    Generates and downloads a specific PDF report from Supabase data.
    """
    try:
        session_uuid = uuid.UUID(request.session_id)
        subject_uuid = uuid.UUID(request.subject_id)
        
        pdf_path = generate_pdf_uc.execute(session_uuid, subject_uuid)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF file was not created")
            
        filename = os.path.basename(pdf_path)
        
        return FileResponse(
            path=pdf_path, 
            filename=filename,
            media_type="application/pdf"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in /generate-pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)