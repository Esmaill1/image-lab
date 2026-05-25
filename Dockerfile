FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for OpenCV (no build-essential — all pip packages use pre-compiled wheels)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
       libgl1 \
       curl \
     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (requirements.txt copied first for layer caching)
COPY requirements.txt ./

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Flask app location (used by Flask CLI if needed)
ENV FLASK_APP=app.py

EXPOSE 5001

# Production: Gunicorn with 2 workers, 120s timeout for image processing
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "app:app"]
