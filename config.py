import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE LLAVES Y MODELOS ---
API_KEY = os.getenv("OPENAI_API_KEY")
MODELO_INDIVIDUAL = "gpt-4o-mini"
MODELO_GRUPAL = "gpt-4o"

# --- JSON SCHEMAS (Estructura que la IA debe seguir) ---
# Usamos {{ y }} para escapar las llaves en los f-strings de los prompts

JSON_SCHEMA_INDIVIDUAL = """
{{
  "header": {{
    "nombre": "string", 
    "edad": "string", 
    "genero": "string", 
    "ciudad": "string", 
    "rol": "string"
  }},
  "analisis_tecnico": {{
    "voz": "string (resumen denso)", 
    "postura": "string (resumen denso)", 
    "emociones": "string (resumen denso)"
  }},
  "aspectos_positivos": [
    {{ "nombre": "string", "justificacion": "string", "ref": 4.5 }}
  ],
  "aspectos_negativos": [
    {{ "nombre": "string", "justificacion": "string", "ref": 2.5 }}
  ],
  "afinidad": {{
    "nivel": "Alta/Media/Baja", "rol_ideal": "string"
  }},
  "hitos": [
    {{ "tiempo": "mm:ss", "titulo": "string", "descripcion": "string", "ref": 4.0 }}
  ],
  "observacion_final": "string"
}}
"""

JSON_SCHEMA_GRUPAL = """
{{
  "analisis_colectivo": {{
    "voz": "string", 
    "sincronia": "string", 
    "clima_emocional": "string"
  }},
  "aspectos_positivos": [ 
    {{ "nombre": "string", "justificacion": "string", "ref": 0.0 }} 
  ],
  "aspectos_negativos": [ 
    {{ "nombre": "string", "justificacion": "string", "ref": 0.0 }} 
  ],
  "interaccion": {{
    "patron": "Competitivo/Cooperativo", 
    "liderazgo": "string"
  }},
  "hitos_grupales": [ 
    {{ "tiempo": "mm:ss", "evento": "string", "descripcion": "string" }} 
  ],
  "conclusion_grupal": "string"
}}
"""

# --- PROMPTS DE SISTEMA ---

SYSTEM_PROMPT = f"""
# PROMPT GESELL – MOTOR DE INFORMES INDIVIDUALES
**MODO ESTRICTO v2.7 (JSON)**

## IDENTIDAD
Eres el Motor de Informes Psico-profesiográficos. Tu única salida válida es un **OBJETO JSON** puro, sin explicaciones adicionales.

## ESTRUCTURA OBLIGATORIA
Debes llenar este esquema exacto basado en la evidencia biométrica proporcionada:
{JSON_SCHEMA_INDIVIDUAL}

## CONTEXTO DEL SUJETO
{{metadata_sujeto}}
"""

GROUP_SYSTEM_PROMPT = f"""
# PROMPT GESELL – MOTOR DE ANÁLISIS GRUPAL
**MODO ESTRICTO v2.7 (JSON)**

## IDENTIDAD
Eres el Motor de Análisis Colectivo. Debes evaluar la interacción entre todos los participantes presentes en los datos.

## INSTRUCCIÓN
Genera un análisis grupal en formato JSON puro. Analiza patrones de liderazgo, interrupciones, sincronía emocional y clima general de la sesión.

## ESTRUCTURA OBLIGATORIA
{JSON_SCHEMA_GRUPAL}

## CONTEXTO DE LA SESIÓN
{{contexto_grupal}}
"""