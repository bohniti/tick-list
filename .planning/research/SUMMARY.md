# Project Research Summary

**Project:** Tick List — Climbing Diary (MCP Server + Dashboard)
**Domain:** Personal climbing logbook with LLM-first interaction via MCP
**Researched:** 2026-03-26
**Confidence:** HIGH

## Executive Summary

This project is a personal climbing logbook where the primary interface is natural language conversation with Claude via the Model Context Protocol, backed by a REST API and a static web dashboard. The correct architecture is a single FastAPI + Uvicorn process that mounts a FastMCP sub-application alongside a conventional REST router, with both sharing a common service layer backed by PostgreSQL 17 + PostGIS. The frontend is static HTML/JS/CSS served by Nginx — no build step, no SPA framework. This is a well-understood stack with high-quality documentation, and the implementation risk is low if the foundational layers are built correctly and in the right order.

The recommended build order is strict: database schema and migrations first (with PostGIS properly configured), then grade normalization utilities, then repositories and services, then MCP tools and REST endpoints as parallel thin adapters over the same service layer. The dashboard is built last because it consumes what the API provides. The three-tier route resolution pattern (local DB → OpenBeta → user-confirmed create) is the central business logic and must be built before any logging feature is complete. Grade normalization is the foundational data utility that almost every feature depends on.

The highest risks in this project are not technical complexity but implementation traps: MCP tool count creep (keep under 15, design around user intents not DB entities), grade conversion edge cases (French sub-grades, bouldering vs sport separation, lossy cross-system conversion), GeoAlchemy2 + Alembic migration configuration (requires explicit env.py setup or autogenerate produces broken migrations), and LLM hallucination of route data (must use a search-then-confirm flow with a `source` field to audit created records). All six critical pitfalls are addressable in Phase 1 scaffolding if treated as first-class requirements rather than afterthoughts.

## Key Findings

### Recommended Stack

The stack is Python 3.12+, FastAPI 0.128.x, FastMCP 3.1.x, PostgreSQL 17 + PostGIS 3.6, SQLAlchemy 2.0 async with GeoAlchemy2, and asyncpg as the driver. Project tooling is uv + ruff. The frontend is Alpine.js 3.15, Chart.js 4.5, and Leaflet.js 1.9.4, all loaded from CDN with pinned versions (and vendored for offline/production use). Every technology choice has HIGH confidence based on official sources with verified version numbers.

**Core technologies:**
- **Python 3.12 + uv**: Runtime and package management — fastest toolchain, widest library compat, lockfile support
- **FastAPI 0.128 + FastMCP 3.1**: Web framework + MCP host — async-native, ASGI, FastMCP mounts directly as a sub-app
- **PostgreSQL 17 + PostGIS 3.6**: Storage — required for spatial queries (crags near location, bounding box searches)
- **SQLAlchemy 2.0 async + GeoAlchemy2**: ORM + spatial column types — 2.0-style `Mapped[]` annotations, async engine
- **asyncpg 0.31**: Database driver — 5x faster than psycopg3 for async; required for SQLAlchemy async engine
- **Alembic 1.18**: Migrations — only migration tool for SQLAlchemy; requires PostGIS-specific env.py configuration
- **Alpine.js 3.15 + Chart.js 4.5 + Leaflet 1.9.4**: Dashboard frontend — no build step, CDN delivery, sufficient for all needed interactivity
- **Nginx + Let's Encrypt**: Reverse proxy + TLS — serves static dashboard directly, proxies /api and /mcp to Uvicorn

**Critical version notes:**
- Use Leaflet **1.9.4 stable**, not 2.0 alpha (plugin ecosystem incompatible)
- Use SQLAlchemy **2.0.x** stable, not 2.1 beta
- Docker image: `postgis/postgis:17-bookworm-postgis-3.6` (not `latest`)

### Expected Features

