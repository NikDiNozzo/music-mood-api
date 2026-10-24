"use strict";

const $ = (id) => document.getElementById(id);
const MOOD_LABELS = {calm: "Спокойное", upbeat: "Позитивное", energetic: "Энергичное", focus: "Для концентрации"};
const GENRE_LABELS = {rock: "Рок", pop: "Поп", electronic: "Электроника", soundtrack: "Саундтрек", classical: "Классика"};
const NOTE = ["♫", "♪", "✦", "♬", "◈"];

function formatDuration(seconds) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

async function getJSON(path) {
  const response = await fetch(path);
  if (!response.ok) {
    let message = `Ошибка запроса (${response.status})`;
    try { const body = await response.json(); message = body.detail || message; } catch (_) { /* no JSON */ }
    throw new Error(typeof message === "string" ? message : "Некорректный запрос");
  }
  return response.json();
}

function textElement(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = content;
  return node;
}

function populateSelect(select, counts, labels, initialLabel) {
  select.replaceChildren();
  if (initialLabel) select.add(new Option(initialLabel, ""));
  for (const key of Object.keys(counts)) select.add(new Option(labels[key] || key, key));
}

function renderCatalog(tracks) {
  const grid = $("track-grid");
  grid.replaceChildren();
  $("track-count").textContent = `${tracks.length}`;
  if (!tracks.length) {
    grid.append(textElement("p", "empty-state", "По этим фильтрам ничего не найдено. Попробуй другой запрос."));
    return;
  }
  for (const track of tracks) {
    const card = textElement("article", "track-card", "");
    const art = textElement("div", `album-art tone-${track.id % 5}`, "");
    art.setAttribute("aria-hidden", "true");
    art.append(textElement("span", "", NOTE[track.id % NOTE.length]));
    const copy = textElement("div", "track-copy", "");
    copy.append(textElement("div", "track-title", track.title));
    copy.append(textElement("div", "track-artist", track.artist));
    const meta = textElement("div", "track-meta", "");
    meta.append(textElement("span", "mood-label", MOOD_LABELS[track.mood] || track.mood));
    meta.append(textElement("span", "", "·"));
    meta.append(textElement("span", "", GENRE_LABELS[track.genre] || track.genre));
    copy.append(meta);
    card.append(art, copy, textElement("span", "track-duration", formatDuration(track.duration_seconds)));
    grid.append(card);
  }
}

let catalogRequest = 0;
async function updateCatalog() {
  const currentRequest = ++catalogRequest;
  const query = new URLSearchParams();
  const search = $("search").value.trim();
  if (search) query.set("q", search);
  if ($("catalog-genre").value) query.set("genre", $("catalog-genre").value);
  if ($("catalog-mood").value) query.set("mood", $("catalog-mood").value);
  try {
    const data = await getJSON(`/tracks?${query.toString()}`);
    if (currentRequest === catalogRequest) renderCatalog(data.tracks);
  } catch (error) {
    if (currentRequest === catalogRequest) $("track-grid").replaceChildren(textElement("p", "empty-state", error.message));
  }
}

function renderPlaylist(data) {
  const container = $("playlist-results");
  container.replaceChildren();
  const summary = textElement("div", "mix-summary", "");
  if (!data.track_count) {
    summary.append(textElement("strong", "", "Пока без треков"));
    summary.append(textElement("p", "message", data.message || "Попробуй другой жанр, настроение или более длинный плейлист."));
    container.append(summary);
    return;
  }
  summary.append(textElement("strong", "", `Готово! ${data.track_count} трек(ов)`));
  summary.append(textElement("p", "", `Общее время ${formatDuration(data.total_seconds)} · лимит ${data.max_minutes} мин`));
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

async function createPlaylist(event) {
  event.preventDefault();
  const button = $("playlist-form").querySelector("button");
  const query = new URLSearchParams({mood: $("playlist-mood").value, max_minutes: $("playlist-minutes").value});
  if ($("playlist-genre").value) query.set("genre", $("playlist-genre").value);
  button.disabled = true;
  try {
    const data = await getJSON(`/playlist?${query.toString()}`);
    renderPlaylist(data);
  } catch (error) {
    $("playlist-results").replaceChildren(textElement("p", "message", error.message));
  } finally { button.disabled = false; }
}

async function initialize() {
  $("playlist-form").addEventListener("submit", createPlaylist);
  $("catalog-genre").addEventListener("change", updateCatalog);
  $("catalog-mood").addEventListener("change", updateCatalog);
  let debounce;
  $("search").addEventListener("input", () => { clearTimeout(debounce); debounce = setTimeout(updateCatalog, 180); });
  try {
    const [tracks, genres, moods, version, health] = await Promise.all([
      getJSON("/tracks"), getJSON("/genres"), getJSON("/moods"), getJSON("/version"), getJSON("/health")
    ]);
    renderCatalog(tracks.tracks);
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
