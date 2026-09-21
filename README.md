# FaceAttend — Enterprise Biometric Face Recognition Attendance System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Milvus](https://img.shields.io/badge/Milvus-2.4%2B-00A4E4.svg)](https://milvus.io/)
[![CI](https://img.shields.io/badge/tests-218%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

FaceAttend is an enterprise biometric attendance and workforce management platform. Built on **FastAPI**, **InsightFace**, **PostgreSQL**, and **Milvus Vector Database**, with a modern **React 19 / TypeScript** administrative portal.

---

## Key Features

- **Biometric Face Verification**: 512-dimensional vector embeddings with InsightFace ArcFace (`buffalo_l`) and Milvus cosine similarity search.
- **Client-Side Stability Verification**: Multi-frame temporal lock on kiosk edge scanners before submitting verification punches.
- **FastAPI REST API**: Fully asynchronous REST API with OAuth2 JWT authentication and role-based access control (`admin`, `security`).
- **Comprehensive Attendance Engine**: Automatic shift calculation, check-in/check-out pairing, idempotency, and End-of-Day (EOD) batch finalization.
- **React Management Portal**: Interactive workforce dashboard with 3D/canvas visualizers, employee enrollment, and daily attendance logs.
- **Automated Audit Logging**: Every scanner verification attempt (success or failure) is logged with camera telemetry and similarity scores.
- **Production Hardened**: Non-root Docker container, Alembic schema migrations, and hermetic automated test suite (**218 tests passing**).

---

## Repository Structure

```text
face-recognition/
├── .github/                    # CI/CD workflows, CodeQL, Dependabot, PR/Issue templates
│   ├── workflows/
│   │   ├── backend-ci.yml      # Pytest automated test pipeline
│   │   ├── frontend-ci.yml     # TypeScript build & verification pipeline
│   │   └── codeql.yml          # GitHub CodeQL static security analysis
│   ├── dependabot.yml          # Automated dependency updates (pip, npm, actions)
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
├── docs/                       # Comprehensive documentation
│   ├── architecture.md         # System topology, biometric pipeline, data models
│   ├── api.md                  # REST API spec & verified RBAC role matrix
│   ├── development.md          # Local developer onboarding & testing guide
│   └── deployment.md           # Multi-stage Docker & production deployment guide
├── frontend/                   # Modern React 19 + TypeScript + Vite management app
│   ├── src/                    # Components, pages, hooks, services, theme
│   ├── package.json            # Node.js dependencies
│   └── .env.example            # Frontend environment variable template
├── infra/                      # Infrastructure as Code
│   └── milvus/                 # Milvus standalone & PostgreSQL 17 Docker Compose
├── migrations/                 # Alembic database schema migrations
├── scripts/                    # Operational utilities (camera test, enrollment, scanners)
├── src/                        # Core Python application package
│   └── app/
│       ├── api/                # FastAPI routers, dependencies, and schemas
│       ├── application/        # Kiosk scanner runtime orchestration
│       ├── core/               # Configuration, security, JWT, and logging
│       ├── database/           # SQLAlchemy 2.0 ORM sessions and base
│       ├── infrastructure/     # Milvus and PostgreSQL repository adapters
│       ├── models/             # Domain data models and UserRole definitions
│       ├── repositories/       # Abstract and concrete repository implementations
│       ├── scheduler/          # Daily automated EOD finalization job
│       ├── services/           # Business logic (attendance, auth, face enrollment)
│       ├── vision/             # InsightFace AI engine and frame processing
│       └── main.py             # CLI entry point
├── tests/                      # Automated test suite (218 hermetic tests)
├── .env.example                # Sanitized root environment template
├── .gitignore                  # Production Git ignore rules
├── .python-version             # Pinned Python version (3.12)
├── Dockerfile                  # Multi-stage production container image
├── alembic.ini                 # Database migration configuration
├── pyproject.toml              # Dependencies & build configuration
├── uv.lock                     # Deterministic dependency lockfile
├── SECURITY.md                 # Vulnerability reporting & security policy
└── CONTRIBUTING.md             # Developer guidelines & conventional commits
```

---

## Quickstart

### Prerequisites
- Python 3.12 & [`uv`](https://github.com/astral-sh/uv)
- Node.js 20+ & `npm`
- Docker & Docker Compose

### 1. Launch Local Infrastructure
```bash
# Start Milvus vector database and PostgreSQL 17
docker compose -f infra/milvus/docker-compose.yml up -d
docker compose -f infra/milvus/postgre/docker-compose.yml up -d
```

### 2. Configure Environment & Install Dependencies
```bash
# Backend setup
cp .env.example .env
uv sync
uv run alembic upgrade head

# Frontend setup
cd frontend
cp .env.example .env
npm install
cd ..
```

### 3. Run Applications
```bash
# Backend API (runs on http://localhost:8000)
uv run uvicorn app.api.main:app --reload

# Frontend Web Portal (runs on http://localhost:5173)
cd frontend && npm run dev
```

---

## Testing

FaceAttend maintains strict test coverage and verification standards:

```bash
# Run backend pytest suite (218 tests)
uv run pytest

# Run frontend type-check & production build
cd frontend && npm run build
```

---

## Documentation Links

- [System Architecture](docs/architecture.md)
- [API Specification & RBAC Matrix](docs/api.md)
- [Local Development Guide](docs/development.md)
- [Production Deployment Guide](docs/deployment.md)
- [Security Policy](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)
