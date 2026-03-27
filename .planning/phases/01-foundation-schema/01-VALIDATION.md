---
phase: 1
slug: foundation-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` — Wave 0 creates `[tool.pytest.ini_options]` section |
| **Quick run command** | `uv run pytest tests/test_grades.py -x` |
| **Full suite command** | `uv run pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds (unit), ~30 seconds (with Docker integration tests) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_grades.py -x`
- **After every plan wave:** Run `uv run pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ROUTE-02 | unit | `uv run pytest tests/test_grades.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | ROUTE-02 | unit | `uv run pytest tests/test_grades.py::test_slash_grades -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | ROUTE-02 | unit | `uv run pytest tests/test_grades.py::test_numeric_ordering -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | INFRA-07 | integration | `uv run pytest tests/test_migrations.py::test_upgrade -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | INFRA-07 | integration | `uv run pytest tests/test_migrations.py::test_downgrade -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | INFRA-02 | smoke | `docker compose up --wait` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 1 | ROUTE-01 | unit | `uv run pytest tests/test_models.py -x` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 1 | ROUTE-04 | integration | `uv run pytest tests/test_migrations.py::test_location_insert -x` | ❌ W0 | ⬜ pending |
| 01-04-03 | 04 | 1 | ROUTE-06 | unit | `uv run pytest tests/test_models.py::test_discipline_enum -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — PostGIS testcontainer fixture + async session fixture
- [ ] `tests/test_grades.py` — grade normalization unit tests (no Docker needed)
- [ ] `tests/test_migrations.py` — Alembic upgrade/downgrade + spatial insert tests
- [ ] `tests/test_models.py` — model structure / enum value tests (no Docker needed)
- [ ] `pyproject.toml` — `[tool.pytest.ini_options]` with `asyncio_default_fixture_loop_scope = "function"`

*pytest marks: `@pytest.mark.docker` for integration tests requiring Docker, unmarked for pure Python unit tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose boots cleanly | INFRA-02 | Requires Docker Desktop running | `docker compose up --wait` and verify `docker compose ps` shows healthy |
| FastMCP sub-app mounts without path conflicts | INFRA-02 | Requires running server | `curl http://localhost:8000/health` returns 200 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
