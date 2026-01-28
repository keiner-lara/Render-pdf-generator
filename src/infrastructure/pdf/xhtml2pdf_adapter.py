import os
import re
import markdown
from io import BytesIO
from xhtml2pdf import pisa
from src.domain.ports import PDFPort

class Xhtml2PdfAdapter(PDFPort):
    """
    Adapter implementation using xhtml2pdf (pisa) to generate PDFs from Markdown/HTML.
    """
    
    def _remove_emojis(self, text: str) -> str:
        emoji_pattern = re.compile("[" 
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub('', text)

    def create_pdf(self, markdown_content: str, filename_prefix: str) -> str:
        """
        Generates a PDF from markdown content and saves it to the artifacts directory.
        Returns the path to the generated PDF.
        """
        # 1. Clean and convert to HTML
        clean_content = self._remove_emojis(markdown_content)
        
        html_body = markdown.markdown(
            clean_content, 
            extensions=['extra', 'codehilite', 'tables']
        )
        
        # 2. Add professional CSS
        css = """
        <style>
            @page { 
                size: A4; 
                margin: 2cm; 
            }
            body { 
                font-family: Helvetica, Arial, sans-serif; 
                font-size: 11px; 
                line-height: 1.6; 
                color: #2c3e50; 
            }
            h1 { 
                color: #1a252f; 
                border-bottom: 3px solid #3498db; 
                padding-bottom: 10px; 
                font-size: 22px; 
                margin-top: 20px;
            }
            h2 { 
                color: #2980b9; 
                margin-top: 25px; 
                border-bottom: 1px solid #bdc3c7; 
                padding-bottom: 5px;
                font-size: 16px; 
            }
            h3 { 
                color: #34495e; 
                margin-top: 15px; 
                font-size: 13px; 
            }
            h4 {
                color: #7f8c8d;
                font-size: 12px;
                margin-top: 10px;
            }
            p {
                text-align: justify;
                margin-bottom: 10px;
            }
            ul, ol {
                margin-left: 20px;
                margin-bottom: 10px;
            }
            li {
                margin-bottom: 5px;
            }
            code { 
                background-color: #f8f9fa; 
                padding: 2px 5px; 
                font-family: Courier; 
                color: #c0392b; 
                font-size: 10px;
            }
            pre { 
                background-color: #f4f6f7; 
                padding: 15px; 
                border: 1px solid #ddd; 
                white-space: pre-wrap; 
                font-size: 9px; 
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0; 
            }
            th { 
                background-color: #34495e; 
                color: white; 
                padding: 10px 8px; 
                text-align: left;
                font-size: 11px;
            }
            td { 
                border: 1px solid #ddd; 
                padding: 8px; 
                font-size: 10px;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            strong {
                color: #2c3e50;
            }
            em {
                color: #7f8c8d;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin: 15px 0;
                color: #555;
                font-style: italic;
            }
        </style>
        """
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                {css}
            </head>
            <body>
                {html_body}
            </body>
        </html>
        """
        
        # 3. Generate PDF
        output_dir = "artifacts"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"{filename_prefix}.pdf")
        
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                BytesIO(full_html.encode("utf-8")), 
                dest=pdf_file
            )
            
        if pisa_status.err:
            raise Exception(f"Error generating PDF: {pisa_status.err}")
            
        return pdf_path
