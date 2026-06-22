import uuid

def test_patient_crud_endpoints(client):
    """Test full CRUD cycle for patients with auth token."""
    # 1. Register and login to obtain token
    client.post(
        "/api/v1/auth/register",
        json={"username": "dr_test", "password": "password123"}
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "dr_test", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. CREATE Patient
    patient_id = str(uuid.uuid4())
    create_response = client.post(
        "/api/v1/patients/",
        headers=headers,
        json={
            "id": patient_id,
            "name": "Aarav Sharma",
            "age": 42,
            "gender": "Male",
            "phone": "9876543210",
            "address": "Delhi PHC Division"
        }
    )
    assert create_response.status_code == 201
    patient_data = create_response.json()
    assert patient_data["id"] == patient_id
    assert patient_data["name"] == "Aarav Sharma"

    # 3. READ Patient by ID
    read_response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=headers
    )
    assert read_response.status_code == 200
    assert read_response.json()["name"] == "Aarav Sharma"

    # 4. UPDATE Patient
    update_response = client.put(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
        json={"name": "Aarav K. Sharma", "age": 43}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Aarav K. Sharma"
    assert update_response.json()["age"] == 43

    # 5. SEARCH Patients
    search_response = client.get(
        "/api/v1/patients/?search=Aarav",
        headers=headers
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert len(search_data["items"]) == 1
    assert search_data["items"][0]["name"] == "Aarav K. Sharma"

    # 6. DELETE Patient
    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=headers
    )
    assert delete_response.status_code == 200
    
    # Confirm deletion
    get_del_response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=headers
    )
    assert get_del_response.status_code == 404

def test_patient_endpoints_unauthorized(client):
    """Verify that requesting patients CRUD without token returns 401."""
    response = client.get("/api/v1/patients/")
    assert response.status_code == 401
