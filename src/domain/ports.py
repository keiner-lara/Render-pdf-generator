from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid

class RepositoryPort(ABC):
    @abstractmethod
    def get_session_by_app_id(self, app_session_id: str): pass

    @abstractmethod
    def get_participants_with_roles(self, session_id: uuid.UUID) -> List[Dict[str, Any]]: pass

    @abstractmethod
    def update_session_status(self, session_id: uuid.UUID, new_status: str): pass

    @abstractmethod
    def save_staging_data(self, session_id: uuid.UUID, source: str, payload: Dict[str, Any]): pass

    @abstractmethod
    def save_cleansed_event(self, event_data: Dict[str, Any]): pass

    @abstractmethod
    def get_cleansed_events(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]: pass

    @abstractmethod
    def save_pdf_artifact(self, report_id: uuid.UUID, blob_path: str): pass

    # --- NUEVOS MÉTODOS PARA CACHÉ ---
    @abstractmethod
    def get_report_by_hash(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, data_hash: str): 
        pass

    @abstractmethod
    def save_report_meta(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, markdown: str, json_data: Dict[str, Any], prompt_hash: str) -> uuid.UUID: 
        pass

class ReportRepositoryPort(ABC):
    @abstractmethod
    def get_report_content(self, session_id: uuid.UUID, subject_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieves report content (JSON) for a given session and subject.
        """
        pass

class AIPort(ABC):
    @abstractmethod
    def generate_report(self, system_prompt: str, user_json_data: str, model: str) -> str: pass

class PDFPort(ABC):
    @abstractmethod
    def create_pdf(self, markdown_content: str, filename_prefix: str) -> str: pass

class CaseServicePort(ABC):
    @abstractmethod
    def fetch_case_data(self, case_id: str) -> Dict[str, Any]:
        pass