**Must have (table stakes) — v1:**
- Ascent logging with route, grade, date, and style (onsight/flash/redpoint/pinkpoint/toprope/attempt) — core product
- Session grouping (date + crag + optional partner + notes) — how climbers think
- Grade normalization across French, UIAA, YDS, Font, V-scale with numeric scoring — foundational for all stats
- Grade pyramid visualization stacked by ascent style — the single most-requested climbing statistic
- Route and crag database with three-tier resolution (local DB → OpenBeta → Claude-created) — enables meaningful logging
- CSV import for 422-route historical dataset — immediate data for dashboard from day one
- Bearer token auth on all endpoints — single-user but exposed to internet
- Docker Compose deployment

**Should have (differentiators) — v1.x:**
- Natural language logging via Claude MCP tools — the core value proposition; depends on data layer being solid
- Crag map with Leaflet + PostGIS spatial queries — after crags have coordinates
- Progression charts (max grade over time, volume trends) — after sufficient logged data exists
- Photo attachment to sessions and ascents
- OpenBeta route enrichment
- Conversational querying via MCP read tools
- CSV export; multi-grade-system toggle on dashboard

**Defer (v2+):**
- Topo image analysis via Claude Vision — high complexity, needs solid photo storage first
- Session narrative generation — low effort but not essential for validation
- Smart route suggestion from context — needs well-populated route database first

**Anti-features (never build):**
- Social features, rankings, leaderboards — single-user tool, wrong scope
- Native mobile app, training plans, indoor gym integration — different products

### Architecture Approach

The architecture is a single ASGI process: FastAPI hosts the REST API at `/api/v1/*` and mounts a FastMCP sub-application at `/mcp`. Both are thin adapters over a shared service layer (SessionService, AscentService, RouteService, GradeService, StatsService). Services call repositories, repositories call the async SQLAlchemy engine backed by asyncpg. Nginx sits in front for TLS termination, static file serving (dashboard), and SSE-friendly proxying (`proxy_buffering off` on `/mcp`). The single most important architectural constraint: no business logic in MCP tools or REST handlers — both are five-line adapters that call service methods.

**Major components:**
1. **Nginx** — TLS termination, static dashboard files, reverse proxy with SSE support for MCP
2. **FastAPI + FastMCP (single process)** — ASGI host; MCP tools and REST endpoints as thin adapters over services
3. **Service Layer** — all business logic: grade normalization, three-tier route resolution, session validation, stats aggregation
4. **Repository Layer** — data access: SQLAlchemy 2.0 async ORM, GeoAlchemy2 spatial queries
5. **PostgreSQL 17 + PostGIS 3.6** — persistent storage with spatial indexes on crag geometry columns
6. **Dashboard (static)** — Alpine.js + Chart.js + Leaflet, fetches from `/api/v1/`, served directly by Nginx

### Critical Pitfalls

1. **MCP tool explosion** — Keep tool count under 15; design around user intents (log_climbing_session, resolve_route, query_stats) not DB entities. Tool selection degrades significantly above 30 tools. Address in Phase 1 before writing any tool code.

2. **Grade conversion as flat lookup table** — Use a numeric scoring system as canonical internal representation; store original grade + system alongside score; never discard the original; separate sport/trad from bouldering grades entirely. Address in Phase 1 before CSV import.

3. **GeoAlchemy2 + Alembic broken migrations** — Configure GeoAlchemy2 Alembic helpers in `env.py` (include_object filter, render_item, process_revision_directives); always review autogenerated migrations; test `alembic upgrade head` + `alembic downgrade base` in CI against empty DB. Address in Phase 1 before first migration is committed.

4. **LLM silently inventing route data** — Implement search-then-confirm flow: Claude must call resolve_route before log_session; tool descriptions must explicitly instruct against fabrication; mark conversation-created routes with `source` field for later auditing. Address in Phase 2 during route resolution implementation.

5. **FastMCP mount path doubling and CORS conflicts** — Mount FastMCP carefully and test actual resulting paths with MCP Inspector; use combine_lifespans to merge FastAPI and FastMCP lifespans; do not add global CORSMiddleware that intercepts sub-app routes. Address in Phase 1 project skeleton.

