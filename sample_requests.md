# Sample API Requests (CURL)

This guide provides command-line examples using `curl` to interact with the Offline-First PHC Management System API.

---

## 1. Environment Setup

To follow along easily, set a shell variable for the API base URL:
```bash
export API_URL="http://localhost:8000/api/v1"
```

---

## 2. Authentication

### Step A: Register a User
```bash
curl -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_karan",
    "password": "securepassword99",
    "full_name": "Dr. Karan Singh",
    "role": "DOCTOR"
  }'
```

### Step B: Authenticate (Login) & Obtain JWT Token
```bash
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dr_karan&password=securepassword99"
```
*Take note of the `access_token` returned.* Set it as a variable for subsequent requests:
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step C: Retrieve Current Doctor Profile
```bash
curl -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. Patient Management

### Create a Patient (with Client-Generated UUID)
```bash
curl -X POST "$API_URL/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "7662c140-5a3d-463d-88ff-c967406a090b",
    "name": "Sonia Gandhi",
    "age": 55,
    "gender": "Female",
    "phone": "9998887776",
    "address": "Green Colony, Lane 3"
  }'
```

### Search Patients by Name
```bash
curl -X GET "$API_URL/patients/?search=Sonia" \
  -H "Authorization: Bearer $TOKEN"
```

### Read Patient Details
```bash
curl -X GET "$API_URL/patients/7662c140-5a3d-463d-88ff-c967406a090b" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Patient Age and Address
```bash
curl -X PUT "$API_URL/patients/7662c140-5a3d-463d-88ff-c967406a090b" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 56,
    "address": "Green Colony, Villa 12"
  }'
```

---

## 4. Consultations & Prescriptions

### Create a Consultation
```bash
curl -X POST "$API_URL/consultations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "e81e360f-b258-4da8-9689-ff4a2fa321f5",
    "patient_id": "7662c140-5a3d-463d-88ff-c967406a090b",
    "symptoms": "Dry cough, sore throat, fatigue",
    "diagnosis": "Pharyngitis",
    "doctor_notes": "Advised throat lozenges and warm water."
  }'
```

### Create a Prescription for the Consultation
```bash
curl -X POST "$API_URL/prescriptions/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "a90df1a0-d790-482a-89a3-5c8e4429e71b",
    "consultation_id": "e81e360f-b258-4da8-9689-ff4a2fa321f5",
    "medicine_name": "Amoxicillin 500mg",
    "dosage": "1 capsule twice daily",
    "duration": "5 days"
  }'
```

---

## 5. Vaccination Record

### Log a Patient Vaccination
```bash
curl -X POST "$API_URL/vaccinations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "fb21cb17-b715-46f9-aa2a-281b37996c56",
    "patient_id": "7662c140-5a3d-463d-88ff-c967406a090b",
    "vaccine_name": "Tetanus Toxoid Booster",
    "vaccination_date": "2026-06-19",
    "status": "COMPLETED"
  }'
```

---

## 6. Sync Operations

### Check Cloud Connection
```bash
curl -X GET "$API_URL/sync/status" \
  -H "Authorization: Bearer $TOKEN"
```

### Trigger Synchronization
```bash
curl -X POST "$API_URL/sync/trigger" \
  -H "Authorization: Bearer $TOKEN"
```

### View Synchronization Queue Logs
```bash
curl -X GET "$API_URL/sync/queue" \
  -H "Authorization: Bearer $TOKEN"
```
