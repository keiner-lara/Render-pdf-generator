from config import SYSTEM_PROMPT, GROUP_SYSTEM_PROMPT
import json

class ReportOrchestrator:
    def __init__(self, db_adapter, ai_adapter, pdf_adapter):
        self.db = db_adapter
        self.ai = ai_adapter
        self.pdf = pdf_adapter

    def generate_all_reports(self, session_id):
        # 1. Get session participants
        participants = self.db.get_participants_with_roles(session_id)     
        # 2. Generate Singles
        for p in participants:
            print(f"AI generating a report for: {p['name']}")
            events = self.db.get_cleansed_events(session_id, p['subject_id'])   
            # We format the prompt with the metadata
            prompt = SYSTEM_PROMPT.format(
                nombre=p['name'], edad=p['age'], genero=p['gender'],
                city=p['city'], role_in_session=p['role']
            )
            report_md = self.ai.generate_report(prompt, json.dumps(events))
            # 3. Final Persistence (Storage Layer)
            report_id = self.db.save_report_meta(session_id, p['subject_id'], "individual", report_md)
            pdf_path = self.pdf.create_pdf(report_md, f"Reporte_{p['app_id']}")
            self.db.save_pdf_artifact(report_id, pdf_path)

        print("All reports have been generated and saved.")