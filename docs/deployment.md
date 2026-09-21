# Production Deployment Guide

## 1. Overview

FaceAttend is designed to be deployed using containerized architectures (Docker, Kubernetes, AWS ECS). The backend utilizes a multi-stage Dockerfile adhering to least-privilege security standards.

---

## 2. Multi-Stage Dockerfile Architecture

The production image build is defined in `Dockerfile`:
1. **Builder Stage**:
   - Base image: `python:3.12-slim`
   - Installs build tools (`build-essential`).
   - Installs Python package wheel into unprivileged user local directory (`/root/.local`).
2. **Runner Stage**:
   - Base image: `python:3.12-slim`
   - Installs system libraries for OpenCV and InsightFace (`libgl1`, `libglib2.0-0`).
   - Creates a non-root system user (`appuser`, UID 10001).
   - Copies clean virtual environment and source code.
   - Runs `uvicorn app.api.main:app` as non-root user.

### Building the Image
```bash
docker build -t faceattend-api:latest .
```

---

## 3. Database Migration Strategy

> [!IMPORTANT]
> Never execute auto-migrations inside the web server container startup script. Run schema migrations as a pre-deployment step.

Before launching or rolling out a new application container, run migrations using an ephemeral container:
```bash
docker run --rm \
  -e DATABASE_URL="postgresql+psycopg://user:pass@db-host:5432/dbname" \
  faceattend-api:latest alembic upgrade head
```

---

## 4. Production Secret & Environment Injection

Do **NOT** mount or copy `.env` files into containers. All sensitive values must be injected via your orchestrator (Kubernetes Secrets, AWS SSM Parameter Store, HashiCorp Vault).

### Required Production Environment Variables

| Variable | Description | Security Requirement |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | Use strong password, SSL mode enabled in production. |
| `MILVUS_URI` | Vector DB connection URI | Point to production Milvus cluster. |
| `MILVUS_COLLECTION_NAME` | Vector collection name | Default: `face_embeddings_v2`. |
| `JWT_SECRET` | Secret key for signing JWTs | **Must be cryptographically random and at least 32 characters**. |
| `CORS_ORIGINS` | Comma-separated allowed origins | Explicit domains only (e.g., `https://attendance.yourcompany.com`). |
| `ENVIRONMENT` | Runtime environment | Set to `production`. |
| `LOG_LEVEL` | Application logging verbosity | Set to `INFO` or `WARNING`. |

---

## 5. Container Probes & Health Checks

Configure orchestrator health probes to monitor service lifecycle:
- **Liveness Probe**: `GET /health` (returns HTTP 200 `{"status": "healthy"}`)
- **Readiness Probe**: `GET /ready` (returns HTTP 200 when both PostgreSQL and Milvus respond successfully)
