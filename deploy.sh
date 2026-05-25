#!/usr/bin/env bash
set -e

echo "Building and starting containers..."
# Use docker-compose to handle building and restarting
docker compose up -d --build

echo "Deployment successful!"

# Clean up old images
docker image prune -f
