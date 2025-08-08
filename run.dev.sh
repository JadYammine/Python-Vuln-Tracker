#!/bin/sh
docker compose -f docker-compose.dev.yml --profile debug build --no-cache
docker compose -f docker-compose.dev.yml --profile debug up