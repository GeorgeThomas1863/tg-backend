# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A React frontend that browses and plays videos stored in a Telegram channel, streamed on-demand through a FastAPI backend. Video bytes never touch local disk — the backend proxies Telegram's file API directly, converting HTTP Range requests into Telegram's own chunked download protocol so the browser's native `<video>` seeking works.

## Commands

Backend (from `backend/`, using `uv`):
- Install deps: `uv sync`
- Run dev server: `uv run python main.py` (reload enabled; listens on `BACKEND_PORT`. `config.py` loads the repo-root `.env` itself via `python-dotenv`, so no `--env-file` flag is needed)
- First run opens an interactive Telethon login prompt (phone + code) in the terminal; after that it reuses the `backend/session` file (gitignored — never commit it)

Required env vars (repo-root `.env`): `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHANNEL` (username or numeric ID), `PW_HASH` (bcrypt hash of the site password — single-quote it so the `$` signs stay literal), `SESSION_SECRET` (signs the session cookie). Optional: `BACKEND_PORT` (default 8000), `FRONTEND_PORT` (default 5173), `FRONTEND_ORIGIN` (defaults to `http://localhost:<FRONTEND_PORT>`, used for CORS).

Frontend (from `frontend/`, using `npm`):
- Install deps: `npm install`
- Run dev server: `npm run dev` (Vite, serves on `FRONTEND_PORT` from the repo-root `.env`, default 5173; `strictPort` is on, so it fails rather than drifting off the CORS-pinned port)
- `vite.config.js` reads the repo-root `.env` and injects `VITE_API_BASE` (an explicit `VITE_API_BASE` wins, else `http://localhost:<BACKEND_PORT>`).

No test suite or linter is configured on either side yet — don't invent `pytest`/`eslint`/`vitest` commands; if tests get added, the runner setup is part of that work.

## Architecture

**Backend** is split by concern, not by feature:
- `main.py` — HTTP only: routes, Range-header parsing, status codes, and the site auth (bcrypt password check via `POST /api/auth`, signed session cookie, `require_auth` dependency gating every data route). Delegates everything Telegram-related to `telegram.py`.
- `telegram.py` — owns the single shared `TelegramClient` (one session, one event loop — sized for the 1-2 user scale this is built for). All streaming/download logic lives here, including the Telegram-specific quirk that download offsets must be 4096-byte aligned.
- `config.py` — env vars plus the download tuning constants (`ALIGN`, `REQUEST_SIZE`) that `telegram.py` depends on.

The core mechanic worth understanding before touching streaming code: `GET /stream/{msg_id}` in `main.py` parses the browser's `Range` header into a byte range, then `telegram.stream_range` re-aligns that range down to Telegram's 4096-byte offset requirement, downloads from the aligned offset, and discards the leading remainder before yielding (and trims the tail so it never emits past the requested end). The two functions' range math has to stay in sync across that file boundary.

`GET /api/videos` and `GET /thumb/{msg_id}` re-resolve messages fresh via `client.get_messages` rather than caching Telethon message objects, to sidestep `file_reference` expiration.

**Frontend** follows one direction of data flow: `hooks/useVideos.js` fetches and holds state → `App.jsx` composes state with presentation → `components/VideoPlayer.jsx` is pure presentation, taking a video object and knowing nothing about fetching. `api/client.js` is the single place that knows the backend base URL (`VITE_API_BASE`, injected by `vite.config.js` from the repo-root `.env`) and builds stream/thumb URLs — components never construct backend URLs themselves.

`App.jsx` currently renders only the single most-recent video (`useVideos(1)`). The near-term direction is a gallery/grid of multiple videos, so `App.jsx`'s single-video assumption is expected to be the first thing that changes — not `useVideos` or `VideoPlayer`, which are already list-shaped.
