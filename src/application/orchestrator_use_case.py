import json
import uuid
import hashlib
from config import SYSTEM_PROMPT, GROUP_SYSTEM_PROMPT, MODELO_INDIVIDUAL, MODELO_GRUPAL

class OrchestratorUseCase:
    def __init__(self, db_adapter, ai_adapter, pdf_adapter):
        self.db = db_adapter
        self.ai = ai_adapter
        self.pdf = pdf_adapter

    def _generate_data_hash(self, prompt: str, events: list) -> str:
        """
        Genera una huella única basada en el prompt y los datos biométricos.
        Garantiza que si el JSON de entrada o el prompt cambian, el hash cambie.
        """
        # sort_keys=True es vital para que el orden de los campos no afecte el hash
        input_string = prompt + json.dumps(events, sort_keys=True)
        return hashlib.sha256(input_string.encode()).hexdigest()

    def run_full_session_process(self, app_session_id: str, json_file_path: str):
        # 1. Obtener la sesión y sus participantes
        session_db = self.db.get_session_by_app_id(app_session_id)
        if not session_db:
            raise Exception(f"No se encontró la sesión con app_id: {app_session_id}")

        participants = self.db.get_participants_with_roles(session_db.session_id)
        final_reports_meta = []

        # --- 1. FASE INDIVIDUAL ---
        for p in participants:
            # Obtener datos limpios de la capa Silver para este sujeto
            events = self.db.get_cleansed_events(session_db.session_id, p['subject_id'])
            
            mapping = {
                "metadata_sujeto": f"Nombre: {p['name']}, Edad: {p['age']}, Genero: {p['gender']}, Ciudad: {p['city']}, Rol: {p['role']}"
            }
            prompt_individual = SYSTEM_PROMPT.format(**mapping)
            
            # --- VERIFICACIÓN DE CACHÉ ---
            current_hash = self._generate_data_hash(prompt_individual, events)
            existing_report = self.db.get_report_by_hash(
                session_db.session_id, p['subject_id'], "individual", current_hash
            )

            if existing_report:
                print(f"✅ [RECOPILACIÓN] Reporte de {p['name']} recuperado de DB. Saltando OpenAI...")
                report_data = existing_report.content_json
                markdown_content = existing_report.content_markdown
                report_id = existing_report.report_id
            else:
                print(f"🤖 [IA] Generando nuevo análisis para: {p['name']}...")
                raw_resp = self.ai.generate_report(prompt_individual, json.dumps(events), model=MODELO_INDIVIDUAL)
                
                try:
                    clean_json = raw_resp.replace("```json", "").replace("```", "").strip()
                    report_data = json.loads(clean_json)
                except json.JSONDecodeError:
                    report_data = {"error": "Invalid JSON", "raw": raw_resp}

                markdown_content = self._json_to_markdown_individual(report_data)

                # Persistencia con el nuevo hash
                report_id = self.db.save_report_meta(
                    session_id=session_db.session_id,
                    subject_id=p['subject_id'],
                    kind="individual",
                    markdown=markdown_content, 
                    json_data=report_data,
                    prompt_hash=current_hash
                )

            # El PDF se genera siempre para asegurar que el archivo físico exista
            pdf_path = self.pdf.create_pdf(markdown_content, f"Reporte_Individual_{p['app_id']}")
            self.db.save_pdf_artifact(report_id, pdf_path)
            final_reports_meta.append({"name": p['name'], "path": pdf_path})

        # --- 2. FASE GRUPAL ---
        print(f"--- Procesando Informe Grupal de la sesión: {app_session_id} ---")
        
        # Obtener TODOS los eventos (subject_id=None)
        group_events = self.db.get_cleansed_events(session_db.session_id, subject_id=None)
        
        contexto = {
            "contexto_grupal": f"Sesión: {app_session_id}, Caso: {session_db.case_id}, Participantes: {len(participants)}"
        }
        prompt_grupal = GROUP_SYSTEM_PROMPT.format(**contexto)

        # VERIFICACIÓN DE CACHÉ GRUPAL
        group_hash = self._generate_data_hash(prompt_grupal, group_events)
        existing_group = self.db.get_report_by_hash(session_db.session_id, None, "group", group_hash)

        if existing_group:
            print(f"✅ [RECOPILACIÓN] Reporte GRUPAL recuperado de DB. Saltando OpenAI...")
            group_data = existing_group.content_json
            markdown_grupal = existing_group.content_markdown
            report_id_group = existing_group.report_id
        else:
            print(f"🤖 [IA] Generando nuevo análisis GRUPAL...")
            raw_resp_group = self.ai.generate_report(prompt_grupal, json.dumps(group_events), model=MODELO_GRUPAL)
            
            try:
                clean_json_group = raw_resp_group.replace("```json", "").replace("```", "").strip()
                group_data = json.loads(clean_json_group)
            except json.JSONDecodeError:
                group_data = {"error": "Invalid Group JSON", "raw": raw_resp_group}
            
            markdown_grupal = self._json_to_markdown_group(group_data)
            
            report_id_group = self.db.save_report_meta(
                session_id=session_db.session_id,
                subject_id=None,
                kind="group",
                markdown=markdown_grupal,
                json_data=group_data,
                prompt_hash=group_hash
            )

        pdf_path_group = self.pdf.create_pdf(markdown_grupal, f"Reporte_Grupal_{app_session_id}")
        self.db.save_pdf_artifact(report_id_group, pdf_path_group)
        final_reports_meta.append({"name": "REPORTE GRUPAL", "path": pdf_path_group})

        return final_reports_meta

    def _json_to_markdown_individual(self, data):
        """Reconstruye el Markdown visual completo para individuos."""
        head = data.get("header", {})
        tec = data.get("analisis_tecnico", {})
        afin = data.get("afinidad", {})
        
        md = f"""
# INFORME DE EVALUACIÓN PSICOPROFESIOGRÁFICA – CÁMARA GESELL
**CÉLULA DE INFORMES | BE-LABS ANALYTICS**

### FICHA DE IDENTIFICACIÓN
- **Nombre:** {head.get('nombre', 'N/A')}
- **Edad:** {head.get('edad', 'N/A')}
- **Género:** {head.get('genero', 'N/A')}
- **Ciudad:** {head.get('ciudad', 'N/A')}
- **Rol en Sesión:** {head.get('rol', 'N/A')}

---
## 1. ANÁLISIS DE SEÑALES TÉCNICAS (EVIDENCIA BIOMÉTRICA)
### A. Perfil de Voz y Prosodia [VOZ]
{tec.get('voz', 'N/A')}

### B. Conducta y Postura [VISIÓN – CUERPO]
{tec.get('postura', 'N/A')}

### C. Emociones y Micro-expresiones [VISIÓN – ROSTRO]
{tec.get('emociones', 'N/A')}

---
## 2. ASPECTOS POSITIVOS DOMINANTES
"""
        for item in data.get("aspectos_positivos", []):
            md += f"• **{item.get('nombre')}:** {item.get('justificacion')} (Ref: {item.get('ref')})\n"

        md += "\n---\n## 3. ASPECTOS NEGATIVOS O LIMITANTES\n"
        for item in data.get("aspectos_negativos", []):
            md += f"• **{item.get('nombre')}:** {item.get('justificacion')} (Ref: {item.get('ref')})\n"

        md += f"""
---
## 4. AFINIDAD CON EL ROL Y ROL IDEAL
- **Afinidad:** {afin.get('nivel', 'N/A')}
- **Rol Ideal:** {afin.get('rol_ideal', 'N/A')}

---
## 5. HITOS CRONOLÓGICOS DESTACADOS
"""
        for h in data.get("hitos", []):
            md += f"• **[{h.get('tiempo')}] – {h.get('titulo')}:** {h.get('descripcion')} (Ref: {h.get('ref')})\n"

        md += f"""
---
## 6. OBSERVACIÓN GENERAL Y RECOMENDACIÓN
{data.get('observacion_final', 'N/A')}
"""
        return md

    def _json_to_markdown_group(self, data):
        """Reconstruye el Markdown visual completo para grupos."""
        col = data.get("analisis_colectivo", {})
        inter = data.get("interaccion", {})
        
        md = f"""
# INFORME GRUPAL - ANÁLISIS COLECTIVO GESELL
**CÉLULA DE INFORMES | BE-LABS ANALYTICS**

---
## 1. DINÁMICA DE GRUPO
- **Perfil de Voz Colectivo:** {col.get('voz', 'N/A')}
- **Sincronía y Ritmo:** {col.get('sincronia', 'N/A')}
- **Clima Emocional General:** {col.get('clima_emocional', 'N/A')}

---
## 2. ASPECTOS POSITIVOS DEL GRUPO
"""
        for item in data.get("aspectos_positivos", []):
            md += f"• **{item.get('nombre')}:** {item.get('justificacion')} (Ref: {item.get('ref')})\n"

        md += "\n## 3. ASPECTOS NEGATIVOS O LIMITANTES DEL GRUPO\n"
        for item in data.get("aspectos_negativos", []):
            md += f"• **{item.get('nombre')}:** {item.get('justificacion')} (Ref: {item.get('ref')})\n"

        md += f"""
---
## 4. INTERACCIÓN Y LIDERAZGO
- **Patrón de Interacción:** {inter.get('patron', 'N/A')}
- **Liderazgo Identificado:** {inter.get('liderazgo', 'N/A')}

---
## 5. HITOS GRUPALES DESTACADOS
"""
        for h in data.get("hitos_grupales", []):
            md += f"• **[{h.get('tiempo')}] {h.get('evento')}:** {h.get('descripcion')}\n"

        md += f"""
---
## 6. CONCLUSIÓN GENERAL Y OBSERVACIONES DEL GRUPO
{data.get('conclusion_grupal', 'N/A')}
"""
        return md