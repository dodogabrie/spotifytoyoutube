# CLAUDE.md

Project context for Claude Code. Keep this short and current: future sessions
read it instead of re-deriving the design.

## What this project is

Bidirectional playlist transfer between **Spotify** and **YouTube Music**.

Two surfaces, one engine:
- Interactive CLI (`cli/`) — Typer + InquirerPy + Rich.
- Web app (`web/`) — FastAPI backend + Vue 3 / Vite / Pinia / Tailwind frontend,
  with a WebSocket stream of progress events.

User constraint: prefer official APIs; the only third-party library auditable
and acceptable is `ytmusicapi` (no public official YouTube Music API exists).

## Architectural spine

`core/transfer/engine.py::TransferEngine` is the only orchestrator. It is
direction-agnostic and only knows two interfaces, both defined in
`core/adapters/base.py`:

- `SourceAdapter` — `list_user_playlists`, `fetch_playlist_tracks`.
- `TargetAdapter` — `search_track`, `find_existing_playlist_by_name`,
  `create_playlist`, `add_tracks`, `clear_playlist`, `playlist_url`.

Both `SpotifyAdapter` and `YTMusicAdapter` implement **both** interfaces.
`core/transfer/direction.py::build_adapters` picks which one is source and
which one is target based on `TransferDirection`.

Adding a third provider = implement one new adapter, extend the direction
enum/factory. Nothing else changes.

### Module map

```
core/
  models.py                 pydantic models, enums (TransferDirection,
                            IdempotencyMode, Provider). The contract.
  config.py                 pydantic-settings, .env loader, get_settings()
  adapters/
    base.py                 SourceAdapter / TargetAdapter ABCs
    spotify_adapter.py      delegates to core/spotify/*
    ytmusic_adapter.py      delegates to core/ytmusic/*
  spotify/                  reader, writer, search, client — uses spotipy
  ytmusic/                  reader, writer, search, client — uses ytmusicapi
  matching/
    normalize.py            strip "feat", "Remaster", parens; accent-fold
    scoring.py              0.5·title + 0.3·artist + 0.15·duration (+0.10 ISRC)
    strategies.py           ordered search-query builders
  auth/
    spotify_auth.py         SpotifyOAuth (CLI, file cache) + SpotifyPKCE (web)
    ytmusic_auth.py         Google device-code flow (we own the polling)
  transfer/
    engine.py               TransferEngine + progress callback
    direction.py            direction → (source, target) factory
    idempotency.py          CREATE_NEW / APPEND / REPLACE / SKIP_IF_EXISTS
    reporter.py             writes reports/report-<ts>.json
cli/
  main.py                   Typer entrypoint
  interactive.py            menu loop with InquirerPy
  progress.py               rich.Progress consumer of TransferProgressEvent
web/backend/
  main.py                   FastAPI app factory, CORS, /api prefix
  sessions.py               in-memory session store + cookie names
  deps.py                   FastAPI deps: get_or_create_session, require_*,
                            require_csrf
  schemas.py                request/response models
  jobs.py                   JobManager (asyncio.Queue per job)
  routers/
    auth_spotify.py         /login (PKCE), /callback, /logout
    auth_ytmusic.py         /start, /poll, /status, /logout
    playlists.py            GET /playlists?provider=...
    transfer.py             POST /transfer, GET /transfer/{id}, WS stream
web/frontend/               Vue 3 SPA — see views/{Home,Login,Playlists,
                            Transfer,Report}View.vue.
                            Visual language documented in
                            web/frontend/DESIGN.md (read it before
                            making UI changes or feeding the frontend
                            to design-aware tools).
tests/
  unit/                     pure functions + mocked spotipy
  integration/              engine end-to-end (fake adapters) + API smoke
```

## Hard conventions

- **The engine never imports a provider module directly.** It only sees
  `SourceAdapter` / `TargetAdapter`. Adding behavior that is "Spotify-only" or
  "YT Music-only" should live in the adapter, not in the engine.
- **No secrets on disk in the web flow.** `web/backend/routers/playlists.py`
  builds a Spotify client from an in-memory `MemoryCacheHandler`; CLI is the
  only place that writes `./secrets/.spotify-cache` and `./secrets/oauth.json`.
