import pytest
from fastapi.testclient import TestClient

from problox import web


@pytest.fixture(autouse=True)
def _clean_sessions():
    web._sessions.clear()
    yield
    web._sessions.clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(web, "SESSIONS_DIR", tmp_path / "sessions")
    return TestClient(web.app)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_root_is_not_a_bare_404(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "ProbloxDev API"


def test_status_creates_session_cookie(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    assert web.COOKIE_NAME in res.cookies
    body = res.json()
    assert body["run"]["status"] == "idle"
    assert body["config"]["roblox_connected"] is False


def test_me_before_login_is_not_connected(client):
    res = client.get("/api/me")
    assert res.status_code == 200
    assert res.json()["connected"] is False


def test_login_without_oauth_configured_is_503(client, monkeypatch):
    # Config est un dataclass frozen: on remplace l'objet entier plutôt que
    # muter un champ.
    from dataclasses import replace

    monkeypatch.setattr(web, "CONFIG", replace(web.CONFIG, roblox_oauth_client_id=None))
    res = client.get("/api/auth/roblox/login", follow_redirects=False)
    assert res.status_code == 503


def test_run_rejects_empty_theme(client):
    res = client.post("/api/run", json={"theme": "   "})
    assert res.status_code == 400


def test_run_dry_run_end_to_end(client, monkeypatch):
    """Sans rojo/toolchain installée (cas CI), le run se termine quand même
    proprement: design généré, puis arrêt propre avec RojoNotFoundError."""
    res = client.post("/api/run", json={"theme": "obby test", "max_iterations": 1})
    assert res.status_code == 200
    assert res.json() == {"started": True}

    import time as _time

    for _ in range(50):
        status = client.get("/api/status").json()
        if status["run"]["status"] != "running":
            break
        _time.sleep(0.1)

    assert status["run"]["status"] == "done"
    logs = client.get("/api/logs?offset=0").json()
    assert any("Design:" in line for line in logs["lines"])


def test_run_cooldown_returns_429(client):
    first = client.post("/api/run", json={"theme": "a"})
    assert first.status_code == 200

    import time as _time

    for _ in range(50):
        status = client.get("/api/status").json()
        if status["run"]["status"] != "running":
            break
        _time.sleep(0.1)

    second = client.post("/api/run", json={"theme": "b"})
    assert second.status_code == 429
    assert "Retry-After" in second.headers


def test_select_experience_requires_connection(client):
    res = client.post(
        "/api/experiences/select", json={"universe_id": "1", "place_id": "2"}
    )
    assert res.status_code == 401


def test_list_experience_places_requires_connection(client):
    res = client.get("/api/experiences/123/places")
    assert res.status_code == 401


def test_list_experience_places_returns_places_for_connected_session(client, monkeypatch):
    from problox import roblox_oauth

    session = web._get_or_create_session(None, web.Response())
    session.tokens = roblox_oauth.TokenSet(access_token="fake", refresh_token=None, expires_at=9999999999)

    monkeypatch.setattr(web, "_oauth_app", lambda: roblox_oauth.OAuthApp("id", "secret", "http://cb"))
    monkeypatch.setattr(roblox_oauth, "ensure_fresh", lambda app, tokens: tokens)
    monkeypatch.setattr(
        web.roblox_cloud,
        "list_universe_places",
        lambda token, universe_id: [{"id": "42", "displayName": "Place principale"}],
    )

    signed = web._serializer.dumps(session.session_id)
    client.cookies.set(web.COOKIE_NAME, signed)
    res = client.get("/api/experiences/123/places")
    assert res.status_code == 200
    assert res.json() == {"places": [{"id": "42", "displayName": "Place principale"}]}
