from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

class UserUpsert(BaseModel):
    email: EmailStr
    name: str
    role: str
    city: Optional[str] = None

class SessionUpsert(BaseModel):
    app_session_id: str
    case_id: str
    status: Optional[str] = "created"
    created_by: Optional[UUID] = None

class SubjectUpsert(BaseModel):
    app_subject_id: str
    name: str
    email: EmailStr
    age: int
    gender: str
    city: str

class ParticipantLink(BaseModel):
    app_session_id: str
    app_subject_id: str
    role: str

class ResponseBase(BaseModel):
    status: str
    id: str
    message: str