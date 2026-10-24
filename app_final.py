"""Music Mood API — учебный музыкальный сервис на FastAPI."""

import logging
import os
from collections import Counter
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query, Request

from music_data import TRACKS

load_dotenv()  # Подхватывает локальный .env, если он есть (в Git его не добавляем).

APP_NAME = os.getenv("APP_NAME", "Music Mood API")
APP_VERSION = "1.0.0"

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("music_mood_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск %s версии %s: %s треков", APP_NAME, APP_VERSION, len(TRACKS))
    yield
    logger.info("Остановка %s", APP_NAME)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Поиск треков и создание небольшого плейлиста под настроение.",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логируем адрес запроса и HTTP-статус ответа."""
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/", tags=["Сервис"])
def root():
    return {
        "message": "Сервис работает",
        "service": APP_NAME,
        "description": "Музыкальный каталог и плейлисты под настроение",
        "docs": "/docs",
    }


@app.get("/health", tags=["Сервис"])
def health():
    return {"status": "ok"}


@app.get("/version", tags=["Сервис"])
def version():
    return {"version": APP_VERSION}


@app.get("/info", tags=["Сервис"])
def info():
    """Сохраняем идею /info из исходной учебной версии."""
    return {
        "app_name": os.getenv("APP_NAME", "Music Mood API"),
        "author": os.getenv("APP_AUTHOR", "Никита"),
    }


@app.get("/tracks", tags=["Музыка"])
def list_tracks(
    genre: str | None = Query(default=None, min_length=1, max_length=50),
    mood: str | None = Query(default=None, min_length=1, max_length=50),
    q: str | None = Query(default=None, min_length=1, max_length=100),
):
    """Показать каталог; необязательные фильтры работают совместно."""
    results = TRACKS
    if genre is not None:
        results = [track for track in results if track["genre"] == genre.strip().casefold()]
    if mood is not None:
        results = [track for track in results if track["mood"] == mood.strip().casefold()]
    if q is not None:
        search = q.strip().casefold()
        results = [
            track for track in results
            if search in track["title"].casefold() or search in track["artist"].casefold()
        ]
    logger.info("Каталог: найдено %s треков", len(results))
    return {"count": len(results), "tracks": results}


@app.get("/genres", tags=["Музыка"])
def list_genres():
    """Количество композиций каждого жанра."""
    counts = Counter(track["genre"] for track in TRACKS)
    return {"genres": dict(sorted(counts.items()))}


@app.get("/tracks/{track_id}", tags=["Музыка"])
def get_track(track_id: int = Path(ge=1)):
    for track in TRACKS:
        if track["id"] == track_id:
            return track
    logger.warning("Трек с id=%s не найден", track_id)
    raise HTTPException(status_code=404, detail="Трек не найден")


def get_default_playlist_minutes() -> int:
    """Безопасно читаем настройку из окружения."""
    raw_value = os.getenv("DEFAULT_PLAYLIST_MINUTES", "15")
    try:
        minutes = int(raw_value)
        if 1 <= minutes <= 180:
            return minutes
    except ValueError:
        pass
    logger.warning("Неверное DEFAULT_PLAYLIST_MINUTES=%r, используем 15", raw_value)
    return 15


@app.get("/playlist", tags=["Музыка"])
def make_playlist(
    mood: str = Query(description="calm, upbeat, energetic или focus", min_length=1, max_length=50),
    max_minutes: int | None = Query(default=None, ge=1, le=180),
):
    """Подобрать треки заданного настроения без превышения времени.

    Алгоритм простой: перебрать каталог по порядку и добавить трек,
    если он целиком помещается в оставшееся время.
    """
    mood = mood.strip().casefold()
    available_moods = {track["mood"] for track in TRACKS}
    if mood not in available_moods:
        raise HTTPException(
            status_code=404,
            detail=f"Настроение не найдено. Доступны: {', '.join(sorted(available_moods))}",
        )

    limit = max_minutes if max_minutes is not None else get_default_playlist_minutes()
    max_seconds = limit * 60
    selected = []
    total_seconds = 0

    for track in TRACKS:
        if track["mood"] == mood and total_seconds + track["duration_seconds"] <= max_seconds:
            selected.append(track)
            total_seconds += track["duration_seconds"]

    logger.info("Плейлист %s на %s мин: %s треков", mood, limit, len(selected))
    return {
        "mood": mood,
        "max_minutes": limit,
        "total_seconds": total_seconds,
        "track_count": len(selected),
        "tracks": selected,
    }
