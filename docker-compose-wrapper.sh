#!/bin/bash
# Wrapper script to use either docker-compose or docker compose

if docker compose version >/dev/null 2>&1; then
    exec docker compose "$@"
elif command -v docker-compose >/dev/null 2>&1; then
    exec docker-compose "$@"
else
    echo "Error: Neither 'docker compose' nor 'docker-compose' found" >&2
    echo "Please install docker-compose: sudo apt install docker-compose" >&2
    exit 1
fi

