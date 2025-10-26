# LeetCode Analytics API – Backend Integration Guide

This guide explains how to prepare the data pipeline, start the API locally, and understand the current behaviour of the v1 endpoints that power the interview analytics dashboard.

## 1. Quick Start

```bash
# 1. Install Python dependencies (pandas/pyarrow/numpy are required for data processing)
pip install -r requirements.txt

# 2. Regenerate datasets (runs dedupe + acceptance-rate imputation + stats precompute)
python cli.py data refresh --force --progress --output detailed

# 3. Start the API server (development settings)
python start_api.py
```

Key notes:
- `data refresh` walks every CSV under `DATA_ROOT_PATH` (see `src/config/settings.py`) and rebuilds:
  - the unified dataset (`.cache/datasets/*.parquet`),
  - the exploded topic dataset,
  - cached company statistics (`.cache/analytics/*.parquet`).
- The refresh step must run after changing loader/processor logic; otherwise the API will serve stale data from the cache.
- First API request after a cold start still incurs a ~3‑5s warm up while caches load into memory.

## 2. Endpoint Status Overview (Oct 2025)

| Category | Endpoint | Status | Typical Response | Notes |
|----------|----------|--------|------------------|-------|
| Health | `/api/v1/health/quick`, `/data`, `/metrics` | ✅ Stable | 20–300 ms | Safe to use for uptime indicators.
| Companies | `/api/v1/companies/stats` | ✅ Stable | 500–900 ms | Supports optional `page`/`page_size`, sorting, timeframe filters. Cached results.
| Companies | `/api/v1/companies/{name}` | ✅ Stable | 400–750 ms | Accepts case-insensitive names; returns enriched breakdowns.
| Problems | `/api/v1/problems/top` | ✅ Stable (heavy) | 1.5–3.0 s | Performs large aggregations; keep `limit≤50` for UI.
| Topics | `/api/v1/topics/trends` | ✅ Stable | 2–3 s | Uses normalised share-of-timeframe slope; returns trend strength + metadata.
| Topics | `/api/v1/topics/frequency` | ✅ Stable | 1–2 s | Falls back to `null` acceptance rates instead of raising.
| Topics | `/api/v1/topics/heatmap` | ✅ Stable | 1–1.5 s | Generates topic × company matrix with totals + metadata.
| Topics | `/api/v1/topics/correlations` | ⚠️ Partial | 2–4 s | Works, but filtering parameters still coarse.
| Analytics | `/api/v1/analytics/correlations` | ⚠️ Slow | 25–35 s on cold cache | Heavy computation; prefetch or queue async.

### Behavioural changes since the October refresh
- **Acceptance-rate imputation**: Missing values are inferred from topic/company peers when possible, otherwise flagged with `acceptance_rate_missing=true`.
- **Duplicate handling**: Unified datasets dedupe on `(title, company, timeframe)`. Response payloads expose `remaining_rows` stats in the CLI output.
- **Empty CSV detection**: Loader reports empty or unreadable files; the last report is available via `DatasetManager.get_last_empty_file_report()` and logged during refresh.
- **Topic trend normalisation**: Trend slopes now operate on percentage share per timeframe bucket, with guardrails for insufficient data (<10 samples per bucket) and a "stable" band.
- **Topic heatmap**: Implemented via `TopicAnalyzer.generate_topic_heatmap`, returning a matrix plus metadata about totals/timeframes.

## 3. Usage Tips for Frontend Integration

- Always kick off the data refresh before running UI integration tests; otherwise `/companies/stats` will complain that `unified_df` is missing.
- Plug pagination controls into `page` and `page_size` (default `page_size=50`, max 1000). Responses include `meta.total`, `meta.total_pages`, and `meta.has_next/has_previous`.
- Topic endpoints share a common structure: `data` array + `meta` object. All new fields use `snake_case`; convert to camelCase client-side if needed.
- Expect 1–3 second latency on topic/problem aggregations. Configure the UI to show slow-loading states after 1 s and timeout messaging around 8 s.
- `/companies/stats` caches the aggregate frame in-memory. To force a refresh (e.g., after editing CSVs) call `python cli.py data refresh --force` and restart the API or hit `/api/v1/system/reload` if exposed.

## 4. Known Gaps & Workarounds

- **Company/topic filters**: Some list endpoints accept filter params that are not yet wired up (they currently return the full cached dataset). Guard the UI with explanatory tooltips when filters are no-ops.
- **Long-tail CSV gaps**: Roughly 900 CSVs are empty. The loader logs them and omits them from downstream stats. Use the empty-file report to prune or backfill data sources.
- **Heavy analytics**: `/analytics/correlations` and `/topics/correlations` still compute on the fly; consider on-demand background jobs or nightly precomputation for production.
- **Environment dependency**: `numpy` and `pandas` rely on native BLAS libraries. If you encounter `Floating point exception: 8` while running CLI commands on macOS sandboxed shells, run the refresh outside the sandbox (e.g., directly on your host terminal) where Accelerate/OpenBLAS is available.

## 5. Verification Checklist

Run this sequence after any backend change:

```bash
python cli.py data refresh --force --progress --output summary
python start_api.py  # in a separate shell

# New shell – smoke tests
curl "http://localhost:8000/api/v1/health/quick"
curl "http://localhost:8000/api/v1/companies/stats?page=1&page_size=25"
curl "http://localhost:8000/api/v1/companies/Google"
curl "http://localhost:8000/api/v1/problems/top?limit=20"
curl "http://localhost:8000/api/v1/topics/trends?limit=20"
curl "http://localhost:8000/api/v1/topics/frequency?limit=50"
curl "http://localhost:8000/api/v1/topics/heatmap?top_topics=15"
```

All of the above should return HTTP 200 with populated `data` arrays and realistic metrics. If any call returns 500, re-run the refresh step with `--force`, inspect `.cache/metadata/*.json` for stale signatures, and review the server logs for the offending CSV or aggregation.

---

With the dataset cache rebuilt and these endpoints behaving consistently, the frontend can safely move beyond mock data and start implementing richer dashboards (Phase 2 onwards).
