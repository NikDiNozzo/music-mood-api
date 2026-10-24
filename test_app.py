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
    assert response.json() == {"version": "1.2.0"}


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


def test_moods():
    response = client.get("/moods")
    assert response.status_code == 200
    assert response.json()["moods"] == {
        "calm": 3, "energetic": 3, "focus": 2, "upbeat": 4
    }


def test_filters_ignore_case_and_surrounding_spaces():
    response = client.get("/tracks", params={"genre": " POP ", "mood": " Calm "})
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_playlist_filters_by_genre():
    response = client.get("/playlist", params={"mood": " CALM ", "genre": " pop ", "max_minutes": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["mood"] == "calm"
    assert body["genre"] == "pop"
    assert body["track_count"] == 2
    assert all(track["genre"] == "pop" for track in body["tracks"])
    assert body["total_seconds"] <= 600


def test_unknown_playlist_genre_returns_404():
    response = client.get("/playlist?mood=calm&genre=metal")
    assert response.status_code == 404
    assert "Жанр не найден" in response.json()["detail"]


def test_whitespace_only_search_returns_422():
    response = client.get("/tracks", params={"q": "   "})
    assert response.status_code == 422


def test_playlist_with_no_matching_tracks_explains_result():
    response = client.get("/playlist?mood=calm&max_minutes=1")
    assert response.status_code == 200
    assert response.json()["track_count"] == 0
    assert "message" in response.json()


def test_catalog_has_unique_ids_and_positive_durations():
    from music_data import TRACKS

    ids = [track["id"] for track in TRACKS]
    assert len(ids) == len(set(ids))
    assert all(track["duration_seconds"] > 0 for track in TRACKS)
    assert all(track["title"] and track["artist"] for track in TRACKS)


def test_visual_ui_serves_html():
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Music Mood" in response.text
    assert 'id="track-grid"' in response.text


def test_static_assets_are_available():
    for asset, content_type in [
        ("/static/styles.css", "text/css"),
        ("/static/app.js", "javascript"),
    ]:
        response = client.get(asset)
        assert response.status_code == 200
        assert content_type in response.headers["content-type"]


def test_root_points_to_visual_interface():
    assert client.get("/").json()["web_ui"] == "/ui"


def test_docs_still_available():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
