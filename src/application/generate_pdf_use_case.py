import uuid
import json
from typing import Optional
from src.domain.ports import ReportRepositoryPort, AIPort, PDFPort

class GeneratePdfUseCase:
    """
    Orchestrates the PDF generation process for both Individual and Group reports.
    Uses flat metadata from the improved Supabase view.
    """
    
    def __init__(self, 
                 report_repo: ReportRepositoryPort, 
                 ai_service: AIPort, 
                 pdf_service: PDFPort):
        self.report_repo = report_repo
        self.ai_service = ai_service
        self.pdf_service = pdf_service

    def execute(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID] = None) -> Optional[str]:
        """
        Generates a PDF for the given session. 
        Infects real metadata (Session ID, Case Title) directly from the report_data.
        """
        # 1. FETCH DATA
        report_data = self.report_repo.get_report_content(session_id, subject_id)
        
        if not report_data:
            tipo_err = "Grupal" if subject_id is None else f"Individual para {subject_id}"
            raise ValueError(f"Reporte {tipo_err} no encontrado para la sesión {session_id}")
            
        content_json = report_data.get("content_json")
        report_kind = report_data.get("kind", "individual")
        report_id = report_data.get("report_id", str(uuid.uuid4()))
        
        if not content_json:
             raise ValueError(f"El reporte {report_kind} no contiene datos JSON")

        # --- JUGADA MBAPPE ACTUALIZADA (DATOS PLANOS) ---
        # Ahora los datos vienen directos desde la vista mejorada de Supabase
        app_sid = report_data.get("app_session_id", "No proporcionado")
        case_title = report_data.get("case_title", "Análisis de Caso")

        # 2. SELECCIONAR PROMPT SEGÚN EL TIPO
        if report_kind == "individual":
            system_prompt = """Eres un experto en análisis de comportamiento y comunicación en equipos de trabajo.
Tu tarea es generar un INFORME DE EVALUACIÓN PSICOPROFESIONAL INDIVIDUAL en español.

El informe debe ser profesional, estructurado y contener:
1. **Datos del Evaluado**: Nombre, rol, sesión, duración
2. **Resumen Ejecutivo**: Síntesis del desempeño
3. **Análisis de Comunicación Verbal**
4. **Análisis de Comunicación No Verbal**
5. **Análisis Emocional**
6. **Fortalezas, Áreas de Mejora y Recomendaciones**

Usa formato Markdown con headers, listas y tablas. NO uses emojis."""
        else:
            system_prompt = """Eres un experto en dinámica de equipos y análisis de comportamiento grupal.
Tu tarea es generar un INFORME DE EVALUACIÓN GRUPAL en español.

El informe debe contener:
1. **Datos de la Sesión**: ID, caso, duración, participantes
2. **Resumen Ejecutivo** de la dinámica grupal
3. **Participantes**: Tabla con nombres y roles
4. **Análisis de Dinámica Grupal**: Liderazgo, comunicación, participación
5. **Momentos Clave, Fortalezas y Recomendaciones grupales**

Usa formato Markdown con headers, listas y tablas. NO uses emojis."""

        # 3. PREPARAR INPUT PARA IA (Metadatos + JSON)
        json_str = json.dumps(content_json, ensure_ascii=False, indent=2)
        
        # Bloque de contexto para que la IA no invente datos
        contexto_real = f"""
DATOS REALES PARA EL ENCABEZADO DEL INFORME (USA ESTOS EXACTAMENTE):
- ID de Sesión: {app_sid}
- Título del Caso: {case_title}
- Tipo de Reporte: {report_kind.upper()}
"""

        # LLAMADA A IA
        markdown_content = self.ai_service.generate_report(
            system_prompt=system_prompt,
            user_json_data=f"{contexto_real}\n\nGenera el informe basándote en estos datos biométricos:\n\n{json_str}",
            model="gpt-4o"
        )
        
        # 4. GENERAR ARCHIVO PDF
        filename = f"informe_{report_kind}_{str(report_id)[:8]}"
        pdf_path = self.pdf_service.create_pdf(markdown_content, filename)
        
        return pdf_path
