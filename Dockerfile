FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for Hugging Face Spaces
RUN useradd -m -u 1000 user
ENV HOME=/home/user
WORKDIR $HOME/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (must be done as root or with correct permissions)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code with correct ownership
COPY --chown=user . .

# Create instance directory and ensure user has access
RUN mkdir -p instance && chown -R user:user instance

# Switch to non-root user
USER user

# Expose port 7860 (required by Hugging Face)
EXPOSE 7860

# Default: start webhook server (which also starts admin panel)
# Use environment variables to handle ports dynamically
CMD ["python", "-m", "webhook.server"]