6. **Async/sync mismatch in DB layer** — Use create_async_engine + async_sessionmaker + asyncpg from day one; no sync SQLAlchemy in a single-process async architecture; no run_sync wrappers. Address in Phase 1 before any feature work.

## Implications for Roadmap

Architecture research defines a clear five-phase build order driven by dependency constraints. The service layer is the linchpin — nothing else works until it exists.

### Phase 1: Foundation — Database, Schema, and Core Infrastructure

**Rationale:** Everything depends on the database layer existing and being correctly configured. Grade normalization is a dependency of CSV import, route creation, and all visualizations. FastAPI + FastMCP skeleton must be proven before adding any tools or endpoints. Six of the eight critical pitfalls are preventable only in this phase.

**Delivers:** Working PostgreSQL + PostGIS in Docker Compose; all SQLAlchemy models (sessions, ascents, routes, crags); Alembic migrations with PostGIS properly configured; async database session factory; FastAPI + FastMCP skeleton with combined lifespans; grade normalization module with numeric scoring for all grade systems; bearer token auth; project structure with models/repositories/services/api/mcp directories.

**Addresses:** Grade normalization (table stakes), crag/location management (foundation for everything), Docker Compose deployment

**Avoids:** GeoAlchemy2+Alembic broken migrations, async/sync mismatch, FastMCP mount path issues, grade conversion as flat lookup table

**Research flag:** None needed — all patterns are well-documented in official sources.

### Phase 2: Data Layer — Repositories, Services, and CSV Import

**Rationale:** Services are the shared core consumed by both MCP and REST. The CSV import provides the 422-route historical dataset that makes the dashboard immediately useful. Building services before any interface layer enforces the architectural constraint that there is one source of truth for business logic.

**Delivers:** All repository classes (SessionRepo, AscentRepo, RouteRepo, CragRepo) with async SQLAlchemy queries; all service classes (SessionService, AscentService, RouteService with three-tier resolution, GradeService, StatsService); OpenBeta GraphQL client with timeout and graceful fallback; CSV import script for 422-route historical dataset with idempotency.

**Addresses:** Three-tier route resolution, OpenBeta integration, historical data import

**Avoids:** LLM hallucination of route data (resolve_route separation), N+1 queries (selectinload in repos), SQL injection (parameterized queries only)

**Research flag:** OpenBeta GraphQL API may need phase-specific research — EU crag data is described as sparse, and the API schema should be verified before building the client.

### Phase 3a: MCP Server — Logging Tools

**Rationale:** MCP tools are thin adapters over Phase 2 services. Can be built in parallel with Phase 3b (REST + dashboard) once services exist. MCP is the primary differentiator and should be validated early. Tool interface design must be locked before implementation.

**Delivers:** FastMCP server with 8-12 task-oriented tools: log_climbing_session (full session + ascents in one tool), resolve_route (search-then-confirm, never fabricate), get_stats, search_crags, manage_photos; MCP Inspector validation; Claude Desktop integration test.

**Addresses:** Natural language logging (core differentiator), conversational querying

**Avoids:** MCP tool explosion (strict count limit, user-intent design), bearer token leakage in tool responses

**Research flag:** May benefit from a brief research pass on FastMCP 3.1 tool parameter schema patterns and session state management — FastMCP 3.x is relatively new and community examples are sparse.

### Phase 3b: REST API and Dashboard

**Rationale:** REST endpoints are thin adapters over the same Phase 2 services. Dashboard is static files consuming the REST API. Can be built in parallel with Phase 3a.

**Delivers:** REST API at `/api/v1/` (sessions, ascents, routes, crags, stats endpoints); static dashboard with grade pyramid (Chart.js stacked bar by ascent style), session timeline, basic stats; Leaflet crag map with PostGIS bounding-box queries; Nginx config for static serving + proxy + SSE; progression charts.

**Addresses:** Grade pyramid visualization, session timeline, crag map, progression over time

