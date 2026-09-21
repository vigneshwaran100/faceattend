# Implementation Plan: Docker E2E / Production-Style Container Validation (Final Approved)

Production-style Docker End-to-End (E2E) validation of the Face Recognition Attendance System. Validates image build reproducibility, build-context isolation, non-root execution, containerized database migrations, API liveness/readiness, CORS preflight headers, JWT authentication, RBAC enforcement, employee management, attendance processing, EOD finalization, container recreation data persistence, test user cleanup, and post-validation automated tests.

---

## Environmental Context & Architecture

> [!CRITICAL]
> **Environment Safety**:
> This E2E validation is permitted only against the local development/test PostgreSQL and Milvus instances. Before any mutating operation, verify that the configured database is not a production environment. Never execute these commands against production infrastructure.

> [!NOTE]
> **Stateful Integration Validation**:
> This validation exercises the Docker containerized API service against the live local development state:
> - `admin` user created in PostgreSQL.
> - `EMP001` (Vigneshwaran) enrolled with 10 real vectors in Milvus `face_embeddings_v2`.
> - Check-in recorded via the physical webcam scanner.
>
> Testing against this state demonstrates that the containerized application correctly accesses, authenticates, and operates on existing production-representative biometric and relational data without regressions.

> [!IMPORTANT]
> **Key Operational Principles**:
> 1. **No Hardcoded Credentials in Commands**: Database URLs are injected dynamically from local environment variables or configuration (`$env:DATABASE_URL`). Raw credentials are never hardcoded in scripts, markdown docs, or reports.
> 2. **Cryptographically Random JWT Secret**: A 32-byte cryptographically random secret (`secrets.token_urlsafe(32)`) is generated at test runtime.
> 3. **Fresh JWT Tokens via Docker API**: All authentication requests are made against the container at `http://localhost:8080/auth/login`. Tokens are signed directly by the container using its dynamic secret.
> 4. **No Service Bypasses**: No artificial manipulation of attendance records through direct internal service calls. State transitions reflect real scanner actions and API endpoints.
> 5. **Controlled Security User & Guaranteed Cleanup**: A dedicated test user with role `security` is created using the existing `AuthService` / `UserRepository` via a runtime-generated temporary password, and is strictly deleted after validation.

---

## Detailed Step-by-Step Execution Plan

### Phase 1: Local Baseline Capture & Environment Safety Guard
1. **Environment Safety Verification**:
   - Verify that the target database is running locally on `localhost:5432` / `host.docker.internal:5432` and is NOT a production instance.
2. **Capture Local Baseline**:
   - Confirm `admin` user exists in PostgreSQL (`users` table).
   - Confirm `EMP001` (Vigneshwaran) exists in PostgreSQL (`employees` table).
   - Confirm `EMP001` check-in record exists in PostgreSQL (`attendance` table).
   - Confirm 10 face embedding vectors for `EMP001` exist in Milvus (`face_embeddings_v2` collection).

### Phase 2: Docker Image Build & Security Inspection
3. **Build Docker Image**:
   ```bash
   docker build -t face-recognition-attendance:latest .
   ```
4. **Build Context & Security Inspection**:
   - Inspect container execution user (`whoami` -> `appuser`, UID 10001).
   - Verify that NO `.env`, `.env.*`, `.git/`, `.venv/`, `logs/`, `tests/`, `.insightface/`, or `infra/milvus/volumes/` entered the image.
   - Verify `alembic.ini`, `migrations/`, and `src/` exist in `/app` and are owned by `appuser`.

### Phase 3: Containerized Database Migrations
5. **Run Migrations via Ephemeral Container**:
   Execute migrations in an ephemeral container using the dynamic database connection environment variable:
   ```powershell
   docker run --rm -e DATABASE_URL="$env:CONTAINER_DATABASE_URL" face-recognition-attendance:latest alembic upgrade head
   ```
6. **Verify Migration Head via Ephemeral Container**:
   Verify migration state in an ephemeral container:
   ```powershell
   docker run --rm -e DATABASE_URL="$env:CONTAINER_DATABASE_URL" face-recognition-attendance:latest alembic current
   ```
   Confirm output confirms `5b73e92c1f0a (head)`.

