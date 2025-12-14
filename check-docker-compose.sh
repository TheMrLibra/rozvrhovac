#!/bin/bash
# Script to check which docker compose command is available

echo "Checking for docker compose commands..."

if docker compose version >/dev/null 2>&1; then
    echo "✓ docker compose (plugin) is available"
    echo "DOCKER_COMPOSE_CMD=docker compose"
    exit 0
elif command -v docker-compose >/dev/null 2>&1; then
    echo "✓ docker-compose (standalone) is available"
    echo "DOCKER_COMPOSE_CMD=docker-compose"
    exit 0
else
    echo "✗ Neither docker compose nor docker-compose found"
    echo "Please install docker-compose: sudo apt install docker-compose"
    exit 1
fi

