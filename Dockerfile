# Use the official Microsoft Playwright image as the base
# This image comes with all browser dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers are already in the image, but we ensure the python wrapper is ready
# We don't need 'playwright install-deps' here because the base image has them
RUN playwright install chromium

# Copy application code
COPY . .

# Create instance directory for SQLite and set permissions
RUN mkdir -p instance && chmod 777 instance

# Handle port (Railway provides PORT env var)
# We default to 8080 or similar if needed, but the server handles dynamic port
EXPOSE 8080

# Default: start webhook server (which also starts admin panel)
# Railway automatically maps the external port to whatever port the app listens on
CMD ["python", "-m", "webhook.server"]