### Phase 4: Application Container Startup & Probes
7. **Launch Application Container**:
   Generate dynamic random JWT secret and run container published on host port `8080`:
   ```powershell
   docker run -d --name attendance-api-e2e -p 8080:8000 `
     -e ENVIRONMENT="production" `
     -e DATABASE_URL="$env:CONTAINER_DATABASE_URL" `
     -e MILVUS_URI="$env:CONTAINER_MILVUS_URI" `
     -e MILVUS_COLLECTION_NAME="face_embeddings_v2" `
     -e JWT_SECRET="$env:DYNAMIC_JWT_SECRET" `
     -e CORS_ORIGINS="http://localhost:3000,http://localhost:5173" `
     face-recognition-attendance:latest
   ```
8. **Liveness, Readiness & CORS Verification**:
   - `GET http://localhost:8080/health` -> HTTP 200 `{"status": "healthy"}`.
   - `GET http://localhost:8080/ready` -> HTTP 200 `{"status": "ready", "ready": true, "dependencies": {"database": {"status": "healthy"}, "milvus": {"status": "healthy"}}}`.
   - `OPTIONS http://localhost:8080/auth/login` with `Origin: http://localhost:3000` -> Verify `Access-Control-Allow-Origin: http://localhost:3000`.

### Phase 5: Authentication & RBAC Verification
9. **Controlled Security User Provisioning**:
   Create a dedicated security user (`username='security_test'`) with a runtime-generated temporary password using existing `AuthService` / `UserRepository`.
10. **Authentication Testing (against port 8080)**:
    - `POST http://localhost:8080/auth/login` (admin) -> HTTP 200, returns container-signed JWT access token.
    - `POST http://localhost:8080/auth/login` (security) -> HTTP 200, returns container-signed JWT access token.
    - `POST http://localhost:8080/auth/login` (invalid password) -> HTTP 401 Unauthorized.
    - Request to `/employees` without `Authorization` header -> HTTP 401 Unauthorized.
11. **RBAC Enforcement**:
    - Using security user token:
      - `POST http://localhost:8080/departments` -> HTTP 403 Forbidden.
      - `POST http://localhost:8080/teams` -> HTTP 403 Forbidden.
      - `POST http://localhost:8080/employees` -> HTTP 403 Forbidden.
      - `POST http://localhost:8080/attendance/end-of-day` -> HTTP 403 Forbidden.
      - `GET http://localhost:8080/employees` -> HTTP 200 OK.
      - `GET http://localhost:8080/attendance` -> HTTP 200 OK.

### Phase 6: Domain & Attendance Workflow Verification
12. **Employee Management**:
    - `GET http://localhost:8080/employees/EMP001` through Docker API -> Returns Vigneshwaran details.
13. **Face Vector & Attendance Integration**:
    - Verify `face_embeddings_v2` in Milvus contains the expected `EMP001` vectors (10 vectors).
    - Query `GET http://localhost:8080/employees/EMP001/attendance` -> Verify today's check-in recorded from real kiosk.
    - Execute real host check-out scanner where camera access is available (or verify existing record).
    - Verify check-out and working-hours calculation through Docker API.
14. **EOD Finalization & Idempotency**:
    - Call `POST http://localhost:8080/attendance/end-of-day` using Docker API with admin token.
    - Verify expected status (`present` / `half_day` / `incomplete`).
    - Call `POST http://localhost:8080/attendance/end-of-day` a second time -> Verify idempotency (no duplicate records, existing record preserved).
15. **Reporting & Audit Logging**:
    - `GET http://localhost:8080/attendance` -> Paginated attendance list.
    - `GET http://localhost:8080/employees/EMP001/attendance/summary` -> Aggregate statistics.
    - `GET http://localhost:8080/audit-logs` -> Scanner audit log entries.

### Phase 7: Container Recreation Persistence Test
16. **Container Recreation Resilience**:
    - Force-remove the running container: `docker rm -f attendance-api-e2e`.
    - Create a new container instance: `attendance-api-e2e-recreated` with the same configuration.
    - Query `GET http://localhost:8080/ready` -> Verify clean startup.
    - Verify existing `EMP001`, attendance records, 10 face vectors, and admin authentication remain completely intact.
17. **Container Teardown**:
    - Remove test container: `docker rm -f attendance-api-e2e-recreated`.

### Phase 8: Test Data Cleanup, Regression Run & Reporting
18. **Test Data Cleanup**:
    - Remove the temporary `security_test` user created for E2E validation.
    - Verify no unexpected data was modified.
19. **Full Automated Test Suite**:
    ```bash
    uv run pytest
    ```
    Confirm all 182 tests pass cleanly with zero regressions.
20. **Final Report Generation**:
    Compile comprehensive, evidence-backed final report covering all checklist items.
