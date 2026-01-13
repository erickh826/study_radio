# Use Debian Bookworm slim as base
FROM debian:bookworm-slim

# Set working directory
WORKDIR /app

# Install Python and system dependencies in stages
# Stage 1: Update package lists and install basic tools
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Python 3.11 and pip (Debian Bookworm default, audioop still exists)
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python (python3 is already available)
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Stage 3: Install build dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 4: Install runtime dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    openssl \
    libssl3 \
    && rm -rf /var/lib/apt/lists/* && \
    update-ca-certificates

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create static directories
RUN mkdir -p static/audio

# Set temporary directory for CRL caching
ENV TMPDIR=/tmp

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
