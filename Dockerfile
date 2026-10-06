# ============================================================
# Frontend
# ============================================================

FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


# ============================================================
# Backend / Python
# ============================================================

FROM python:3.14-slim-trixie AS backend-builder

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src ./src

RUN uv venv /app/.venv --python /usr/local/bin/python3.14

RUN --mount=type=cache,target=/root/.cache \
    uv pip install \
        --python /app/.venv/bin/python \
        .

RUN find /app/.venv/lib/python3.14/site-packages -depth \
        \( \
            -type d -name 'test' -o \
            -type d -name 'tests' -o \
            -type d -name '__pycache__' \
        \) \
        -exec rm -rf {} + \
    && \
    find /app/.venv/lib/python3.14/site-packages -type f \
        \( \
            -name '*.pyc' -o \
            -name '*.pyo' \
        \) \
        -delete


# ============================================================
# ExifTool / Perl
# ============================================================

FROM debian:trixie-slim AS exiftool-builder

ARG EXIFTOOL_VERSION=13.59

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        perl \
        libcrypt1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN curl -fsSL \
        "https://sourceforge.net/projects/exiftool/files/Image-ExifTool-${EXIFTOOL_VERSION}.tar.gz/download" \
        -o exiftool.tar.gz \
    && tar -xzf exiftool.tar.gz \
    && mv "Image-ExifTool-${EXIFTOOL_VERSION}" /opt/exiftool \
    && rm exiftool.tar.gz

# ------------------------------------------------------------
# Verify ExifTool in the complete Debian builder.
# ------------------------------------------------------------

RUN /usr/bin/perl /opt/exiftool/exiftool -ver


# ------------------------------------------------------------
# Prepare runtime filesystem.
# ------------------------------------------------------------

RUN mkdir -p \
        /runtime/usr/bin \
        /runtime/usr/lib \
        /runtime/usr/local/lib \
        /runtime/usr/local/share \
        /runtime/usr/share \
        /runtime/lib \
        /runtime/opt


# ------------------------------------------------------------
# Perl executable.
# ------------------------------------------------------------

RUN cp -L \
        /usr/bin/perl \
        /runtime/usr/bin/perl


# ------------------------------------------------------------
# ExifTool.
#
# ExifTool's own lib directory contains the majority of its
# Perl modules.
# ------------------------------------------------------------

RUN cp -a \
        /opt/exiftool \
        /runtime/opt/exiftool


# ------------------------------------------------------------
# Copy every Perl @INC directory.
#
# This is the important part. It includes modules such as:
#
#   File/Glob.pm
#
# rather than assuming they live in only /usr/share/perl.
# ------------------------------------------------------------

RUN perl -e 'print join("\n", @INC), "\n"' \
    | while read -r inc; do \
        if [ -d "$inc" ]; then \
            mkdir -p "/runtime$inc"; \
            cp -a "$inc"/. "/runtime$inc"/; \
        fi; \
    done


# ------------------------------------------------------------
# Copy every shared library required by Perl.
#
# This includes libcrypt.so.1 and other native dependencies.
# ------------------------------------------------------------

RUN ldd /usr/bin/perl \
    | awk '/=> \// {print $3} /^\// {print $1}' \
    | sort -u \
    | while read -r lib; do \
        if [ -f "$lib" ]; then \
            mkdir -p "/runtime$(dirname "$lib")"; \
            cp -L "$lib" "/runtime$lib"; \
        fi; \
    done


# ------------------------------------------------------------
# Verify the assembled runtime.
#
# Run Perl using the copied runtime files, not the builder's
# original filesystem.
# ------------------------------------------------------------

RUN echo "=== Perl @INC ===" \
    && /usr/bin/perl -e 'print join("\n", @INC), "\n"' \
    && echo "=== Perl dependencies ===" \
    && ldd /usr/bin/perl \
    && echo "=== ExifTool version ===" \
    && /usr/bin/perl /opt/exiftool/exiftool -ver


# ============================================================
# Runtime
# ============================================================

FROM gcr.io/distroless/cc-debian13:nonroot

ENV TZ=UTC


# ============================================================
# Python
# ============================================================

COPY --from=backend-builder \
    /usr/local/bin/python3.14 \
    /usr/local/bin/python3.14

COPY --from=backend-builder \
    /usr/local/lib/python3.14 \
    /usr/local/lib/python3.14

COPY --from=backend-builder \
    /usr/local/lib/libpython3.14.so* \
    /usr/local/lib/


# ============================================================
# Python virtual environment
# ============================================================

COPY --from=backend-builder \
    --chown=nonroot:nonroot \
    /app/.venv \
    /app/.venv


# ============================================================
# Backend
# ============================================================

COPY --from=backend-builder \
    --chown=nonroot:nonroot \
    /app/src \
    /app/src


# ============================================================
# React production build
# ============================================================

COPY --from=frontend-builder \
    --chown=nonroot:nonroot \
    /app/frontend/dist \
    /app/src/backend/frontend


# ============================================================
# Perl runtime
# ============================================================

COPY --from=exiftool-builder \
    /runtime/usr/bin/perl \
    /usr/bin/perl

COPY --from=exiftool-builder \
    /runtime/usr/lib/ \
    /usr/lib/

COPY --from=exiftool-builder \
    /runtime/usr/local/lib/ \
    /usr/local/lib/

COPY --from=exiftool-builder \
    /runtime/usr/local/share/ \
    /usr/local/share/

COPY --from=exiftool-builder \
    /runtime/usr/share/ \
    /usr/share/

COPY --from=exiftool-builder \
    /runtime/lib/ \
    /lib/


# ============================================================
# ExifTool
# ============================================================

COPY --from=exiftool-builder \
    /runtime/opt/exiftool \
    /opt/exiftool


# ============================================================
# Application
# ============================================================

WORKDIR /app

ENV PATH="/usr/local/bin:/app/.venv/bin:/opt/exiftool:$PATH" \
    PYTHONPATH="/app/src:/app/.venv/lib/python3.14/site-packages" \
    METADATA_EXIFTOOL_BINARY="/opt/exiftool/exiftool" \
    METADATA_WORKSPACE_ROOT="/tmp/metadata-editor/sessions"

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
