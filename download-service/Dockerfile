FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the download service
COPY download_server.py .

# Note: The shared module will be mounted as a volume at runtime
# This allows the shared code to be accessible without embedding it in the image

# Expose the download service port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run the download service
CMD ["python", "download_server.py"]