**Avoids:** Returning raw ORM objects (always use Pydantic response schemas), building a frontend build pipeline (CDN + vendor only), loading all chart data on page load (lazy-load per tab)

**Research flag:** None needed — Chart.js, Leaflet, and FastAPI router patterns are well-documented.

### Phase 4: Enrichment and Polish

**Rationale:** Photo attachment, CSV export, multi-grade-system toggle, and session narrative generation are all v1.x enhancements that require the core product to be working and validated first. OpenBeta integration is partially built in Phase 2 (client + three-tier resolution); this phase completes the UI surface for it.

**Delivers:** Photo attachment to sessions and ascents (Pillow for resize/thumbnail, Nginx for serving); CSV export endpoint; multi-grade-system display toggle on dashboard; session narrative generation via MCP read tools; route `source` field auditing UI on dashboard.

**Addresses:** Data export (GDPR expectation), photo attachment, multi-grade display

**Avoids:** None new — polish phase

**Research flag:** None needed.

### Phase 5: Deployment and CI/CD

**Rationale:** Deployment hardening should come last once the application is feature-complete. Setting up CI/CD on a moving codebase adds friction without benefit.

**Delivers:** Production Dockerfile; docker-compose.yml with named volumes (not bind mounts); Nginx TLS config with Let's Encrypt certbot; GitHub Actions CI (ruff lint, pytest, Docker build, deploy on main); rate limiting at Nginx layer; environment-based secrets management.

**Addresses:** Docker Compose deployment (production-ready), bearer token security (env vars, not hardcoded)

**Avoids:** Hardcoded credentials in Docker Compose or git history

**Research flag:** None needed — standard patterns.

### Phase Ordering Rationale

- **Foundation before services, services before interfaces:** The architecture.md build order is clear. Models/schema must exist before repositories. Repositories before services. Services before MCP tools and REST endpoints. This is not optional — the dependency chain is hard.
- **Grade normalization in Phase 1, not Phase 2:** Grade normalization is a dependency of CSV import (Phase 2). If it's built in Phase 2, CSV import must wait. Building it in Phase 1 with the schema means Phase 2 can proceed without blocking.
- **MCP and REST in parallel (Phase 3a/3b):** Both consume services; neither depends on the other. Parallel development is safe and faster.
- **Import in Phase 2, not Phase 4:** Historical data makes the dashboard immediately useful. The 422-route dataset should be importable by end of Phase 2 so the dashboard has real data to visualize from first run.
- **Deployment last:** No benefit to production deployment until features are validated. Development stays in Docker Compose until Phase 5.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (OpenBeta integration):** OpenBeta GraphQL API schema and EU data coverage should be verified before building the client — EU crag data is described as sparse in feature research, which affects the value of the three-tier resolution flow.
- **Phase 3a (FastMCP 3.1 patterns):** FastMCP 3.x is the current major version but community examples are still catching up. The combine_lifespans pattern and session state management in tools should be verified against the current 3.1.x docs before implementation.

Phases with standard patterns (skip research-phase):
- **Phase 1:** PostgreSQL + PostGIS + SQLAlchemy async + Alembic are all mature, well-documented technologies. Pitfalls are known and preventable.
- **Phase 3b:** Chart.js, Leaflet, and FastAPI REST routers are extremely well-documented. No novel integration challenges.
- **Phase 4:** All enrichment features follow patterns established in prior phases.
- **Phase 5:** Docker, Nginx, GitHub Actions, Let's Encrypt are standard patterns with no project-specific complexity.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified with official PyPI/GitHub/Docker Hub sources and exact version numbers confirmed. No speculative recommendations. |
| Features | HIGH | Based on direct analysis of competitors (TheCrag, 8a.nu/Vertical Life, Mountain Project) and climbing app review sources. Feature prioritization grounded in product value, not assumption. |
| Architecture | HIGH | Patterns verified against official FastMCP docs, FastAPI best practices, SQLAlchemy 2.0 async documentation. The combine_lifespans and shared service layer patterns are explicitly documented. |
| Pitfalls | HIGH | Most pitfalls verified across multiple independent sources. MCP tool count thresholds are from AWS prescriptive guidance and Speakeasy research. GeoAlchemy2+Alembic issues are documented in official GeoAlchemy2 docs. |

