#!/usr/bin/env bash
# ============================================================
# AI Title Verification — PSS06 · Team CODECRAFTERS (TSEC)
# One-command local run: build frontend + start backend.
# The full product is then served on http://localhost:8000
# ============================================================
set -e
cd "$(dirname "$0")"

echo "==> Installing backend dependencies"
pip install -r requirements.txt

echo "==> (Optional) sentence-transformers engine"
pip install torch --index-url https://download.pytorch.org/whl/cpu \
  && pip install sentence-transformers \
  || echo "    skipping ST engine — demo semantic matching will be used instead"

if [ ! -d frontend/dist ]; then
  echo "==> Building frontend"
  cd frontend
  npm install
  npm run build
  cd ..
fi

echo "==> Starting AI Title Verification on http://localhost:8000"
cd backend
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
