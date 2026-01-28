import uuid
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. PATH Settings
sys.path.append(os.getcwd())
from src.infrastructure.persistence.models import (
    User, UserCredentials, Case, Subject, Session, SessionSubject, Base
)
# 2. Connection settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Qwe.123*@localhost:5432/strix_final")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def run_seed():
    print("Starting data population with duplicate validation...")
    try:
        # --- 1. INSERT STAFF USERS ---
        print("Procesando perfiles de Staff...")
        staff_data = [
            {"email": "admin@be-labs.com", "name": "Juliana Vargas", "role": "admin", "city": "Bogotá"},
            {"email": "scientist@be-labs.com", "name": "Marlon", "role": "scientist", "city": "Medellín"},
            {"email": "analyst@be-labs.com", "name": "Andres", "role": "analyst", "city": "Cali"}
        ]

        staff_map = {}
        for staff in staff_data:
            # We check if the user already exists by email
            existing_user = db.query(User).filter(User.email == staff["email"]).first()          
            if existing_user:
                # If it exists, we update its data.
                existing_user.name = staff["name"]
                existing_user.role = staff["role"]
                user_id = existing_user.id
                print(f"  -> Usuario {staff['email']} actualizado.")
            else:
                # If it doesn't exist, we create a new one.
                user_id = uuid.uuid4()
                new_user = User(
                    id=user_id,
                    email=staff["email"],
                    name=staff["name"],
                    role=staff["role"],
                    city=staff["city"]
                )
                db.add(new_user)
                print(f"-> User {staff['email']} created.")
            
            db.flush() # Synchronize with the DB to ensure the ID is available
            
            # Secure Credentials (Password: 'Pass_123*')
            existing_cred = db.query(UserCredentials).filter(UserCredentials.user_id == user_id).first()
            if not existing_cred:
                db.add(UserCredentials(
                    user_id=user_id,
                    password_hash="pbkdf2:sha256:260000$static_salt$password_hash_placeholder"
                ))
            
            staff_map[staff["role"]] = user_id

        print("Processing Use Case...")
        case_id = "SEV2-AUTH-TOKEN"
        existing_case = db.query(Case).filter(Case.case_id == case_id).first()
        if not existing_case:
            db.add(Case(
                case_id=case_id, 
                title="Análisis de Bug 401 Intermitente", 
                description="Simulación de expiración de token."
            ))

        # ---  INSERT PARTICIPANTS---
        print("Processing Participants...")
        subjects_data = [
            {"app_id": "P1", "name": "Carlos Vega", "email": "carlos@mail.com", "city": "Bogotá", "age": 35, "gender": "Masculino", "role": "Dev Sr / facilitador"},
            {"app_id": "P2", "name": "Luis Martínez", "email": "luis@mail.com", "city": "Medellín", "age": 28, "gender": "Masculino", "role": "Dev (evaluado)"},
            {"app_id": "P3", "name": "Marta González", "email": "marta@mail.com", "city": "Cali", "age": 31, "gender": "Femenino", "role": "QA"},
            {"app_id": "P4", "name": "Ana Ruiz", "email": "ana@mail.com", "city": "Bogotá", "age": 33, "gender": "Femenino", "role": "PM / coordinación"},
            {"app_id": "P5", "name": "Diego Pérez", "email": "diego@mail.com", "city": "Medellín", "age": 24, "gender": "Masculino", "role": "Dev Jr / soporte"}
        ]

        subject_uuids = {}
        for p in subjects_data:
            existing_sub = db.query(Subject).filter(Subject.app_subject_id == p["app_id"]).first()
            if existing_sub:
                subj_id = existing_sub.subject_id
            else:
                subj_id = uuid.uuid4()
                db.add(Subject(
                    subject_id=subj_id,
                    app_subject_id=p["app_id"],
                    name=p["name"],
                    email=p["email"],
                    city=p["city"],
                    age=p["age"],
                    gender=p["gender"]
                ))
            subject_uuids[p["app_id"]] = {"uuid": subj_id, "role": p["role"]}

        print("Processing Group Session...")
        app_session_id = "HSL-POC-SESSION-03"
        existing_session = db.query(Session).filter(Session.app_session_id == app_session_id).first()
        
        if existing_session:
            session_uuid = existing_session.session_id
        else:
            session_uuid = uuid.uuid4()
            db.add(Session(
                session_id=session_uuid,
                app_session_id=app_session_id,
                case_id=case_id,
                status="created",
                created_by=staff_map["admin"]
            ))
        # --- LINKING PARTICIPANTS---
        print(" Synchronizing session roles...")
        for app_id, info in subject_uuids.items():
            # We removed old links for this session to avoid duplicates in the intermediate table
            db.query(SessionSubject).filter(
                SessionSubject.session_id == session_uuid, 
                SessionSubject.subject_id == info["uuid"]
            ).delete()
            
            db.add(SessionSubject(
                session_id=session_uuid,
                subject_id=info["uuid"],
                role_in_session=info["role"]
            ))

        db.commit()
        print("\n SEED COMPLETED WITHOUT DUPLICATES.")

    except Exception as e:
        db.rollback()
        print(f"\n CRITICAL ERROR IN THE SEED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()