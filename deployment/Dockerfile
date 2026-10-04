FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 praxis
WORKDIR /app
RUN pip install --timeout 60 --retries 5 pip==26.2.1
RUN pip install --timeout 60 --retries 5 --resume-retries 5 --index-url https://download.pytorch.org/whl/cpu torch==2.14.0 torchaudio==2.11.0
ARG PRAXIS_DEP_REV=20261002
RUN test -n "$PRAXIS_DEP_REV"
COPY backend/pyproject.toml /tmp/praxis-pyproject.toml
RUN test -s /tmp/praxis-pyproject.toml
RUN python -c "import tomllib,subprocess; deps=tomllib.load(open('/tmp/praxis-pyproject.toml','rb'))['project']['dependencies']; subprocess.check_call(['pip','install','--timeout','60','--retries','5','--resume-retries','5',*deps])"
RUN python -c "import importlib.metadata as m, websockets; assert m.version('websockets') and getattr(websockets, '__version__', None)"
RUN pip install --timeout 60 --retries 5 --resume-retries 5 setuptools==84.0.0
ARG PRAXIS_SOURCE_REV=20261002
RUN test -n "$PRAXIS_SOURCE_REV"
COPY backend /app/backend
RUN test -s /app/backend/src/praxis/main.py && test -s /app/backend/src/praxis/voip.py
RUN pip install --no-build-isolation --no-deps --timeout 60 --retries 5 /app/backend
RUN pip check \
    && pip uninstall --yes pip
COPY scripts/migrate_and_grant.py scripts/create_admin.py scripts/create_host.py scripts/reset_account_password.py /app/scripts/
RUN test -s /app/scripts/create_host.py
COPY docs/model-assets.json /app/docs/model-assets.json
RUN mkdir -p /app/.cache && chown -R praxis:praxis /app/.cache
USER praxis
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "praxis.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--ws-max-size", "262144", "--ws-ping-interval", "60", "--ws-ping-timeout", "60", "--no-access-log"]