- **CSRF**: every non-GET API endpoint depends on `require_csrf`. The frontend
  axios instance (`web/frontend/src/api/client.ts`) attaches the
  `X-CSRF-Token` header from the `XSRF-TOKEN` cookie automatically.
- **Progress events are the public contract** between engine and any UI:
  `TransferProgressEvent` in `core/models.py`. CLI and WebSocket both consume
  the same payload shape.
- **Matching threshold** is read from settings (`MATCH_SCORE_THRESHOLD`,
  default 0.62). Don't hardcode in adapters; pass it via constructor.
- **Idempotency** is resolved by `core/transfer/idempotency.py::resolve_target`
  and returns an action label that the engine records in the report. Engines,
  adapters, and routers should never duplicate the resolution logic.

## Auth flows in one paragraph each

- **Spotify (CLI)**: spotipy's `SpotifyOAuth` spawns a local server on
  `:8888/callback`, caches the token at `./secrets/.spotify-cache` with mode
  0600.
- **Spotify (web)**: `SpotifyPKCE` — random `state` lives in the server session,
  the code verifier too; callback verifies `state`, exchanges the code, stores
  the token only in the in-memory session.
- **YouTube Music**: device-code flow is implemented directly against
  `oauth2.googleapis.com/device/code` and `/token` in
  `core/auth/ytmusic_auth.py`. CLI blocks in `wait_for_authorization`; web
  returns the user code to the SPA and the SPA polls `/api/auth/ytmusic/poll`
  every `interval` seconds.

The ytmusicapi library itself is **unofficial** for everything after auth.
Treat any change in YT Music behavior as an upstream API drift, not a bug
in this codebase. Keep ytmusicapi pinned in `requirements.txt`.

## Commands

```bash
# Python
.venv/bin/python -m pytest -q            # 29 tests
.venv/bin/python -m cli.main             # interactive CLI menu
.venv/bin/uvicorn web.backend.main:app --reload --port 8000

# Frontend (web/frontend)
npm install
npm run build                            # type-checks + builds
npm run dev                              # Vite on :5173, proxies /api → :8000
```

## Things to avoid

- Don't add a `cli/` ↔ `web/` shortcut. Both call `core/` only.
- Don't widen Spotify scopes beyond what's needed (currently
  `playlist-read-private playlist-read-collaborative playlist-modify-private
  playlist-modify-public`).
- Don't reintroduce a JSON file token cache in the web flow. If we ever need
  persistence, plug a Redis-backed `SessionStore` behind the existing
  in-memory one; the interface is intentionally narrow.
- Don't log raw tokens or device user codes. `core/logging_setup.py` installs
  a regex scrubber; rely on it but don't print secrets unconditionally.

## Driving Claude Design (UI restyling)

Restyling passes on the SPA are run via Anthropic's Claude Design tool,
not by hand. The frontend has been prepped for it: semantic Tailwind
tokens (`web/frontend/tailwind.config.js`), reusable components
(`web/frontend/src/components/`), a brief (`web/frontend/DESIGN.md`)
and a visual baseline (`docs/screenshots/`, 10 PNGs covering desktop +
mobile of all 5 routes).

The **operator runbook** for actually driving the tool lives in
`web/frontend/CLAUDE_DESIGN.md`. It tells you exactly which files to
upload (or which folders to scope the repo reading to), what to
deliberately *not* upload, and contains a ready-to-paste prompt with
the hard constraints already encoded (no flow change, no event-name
change, dual-brand parity, Tailwind-only, accessibility floor). Keep
that runbook in sync with `DESIGN.md` whenever tokens or component
names move.

After a Claude Design pass: `npm run build` in `web/frontend/`,
`pytest -q` at the root, then re-shoot `docs/screenshots/` so the
next pass has a fresh baseline.

## Default assumptions still in force

- Single-user/local tool (web sessions are in-memory).
- Target playlist privacy mirrors the source (`public` flag passed through);
  if source has no notion of public, default to `PRIVATE`.
- No cover-art transfer in v1 (ytmusicapi supports it, can be added behind a
  flag later).
- Only **playlists** are transferred, not liked songs / followed artists /
  saved albums.
