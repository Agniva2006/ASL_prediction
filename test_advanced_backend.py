import os
import numpy as np
from fastapi.testclient import TestClient

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from backend.app import app

client = TestClient(app)

def test_advanced_api():
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

    # Upgrade user to developer plan to authorize premium model execution
    from backend.auth import load_users, save_users
    users = load_users()
    if username in users:
        users[username]["plan"] = "developer"
        save_users(users)
    print("User Upgraded to Developer Plan in test database.")

    # 3. Log in to retrieve JWT access token
    res_login = client.post("/auth/login", json={
        "username": username,
        "password": "test_password_123"
    })
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("User Login Successful! JWT obtained.")

    # 4. Static MLP Prediction test
    dummy_kp = np.random.uniform(-0.5, 0.5, size=63).tolist()
    res_mlp = client.post("/predict", json={"keypoints": dummy_kp}, headers=headers)
    assert res_mlp.status_code == 200, f"MLP predict failed: {res_mlp.text}"
    print("POST /predict response:", res_mlp.json())
    
    # 5. Spatial-Temporal Transformer Sequence Prediction test
    dummy_seq = [np.random.uniform(-0.5, 0.5, size=63).tolist() for _ in range(16)]
    res_trans = client.post("/predict_sequence", json={"sequence": dummy_seq}, headers=headers)
    assert res_trans.status_code == 200, f"Transformer sequence predict failed: {res_trans.text}"
    print("POST /predict_sequence response:", res_trans.json())
    
    # 6. Sign Diffusion Synthesizer test
    res_diff = client.post("/synthesize_sign", json={"prompt": "hello"}, headers=headers)
    assert res_diff.status_code == 200, f"Diffusion synthesize failed: {res_diff.text}"
    data_diff = res_diff.json()
    print(f"POST /synthesize_sign response (prompt={data_diff['prompt']}, model={data_diff['model']}): {data_diff['num_frames']} frames synthesized!")
    
    print("\nSUCCESS: All AI Engine Endpoints (MLP, Transformer, Sign Diffusion) passed unit testing!")

if __name__ == "__main__":
    test_advanced_api()

