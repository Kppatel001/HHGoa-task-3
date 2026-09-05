FROM python:3.11-slim

# System libs for OpenCV + build tools so InsightFace's Cython ext compiles.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libgomp1 curl \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-insightface.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy==1.26.4" "Cython>=0.29" && \
    pip install --no-cache-dir -r requirements.txt
# Genuine cross-photo face recognition (ArcFace). Non-fatal if it can't build —
# the app falls back to the OpenCV engine automatically.
RUN pip install --no-cache-dir -r requirements-insightface.txt || \
    echo "InsightFace not installed; using OpenCV engine"

COPY . .

# OpenCV is the always-on face engine; InsightFace is optional (see
# requirements-insightface.txt) and downloads its model pack here if installed.
ENV INSIGHTFACE_HOME=/app/.insightface
EXPOSE 8000

# Bind to the host-provided $PORT (Render/Railway/Fly) or 8000 locally.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
