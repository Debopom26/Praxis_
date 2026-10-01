FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 praxis
WORKDIR /app
COPY backend /app/backend
RUN pip install --timeout 60 --retries 5 pip==26.2.1
RUN pip install --timeout 60 --retries 5 --resume-retries 5 --index-url https://download.pytorch.org/whl/cpu torch==2.14.0 torchaudio==2.11.0
RUN pip install --timeout 60 --retries 5 --resume-retries 5 /app/backend
RUN pip install --timeout 60 --retries 5 --resume-retries 5 setuptools==84.0.0 \
    && pip check \
    && pip uninstall --yes pip
COPY scripts/migrate_and_grant.py scripts/create_admin.py /app/scripts/
COPY docs/model-assets.json /app/docs/model-assets.json
RUN mkdir -p /app/.cache && chown -R praxis:praxis /app/.cache
USER praxis
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "praxis.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--ws-max-size", "262144", "--no-access-log"]