**Overall confidence:** HIGH

### Gaps to Address

- **OpenBeta EU data coverage:** The research notes EU crag data in OpenBeta is sparse. The three-tier resolution design assumes OpenBeta will provide some value for a primarily European climber. This should be validated early in Phase 2 by querying a few known EU crags against the live API before building the full client. If data is too sparse, the resolution logic simplifies to local DB → user-confirmed create, which is still valid.

- **Grade normalization edge cases for specific target crags:** The research defines the approach correctly (numeric scoring, separate sport/boulder, store original). The actual conversion table values for UIAA sub-grades and the boundary cases (where UIAA VII maps in the French system) should be validated against the existing blog JavaScript code noted in PROJECT.md, which has already solved some of these mappings.

- **FastMCP 3.1 tool session context:** The architecture calls for MCP tools to get database sessions via the shared async session factory. The exact mechanism for injecting application state (like the session factory) into FastMCP tool handlers in the 3.1.x API should be verified during Phase 3a planning — the pattern exists but the API surface may differ from FastAPI's Depends() approach.

## Sources

### Primary (HIGH confidence)
- [FastMCP PyPI + 3.0 GA announcement](https://pypi.org/project/fastmcp/) — v3.1.1, MCP server framework
- [FastMCP + FastAPI Integration docs](https://gofastmcp.com/integrations/fastapi) — mount path, CORS, lifespan patterns
- [FastMCP HTTP Deployment docs](https://gofastmcp.com/deployment/http) — SSE transport, Nginx config, production patterns
- [FastAPI PyPI](https://pypi.org/project/fastapi/) — v0.128.x
- [SQLAlchemy releases](https://github.com/sqlalchemy/sqlalchemy/releases) — v2.0.48, async patterns
- [GeoAlchemy2 docs](https://geoalchemy-2.readthedocs.io/) — v0.18.4, Alembic integration, migration helpers
- [Alembic docs](https://alembic.sqlalchemy.org/en/latest/) — v1.18.4
- [asyncpg PyPI](https://pypi.org/project/asyncpg/) — v0.31.0
- [Pydantic releases](https://github.com/pydantic/pydantic/releases) — v2.12.5
- [postgis/postgis Docker Hub](https://hub.docker.com/r/postgis/postgis) — PG17+PostGIS 3.6 image
- [Leaflet.js download](https://leafletjs.com/download.html) — v1.9.4 stable
- [Alpine.js GitHub](https://github.com/alpinejs/alpine/releases) — v3.15.x
- [Chart.js npm](https://www.npmjs.com/package/chart.js) — v4.5.1

### Secondary (MEDIUM confidence)
- [TheCrag logbook/ticking/grades/import/export docs](https://www.thecrag.com/en/article/ticking) — feature benchmarking
- [8a.nu / Vertical Life](https://www.8a.nu/) — competitor feature analysis
- [Mountain Project tick pyramid discussion](https://www.mountainproject.com/forum/topic/114054803) — grade pyramid as missing feature
- [AWS MCP Tool Design Strategy](https://docs.aws.amazon.com/prescriptive-guidance/latest/mcp-strategies/mcp-tool-strategy.html) — tool granularity guidelines
- [Speakeasy: Less is More for MCP](https://www.speakeasy.com/mcp/tool-design/less-is-more) — tool count thresholds
- [FastAPI Layered Architecture with DI](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo) — service + repository pattern
- [Cleanlab: LLM Structured Output Benchmarks](https://cleanlab.ai/blog/structured-output-benchmark/) — hallucination in structured extraction

### Tertiary (LOW confidence)
- [Jentic: The MCP Tool Trap](https://jentic.com/blog/the-mcp-tool-trap) — tool overload consequences (single source, but consistent with AWS guidance)

---
*Research completed: 2026-03-26*
*Ready for roadmap: yes*
