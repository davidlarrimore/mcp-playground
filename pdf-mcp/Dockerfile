FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates nodejs npm \
       libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0 \
       libffi-dev shared-mime-info \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pdf_mcp ./pdf_mcp
COPY start-pdf.sh /usr/local/bin/start-pdf.sh
RUN chmod +x /usr/local/bin/start-pdf.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-pdf.sh"]
