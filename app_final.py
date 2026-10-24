"""Music Mood API — небольшой музыкальный сервис на FastAPI."""

import logging
import os
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from music_data import TRACKS

load_dotenv()  # Локальные настройки .env не публикуем в Git.

APP_NAME = os.getenv("APP_NAME", "Music Mood API")
APP_VERSION = "1.3.0"
STATIC_DIR = Path(__file__).resolve().parent / "static"

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
    description=(
        "Музыкальный каталог и генератор плейлистов. "
        "**[Открыть визуальный интерфейс](/ui)** · "
        "[Проверить состояние](/health). "
        "Все данные демонстрационные; сервис не воспроизводит аудио."
    ),
    openapi_tags=[
        {"name": "Музыка", "description": "Поиск по каталогу, жанры, настроения и плейлисты."},
        {"name": "Сервис", "description": "Состояние, версия и параметры приложения."},
    ],
    lifespan=lifespan,
)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логируем HTTP-метод, адрес запроса и код ответа."""
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


def normalize_filter(value: str, name: str) -> str:
    """Игнорируем регистр и внешние пробелы, но запрещаем пустые значения."""
    normalized = value.strip().casefold()
    if not normalized:
        raise HTTPException(status_code=422, detail=f"Параметр {name} не может быть пустым")
    return normalized


@app.get("/", tags=["Сервис"])
def root():
    return {
        "message": "Сервис работает",
        "service": APP_NAME,
        "description": "Музыкальный каталог и плейлисты под настроение",
        "docs": "/docs",
        "web_ui": "/ui",
    }


@app.get("/ui", include_in_schema=False)
def web_interface():
    """Визуальная страница для людей; JSON API и Swagger остаются доступны."""
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/health", tags=["Сервис"])
def health():
    return {"status": "ok"}


@app.get("/version", tags=["Сервис"])
def version():
    return {"version": APP_VERSION}


@app.get("/info", tags=["Сервис"])
def info():
    """Сохраняем учебный маршрут и настройку через переменную окружения."""
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
    """Показываем каталог с необязательными совместно работающими фильтрами."""
    results = TRACKS

    if genre is not None:
        genre = normalize_filter(genre, "genre")
        results = [track for track in results if track["genre"] == genre]
    if mood is not None:
        mood = normalize_filter(mood, "mood")
        results = [track for track in results if track["mood"] == mood]
    if q is not None:
        search = normalize_filter(q, "q")
        results = [
            track
            for track in results
            if search in track["title"].casefold() or search in track["artist"].casefold()
        ]

    logger.info("Каталог: найдено %s треков", len(results))
    return {"count": len(results), "tracks": results}


@app.get("/genres", tags=["Музыка"])
def list_genres():
    """Возвращаем жанры и количество треков в каждом из них."""
    counts = Counter(track["genre"] for track in TRACKS)
    return {"genres": dict(sorted(counts.items()))}


@app.get("/moods", tags=["Музыка"])
def list_moods():
    """Подсказываем пользователю допустимые значения параметра mood."""
    counts = Counter(track["mood"] for track in TRACKS)
    return {"moods": dict(sorted(counts.items()))}


@app.get("/tracks/{track_id}", tags=["Музыка"])
def get_track(track_id: int = ApiPath(ge=1)):
    for track in TRACKS:
        if track["id"] == track_id:
            return track
    logger.warning("Трек с id=%s не найден", track_id)
    raise HTTPException(status_code=404, detail="Трек не найден")


def get_default_playlist_minutes() -> int:
    """Безопасно читаем длительность плейлиста из переменной окружения."""
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
    genre: str | None = Query(default=None, min_length=1, max_length=50),
):
    """Подбираем песни по настроению, жанру и ограничению времени.

    Это детерминированный алгоритм: идём по каталогу и добавляем песню,
    если она полностью помещается в оставшееся время.
    """
    mood = normalize_filter(mood, "mood")
    available_moods = {track["mood"] for track in TRACKS}
    if mood not in available_moods:
        logger.warning("Неизвестное настроение: %s", mood)
        raise HTTPException(
            status_code=404,
            detail=f"Настроение не найдено. Доступны: {', '.join(sorted(available_moods))}",
        )

    if genre is not None:
        genre = normalize_filter(genre, "genre")
        available_genres = {track["genre"] for track in TRACKS}
        if genre not in available_genres:
            logger.warning("Неизвестный жанр: %s", genre)
            raise HTTPException(
                status_code=404,
                detail=f"Жанр не найден. Доступны: {', '.join(sorted(available_genres))}",
            )

    limit = max_minutes if max_minutes is not None else get_default_playlist_minutes()
    max_seconds = limit * 60
    matching_tracks = [
        track for track in TRACKS
        if track["mood"] == mood and (genre is None or track["genre"] == genre)
    ]
    selected = []
    total_seconds = 0

    for track in matching_tracks:
        if total_seconds + track["duration_seconds"] <= max_seconds:
            selected.append(track)
            total_seconds += track["duration_seconds"]

    available_seconds = sum(track["duration_seconds"] for track in matching_tracks)
    logger.info(
        "Плейлист: настроение=%s, жанр=%s, лимит=%s мин, найдено=%s, выбрано=%s",
        mood, genre or "любой", limit, len(matching_tracks), len(selected),
    )
    result = {
        "mood": mood,
        "genre": genre,
        "max_minutes": limit,
        "total_seconds": total_seconds,
        "track_count": len(selected),
        "available_count": len(matching_tracks),
        "available_seconds": available_seconds,
        "unused_seconds": max_seconds - total_seconds,
        "tracks": selected,
    }
    if not matching_tracks:
        result["message"] = "По выбранным настроению и жанру в каталоге пока нет треков. Попробуйте другой жанр."
    elif not selected:
        shortest = min(track["duration_seconds"] for track in matching_tracks)
        result["message"] = (
            f"Ни один из {len(matching_tracks)} треков не помещается в {limit} мин. "
            f"Самая короткая композиция длится {shortest // 60}:{shortest % 60:02d}. "
            "Увеличьте длительность."
        )
    elif len(selected) == len(matching_tracks) and total_seconds < max_seconds:
        result["notice"] = (
            f"Все {len(selected)} доступных треков уже включены. "
            "Чтобы собрать более длинный плейлист, выберите другой жанр или «Любой жанр»."
        )
    return result
