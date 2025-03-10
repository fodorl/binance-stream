FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python files
COPY *.py ./

# Copy the web package
COPY web ./web

# Copy the cache package
COPY cache ./cache

# Copy static files and templates
COPY static ./static
COPY templates ./templates

# Copy SSL certificates if they exist
COPY certs ./certs

# Create logs directory
RUN mkdir -p logs

# Create cache data directory
RUN mkdir -p cache_data

# Copy README
COPY README.md .

# Run as non-root user for better security
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose the web port
EXPOSE 5000 5050

# Run the application
CMD ["python3", "main.py"]
