#!/usr/bin/env bash
set -e

docker build -t image-lab:latest .

echo "Removing old container..."
docker stop image-lab-container || true
docker rm image-lab-container || true

echo "Starting new container..."
docker run -d \
  --name image-lab-container \
  --restart unless-stopped \
  -e NEW_RELIC_LICENSE_KEY="$NEW_RELIC_LICENSE_KEY" \
  -e NEW_RELIC_APP_NAME="$NEW_RELIC_APP_NAME" \
  -e NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true \
  -p 5000:5000 \
  image-lab:latest

echo "Deployment successful!"
docker image prune -f
