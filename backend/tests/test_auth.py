"""Auth tests: check_password, the login contract, and the 401 gates."""

import main
import telegram


# --- check_password ---


def test_check_password_accepts_the_correct_password():
    assert main.check_password("test-password") is True


def test_check_password_rejects_a_wrong_password():
    assert main.check_password("wrong-password") is False


def test_check_password_returns_false_for_invalid_hash(monkeypatch):
    # A malformed PW_HASH must be caught (ValueError), not crash the route.
    monkeypatch.setattr(main, "PW_HASH", "not-a-bcrypt-hash")
    assert main.check_password("test-password") is False


# --- POST /api/auth ---


def test_login_wrong_password_returns_200_with_success_false(client):
    resp = client.post("/api/auth", json={"pw": "nope"})
    assert resp.status_code == 200
    assert resp.json()["success"] is False


def test_login_correct_password_sets_session_cookie(client, monkeypatch):
    async def fake_list_videos(limit=50):
        return []

    monkeypatch.setattr(telegram, "list_videos", fake_list_videos)

    resp = client.post("/api/auth", json={"pw": "test-password"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # The cookie must round-trip: a data route now succeeds on the same client.
    assert client.get("/api/videos").status_code == 200


def test_login_missing_pw_field_returns_422(client):
    assert client.post("/api/auth", json={}).status_code == 422


# --- unauthenticated gates (one per route: each can regress independently) ---


def test_unauthenticated_videos_returns_401(client):
    assert client.get("/api/videos").status_code == 401


def test_unauthenticated_stream_returns_401(client):
    assert client.get("/stream/1").status_code == 401


def test_unauthenticated_thumb_returns_401(client):
    assert client.get("/thumb/1").status_code == 401
