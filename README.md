# BE-LABS ANALYTICS: Gesell AI Motor
### Hexagonal Architecture + Medallion Data Lake + Smart Caching

This system is an advanced psycho-professional analysis engine. It processes biometric telemetry from Gesell chambers using a layered architecture, transforming raw data into high-fidelity AI reports while optimizing costs via an intelligent Smart Caching system.

---

## Prerequisites

Ensure the following are installed:
1.  **Docker & Docker Compose**.
2.  **Make** (For Windows, use Git Bash, WSL2, or install `make`. Otherwise, use the equivalent `docker-compose` commands provided).
3.  A valid **OpenAI API Key**.
4.  A `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=your_api_key_here
    DATABASE_URL=postgresql://postgres:Qwe.123*@db:5432/strix_final
    CASE_SERVICE_URL=https://httpbin.org/status
    ```

---

## Installation & Deployment (Step-by-Step)

### 1. Build and Start Infrastructure
**Linux/macOS:** `make build && make up`
**Windows:** `docker-compose build && docker-compose up -d`

### 2. Database Preparation
**Linux/macOS:**
```bash
make init-db
docker-compose exec app alembic stamp head
```
**Windows:**
```powershell
docker-compose exec app python init_db.py
docker-compose exec app python seed_initial_data.py
docker-compose exec app alembic stamp head
```

---

## Swagger Testing Guide (Payloads & Examples)

Access the interactive documentation at: `http://localhost:8000/docs`

### 1. Ingestion API: POST /ingest/user (HU-S3-02-T03)
Use this endpoint to verify **Upsert** and **Idempotency** logic.

**Example Payload:**
Copy and paste this into the request body:
```json
{
  "email": "keiner_dev@be-labs.com",
  "name": "Keiner Developer",
  "role": "analyst",
  "city": "Barranquilla"
}
```
*   **Verification:** The first execution returns a `200 OK` with a unique UUID. 
*   **Idempotency Test:** Execute the exact same request again. The system will return the **same UUID**, confirming no duplicate rows were created.

### 2. HTTP Client: GET /test/external-case/{case_id} (HU-S3-03-T02)
Use this to verify the resilient communication with external services.

*   **Scenario A (Controlled Error):** If your `.env` has `CASE_SERVICE_URL=https://httpbin.org/status`, enter **`500`** as the `case_id`.
    *   **Result:** You will receive a `502 Bad Gateway` with the message "External service failed with status 500".
*   **Scenario B (Success):** Change your `.env` to `CASE_SERVICE_URL=https://httpbin.org/anything` and restart. Enter **`1`** as the `case_id`.
    *   **Result:** You will receive the parsed JSON from the external service.

### 3. Full Automation: POST /process/full-json-automation
*   **Action:** Click "Execute" (No parameters required).
*   **Result:** This triggers the entire pipeline using the local `Data/Sesion_grupal.json` file, creating all 6 reports (5 individual, 1 group) in the `/artifacts` folder.

---

## Smart Caching Magic

*   **First Run:** The system calls OpenAI, consumes tokens, and generates the reports.
*   **Subsequent Runs:** The system detects an identical data hash, **skips OpenAI**, and retrieves the reports from the database.
*   **Result:** 100% token savings and instant report generation.

---

## SQL Data Inspection

Use these commands to verify the internal state of the database:

**Verify Users:**
```bash
docker-compose exec db psql -U postgres -d strix_final -c "SELECT name, email, role FROM operational.users;"
```

**Verify Generated Reports:**
```bash
docker-compose exec db psql -U postgres -d strix_final -c "SELECT report_id, session_id, kind, generated_at FROM artifacts.reports;"
```

---

## Makefile Quick Reference

| Command | Equivalent Command (Windows) | Description |
| :--- | :--- | :--- |
| `make up` | `docker-compose up -d` | Starts the services. |
| `make init-db` | `python init_db.py && ...` | Prepares the database. |
| `make run` | `python src/main.py` | Runs interactive pipeline. |
| `make api` | `docker-compose up app` | Runs the API service. |
| `make clean` | `rm artifacts/*.pdf` | Clears generated reports. |

---

## Output
Generated PDFs are mapped to your local machine in the `./artifacts/` folder.

**Developed by the BE-LABS ANALYTICS Team.**