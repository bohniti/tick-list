---
status: complete
phase: 01-foundation-schema
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-03-27T11:00:00Z
updated: 2026-03-27T12:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Run `docker compose up -d` to start PostgreSQL+PostGIS. Wait for healthy status. Then run `uv run uvicorn tick_list.api:app --port 8000` — server boots without import errors. `curl http://localhost:8000/health` returns `{"status":"ok"}`.
result: pass
note: Required fix — postgis/postgis:17-3.6 image didn't exist, changed to 17-3.5

### 2. Docker Compose Config Validates
expected: Run `docker compose config` — outputs valid YAML with no errors. Shows postgis/postgis:17-3.5 image, healthcheck with pg_isready, named pgdata volume, and port 5433 exposed in override.
result: pass

### 3. Alembic Migration Runs Against Live DB
expected: With Docker DB running, run `uv run alembic upgrade head`. All tables created without errors. Verify with `docker compose exec db psql -U tick_list -c "\dt"` — shows locations, routes, sessions, ascents, photos tables. Then `uv run alembic downgrade base` completes cleanly.
result: pass
note: Required fix — local PostgreSQL on port 5432 conflicted with Docker, changed to port 5433

### 4. Grade Normalization Spot Check
expected: normalize_to_french('7+', 'uiaa') returns '7a+', grade_to_numeric('7a+') returns 5.7, normalize_to_french('5.10a', 'yds') returns '6b'.
result: pass

### 5. FastMCP Mount Accessible
expected: curl http://localhost:8000/mcp returns a response (not 404). MCP sub-app is mounted and reachable.
result: pass
note: Returns 307 redirect to /mcp/ — mount is active

### 6. Model Tests Pass
expected: uv run pytest tests/test_models.py tests/test_grades.py -v — all 44 tests pass.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
