# ==============================================================================
# Multi-stage production Dockerfile for Face Recognition Attendance System
# ==============================================================================
#
# Deployment Note:
#   Database migrations MUST be executed as an explicit deployment step prior
#   to starting the application service:
#
#   1. Run Database Migrations:
#      docker run --rm <image> alembic upgrade head
#
#   2. Start API Service Container:
#      docker run -d -p 8000:8000 <image>
#
# Secret Management Note:
#   Do NOT mount or copy .env files into containers or production hosts.
#   In production, inject environment variables (DATABASE_URL, JWT_SECRET,
#   MILVUS_URI, CORS_ORIGINS) securely via orchestrator secrets:
#   - Kubernetes Secrets / ConfigMaps
#   - AWS ECS Task Definition (Secrets Manager / SSM Parameter Store)
#   - HashiCorp Vault / Cloud Secret Managers
# ==============================================================================

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

# Create dummy package file structure to allow package installation
RUN mkdir -p src/app && touch src/app/__init__.py src/app/main.py

RUN pip install --no-cache-dir --user .

# Remove dummy build artifacts so site-packages does not shadow real source code
RUN rm -rf /root/.local/lib/python*/site-packages/app* /root/.local/lib/python*/site-packages/face_recognition*

# Production runner stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime dependencies for OpenCV and InsightFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -s /bin/bash appuser

# Copy installed Python packages to appuser home
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application source code, Alembic config, and migrations
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/

# Set ownership of the working directory
RUN chown -R appuser:appuser /app

# Configure environment
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run API server with signal handling for graceful shutdown
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
