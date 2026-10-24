"use strict";

const $ = (id) => document.getElementById(id);
const MOOD_LABELS = {calm: "Спокойное", upbeat: "Позитивное", energetic: "Энергичное", focus: "Для концентрации"};
const GENRE_LABELS = {rock: "Рок", pop: "Поп", electronic: "Электроника", soundtrack: "Саундтрек", classical: "Классика"};
const NOTE = ["♫", "♪", "✦", "♬", "◈"];
const STORAGE_KEY = "music-mood-last-playlist-v1";
const PAGE_SIZE = 16;
let catalogTracks = [];
let visibleTracks = PAGE_SIZE;
let catalogRequest = 0;
let savedPlaylist = null;
let lastFocusedElement = null;

function formatDuration(seconds) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

async function getJSON(path) {
  const response = await fetch(path);
  if (!response.ok) {
    let message = `Ошибка запроса (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch (_) { /* Сервер не вернул JSON. */ }
    throw new Error(typeof message === "string" ? message : "Некорректный запрос");
  }
  return response.json();
}

function textElement(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = content;
  return element;
}

function populateSelect(select, counts, labels, initialLabel) {
  select.replaceChildren();
  if (initialLabel) select.add(new Option(initialLabel, ""));
  for (const key of Object.keys(counts)) select.add(new Option(labels[key] || key, key));
}

function createTrackCard(track) {
  const card = textElement("article", "track-card", "");
  const art = textElement("div", `album-art tone-${track.id % 5}`, "");
  art.setAttribute("aria-hidden", "true");
  art.append(textElement("span", "", NOTE[track.id % NOTE.length]));
  const copy = textElement("div", "track-copy", "");
  copy.append(textElement("div", "track-title", track.title));
  copy.append(textElement("div", "track-artist", track.artist));
  const meta = textElement("div", "track-meta", "");
  meta.append(
    textElement("span", "mood-label", MOOD_LABELS[track.mood] || track.mood),
    textElement("span", "", "·"),
    textElement("span", "", GENRE_LABELS[track.genre] || track.genre)
  );
  copy.append(meta);
  card.append(art, copy, textElement("span", "track-duration", formatDuration(track.duration_seconds)));
  return card;
}

function renderCatalog() {
  const grid = $("track-grid");
  const moreButton = $("show-more-tracks");
  grid.replaceChildren();
  $("track-count").textContent = String(catalogTracks.length);
  if (!catalogTracks.length) {
    grid.append(textElement("p", "empty-state", "По выбранным фильтрам треков нет. Попробуй другой жанр, настроение или поисковый запрос."));
    moreButton.hidden = true;
    return;
  }
  for (const track of catalogTracks.slice(0, visibleTracks)) grid.append(createTrackCard(track));
  const count = Math.min(visibleTracks, catalogTracks.length);
  moreButton.hidden = count >= catalogTracks.length;
  moreButton.textContent = `Показать ещё · ${count} из ${catalogTracks.length}`;
}

async function updateCatalog() {
  const currentRequest = ++catalogRequest;
  const query = new URLSearchParams();
  const search = $("search").value.trim();
  if (search) query.set("q", search);
  if ($("catalog-genre").value) query.set("genre", $("catalog-genre").value);
  if ($("catalog-mood").value) query.set("mood", $("catalog-mood").value);
  try {
    const data = await getJSON(`/tracks?${query.toString()}`);
    if (currentRequest !== catalogRequest) return;
    catalogTracks = data.tracks;
    visibleTracks = PAGE_SIZE;
    renderCatalog();
  } catch (error) {
    if (currentRequest !== catalogRequest) return;
    catalogTracks = [];
    $("track-count").textContent = "0";
    $("show-more-tracks").hidden = true;
    $("track-grid").replaceChildren(textElement("p", "empty-state", `Не удалось загрузить каталог: ${error.message}`));
  }
}

function renderPlaylist(data, container) {
  container.replaceChildren();
  const summary = textElement("div", "mix-summary", "");
  if (!data || !data.track_count) {
    summary.append(textElement("strong", "", "Пока без треков"));
    summary.append(textElement("p", "message", data?.message || "Собери подборку — она появится здесь."));
    container.append(summary);
    return;
  }
  summary.append(textElement("strong", "", `${data.track_count} треков · ${formatDuration(data.total_seconds)}`));
  summary.append(textElement("p", "", `${MOOD_LABELS[data.mood] || data.mood} · ${data.genre ? (GENRE_LABELS[data.genre] || data.genre) : "Все жанры"} · лимит ${data.max_minutes} мин`));
  data.tracks.forEach((track, index) => {
    const item = textElement("div", "mix-track", "");
    item.append(textElement("span", "mix-index", String(index + 1).padStart(2, "0")));
    const content = textElement("div", "", "");
    content.append(textElement("div", "mix-name", track.title), textElement("div", "mix-artist", track.artist));
    item.append(content, textElement("span", "mix-duration", formatDuration(track.duration_seconds)));
    summary.append(item);
  });
  container.append(summary);
}

function showFeedback(message, type) {
  const note = $("playlist-feedback");
  note.textContent = message;
  note.className = `feedback-note ${type}`;
  note.hidden = !message;
}

function loadSavedPlaylist() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (parsed && Array.isArray(parsed.tracks) && parsed.track_count > 0 && parsed.track_count === parsed.tracks.length) {
      savedPlaylist = parsed;
    }
  } catch (_) { /* Локальное хранилище может быть отключено пользователем. */ }
  updateSavedBadge();
}

function updateSavedBadge() {
  $("saved-track-count").textContent = savedPlaylist ? String(savedPlaylist.track_count) : "0";
}

function savePlaylist(data) {
  savedPlaylist = data;
  updateSavedBadge();
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (_) { /* В текущей вкладке плейлист всё равно доступен. */ }
}

function openSavedPlaylist() {
  lastFocusedElement = document.activeElement;
  const dialog = $("saved-playlist-dialog");
  if (savedPlaylist) {
    renderPlaylist(savedPlaylist, $("saved-playlist-content"));
  } else {
    $("saved-playlist-content").replaceChildren(
      textElement("p", "empty-state", "Пока нет сохранённого плейлиста. Выбери настроение, жанр и длительность, затем нажми «Создать подборку».")
    );
  }
  dialog.hidden = false;
  document.body.classList.add("drawer-open");
  $("close-playlist").focus();
}

function closeSavedPlaylist() {
  $("saved-playlist-dialog").hidden = true;
  document.body.classList.remove("drawer-open");
  if (lastFocusedElement) lastFocusedElement.focus();
}

async function createPlaylist(event) {
  event.preventDefault();
  const button = $("playlist-form").querySelector("button[type=submit]");
  const query = new URLSearchParams({
    mood: $("playlist-mood").value,
    max_minutes: $("playlist-minutes").value
  });
  if ($("playlist-genre").value) query.set("genre", $("playlist-genre").value);
  button.disabled = true;
  showFeedback("Подбираем композиции…", "info");
  try {
    const data = await getJSON(`/playlist?${query.toString()}`);
    renderPlaylist(data, $("playlist-results"));
    if (!data.track_count) {
      showFeedback(data.message || "Подходящих композиций нет. Попробуй другой жанр или больше времени.", "warning");
    } else {
      savePlaylist(data);
      const info = data.notice ? ` ${data.notice}` : "";
      showFeedback(`Готово: ${data.track_count} треков на ${formatDuration(data.total_seconds)}. Подборка сохранена в разделе «Мой плейлист».${info}`, data.notice ? "warning" : "success");
    }
  } catch (error) {
    showFeedback(`Не удалось создать плейлист: ${error.message}`, "error");
    $("playlist-results").replaceChildren(textElement("p", "message", "Проверь параметры и попробуй снова."));
  } finally {
    button.disabled = false;
  }
}

async function initialize() {
  $("playlist-form").addEventListener("submit", createPlaylist);
  $("catalog-genre").addEventListener("change", updateCatalog);
  $("catalog-mood").addEventListener("change", updateCatalog);
  $("show-more-tracks").addEventListener("click", () => {
    visibleTracks += PAGE_SIZE;
    renderCatalog();
  });
  $("my-playlist-link").addEventListener("click", openSavedPlaylist);
  $("close-playlist").addEventListener("click", closeSavedPlaylist);
  $("saved-playlist-dialog").addEventListener("click", (event) => {
    if (event.target.hasAttribute("data-close-playlist")) closeSavedPlaylist();
  });
  $("new-playlist-button").addEventListener("click", () => {
    closeSavedPlaylist();
    $("playlist-editor").scrollIntoView({behavior: "smooth", block: "start"});
    $("playlist-mood").focus({preventScroll: true});
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("saved-playlist-dialog").hidden) closeSavedPlaylist();
    if (event.key === "Tab" && !$("saved-playlist-dialog").hidden) {
      const controls = [$("close-playlist"), $("new-playlist-button")];
      if (event.shiftKey && document.activeElement === controls[0]) {
        event.preventDefault(); controls[1].focus();
      } else if (!event.shiftKey && document.activeElement === controls[1]) {
        event.preventDefault(); controls[0].focus();
      }
    }
  });
  let debounce;
  $("search").addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(updateCatalog, 180);
  });
  loadSavedPlaylist();
  try {
    const [tracks, genres, moods, version, health] = await Promise.all([
      getJSON("/tracks"), getJSON("/genres"), getJSON("/moods"), getJSON("/version"), getJSON("/health")
    ]);
    catalogTracks = tracks.tracks;
    renderCatalog();
    populateSelect($("catalog-genre"), genres.genres, GENRE_LABELS, "Все жанры");
    populateSelect($("catalog-mood"), moods.moods, MOOD_LABELS, "Все настроения");
    populateSelect($("playlist-genre"), genres.genres, GENRE_LABELS, "Любой жанр");
    populateSelect($("playlist-mood"), moods.moods, MOOD_LABELS);
    $("playlist-mood").value = "calm";
    $("app-version").textContent = `· v${version.version}`;
    const status = $("api-status");
    status.textContent = health.status === "ok" ? "Сервис работает" : "Проверьте сервис";
    status.classList.add(health.status === "ok" ? "ok" : "error");
    status.prepend(textElement("i", "", ""));
  } catch (error) {
    $("track-grid").replaceChildren(textElement("p", "empty-state", `Не удалось загрузить каталог: ${error.message}`));
    $("api-status").textContent = "Нет соединения с API";
    $("api-status").classList.add("error");
  }
}

document.addEventListener("DOMContentLoaded", initialize);
