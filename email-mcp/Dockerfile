FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY email_mcp ./email_mcp

EXPOSE 8000

CMD ["uvicorn", "email_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
