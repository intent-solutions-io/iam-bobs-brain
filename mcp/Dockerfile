# Bob's MCP Server
# Runs on Cloud Run, provides tools to Bob's Brain agents

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8080

CMD ["python", "-m", "src.server"]
