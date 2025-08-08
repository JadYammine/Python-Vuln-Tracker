#!/bin/sh
docker compose -f docker-compose.dev.yml --profile perf build --no-cache
docker compose -f docker-compose.dev.yml --profile perf up
