"""Автоматические проверки API: python -m pytest -v."""

from fastapi.testclient import TestClient

from app_final import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "1.0.0"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Сервис работает"


def test_tracks_catalog():
    response = client.get("/tracks")
    assert response.status_code == 200
    assert response.json()["count"] == 12


def test_filter_tracks_by_genre_and_mood():
    response = client.get("/tracks?genre=pop&mood=calm")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert all(track["genre"] == "pop" and track["mood"] == "calm" for track in body["tracks"])


def test_search_by_artist_case_insensitive():
    response = client.get("/tracks?q=QUEEN")
    assert response.status_code == 200
    assert response.json()["tracks"][0]["artist"] == "Queen"


def test_get_track_by_id():
    response = client.get("/tracks/2")
    assert response.status_code == 200
    assert response.json()["title"] == "Numb"


def test_unknown_track_returns_404():
    response = client.get("/tracks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Трек не найден"


def test_playlist_respects_duration_limit():
    response = client.get("/playlist?mood=calm&max_minutes=10")
    assert response.status_code == 200
    body = response.json()
    assert body["track_count"] >= 1
    assert body["total_seconds"] <= 600
    assert all(track["mood"] == "calm" for track in body["tracks"])
    assert sum(track["duration_seconds"] for track in body["tracks"]) == body["total_seconds"]


def test_unknown_mood_returns_404():
    response = client.get("/playlist?mood=unknown")
    assert response.status_code == 404


def test_invalid_duration_returns_422():
    response = client.get("/playlist?mood=focus&max_minutes=0")
    assert response.status_code == 422


def test_playlist_reads_environment_variable(monkeypatch):
    monkeypatch.setenv("DEFAULT_PLAYLIST_MINUTES", "7")
    response = client.get("/playlist?mood=focus")
    assert response.status_code == 200
    assert response.json()["max_minutes"] == 7


def test_invalid_environment_variable_uses_safe_default(monkeypatch):
    monkeypatch.setenv("DEFAULT_PLAYLIST_MINUTES", "oops")
    response = client.get("/playlist?mood=focus")
    assert response.status_code == 200
    assert response.json()["max_minutes"] == 15


def test_genres():
    response = client.get("/genres")
    assert response.status_code == 200
    assert response.json()["genres"]["pop"] == 4


def test_info_uses_environment(monkeypatch):
    monkeypatch.setenv("APP_AUTHOR", "Test Author")
    response = client.get("/info")
    assert response.status_code == 200
    assert response.json()["author"] == "Test Author"
