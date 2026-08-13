import os
import numpy as np
from fastapi.testclient import TestClient

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from backend.app import app

client = TestClient(app)

def test_api():
    # 1. Health check
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root failed: {res_root.text}"
    print("GET / response:", res_root.json())
    
    # 2. Register a temporary test user
    import secrets
    username = f"test_user_{secrets.token_hex(4)}"
    reg_body = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "role": "student",
        "password": "test_password_123"
    }
    res_reg = client.post("/auth/register", json=reg_body)
    assert res_reg.status_code == 200, f"Register failed: {res_reg.text}"
    print("User Registration Successful!")

    # 3. Log in to retrieve JWT access token
    res_login = client.post("/auth/login", json={
        "username": username,
        "password": "test_password_123"
    })
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("User Login Successful! JWT obtained.")

    # 4. Prediction test with dummy 63 keypoints (authenticated)
    dummy_kp = np.random.uniform(-0.5, 0.5, size=63).tolist()
    res_pred = client.post("/predict", json={"keypoints": dummy_kp}, headers=headers)
    assert res_pred.status_code == 200, f"Predict failed: {res_pred.text}"
    
    data = res_pred.json()
    print("POST /predict response:", data)
    assert "prediction" in data
    assert "confidence" in data
    assert "top_3" in data
    assert len(data["top_3"]) == 3
    print("SUCCESS: FastAPI backend passed all endpoint unit tests!")

if __name__ == "__main__":
    test_api()

