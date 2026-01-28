import os
import requests
import logging
from typing import Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.domain.ports import CaseServicePort

# Configuración de logs seguros
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CaseServiceClient")

class CaseServiceClient(CaseServicePort):
    def __init__(self):
        # Requerimiento: base_url desde env var
        self.base_url = os.getenv("CASE_SERVICE_URL", "http://external-case-service.local")
        self.timeout = 5  # Requerimiento: timeout de 5 segundos
        self.max_retries = 3
        
        # Requerimiento: retries limitados (Estrategia de reintento)
        self.session = requests.Session()
        retries = Retry(
            total=self.max_retries,
            backoff_factor=1, # Espera 1s, 2s, 4s...
            status_forcelist=[500, 502, 503, 504] # Reintenta en errores 5xx
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def fetch_case_data(self, case_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/cases/{case_id}"
        
        try:
            # AC: Dado un 200, retorna JSON parseado
            logger.info(f"Fetching case data from URL: {url} (Timeout: {self.timeout}s)")
            
            response = self.session.get(url, timeout=self.timeout)
            
            # Lanza excepción si el código no es 2xx
            response.raise_for_status()
            
            return response.json()

        except requests.exceptions.Timeout:
            # AC: Dado timeout, falla controlado y rastro en logs seguros
            logger.error(f"Timeout Error: The request to CaseService timed out. CaseID: {case_id}")
            raise Exception("Case Service is not responding (Timeout).")

        except requests.exceptions.HTTPError as e:
            # AC: Dado 5xx, falla controlado
            status_code = e.response.status_code
            logger.error(f"HTTP Error {status_code}: failed to fetch CaseID: {case_id}")
            # Requerimiento: logs sin payload completo (no logueamos e.response.text)
            raise Exception(f"External service failed with status {status_code}.")

        except Exception as e:
            logger.error(f"Unexpected Error fetching CaseID: {case_id} | Type: {type(e).__name__}")
            raise Exception("An unexpected error occurred while contacting the Case Service.")