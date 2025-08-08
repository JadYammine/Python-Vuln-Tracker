### Technical Overview: Architecture and Performance

This document consolidates the design rationale and performance strategy for the Python Vulnerability Tracker. Use it as a single reference during code reviews and demos.

### Executive summary

- **Goal**: Fast, reliable vulnerability lookups with predictable latency under load
- **Approach**: Batch-first API usage, bounded concurrency, efficient caching, and observability
- **Outcomes**: Lower request counts, stable p95 latency, and clearer operational metrics

### Core architecture decisions (with rationale)

1) Batch first: `POST /v1/querybatch` → `GET /v1/vulns/{id}`
- Fewer round-trips; better deduplication of vuln IDs
- Cache-friendly, idempotent detail lookups
- Naturally parallelizable detail fetches with bounded concurrency

2) Background scanning workers
- Keep request handlers fast (202 Accepted) for good p95/p99
- Bounded worker pool applies backpressure and isolates timeouts/retries
- Clearer metrics (queue depth, in-flight scans) and easier horizontal scaling

3) Concurrency: `asyncio.gather` vs sequential awaits
- Concurrent scheduling minimizes wall-clock time for I/O-bound detail fetches
- Wall time ~= slowest call, not sum of all calls
- Pair with semaphore/rate limiter to cap concurrency safely

4) Caching strategy: LRU over simple TTL
- Keeps hot entries; evicts the least useful when memory-bound
- Predictable memory caps; lower miss rate on skewed access
- Optional TTL provides freshness without sacrificing LRU benefits

5) Parse requirements at ingestion (not background)
- Immediate validation and feedback; avoid queuing bad work
- Atomic ingestion: parse → normalize → persist → enqueue scan
- Reserve workers for the truly expensive (network-bound) part

6) Hashed cache keys (not plain string formatting)
- Canonical, compact, ASCII-safe, and privacy-preserving
- Negligible collision risk (e.g., SHA-256) and easy namespacing/versioning

7) Separated schemas and domain models
- Domain models (`src/domain/`) represent internal business logic and data structures
- Schema models (`src/schemas/`) handle client-facing API serialization/validation
- Clean separation enables internal refactoring without breaking API contracts
- Pydantic schemas provide automatic validation, documentation, and OpenAPI generation

8) HTTP/2 for external API calls
- OSV client uses HTTP/2 with multiplexing for concurrent vulnerability detail requests
- Single connection handles multiple simultaneous requests vs separate connections per request
- Header compression (HPACK) reduces overhead for repeated API calls
- Longer keepalive timeouts (60s) maximize connection reuse benefits
- Particularly effective for high-concurrency vulnerability detail fetching

### Performance playbook

- HTTP layer: connection pooling, timeouts, retry/backoff on 429, rate limiting
- Async model: `asyncio.gather` for bulk I/O; semaphore to bound concurrency
- Caching: in-memory LRU + optional TTL; cache stats exposed for tuning. End-to-end performance is dominated by avoiding external API calls; cache CPU overhead is negligible compared to network latency.
- FastAPI runtime: `uvloop`, gzip, minimal logging in perf profile
- Profiles: `debug` (reload, debugpy) vs `perf` (no debugpy, optimized flags)

### Monitoring and diagnostics

- `/metrics`: health, uptime, request stats, cache stats, external API counters
- Execution time header: `X-Execution-Time-ms` per request
- Project stats endpoint for cache and scan performance

### Demo flow (10–12 minutes)

1) Architecture quick tour: batch → detail, background workers, caching
2) Run perf profile; show `/health` and `/metrics`
3) Upload requirements; observe fast ingestion (validated), scan runs in background
4) Show cache hits on repeated lookups; discuss LRU vs TTL
5) Discuss request/scan counters and rate-limit handling

### Q&A prompts

- How does the system behave under rate limiting (429)?
- What happens if a scan fails mid-way? How are retries handled?
- How to tune concurrency and cache sizes in production?

### Future work (high impact)

- Persistent storage (PostgreSQL), idempotent jobs, and resumable scans
- Distributed cache (opt-in) and cache warming
- Prometheus/Grafana integration and SLO-based alerting


