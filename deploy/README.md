# Deploy guide

Two supported deployment shapes, same Docker image:

| Shape | File | Where it listens | Use it for |
| --- | --- | --- | --- |
| **Local Docker test** | `docker-compose.local.yml` | `http://127.0.0.1:8000` on the host | Smoke-testing the production image before exposing it. |
| **Production** | `docker-compose.yml` | Internal Docker network only, exposed by a `cloudflared` sidecar | Putting the app on the public internet via a Cloudflare Tunnel — no router/firewall changes needed. |

The Dockerfile builds the Vue SPA and bakes it into the Python image, so the
FastAPI process serves both the API and the SPA on `:8000`. Sessions live in
memory (single-user tool, by design).

---

## 1. Prerequisites

- Docker Engine 24+ and the Compose plugin (`docker compose version`).
- Spotify app credentials (Spotify Developer Dashboard).
- YouTube Music OAuth credentials (Google Cloud Console, client type
  *TVs and Limited Input devices*, YouTube Data API v3 enabled).
- For production only: a Cloudflare account with a domain on Cloudflare and
  Zero Trust enabled (the free tier is enough).

---

## 2. Local Docker test (`docker-compose.local.yml`)

Use this to verify the production image end-to-end on your laptop before
plugging it into the tunnel. No public exposure, no HTTPS, no Cloudflare.

### 2.1 Configure `.env`

```bash
cp .env.example .env
$EDITOR .env
```

For the local test, only these matter:

| Variable | Value |
| --- | --- |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | from Spotify dashboard |
| `YTMUSIC_CLIENT_ID` / `YTMUSIC_CLIENT_SECRET` | from Google Cloud Console |
| `APP_SECRET_KEY` | `openssl rand -hex 32` |

`PUBLIC_BASE_URL` and `TUNNEL_TOKEN` can stay blank — the local compose file
overrides everything it needs and never reads them.

### 2.2 Configure Spotify redirect URI

In the Spotify dashboard, the app's *Redirect URIs* list must contain (exact
match, no trailing slash):

```
http://127.0.0.1:8000/api/auth/spotify/callback
```

YouTube Music doesn't need a redirect URI (device-code flow).

### 2.3 Run

```bash
docker compose -f docker-compose.local.yml up --build
```

Open <http://127.0.0.1:8000>. Logs stream in the terminal; `Ctrl+C` stops.
To run detached:

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml logs -f
docker compose -f docker-compose.local.yml down
```

State (reports, any persisted artefacts) lives in the named volume
`spotifytoyoutube_app_data_local`. Use `docker compose -f docker-compose.local.yml
down -v` to wipe it.

---

## 3. Production with Cloudflare Tunnel (`docker-compose.yml`)

```
Internet ── https://your-domain ── Cloudflare edge ── (outbound only) ── cloudflared ── app:8000
```

Nothing is listened on the host. The `cloudflared` container opens an outbound
connection to Cloudflare's edge; Cloudflare routes incoming HTTPS requests
through that connection to the `app` container on the Docker network. No port
forwarding, no inbound firewall rule, no TLS certificate to manage.

### 3.1 Create the Tunnel (one-off)

1. Cloudflare Zero Trust dashboard → **Networks → Tunnels → Create a tunnel**.
2. Connector type: **Cloudflared**. Name it, e.g. `spotifytoyoutube`.
3. The wizard shows a **tunnel token** (long string starting with `eyJ...`).
   Copy it — you'll put it in `.env` as `TUNNEL_TOKEN`. You can re-read it any
   time from the tunnel's detail page.
4. **Public Hostnames → Add a public hostname**:
   - *Subdomain* + *Domain*: e.g. `playlists` + `example.com`.
   - *Type*: `HTTP` (not HTTPS — Cloudflare terminates TLS at the edge and
     reaches the container over plain HTTP inside the Docker network).
   - *URL*: `app:8000` (the docker-compose service name; cloudflared resolves
     it via the shared Docker network).
5. Save. Cloudflare creates the DNS record automatically.

### 3.2 Configure Spotify redirect URI

In the Spotify dashboard add (exact match):

```
https://playlists.example.com/api/auth/spotify/callback
```

Keep any existing local entries alongside it.

### 3.3 Configure `.env`

```bash
cp .env.example .env
$EDITOR .env
```

Required fields:

| Variable | Value |
| --- | --- |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | from Spotify dashboard |
| `YTMUSIC_CLIENT_ID` / `YTMUSIC_CLIENT_SECRET` | from Google Cloud Console |
| `APP_SECRET_KEY` | `openssl rand -hex 32` |
| `PUBLIC_BASE_URL` | `https://playlists.example.com` (no trailing slash) |
| `TUNNEL_TOKEN` | the token from step 3.1 |

`docker-compose.yml` derives `SPOTIFY_REDIRECT_URI` and `WEB_CORS_ORIGINS`
from `PUBLIC_BASE_URL`.

### 3.4 Run

```bash
docker compose up -d --build
docker compose logs -f
```

First boot takes a few seconds for `cloudflared` to register and propagate the
route. Then open `https://playlists.example.com`.

### 3.5 Updates

```bash
git pull
docker compose up -d --build
docker compose logs -f app
```

The named volume `spotifytoyoutube_app_data` survives rebuilds.

### 3.6 Stop / reset

```bash
docker compose down              # keep data
docker compose down -v           # also delete the volume
```

---

## 4. Hardening notes (optional but recommended)

- **Cloudflare Access** in front of the tunnel: in the same Zero Trust
  dashboard, attach an Access application to the public hostname and require a
  one-time PIN or Google SSO. The app has no built-in authentication, so this
  is the simplest way to make sure only you can hit it.
- **Token rotation**: regenerate `TUNNEL_TOKEN` and `APP_SECRET_KEY` from time
  to time. Restart the stack afterwards.
- **Backups**: nothing strictly needs backup (reports are derivative, sessions
  are in-memory). If you want to persist `reports/` outside the volume, bind
  mount a host directory to `/data/reports` instead of using the named volume.

---

## 5. Troubleshooting

- **502 from Cloudflare**: `cloudflared` can't reach `app:8000`. Check
  `docker compose ps` (the `app` container must be *healthy*) and
  `docker compose logs cloudflared`. The public hostname's *Service* field must
  be exactly `http://app:8000`.
- **Spotify `redirect_uri_mismatch`**: the URI in the Spotify dashboard must
  be byte-identical to `${PUBLIC_BASE_URL}/api/auth/spotify/callback` (prod) or
  `http://127.0.0.1:8000/api/auth/spotify/callback` (local). Mind scheme,
  trailing slash, and `127.0.0.1` vs `localhost`.
- **CSRF token mismatch in browser**: in production the cookies must be
  `Secure` (HTTPS only) — that's the default in `docker-compose.yml`. In the
  local compose they must NOT be `Secure` (plain HTTP) — that's the default in
  `docker-compose.local.yml`. Don't cross-wire them.
- **WebSocket transfers hanging**: Cloudflare Tunnel proxies WebSockets
  transparently for `HTTP` services; nothing extra to configure. If the SPA
  shows no progress events, double-check the public hostname is `HTTP`
  (not `HTTPS`) and that `app` is healthy.
- **Sessions vanish on restart**: web sessions are in-memory by design. A
  restart of the `app` container logs everyone out — expected for a single-user
  tool.
- **Port 8000 already in use** (local compose): change the host side of the
  mapping in `docker-compose.local.yml` to e.g. `127.0.0.1:8088:8000` and
  update the Spotify redirect URI accordingly.
