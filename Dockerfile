# KinderAi -- Streamlit app
#
# Build:  docker build -t kinderai .
# Run:    docker run --rm -p 8501:8501 --env-file .env kinderai
#
# Runs fully offline out of the box (GEMINI_USE_STUB=true by default). To use
# the real Gemini API, pass GEMINI_API_KEY and GEMINI_USE_STUB=false via
# --env-file or -e flags.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# SQLite database and generated index are written under app/, so make sure
# the runtime user can write there even if the image is run as non-root.
RUN useradd --create-home --shell /bin/bash kinderai \
    && chown -R kinderai:kinderai /app
USER kinderai

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
