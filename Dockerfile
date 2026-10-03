# QueryPilot API: FastAPI + the LangGraph agent.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Dependencies first, so code changes don't reinstall them (layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY semantic ./semantic

# Data (data/) and secrets (.env, .secrets/) are never baked into the image;
# docker-compose.yml provides them at run time.
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "--factory", "backend.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
