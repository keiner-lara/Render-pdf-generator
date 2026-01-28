import os
import uuid
import httpx
from typing import Optional, Dict, Any, List
from src.domain.ports import ReportRepositoryPort

class SupabaseReportRepository(ReportRepositoryPort):
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

    def get_report_content(self, session_id: uuid.UUID, subject_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        endpoint = f"{self.supabase_url}/rest/v1/vw_reports"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {
            "session_id": f"eq.{session_id}",
            "subject_id": f"eq.{subject_id}",
            "select": "report_id,content_json,content_markdown,kind"
        }
        
        with httpx.Client() as client:
            try:
                response = client.get(endpoint, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            except Exception as e:
                print(f"Error fetching report from Supabase: {e}")
        return None

    # --- IMPLEMENTACIONES OBLIGATORIAS (MÉTODOS FALTANTES) ---

    def get_participants_with_roles(self, session_id: uuid.UUID) -> List[Dict[str, Any]]:
        return []

    def update_session_status(self, session_id: uuid.UUID, new_status: str):
        pass

    def save_staging_data(self, session_id: uuid.UUID, source: str, payload: Dict[str, Any]):
        pass

    def save_cleansed_event(self, event_data: Dict[str, Any]):
        pass

    def get_cleansed_events(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        return []

    def save_pdf_artifact(self, report_id: uuid.UUID, blob_path: str):
        pass

    def get_report_by_hash(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, data_hash: str):
        return None

    def save_report_meta(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, markdown: str, json_data: Dict[str, Any], prompt_hash: str) -> uuid.UUID:
        # Retorno un UUID dummy para evitar errores de tipo si se llama
        return uuid.uuid4()