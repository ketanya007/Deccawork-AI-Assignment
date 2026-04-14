# Use a guaranteed Python 3.12 base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its system dependencies for Chromium
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create instance directory for SQLite and set permissions
RUN mkdir -p instance && chmod 777 instance

# Handle port (Railway provides PORT env var)
EXPOSE 8080

# Default: start webhook server
CMD ["python", "-m", "webhook.server"]
