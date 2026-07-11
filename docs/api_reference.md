# Aether HTTP API Endpoints Reference

All API requests require Bearer token authorization headers:
`Authorization: Bearer <jwt_access_token>`

---

## 1. Authentication Services

### `POST /v1/auth/login`
* **Request Body**:
  ```json
  { "email": "user@aether.com", "password": "mypassword" }
  ```
* **Response (200 OK)**:
  ```json
  { "access_token": "jwt_string", "refresh_token": "jwt_string" }
  ```

---

## 2. Personal Memory Controls

### `GET /v1/memory`
* **Query Parameters**: `organization_id` (UUID)
* **Response (200 OK)**:
  ```json
  [
    {
      "id": "uuid_string",
      "fact": "User prefers python-based tools",
      "consent_status": "consented",
      "created_at": "2026-07-11T13:00:00Z"
    }
  ]
  ```

### `POST /v1/memory`
* **Request Body**:
  ```json
  {
    "organization_id": "uuid_string",
    "fact": "User is standardizing Compose deployment",
    "consent_status": "consented"
  }
  ```
* **Response (201 Created)**:
  ```json
  { "status": "created", "memory_id": "uuid_string" }
  ```

---

## 3. Administration & Policy Settings

### `GET /v1/admin/policy`
* **Query Parameters**: `organization_id` (UUID)
* **Response (200 OK)**:
  ```json
  {
    "retention_days_notifications": 30,
    "retention_days_audit_logs": 90,
    "break_glass_active": false,
    "break_glass_reason": null
  }
  ```

### `POST /v1/admin/policy/override`
* **Request Body**:
  ```json
  {
    "organization_id": "uuid_string",
    "active": true,
    "reason": "Investigating critical Celery task deadlock"
  }
  ```
* **Response (200 OK)**:
  ```json
  { "status": "updated", "break_glass_active": true }
  ```

---

## 4. Usage Reporting & Analytics

### `GET /v1/analytics/summary`
* **Query Parameters**: `organization_id` (UUID)
* **Response (200 OK)**:
  ```json
  {
    "total_cost": 0.03550,
    "total_events": 142
  }
  ```

### `GET /v1/analytics/export`
* **Query Parameters**: `organization_id` (UUID)
* **Response (200 OK)**:
  * Returns raw CSV file data (`usage_export.csv`) containing headers:
    `id,event_name,category,cost,units,created_at`
