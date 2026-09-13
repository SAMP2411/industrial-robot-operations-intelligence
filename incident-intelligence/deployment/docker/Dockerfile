FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml /app/
COPY apps /app/apps
COPY packages /app/packages
COPY connectors /app/connectors
COPY tools/bootstrap_admin.py /app/tools/bootstrap_admin.py
COPY deployment /app/deployment
COPY alembic.ini /app/alembic.ini
RUN pip install --no-cache-dir ".[postgres]"
RUN useradd --create-home --uid 10001 rfii && mkdir -p /data/uploads /data/reports && chown -R rfii:rfii /data
USER rfii
CMD ["sh", "-c", "alembic upgrade head && uvicorn apps.diagnostic_api.main:app --host 0.0.0.0 --port 8000"]
