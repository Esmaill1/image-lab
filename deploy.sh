#!/usr/bin/env bash
set -e

# Navigate to the project directory
cd /home/ubuntu/imageprocessing-app

# 1. Pull latest code
git pull origin main

# 2. Build the new Docker image
echo "Building Docker image..."
docker build -t image-lab:latest .

# 3. Stop and remove the existing container (if it exists)

echo "Removing old container..."
docker stop image-lab-container || true
docker rm image-lab-container || true

# 4. Run the new container

echo "Starting new container..."
docker run -d \
  --name image-lab-container \
  --restart unless-stopped \
  -p 5000:5000 \
  image-lab:latest

echo "Deployment successful!"

docker image prune -f
