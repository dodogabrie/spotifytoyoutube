# syntax=docker/dockerfile:1.6

# --- Stage 1: build the Vue SPA -------------------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /app/web/frontend

COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci

COPY web/frontend/ ./
RUN npm run build


# --- Stage 2: Python runtime ----------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WEB_STATIC_DIR=/app/web/frontend/dist \
    SESSION_COOKIE_SECURE=true \
    REPORTS_DIR=/data/reports \
    SECRETS_DIR=/data/secrets

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates tini \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 1000 app \
 && useradd  --system --uid 1000 --gid app --create-home --home-dir /home/app app \
 && mkdir -p /data/reports /data/secrets \
 && chown -R app:app /data

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY core/ ./core/
COPY web/backend/ ./web/backend/
COPY cli/ ./cli/
COPY pyproject.toml README.md ./

COPY --from=frontend /app/web/frontend/dist ./web/frontend/dist

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
