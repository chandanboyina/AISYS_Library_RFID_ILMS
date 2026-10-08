import os

os.environ["DATABASE_URL"] = "sqlite:///./test_aisys.db"

from fastapi.testclient import TestClient
from app.main import app


def auth(client):
    r = client.post("/api/auth/login", data={"username": "admin", "password": "Admin@12345"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_health():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "UP"


def test_book_member_rfid_flow():
    with TestClient(app) as client:
        h = auth(client)
        assert client.post("/api/books", json={"accession_no": "T-001", "title": "Test Book"}, headers=h).status_code in (200, 409)
        assert client.post("/api/members", json={"member_no": "TM-001", "name": "Test Member"}, headers=h).status_code in (200, 409)
        assert client.post("/api/rfid/associate", json={"accession_no": "T-001", "tag_id": "TAG-T-001"}, headers=h).status_code in (200, 409)
        r = client.post("/api/rfid/read", json={"tag_id": "TAG-T-001", "shelf": "S1", "expected_shelf": "S1"}, headers=h)
        assert r.status_code == 200
        assert r.json()["status"] == "FOUND"


def test_circulation():
    with TestClient(app) as client:
        h = auth(client)
        client.post("/api/books", json={"accession_no": "T-002", "title": "Circulation Book"}, headers=h)
        client.post("/api/members", json={"member_no": "TM-002", "name": "Member 2"}, headers=h)
        assert client.post("/api/circulation/checkout", json={"member_no": "TM-002", "accession_no": "T-002", "protocol": "NCIP2"}, headers=h).status_code == 200
        assert client.post("/api/circulation/renew", json={"accession_no": "T-002", "protocol": "SIP2"}, headers=h).status_code == 200
        assert client.post("/api/circulation/checkin", json={"accession_no": "T-002", "protocol": "NCIP2"}, headers=h).status_code == 200


def test_rbac_and_gate():
    with TestClient(app) as client:
        admin = auth(client)
        assert client.post("/api/gate/event", json={"tag_id": "UNKNOWN-TAG", "security_bit": True, "cctv_ref": "mock://cctv/test"}, headers=admin).status_code == 200
        operator_login = client.post("/api/auth/login", data={"username": "operator", "password": "Operator@12345"})
        assert operator_login.status_code == 200
        operator = {"Authorization": "Bearer " + operator_login.json()["access_token"]}
        assert client.post("/api/admin/config", json={"key": "test", "value": "denied"}, headers=operator).status_code == 403


def test_inventory_and_misplaced():
    with TestClient(app) as client:
        h = auth(client)
        client.post("/api/books", json={"accession_no": "T-003", "title": "Inventory Book"}, headers=h)
        client.post("/api/rfid/associate", json={"accession_no": "T-003", "tag_id": "TAG-T-003"}, headers=h)
        r = client.post("/api/rfid/read", json={"tag_id": "TAG-T-003", "shelf": "B-02", "expected_shelf": "A-01"}, headers=h)
        assert r.status_code == 200
        assert r.json()["status"] == "MISPLACED"

def test_ilms_operational_endpoints_and_configurable_fine_limit():
    with TestClient(app) as client:
        h = auth(client)
        client.post('/api/books', json={'accession_no':'T-004','title':'Admin Book'}, headers=h)
        client.post('/api/members', json={'member_no':'TM-004','name':'Fine Member'}, headers=h)
        assert client.get('/api/acquisitions', headers=h).status_code == 200
        assert client.get('/api/serials', headers=h).status_code == 200
        assert client.get('/api/rfid/tags', headers=h).status_code == 200
        assert client.get('/api/notifications', headers=h).status_code == 200
        assert client.get('/api/admin/users', headers=h).status_code == 200
        assert client.get('/api/admin/config', headers=h).status_code == 200
        assert client.post('/api/admin/config', json={'key':'fine_limit','value':'50'}, headers=h).status_code == 200
        assert client.post('/api/members/TM-004/fine?amount=51', headers=h).status_code == 200
        blocked = client.post('/api/circulation/checkout', json={'member_no':'TM-004','accession_no':'T-004','protocol':'NCIP2'}, headers=h)
        assert blocked.status_code == 409
        assert '50.00' in blocked.text
        assert client.get('/api/migration/runs/999999', headers=h).status_code == 404
