class DataRefinery:
    def __init__(self, db_adapter):
        self.db = db_adapter

    def run_refinery(self, session_id):
        print(f"🔍 Iniciando auditoría y limpieza para la sesión {session_id}...")
        
        # 1. Obtener datos de la sala de espera
        pending_data = self.db.get_pending_audit(session_id)
        
        for record in pending_data:
            # Extraemos el ID del sujeto del JSON (P1, P4, etc.)
            app_subject_id = record.raw_payload.get("person_id")
            
            # Buscamos el UUID real de ese sujeto en la base de datos
            subject = self.db.get_subject_by_app_id(app_subject_id)
            
            if subject:
                # 2. Promoción a Capa Silver (Cleansed)
                # Aquí el dato ya está "limpio" porque sabemos de quién es.
                self.db.save_cleansed_event(
                    session_id=session_id,
                    subject_id=subject.subject_id,
                    source_type=record.source_cell,
                    payload=record.raw_payload,
                    t_start=record.raw_payload.get("t_start_ms", 0)
                )
        
        # 3. Marcar la sesión como 'cleansed'
        self.db.update_session_status(session_id, 'cleansed')
        print("✨ Refinería completada. Datos unificados en la capa Silver.")