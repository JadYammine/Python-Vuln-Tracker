#!/bin/sh
docker compose -f docker-compose.dev.yml build --no-cache
docker compose --profile test -f docker-compose.dev.yml run --rm test