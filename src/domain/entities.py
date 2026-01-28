from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class BiometricEvent(BaseModel):
    session_id: UUID
    subject_id: Optional[UUID]
    source_type: str  # 'vision' o 'voice'
    processed_payload: Dict[str, Any]
    t_start_ms: int

class SessionReport(BaseModel):
    session_id: UUID
    subject_id: Optional[UUID]
    kind: str  # 'individual' o 'group'
    content_markdown: str
    content_json: Dict[str, Any]
    model_version: str