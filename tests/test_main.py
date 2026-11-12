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


def test_patients_for_condition():
    with TestClient(app) as c:
        r = c.get("/condition_patients/38341003")  # Hypertensive disorder
        assert r.status_code == 200
        body = r.json()
        assert body["condition_code"] == "38341003"
        pairs = {(m["condition"]["id"], m["patient"]["id"]) for m in body["matches"]}
        assert pairs == {
            ("cond-nw-001", "noah-wyle"),
            ("cond-kl-002", "katherine-lanasa"),
            ("cond-ah-001", "ayesha-harris"),
        }

        r = c.get("/condition_patients/does-not-exist")
        assert r.status_code == 200
        assert r.json() == {"condition_code": "does-not-exist", "matches": []}
