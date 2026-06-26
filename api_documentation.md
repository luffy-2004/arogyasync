# API Documentation - Offline-First PHC Management System

This document outlines the API endpoints, authentication flow, and synchronization hooks for the Offline-First PHC Management System.

---

## Base Configuration

* **API Base URL**: `http://localhost:8000/api/v1`
* **Content-Type**: `application/json`
* **Authentication Scheme**: OAuth2 Bearer Token (JWT)

---

## 1. Authentication Module

### Register a User/Doctor
* **Endpoint**: `POST /auth/register`
* **Auth Required**: No (Public for initial clinic setups)
* **Request Body**:
  ```json
  {
    "username": "dr_amit",
    "password": "securepassword123",
    "full_name": "Dr. Amit Verma",
    "role": "DOCTOR"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "username": "dr_amit",
    "full_name": "Dr. Amit Verma",
    "role": "DOCTOR",
    "id": "a90df1a0-d790-482a-89a3-5c8e4429e71b",
    "created_at": "2026-06-19T10:30:00Z",
    "updated_at": "2026-06-19T10:30:00Z"
  }
  ```

### User Login (Obtain Token)
* **Endpoint**: `POST /auth/login`
* **Auth Required**: No
* **Request Body**: Form Data (`application/x-www-form-urlencoded`)
  * `username`: `dr_amit`
  * `password`: `securepassword123`
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

### Get Current User Profile
* **Endpoint**: `GET /auth/me`
* **Headers**: `Authorization: Bearer <access_token>`
* **Response (200 OK)**:
  ```json
  {
    "username": "dr_amit",
    "full_name": "Dr. Amit Verma",
    "role": "DOCTOR",
    "id": "a90df1a0-d790-482a-89a3-5c8e4429e71b",
    "created_at": "2026-06-19T10:30:00Z",
    "updated_at": "2026-06-19T10:30:00Z"
  }
  ```

---

## 2. Patient Management Module

All endpoints below require a valid `Authorization: Bearer <access_token>` header.

### Create Patient
* **Endpoint**: `POST /patients/`
* **Description**: Create a new patient. The client can optionally supply a UUID. This is critical for offline client nodes to ensure unique identifier generation before synchronisation.
* **Request Body**:
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Rajesh Kumar",
    "age": 45,
    "gender": "Male",
    "phone": "9876543210",
    "address": "Village 2, block A"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Rajesh Kumar",
    "age": 45,
    "gender": "Male",
    "phone": "9876543210",
    "address": "Village 2, block A",
    "created_at": "2026-06-19T10:32:10Z",
    "updated_at": "2026-06-19T10:32:10Z"
  }
  ```

### List Patients (with optional Name Search & Pagination)
* **Endpoint**: `GET /patients/?skip=0&limit=100&search=Rajesh`
* **Response (200 OK)**:
  ```json
  {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Rajesh Kumar",
        "age": 45,
        "gender": "Male",
        "phone": "9876543210",
        "address": "Village 2, block A",
        "created_at": "2026-06-19T10:32:10Z",
        "updated_at": "2026-06-19T10:32:10Z"
      }
    ],
    "total": 1
  }
  ```

### Update Patient
* **Endpoint**: `PUT /patients/{patient_id}`
* **Request Body**:
  ```json
  {
    "age": 46,
    "phone": "9876543211"
  }
  ```
* **Response (200 OK)**: (Returns full updated record)

### Delete Patient
* **Endpoint**: `DELETE /patients/{patient_id}`
* **Response (200 OK)**: (Returns deleted record details)

---

## 3. Consultation, Prescription & Vaccination Modules

### Create Consultation
* **Endpoint**: `POST /consultations/`
* **Request Body**:
  ```json
  {
    "id": "110e8400-e29b-41d4-a716-446655440111",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "symptoms": "Fever, Body ache",
    "diagnosis": "Mild influenza",
    "doctor_notes": "Prescribed rest and hydration."
  }
  ```

### Create Prescription
* **Endpoint**: `POST /prescriptions/`
* **Request Body**:
  ```json
  {
    "id": "220e8400-e29b-41d4-a716-446655440222",
    "consultation_id": "110e8400-e29b-41d4-a716-446655440111",
    "medicine_name": "Paracetamol 650mg",
    "dosage": "1 tablet thrice a day",
    "duration": "3 days"
  }
  ```

### Create Vaccination Record
* **Endpoint**: `POST /vaccinations/`
* **Request Body**:
  ```json
  {
    "id": "330e8400-e29b-41d4-a716-446655440333",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "vaccine_name": "Covaxin Booster",
    "vaccination_date": "2026-06-19",
    "status": "COMPLETED"
  }
  ```

---

## 4. Synchronization Engine

### Trigger Sync
* **Endpoint**: `POST /sync/trigger`
* **Description**: Pushes all pending SQLite changes to central PostgreSQL and performs LWW conflict checks.
* **Response (200 OK)**:
  ```json
  {
    "processed": 4,
    "success": 4,
    "failed": 0,
    "ignored_conflict": 0,
    "converged": 0
  }
  ```

### Check Sync Engine Status
* **Endpoint**: `GET /sync/status`
* **Response (200 OK)**:
  ```json
  {
    "cloud_connected": true
  }
  ```

### Read Sync Queue Log
* **Endpoint**: `GET /sync/queue?skip=0&limit=10`
* **Response (200 OK)**:
  ```json
  [
    {
      "entity_type": "patient",
      "entity_id": "550e8400-e29b-41d4-a716-446655440000",
      "operation_type": "CREATE",
      "sync_status": "SYNCED",
      "error_message": null,
      "id": "990df1a0-d790-482a-89a3-5c8e4429e99a",
      "timestamp": "2026-06-19T10:32:10Z",
      "created_at": "2026-06-19T10:32:10Z",
      "updated_at": "2026-06-19T10:32:10Z"
    }
  ]
  ```
