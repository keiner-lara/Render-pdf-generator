import os
import sys
import json
from dotenv import load_dotenv
# 1.Route Configuration for Hexagonal Architecture
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Import of Adapters (Infrastructure)
from src.infrastructure.persistence.sqlalchemy_adapter import SQLAlchemyAdapter
from src.infrastructure.openai.openai_adapter import OpenAIAdapter
from src.infrastructure.pdf.reportlab_adapter import ReportLabAdapter
# Importing the Use Case (Application)
from src.application.orchestrator_use_case import OrchestratorUseCase
# Configuration Import
from config import API_KEY, MODELO_INDIVIDUAL, MODELO_GRUPAL, SYSTEM_PROMPT, GROUP_SYSTEM_PROMPT
def run_pipeline():
    """
    Ingesta -> Auditoría -> Refinería -> OpenAI -> Storage
    """
    load_dotenv()
    # Connection configuration (Local Ubuntu / Supabase)
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:Qwe.123*@localhost:5432/strix_final")
    
    print("\n" + "="*60)
    print("   BE-LABS ANALYTICS")
    print("   Flujo: Bronze -> Silver -> OpenAI -> Artifacts")
    print("="*60)

    try:
        # 2.Adapter Initialization
        db_adapter = SQLAlchemyAdapter(db_url)
        ai_adapter = OpenAIAdapter(api_key=API_KEY) 
        pdf_adapter = ReportLabAdapter()

        # 3. Use Case Initialization
        orchestrator = OrchestratorUseCase(db_adapter, ai_adapter, pdf_adapter)

        # 4.Input File Selection
        data_dir = "Data"
        files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        if not files:
            print("No JSON files were found in the folder in Data/")
            return

        print("\n Files detected:")
        for i, f in enumerate(files):
            print(f"  [{i+1}] {f}")
        choice = input("\n Select the file number to process:")
        selected_file = files[int(choice) - 1]
        json_path = os.path.join(data_dir, selected_file)
        # 5. PROCESS EXECUTION N+1
        print(f"\n Starting processing of: {selected_file}")  
        # We read the JSON to identify the session.
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            app_session_id = raw_data["json"]["session_meta"]["session_id"]
        results = orchestrator.run_full_session_process(app_session_id, json_path)

        # 6. Execution Summary
        print("\n" + "*"*50)
        print("PIPELINE SUCCESSFULLY COMPLETED")
        print("*"*50)
        print(f"Individual Reports: {len(results) - 1}")
        print(f"Group Reports: 1")
        print(f"Location: Folder 'artifacts/'")
        for r in results:
            print(f"{r['name']}: {r['path']}")
        
        print("\n" + "="*60 + "\n")
    except Exception as e:
        print(f"\n CRITICAL PIPELINE ERROR: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("Error: The OPENAI_API_KEY is missing from the file.env")
    else:
        run_pipeline()