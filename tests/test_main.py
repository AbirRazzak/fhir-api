from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_resources_loaded_on_startup():
    with TestClient(app):  # context manager runs the lifespan
        patient = app.state.resources["Patient"]["noah-wyle"]
    assert patient.name[0].family == "Wyle"


def test_read_resource():
    with TestClient(app) as c:
        r = c.get("/Patient/noah-wyle")
        assert r.status_code == 200
        assert r.json() == {
            "resourceType": "Patient",
            "id": "noah-wyle",
            "name": [{"use": "official", "family": "Wyle", "given": ["Noah"]}],
            "gender": "male",
            "birthDate": "1971-06-04",
            "active": True,
        }
        assert c.get("/Patient/nobody").status_code == 404
        assert c.get("/Spaceship/noah-wyle").status_code == 404
