FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ is mounted at /data via docker-compose volumes
# For dev runs (uvicorn directly), DATA_DIR auto-resolves relative to this file

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host $BACKEND_HOST --port $BACKEND_PORT"]
