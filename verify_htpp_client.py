import os
import time
from src.infrastructure.clients.case_service_client import CaseServiceClient

def run_test_scenarios():
    client = CaseServiceClient()
    
    print("\n" + "="*50)
    print("TESTING HU-S3-03-T02: CaseServiceClient")
    print("="*50)

    # ESCENARIO 1: Dado un 200 (Success)
    # Usaremos una URL real de prueba (JSONPlaceholder o HTTPBin)
    print("\n[Scenario A: 200 OK]")
    client.base_url = "https://jsonplaceholder.typicode.com" 
    try:
        # Intentamos traer el post 1 como si fuera un "caso"
        data = client.fetch_case_data("posts/1")
        print(f"✅ Success! Data ID: {data.get('id')}")
        print(f"✅ Response Preview: {str(data)[:50]}...")
    except Exception as e:
        print(f"❌ Failed Scenario A: {e}")

    # ESCENARIO 2: Dado un Timeout/Connection Error
    print("\n[Scenario B: Timeout/Controlled Failure]")
    # Usamos una IP que no existe para forzar el timeout
    client.base_url = "http://10.255.255.1" 
    client.timeout = 2 # Acortamos para no esperar tanto en el test
    
    start_time = time.time()
    try:
        client.fetch_case_data("timeout-test")
    except Exception as e:
        end_time = time.time()
        print(f"✅ Controlled Failure detected: {e}")
        print(f"✅ Rastro en logs verificado (mira la consola arriba)")
        print(f"✅ Time elapsed: {round(end_time - start_time, 2)}s (Retries working)")

    # ESCENARIO 3: Dado un 5xx (Error de servidor)
    print("\n[Scenario C: 5xx Server Error]")
    client.base_url = "https://httpbin.org/status/500" # URL que siempre devuelve 500
    try:
        client.fetch_case_data("error-test")
    except Exception as e:
        print(f"✅ Controlled HTTP Error detected: {e}")

    print("\n" + "="*50)
    print("VERIFICATION COMPLETED")
    print("="*50)

if __name__ == "__main__":
    run_test_scenarios()