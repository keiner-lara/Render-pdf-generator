import json
from src.infrastructure.persistence.models import IngestionStaging

class TelemetryIngestor:
    def __init__(self, db_adapter):
        self.db = db_adapter

    def ingest_from_file(self, session_id, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            full_json = json.load(f)
        
        # We extract the individual events (reports_flat)
        reports = full_json["json"]["reports_flat"]
        print(f"Received {len(reports)} events. Sending to Staging (Audit)...")

        for r in reports:
            self.db.save_staging_data(
                session_id=session_id,
                source=r["source_cell"],
                payload=r
            )
        print("Ingestion completed in the Bronze layer.")