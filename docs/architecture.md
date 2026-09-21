# FaceAttend System Architecture

## 1. High-Level Architecture Overview

FaceAttend is an enterprise-grade biometric attendance and workforce management system. It combines high-throughput computer vision face analysis with vector similarity search and a relational database for audit logging and time-tracking.

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Tier                            │
│  ┌──────────────────────────────┐  ┌─────────────────────┐  │
│  │   React / Vite Web Portal    │  │ Physical Edge Kiosk │  │
│  │   (MUI, Three.js, Camera)    │  │ (OpenCV / Python)   │  │
│  └──────────────┬───────────────┘  └──────────┬──────────┘  │
└─────────────────┼─────────────────────────────┼─────────────┘
                  │ HTTPS / JSON & Multipart    │
                  ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Tier (FastAPI)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ REST API Routers:                                     │  │
│  │   /auth, /employees, /attendance, /departments, etc.  │  │
│  └──────────────┬─────────────────────────┬──────────────┘  │
│                 │                         │                 │
│  ┌──────────────▼─────────────┐  ┌────────▼──────────────┐  │
│  │   InsightFace AI Engine    │  │ Domain Service Layer  │  │
│  │ (Detection & 512d Vectors) │  │ (Attendance, Auth)    │  │
│  └──────────────┬─────────────┘  └────────┬──────────────┘  │
└─────────────────┼─────────────────────────┼─────────────────┘
                  │ Vector Similarity       │ Relational ORM
                  ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Tier                              │
│  ┌──────────────────────────────┐  ┌─────────────────────┐  │
│  │      Milvus Vector DB        │  │     PostgreSQL 17   │  │
│  │  (face_embeddings_v2, COSINE)│  │ (Relational Data)   │  │
│  └──────────────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Processing Pipeline

Biometric attendance verification follows a deterministic 5-stage pipeline:

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────────────┐
│ 1. Face      │ ──> │ 2. Quality         │ ──> │ 3. Client-Side       │
│ Detection    │     │ Validation         │     │ Stability Check      │
│ (SCRFD / 320)│     │ (Confidence/Blur)  │     │ (Consecutive Frames) │
└──────────────┘     └────────────────────┘     └──────────────────────┘
                                                           │
                                                           ▼
┌──────────────────────┐                        ┌──────────────────────┐
│ 5. Attendance        │ <───────────────────── │ 4. Vector Similarity │
│ Decision & Audit Log │                        │ Recognition          │
│ (PostgreSQL record)  │                        │ (Milvus Cosine > 0.6)│
└──────────────────────┘                        └──────────────────────┘
```

### Stage 1: Face Detection
- Detects bounding boxes and facial landmarks using InsightFace (`buffalo_l` model, SCRFD detector at 320x320 resolution).
- Multiple faces in frame result in rejection (`MULTIPLE_FACES_DETECTED`) to prevent identity ambiguity.

### Stage 2: Quality Validation
- Validates detection confidence (threshold $\ge 0.60$).
- Validates bounding box dimensions to ensure face scale is sufficient for embedding extraction.
- Validates image sharpness to reject motion blur or occluded captures.

### Stage 3: Client-Side Stability Check
- The physical scanner/kiosk UI implements temporal stabilization across consecutive video frames.
- Requires $N$ consecutive matching frames (default: 5 frames) to confirm positive visual lock before submitting verification requests.

### Stage 4: Vector Similarity Recognition
- Extracts a 512-dimensional normalized embedding vector from the aligned face crop using InsightFace ArcFace (`buffalo_l`).
- Queries Milvus vector database collection (`face_embeddings_v2`) using `COSINE` metric.
- Matches are accepted if similarity score exceeds `FACE_SIMILARITY_THRESHOLD` (default: 0.60).

### Stage 5: Attendance Decision & Audit Logging
- **Check-In**: Verifies active employee status, creates today's attendance record with `status='in_progress'`, and logs `face_scan` event.
- **Check-Out**: Finds existing check-in record, updates check-out timestamp, calculates working hours, updates status (`present`, `half_day`), and logs event.
- Every scan attempt (success or failure) is logged to `scanner_audit_logs` for compliance.

---

## 3. Storage Architecture

### PostgreSQL 17 (Relational Database)
Managed via **SQLAlchemy 2.0** ORM and **Alembic** migrations:
- `users`: Authentication credentials (bcrypt password hashes) and roles (`admin`, `security`).
- `employees`: Core workforce records (`employee_id`, `name`, `email`, department, team, status).
- `departments` & `teams`: Organizational structure.
- `attendance`: Daily punch records (`check_in`, `check_out`, `working_hours`, `status`).
- `scanner_audit_logs`: Detailed kiosk telemetry (`scanner_type`, `event_type`, `similarity`, `status`).

### Milvus 2.4+ / 3.0 (Vector Database)
- **Collection**: `face_embeddings_v2`
- **Fields**:
  - `id`: Auto-generated vector entity ID.
  - `employee_id`: String identifier mapping vector to PostgreSQL `employees.employee_id`.
  - `embedding`: Float vector of dimension 512.
- **Index**: `HNSW` or `IVF_FLAT` with `COSINE` metric for sub-millisecond retrieval across tens of thousands of enrolled employees.

---

## 4. End-of-Day (EOD) Finalization Scheduler

The system includes an automated background scheduler (`APScheduler`) configured to run daily (default: 22:00):
1. Identifies all employees with active status.
2. Evaluates attendance records for the day:
   - Completed shifts $\ge 8$ hours marked as `present`.
   - Shifts between 4 and 8 hours marked as `half_day`.
   - Check-ins without a check-out marked as `incomplete`.
   - Employees with no check-in marked as `absent`.
3. The process is fully idempotent and safe to run multiple times without duplicating or overwriting valid punches.
