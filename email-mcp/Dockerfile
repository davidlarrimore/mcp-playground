FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY email_mcp ./email_mcp
COPY start-email.sh /usr/local/bin/start-email.sh
RUN chmod +x /usr/local/bin/start-email.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-email.sh"]
