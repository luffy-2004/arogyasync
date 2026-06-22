def test_user_registration(client):
    """Test user registration endpoint."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "doctor_test",
            "password": "testpassword123",
            "full_name": "Test Doctor",
            "role": "DOCTOR"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "doctor_test"
    assert data["full_name"] == "Test Doctor"
    assert data["role"] == "DOCTOR"
    assert "id" in data

def test_user_registration_duplicate(client):
    """Test user registration with existing username throws error."""
    payload = {
        "username": "doctor_test",
        "password": "testpassword123",
        "full_name": "Test Doctor",
        "role": "DOCTOR"
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_success(client):
    """Test successful user login and token generation."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "doctor_test",
            "password": "testpassword123",
            "full_name": "Test Doctor",
            "role": "DOCTOR"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "doctor_test", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data

def test_login_invalid_password(client):
    """Test login with incorrect password fails."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={"username": "doctor_test", "password": "testpassword123"}
    )
    
    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "doctor_test", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"

def test_get_current_user_authenticated(client):
    """Test retrieving authenticated user profile using token."""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={"username": "doctor_test", "password": "testpassword123", "full_name": "Test Doctor"}
    )
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "doctor_test", "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]
    
    # Get profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "doctor_test"
    assert data["full_name"] == "Test Doctor"

def test_get_current_user_unauthorized(client):
    """Test retrieving profile without valid token fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
