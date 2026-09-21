# FaceAttend API Specification & Integration Guide

The FaceAttend REST API is implemented with **FastAPI**. When running locally, interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 1. Authentication & RBAC Matrix

Authentication uses standard **OAuth2 with Bearer JWT tokens** (HMAC-SHA256).

### Verified Role Definitions
The system implements two distinct system roles defined in `UserRole` (`app.models.user_role`):

| Role | Description |
| :--- | :--- |
| `admin` | Full administrative control: user management, employee registration, department/team setup, manual attendance adjustment, EOD batch finalization. |
| `security` | Kiosk operator: face verification scan execution, read-only employee lookup, attendance viewing. |

### Endpoint Authorization Matrix

| Endpoint | Method | Required Role | Description |
| :--- | :---: | :---: | :--- |
| `/auth/login` | `POST` | Public | Authenticate with username & password; returns JWT access token. |
| `/employees` | `GET` | `admin`, `security` | List employees with pagination and filters. |
| `/employees/{id}` | `GET` | `admin`, `security` | Get employee details by employee ID. |
| `/employees` | `POST` | `admin` | Register a new employee. |
| `/employees/{id}/enroll-face` | `POST` | `admin` | Enroll biometric face embedding samples (Milvus). |
| `/departments` | `GET` | `admin`, `security` | List departments. |
| `/departments` | `POST` | `admin` | Create a new department. |
| `/teams` | `GET` | `admin`, `security` | List teams. |
| `/teams` | `POST` | `admin` | Create a new team. |
| `/attendance` | `GET` | `admin`, `security` | List attendance records with date filters. |
| `/attendance/verify-face` | `POST` | `admin`, `security` | Kiosk endpoint: verify face image against vector database. |
| `/attendance/daily-report` | `GET` | `admin`, `security` | Aggregated attendance report for a specified date. |
| `/attendance/end-of-day` | `POST` | `admin` | Trigger End-of-Day attendance finalization batch job. |
| `/audit-logs` | `GET` | `admin` | Retrieve scanner audit event logs. |
| `/health` | `GET` | Public | Liveness probe (HTTP 200). |
| `/ready` | `GET` | Public | Readiness probe (verifies PostgreSQL and Milvus connectivity). |

---

## 2. Authentication Endpoint

### `POST /auth/login`
Authenticates a user and issues a Bearer JWT token.

**Request Body (Form URL-Encoded or JSON)**:
```json
{
  "username": "admin",
  "password": "YourPasswordHere"
}
```

**Response (`HTTP 200 OK`)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin"
}
```

---

## 3. Biometric Verification (Kiosk Scanning)

### `POST /attendance/verify-face`
Uploads a single camera frame from a kiosk to perform detection, recognition, and check-in/check-out punch.

**Headers**:
- `Authorization: Bearer <access_token>`

**Request (Multipart Form-Data)**:
- `image`: Binary JPEG/PNG image file.
- `scanner_type`: String (`CHECK_IN` or `CHECK_OUT`).

**Response Examples**:

#### Success (`HTTP 200 OK`)
```json
{
  "success": true,
  "status": "ACCESS_GRANTED",
  "employee_id": "EMP001",
  "employee_name": "Vigneshwaran S",
  "attendance_id": "c7a8b9e0-1234-5678-90ab-cdef12345678",
  "similarity": 0.92,
  "message": "Check-in recorded successfully"
}
```

#### No Face Detected (`HTTP 200 OK`)
```json
{
  "success": false,
  "status": "NO_FACE_DETECTED",
  "employee_id": null,
  "message": "No face found in camera frame"
}
```

#### Unrecognized Face (`HTTP 200 OK`)
```json
{
  "success": false,
  "status": "UNRECOGNIZED_FACE",
  "employee_id": null,
  "similarity": 0.42,
  "message": "Face did not match any enrolled employee"
}
```

---

## 4. Attendance Management Endpoints

### `GET /attendance`
Query attendance logs.
- Query parameters: `page`, `page_size`, `date`, `employee_id`, `department_id`.

### `POST /attendance/end-of-day`
Runs the daily attendance finalization algorithm to compute shift hours, mark absent employees, and close the current working date.
- Header: `Authorization: Bearer <admin_access_token>`
- Idempotent: Can be run multiple times safely.
