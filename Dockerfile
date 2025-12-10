FROM python:3.11-slim

WORKDIR /app

# Install small set of OS libraries that are commonly required by OpenCV wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       build-essential \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
       libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Use a cached wheel install from requirements
COPY requirements.txt ./

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Environment for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

# Default command: run Flask development server listening on 0.0.0.0
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
