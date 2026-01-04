# GitHub Webhook - Cloud Run Deployment
# R3 Compliant: Gateway only (no Runner)
# Phase H: Universal Autonomous AI Crew - Event Triggers

FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy webhook service
COPY main.py .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
