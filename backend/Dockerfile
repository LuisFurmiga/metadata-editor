FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    METADATA_EXIFTOOL_BINARY=/usr/bin/exiftool \
    METADATA_WORKSPACE_ROOT=/tmp/metadata-editor/sessions

RUN apt-get update \
    && apt-get install --no-install-recommends -y libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY requirements.txt ./
RUN pip install --requirement requirements.txt

COPY app ./app
RUN mkdir -p /tmp/metadata-editor/sessions \
    && chown -R app:app /tmp/metadata-editor

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)); raise SystemExit(0 if data['exiftool']['available'] else 1)"]

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
