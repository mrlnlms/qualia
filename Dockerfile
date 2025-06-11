# Multi-stage Dockerfile for Qualia Core
# Optimized for size and security

# Stage 1: Builder
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Stage 2: Runtime
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 qualia

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/qualia/.local
COPY --from=builder /root/nltk_data /home/qualia/nltk_data

# Copy application code
COPY --chown=qualia:qualia . .

# Set environment variables
ENV PATH=/home/qualia/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/home/qualia/nltk_data

# Create necessary directories
RUN mkdir -p cache output && \
    chown -R qualia:qualia cache output

# Switch to non-root user
USER qualia

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Default command
CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000"]