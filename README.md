# spotifytoyoutube

Bidirectional playlist transfer between Spotify and YouTube Music.

Two interchangeable interfaces share one engine:
- **Interactive CLI** (Typer + InquirerPy + Rich).
- **Web app** (FastAPI backend + Vue 3 + Tailwind frontend), with live WebSocket progress.

The engine is direction-agnostic: it talks to `SourceAdapter` and `TargetAdapter`
interfaces implemented by Spotify and YouTube Music modules. The same matching,
idempotency and reporting code runs in both directions.

---

## Libraries used (and why)

| Concern | Library | License | Why |
| --- | --- | --- | --- |
| Spotify API | [`spotipy`](https://github.com/spotipy-dev/spotipy) | MIT | Thin, well-maintained wrapper that talks only to the official Spotify Web API. |
| YouTube Music | [`ytmusicapi`](https://github.com/sigma67/ytmusicapi) | MIT | YouTube Music has **no public official API**. ytmusicapi authenticates through Google's official OAuth endpoints and emulates the YT Music web client for everything else. |
| Matching | `rapidfuzz` | MIT | Fast token-set ratio scoring. |
| Backend | `fastapi`, `uvicorn`, `pydantic` | MIT / BSD | Standard. |
| Frontend | Vue 3, Pinia, Vite, Tailwind | MIT | Standard. |

### Security audit notes for `ytmusicapi`

- The OAuth handshake (`core/auth/ytmusic_auth.py`) hits only Google's official
  endpoints (`oauth2.googleapis.com/device/code`, `oauth2.googleapis.com/token`).
  We re-implement the device-code flow locally instead of going through
  `ytmusicapi.setup_oauth` so the web flow can drive it step by step and we
  control exactly where credentials go.
- Once authorized, `ytmusicapi` itself emulates YT Music's internal web client
  with `Authorization: Bearer <google_token>`. Because this is unofficial it
  can break if Google changes the internal API; the wrapper is therefore
  isolated behind `core/ytmusic/*` so we can swap it out if needed.
- The library is pinned to a known-good major version in `requirements.txt`.

---

## Getting started

### 1. Clone & install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

For the web frontend:

```bash
cd web/frontend && npm install
```

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in the values.

**Spotify** — at <https://developer.spotify.com/dashboard>:
- Create an app, then under *Redirect URIs* add both:
  - `http://127.0.0.1:8000/api/auth/spotify/callback` (web)
  - `http://127.0.0.1:8888/callback` (CLI)
- Copy *Client ID* and *Client Secret* into `.env`.

**YouTube Music** — at <https://console.cloud.google.com>:
1. Create a project (or reuse one).
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen as *External* and add yourself as a test
   user.
4. Create OAuth credentials of type **TVs and Limited Input devices**
   (required by the device-code flow).
5. Copy the *Client ID* and *Client Secret* into `.env`.

### 3. Run

**CLI**:

```bash
python -m cli.main          # interactive menu
python -m cli.main login-spotify
python -m cli.main login-ytmusic
```

**Web (two processes)**:

```bash
# Terminal 1 — backend
uvicorn web.backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd web/frontend && npm run dev
```

Open <http://localhost:5173>, pick a direction, connect both accounts,
choose playlists, watch the live progress, download the JSON report.

---

## Project layout

```
core/                 shared transfer engine + provider adapters
cli/                  interactive CLI (Typer + InquirerPy + Rich)
web/backend/          FastAPI app (auth flows, jobs, WebSocket stream)
web/frontend/         Vue 3 + Vite + Pinia + Tailwind SPA
tests/                pytest unit + integration suite
reports/              JSON transfer reports (gitignored)
secrets/              spotipy cache + ytmusic oauth.json (gitignored)
```

### Adapter abstraction (`core/adapters/base.py`)

`SourceAdapter` reads playlists and their tracks. `TargetAdapter` searches the
target catalogue, creates playlists, finds existing ones for idempotency, and
adds tracks. `SpotifyAdapter` and `YTMusicAdapter` implement **both**
interfaces, so swapping the direction is a one-liner in
`core/transfer/direction.py`.

### Matching

- Normalize titles (drop `feat./remaster/parenthetical`, fold accents).
- Score = 0.5·title + 0.3·artist + 0.15·duration (+ 0.10 if ISRC matches).
- Default threshold: 0.62 (configurable via `MATCH_SCORE_THRESHOLD`).
- Strategy order:
  - **Spotify target**: ISRC query → `track:"…" artist:"…"` → free-text.
  - **YT Music target**: ISRC query → `"<title> <artist>"` `filter=songs` →
    normalized fallback → `filter=videos`.

### Idempotency modes

- `create_new` (default): suffix `(2)`, `(3)`… on name collision.
- `append`: add only into an existing same-named playlist.
- `replace`: wipe the existing playlist first, then refill.
- `skip_if_exists`: leave the existing playlist untouched.

---

## Security

- Web sessions are stored in memory and identified by an HttpOnly cookie. Tokens
  never touch disk in the web flow.
- CSRF protection is double-submit: every non-GET request must echo the
  `XSRF-TOKEN` cookie back as the `X-CSRF-Token` header.
- Spotify OAuth uses PKCE plus a random `state` parameter, verified on
  callback.
- Logs scrub anything that looks like an OAuth token, refresh token, client
  secret or device user code.
- `.env`, `oauth.json`, the spotipy cache and the `reports/` directory are
  gitignored. Never commit secrets.

---

## Development

```bash
pytest -q                            # full unit + integration suite
ruff check .                         # lint
mypy core cli web/backend            # type-check
cd web/frontend && npm run build     # build & type-check the SPA
```
