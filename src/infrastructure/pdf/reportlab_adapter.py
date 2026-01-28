import os
import markdown2
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.colors import black, HexColor
from src.domain.ports import PDFPort

class ReportLabAdapter(PDFPort):
    def create_pdf(self, markdown_content: str, filename_prefix: str) -> str:
        # Route configuration
        output_dir = "artifacts"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"{filename_prefix}.pdf")
        # Document Settings
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, 
                                rightMargin=50, leftMargin=50, 
                                topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        elements = []

        # Clean paragraph style
        estilo_parrafo = ParagraphStyle(
            'Gessel_Normal',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )
        # Convert Markdown to HTML
        html_content = markdown2.markdown(markdown_content, extras=["tables"])
        soup = BeautifulSoup(html_content, 'html.parser')
        # --- SEQUENTIAL PROCESSING  ---
        for element in soup.contents:
            if element.name is None: continue
            if element.name in ['h1', 'h2', 'h3']:
                level = element.name[1]
                size = 14 if level == '1' else 12
                style = ParagraphStyle(f'H{level}', parent=styles['Heading1'], fontSize=size, spaceBefore=12, spaceAfter=6)
                elements.append(Paragraph(element.get_text().strip(), style))
            
            # Paragraphs
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    elements.append(Paragraph(text, estilo_parrafo))
            
            # List 
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li'):
                    bullet_text = f"• {li.get_text().strip()}"
                    elements.append(Paragraph(bullet_text, estilo_parrafo))
                elements.append(Spacer(1, 5))

            # Tables
            elif element.name == 'table':
                table_data = []
                for row in element.find_all('tr'):
                    row_content = [Paragraph(cell.get_text().strip(), estilo_parrafo) for cell in row.find_all(['td', 'th'])]
                    table_data.append(row_content)
                
                if table_data:
                    t = Table(table_data, colWidths=[120, 50, 280]) 
                    t.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#F0F0F0')),
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 10))
            elif element.name == 'hr':
                elements.append(Spacer(1, 5))

        # Build the PDF
        try:
            doc.build(elements)
            print(f"PDF successfully generated: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Error building PDF {e}")
            raise e