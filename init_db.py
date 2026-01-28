import sys
import os
from sqlalchemy import create_engine, text

# 1. PATH configuration to find the models in the src folder
sys.path.append(os.getcwd())
from src.infrastructure.persistence.models import Base

# 2. Connection settings (Adjusted to your password)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Qwe.123*@localhost:5432/strix_final")
engine = create_engine(DATABASE_URL)

def initialize_database():
    print("Starting physical construction of the database...")
    
    try:
        with engine.begin() as connection:
            schemas = [
                'operational', 
                'audit', 
                'cleansed', 
                'artifacts', 
                'logs'
            ]
            
            for schema in schemas:
                print(f"Creating schema: {schema}")
                connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            
            # B. Create Security Extension
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            
            # C.Create all tables defined in models.py
            print("Creating tables in all schemas...")
            #`create_all` analyzes foreign keys and creates the tables in the correct order.
            Base.metadata.create_all(connection)      
        print("Database successfully built.")
        
        # D. Alembic Seal 
        print("Don't forget to run: alembic stamp head")

    except Exception as e:
        print(f"Critical error initializing the database: {e}")

if __name__ == "__main__":
    initialize_database()