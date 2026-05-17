# Deploy: Docker + Cloudflare Tunnel

Single-container deploy (FastAPI + built Vue SPA on the same process), exposed
to the public internet by a `cloudflared` sidecar over a Cloudflare Tunnel.
No ports are opened on the host: traffic only flows outbound from `cloudflared`
to Cloudflare's edge.

```
Internet ── https://your-domain ── Cloudflare edge ── (outbound) ── cloudflared ── app:8000
```

## 1. Prepare the Cloudflare Tunnel (one-off)

1. Cloudflare Zero Trust dashboard -> **Networks -> Tunnels -> Create a tunnel**.
2. Connector type: **Cloudflared**. Name it, e.g. `spotifytoyoutube`.
3. Copy the **tunnel token** that the wizard shows (long string starting with
   `eyJ...`). You will put this in `.env` as `TUNNEL_TOKEN`.
4. Under **Public Hostnames**, add a route:
   - Subdomain + Domain: e.g. `playlists` + `example.com`.
   - Service: `HTTP` `app:8000`
     (`app` is the docker-compose service name; cloudflared resolves it over the
     internal Docker network.)
5. Save. DNS is created automatically.

## 2. Configure OAuth providers

### Spotify

In the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard),
edit your app and add this redirect URI (must match exactly):

```
https://playlists.example.com/api/auth/spotify/callback
```

You can keep the local `http://127.0.0.1:8000/...` and `http://127.0.0.1:8888/callback`
entries alongside it.

### YouTube Music

Nothing extra: the device-code flow doesn't use a fixed redirect URI. Just make
sure your Google OAuth consent screen lists you as a test user and the client
type is **TVs and Limited Input devices**.

## 3. Configure `.env`

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
| `TUNNEL_TOKEN` | the token from step 1 |

`docker-compose.yml` derives `SPOTIFY_REDIRECT_URI` and `WEB_CORS_ORIGINS` from
`PUBLIC_BASE_URL`, so you don't have to touch them.

## 4. Run

```bash
docker compose up -d --build
docker compose logs -f
```

Open `https://playlists.example.com` in your browser. The `cloudflared`
container will register the tunnel and the `app` container will serve both the
API and the SPA on `:8000` inside the Docker network.

## 5. Updates

```bash
git pull
docker compose up -d --build
```

Reports and (for the CLI usage path) OAuth caches persist in the `app_data`
named volume mounted at `/data`.

## Troubleshooting

- **502 from Cloudflare**: the tunnel can't reach `app:8000`. Check
  `docker compose ps` and `docker compose logs cloudflared` — the public
  hostname's service field must be exactly `http://app:8000`.
- **Spotify redirect_uri_mismatch**: the URI in the Spotify dashboard must be
  byte-identical to `${PUBLIC_BASE_URL}/api/auth/spotify/callback`. Mind the
  scheme (`https`) and the absence of a trailing slash.
- **CSRF token mismatch in browser**: usually `SESSION_COOKIE_SECURE=true` over
  HTTP. Behind Cloudflare Tunnel the connection is HTTPS end-to-user, so this
  is the correct setting; if you ever test the container directly over plain
  HTTP, flip it to `false`.
- **WebSocket disconnects**: Cloudflare Tunnel proxies WebSockets transparently
  for HTTP services — nothing extra to configure. If the SPA shows the transfer
  hanging, check that the public hostname's service is `HTTP` (not `HTTPS`) and
  that `app` is healthy.
- **Sessions vanish on restart**: web sessions are in-memory by design. A
  restart of the `app` container logs everyone out — expected for a single-user
  tool.
