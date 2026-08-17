# ================================================================
# AI Title Verification — PSS06 · Team CODECRAFTERS (TSEC)
# Single-image deployment: React build + FastAPI + SQLite, one origin
# (frontend and API served together — no CORS issues).
# Works on Render / Railway / Fly.io / Hugging Face Spaces / any VM.
#
# Default image = LIGHT tier: full verification engine with the
# labelled demo-concept semantic engine (fits 512 MB free tiers).
# On 2GB+ machines enable the full multilingual embedding engine:
#   docker build --build-arg INSTALL_ST=1 -t title-verification .
# ================================================================

# ---- stage 1: frontend build ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- stage 2: runtime ----
FROM python:3.12-slim
ARG INSTALL_ST=0
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8000

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_ST" = "1" ]; then \
         pip install torch --index-url https://download.pytorch.org/whl/cpu \
         && pip install sentence-transformers ; \
       fi

COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./frontend/dist

# SQLite lives in /app/data (volume-able). On ephemeral filesystems the demo
# dataset simply re-seeds at startup; submission history resets on redeploy —
# acceptable for a prototype and documented in DEPLOYMENT.md.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=25s \
  CMD python -c "import urllib.request,os;urllib.request.urlopen('http://localhost:%s/api/health'%os.environ.get('PORT',8000),timeout=5)"

CMD ["sh", "-c", "cd /app/backend && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
