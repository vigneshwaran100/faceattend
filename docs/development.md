# Local Development & Testing Guide

This document provides complete instructions for setting up, developing, and testing the FaceAttend system locally.

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:
- **Python**: `3.12` (pinned in `.python-version`)
- **uv**: Modern, fast Python package manager (`pip install uv` or via standalone installer)
- **Node.js**: `v20+` and `npm`
- **Docker & Docker Compose**: For local PostgreSQL and Milvus vector database
- **Webcam / Camera**: Optional, required only for edge scanner scripts

---

## 2. Infrastructure Setup (Docker)

Start the local storage infrastructure (PostgreSQL & Milvus vector database):

```bash
# Start Milvus standalone (etcd, minio, milvus)
docker compose -f infra/milvus/docker-compose.yml up -d

# Start PostgreSQL 17 database & pgAdmin
docker compose -f infra/milvus/postgre/docker-compose.yml up -d
```

Verify services are healthy:
- Milvus: `http://localhost:19530`
- PostgreSQL: `localhost:5432` (database: `smart_attendance`)
- pgAdmin (optional): `http://localhost:5050`

---

## 3. Backend Setup

### Environment File
Copy the environment template and configure your local settings:
```bash
cp .env.example .env
```

### Dependency Installation & Virtual Environment
Install all dependencies (including development test dependencies) using `uv`:
```bash
uv sync
```

### Database Migrations
Apply the latest Alembic schema migrations:
```bash
uv run alembic upgrade head
```

### Running the Backend Server
Start the FastAPI server with auto-reload:
```bash
uv run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Readiness check: `http://localhost:8000/ready`

---

## 4. Frontend Setup

### Environment File
Navigate to the `frontend/` directory and configure environment:
```bash
cd frontend
cp .env.example .env
```

### Install Dependencies & Start Dev Server
```bash
npm install
npm run dev
```
The React management portal will run on `http://localhost:5173`.

---

## 5. Running Tests & Validation

### Backend Pytest Suite
FaceAttend has a hermetic test suite with **218 automated tests**:
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with code coverage
uv run pytest --cov=app --cov-report=term-missing
```

#### Test Suite Breakdown (218 Tests Total)
- `tests/api/`: 57 tests (Auth, attendance, employees, RBAC, kiosk verification)
- `tests/core/`: 28 tests (Configuration, production hardening, secret safety)
- `tests/models/`: 4 tests (Domain entity invariants)
- `tests/repositories/`: 30 tests (PostgreSQL & Milvus persistence abstractions)
- `tests/services/`: 91 tests (Attendance, enrollment, quality, recognition logic)
- `tests/vision/`: 8 tests (Face tracking, IoU calculations)

### Frontend Build & Type Check
Verify TypeScript typing and production bundling:
```bash
cd frontend
npm run build
```

---

## 6. Edge Utility Scripts

Helper scripts located in `scripts/`:
- `create_user.py`: Creates or updates operator credentials (`uv run python scripts/create_user.py --username admin --password admin123`).
- `test_camera.py`: Validates local OpenCV camera capture (`uv run python scripts/test_camera.py`).
- `test_database_connection.py`: Checks PostgreSQL connectivity.
- `test_milvus_connection.py`: Checks Milvus connectivity.
- `register_employee_face.py`: Interactive camera-based face vector enrollment.
- `check_in_scanner.py`: Runs interactive desktop check-in scanner.
- `check_out_scanner.py`: Runs interactive desktop check-out scanner.
- `finalize_attendance.py`: Manually triggers daily attendance calculation.
