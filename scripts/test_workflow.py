import requests
import time

BASE_URL = "http://localhost:8000"
USER_ID = "test_user_123"

def print_step(msg):
    print(f"\n==> {msg}")

def test_workflow():
    print_step("Health check")
    resp = requests.get(f"{BASE_URL}/health")
    resp.raise_for_status()
    print("Health OK:", resp.json())
    
    print_step("Login")
    resp = requests.post(f"{BASE_URL}/auth/oauth", json={
        "provider": "test",
        "subject": "test_user_123",
        "email": "test@example.com",
        "name": "Test User"
    })
    resp.raise_for_status()
    user = resp.json()
    print("Login OK:", user)
    user_id = user['id']
    
    print_step("Seeding demo paper")
    resp = requests.post(f"{BASE_URL}/users/{user_id}/demo-paper")
    resp.raise_for_status()
    paper = resp.json()
    paper_id = paper['id']
    print(f"Seeded demo paper ID: {paper_id}")
    
    print_step("Getting system spec")
    resp = requests.get(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/system-spec")
    if resp.status_code == 404:
        print("System spec not found, generating...")
        resp = requests.post(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/system-spec")
        resp.raise_for_status()
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/system-spec")
    resp.raise_for_status()
    print("System spec OK")
    
    print_step("Approving system spec")
    resp = requests.patch(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/system-spec", json={"approve": True})
    resp.raise_for_status()
    print("System spec approved")
    
    print_step("Getting implementation blueprint")
    resp = requests.get(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/implementation-blueprint")
    if resp.status_code == 404:
        print("Blueprint not found, generating...")
        resp = requests.post(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/implementation-blueprint")
        resp.raise_for_status()
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/implementation-blueprint")
    resp.raise_for_status()
    print("Blueprint OK")
    
    print_step("Approving blueprint")
    resp = requests.patch(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/implementation-blueprint", json={"approve": True})
    resp.raise_for_status()
    print("Blueprint approved")
    
    print_step("Generating baseline project")
    resp = requests.post(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/baseline-project")
    resp.raise_for_status()
    print("Baseline project generated OK")
    
    print_step("Running baseline project")
    resp = requests.post(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/baseline-project/run")
    resp.raise_for_status()
    print("Run completed OK")
    
    print_step("Getting reproduction report")
    resp = requests.get(f"{BASE_URL}/users/{user_id}/papers/{paper_id}/reproduction-report")
    resp.raise_for_status()
    print("Reproduction report OK")
    
if __name__ == '__main__':
    test_workflow()
