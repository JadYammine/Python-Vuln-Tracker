### Slide 1 — Problem & Goal

- Assignment: fast, reliable vulnerability tracking
- Goal: reduce latency, improve throughput, add observability

### Slide 2 — High-level Architecture

- Batch-first API: `POST /v1/querybatch` → `GET /v1/vulns/{id}`
- Background scanning workers
- In-memory LRU cache (+ optional TTL)

### Slide 3 — Why Batch + Detail

- Fewer round-trips; dedupe vuln IDs
- Cacheable idempotent details
- Parallel detail fetches with bounded concurrency

### Slide 4 — Concurrency Model

```python
tasks = [vuln_detail(vid) for vid in uniq_ids]
results = await asyncio.gather(*tasks)
```
- Wall time ~= slowest call, not sum
- Use semaphore/rate limiting for safety

### Slide 5 — Background Workers

- Keep API p95 low (fast 202)
- Backpressure, retries, isolation from upstream slowness
- Measurable queue depth and in-flight tasks

### Slide 6 — Caching Strategy

- LRU over TTL-only: memory bound, preserves hot entries
- Hash cache keys: canonical, compact, private, namespaced

### Slide 7 — Network & JSON Optimizations

- HTTP/2: multiplexing, header compression, longer keepalive
- orjson: 3-5x faster JSON serialization/deserialization
- Connection pooling, timeouts, backoff on 429

### Slide 8 — Runtime Optimizations

- `uvloop`, gzip, minimized logs (perf profile)
- Separated debug vs perf Docker profiles

### Slide 9 — Monitoring

- `/metrics` + `X-Execution-Time-ms`
- Project stats endpoint; cache hit rates

### Slide 10 — Demo Plan

- Start perf profile → show `/health` & `/metrics`
- Upload requirements → immediate validation → background scan
- Repeat to show cache hits; discuss rate-limits
- Highlight HTTP/2 multiplexing and orjson performance

### Slide 11 — Future Work

- Postgres + idempotent jobs; distributed cache (opt-in)
- Prometheus/Grafana; SLOs and alerting


