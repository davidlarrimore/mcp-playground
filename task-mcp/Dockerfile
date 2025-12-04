FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY task_mcp ./task_mcp
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-task.sh"]
