import uuid
from typing import Optional
from src.domain.ports import ReportRepositoryPort, AIPort, PDFPort

class GeneratePdfUseCase:
    """
    Orchestrates the PDF generation process:
    1. Fetch report data from Repository (Supabase)
    2. detailed content generation via AI (OpenAI) - if needed or if just converting existing markdown
    3. PDF creation via PDFPort
    """
    
    def __init__(self, 
                 report_repo: ReportRepositoryPort, 
                 ai_service: AIPort, 
                 pdf_service: PDFPort):
        self.report_repo = report_repo
        self.ai_service = ai_service
        self.pdf_service = pdf_service

    def execute(self, session_id: uuid.UUID, subject_id: uuid.UUID) -> Optional[str]:
        """
        Generates a PDF for the given session and subject.
        Returns the path to the generated PDF file.
        """
        # 1. Fetch Report Data
        report_data = self.report_repo.get_report_content(session_id, subject_id)
        if not report_data:
            raise ValueError(f"Report not found for session {session_id} and subject {subject_id}")
            
        content_json = report_data.get("content_json")
        report_kind = report_data.get("kind", "individual")
        report_id = report_data.get("report_id", str(uuid.uuid4()))
        
        if not content_json:
             raise ValueError("Report data contains no content_json")

        # 2. Generate Markdown via AI
        # Logic adapted from Demo3's pdf_generator.py
        
        if report_kind == "individual":
            system_prompt = """Eres un experto en análisis de comportamiento y comunicación en equipos de trabajo.
Tu tarea es generar un INFORME DE EVALUACIÓN PSICOPROFESIONAL INDIVIDUAL en español, 
basándote en los datos JSON proporcionados.

El informe debe ser profesional, estructurado y contener:
1. **Datos del Evaluado**: Nombre, rol, sesión, duración
2. **Resumen Ejecutivo**: Breve síntesis del desempeño observado
3. **Análisis de Comunicación Verbal**: 
   - Prosodia (volumen, tono, velocidad)
   - Turnos de palabra e interrupciones
   - Calidad del discurso (argumentación, claridad)
4. **Análisis de Comunicación No Verbal**:
   - Postura y orientación corporal
   - Contacto visual
   - Gestos y nivel de agitación
5. **Análisis Emocional**:
   - Emociones detectadas
   - Valencia y arousal
6. **Fortalezas Observadas**
7. **Áreas de Mejora**
8. **Recomendaciones**

Usa formato Markdown con headers, listas y tablas cuando corresponda.
NO uses emojis. Sé objetivo y profesional."""
        else:
            system_prompt = """Eres un experto en dinámica de equipos y análisis de comportamiento grupal.
Tu tarea es generar un INFORME DE EVALUACIÓN GRUPAL en español,
basándote en los datos JSON proporcionados.

El informe debe ser profesional, estructurado y contener:
1. **Datos de la Sesión**: ID, caso, duración, participantes
2. **Resumen Ejecutivo**: Síntesis de la dinámica grupal observada
3. **Participantes**: Tabla con nombres, roles y descripción breve
4. **Análisis de Dinámica Grupal**:
   - Distribución de participación
   - Patrones de comunicación
   - Liderazgo emergente
5. **Análisis por Participante**: Breve resumen de cada uno
6. **Momentos Clave**: Eventos significativos detectados
7. **Fortalezas del Equipo**
8. **Áreas de Mejora Grupal**
9. **Recomendaciones**

Usa formato Markdown con headers, listas y tablas cuando corresponda.
NO uses emojis. Sé objetivo y profesional."""

        import json
        json_str = json.dumps(content_json, ensure_ascii=False, indent=2)
        
        # Use existing AI Port
        markdown_content = self.ai_service.generate_report(
            system_prompt=system_prompt,
            user_json_data=f"Genera el informe basándote en estos datos:\n\n{json_str}",
            model="gpt-4o"
        )
        
        # 3. Generate PDF
        # Clean special chars from filename
        filename = f"informe_{report_kind}_{str(report_id)[:8]}"
        pdf_path = self.pdf_service.create_pdf(markdown_content, filename)
        
        return pdf_path
