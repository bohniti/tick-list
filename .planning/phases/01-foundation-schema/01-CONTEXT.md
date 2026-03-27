# Phase 1: Foundation & Schema - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a running PostgreSQL+PostGIS database with all tables, a grade normalization module, and a FastAPI+FastMCP skeleton that boots in Docker Compose. This phase creates the data layer and project structure that all subsequent phases build on.

</domain>

<decisions>
## Implementation Decisions

### Grade Normalization
- **D-01:** Reuse the existing blog's numeric scoring scale from the JS code at `bohniti.github.io`. Port and extend to cover all systems. Ensures historical consistency with existing dataset.
- **D-02:** French is the canonical grade system. Everything converts to French on input. Original grading system stored as metadata, but French is the single grade of record.
- **D-03:** Bouldering grades (Font/V-scale) use a separate numeric scoring axis from route grades (French/UIAA/YDS). No cross-discipline comparison implied.
- **D-04:** Full sub-grade modifier support: handle +, -, / (slash grades like 6a/b meaning "between 6a and 6b"), and optional letter suffixes. Existing dataset uses these — dropping them loses precision.
- **D-05:** Multipitch routes store a single route-level grade (crux/guidebook grade) plus a `pitches` integer field. Ascent logged as one entry. Notes field for per-pitch detail. Pitch-by-pitch logging is out of scope.

### Location Hierarchy
- **D-06:** Location hierarchy: country > area > crag > sector. Country is the top level since climbing spans multiple countries (Austria, Italy, Croatia, Germany, Canada).
- **D-07:** Every level in the hierarchy gets its own PostGIS coordinate point. Enables map zoom levels: country/area pins when zoomed out, crag/sector when zoomed in.
- **D-08:** Claude's Discretion on table design — self-referential single table vs separate tables. (Claude recommended self-referential with parent_id and type enum.)

### Session & Ascent Model
- **D-09:** Partners stored as a text array field on the session. No separate partners table — partners are names mentioned in conversation, purely informational.
- **D-10:** Conditions stored as a freeform text field on the session. No structured weather schema — matches the conversational logging approach.
- **D-11:** Single `style` enum field on ascents (onsight, flash, redpoint, repeat, attempt, toprope, hangdog). Style implies the result (send vs no-send). No separate `result` field.
- **D-12:** Ascents have an optional 1-5 star rating field for personal route quality scores.

### Project Skeleton
- **D-13:** Top-level Python package named `tick_list`. Import as `from tick_list.models import ...`.
- **D-14:** Flat module structure: `tick_list/models.py`, `tick_list/services.py`, `tick_list/api.py`, `tick_list/mcp.py`, `tick_list/grades.py`. Single package, no domain sub-packages.
- **D-15:** Static dashboard files live at `static/` at the project root. Nginx serves this directory directly in production.
- **D-16:** Configuration via Pydantic Settings + `.env` file. DATABASE_URL, API_TOKEN, etc. loaded from environment variables.

### Photo Storage
- **D-17:** Photos stored on the local filesystem in `data/photos/`. Docker volume mount persists across deploys. Nginx serves them directly.
- **D-18:** UUID filenames in a flat directory: `data/photos/{uuid}.jpg`. Photo metadata (original name, type like topo/send) lives in the database.
- **D-19:** Generate thumbnails on upload using Pillow (e.g., 400px wide) alongside the original. Dashboard loads thumbnails in lists, full-size on click.

### Database Conventions
- **D-20:** UUID primary keys on all tables. No sequential integer IDs leaking in API responses.
- **D-21:** Hard deletes — DELETE removes the row. Single-user app, database backups cover accidental deletion.
- **D-22:** All tables have `created_at` (server default NOW) and `updated_at` (auto-updated on change) timestamp columns.

### Testing Approach
- **D-23:** Database tests use testcontainers-python to spin up real PostgreSQL+PostGIS containers. No SQLite substitution — catches migration and spatial query bugs.
- **D-24:** Phase 1 testing priority: grade normalization round-trips (the tricky logic) and Alembic upgrade/downgrade. Skip API endpoint tests until Phase 4.

### Docker Compose Setup
- **D-25:** Single `docker-compose.yml` base config + `docker-compose.override.yml` for dev extras (volume mounts, exposed ports). Production uses only the base file.
- **D-26:** Dev workflow: PostgreSQL+PostGIS runs in Docker, FastAPI app runs locally via `uv run uvicorn`. Connect via localhost:5432. No container rebuild on code changes.

### Claude's Discretion
- Location table design approach (self-referential recommended but Claude has flexibility)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Data & Grade Logic
- `/Users/timo/Development/bohniti.github.io/static/files/dataset.csv` — The 422-route historical dataset with French-normalized grades, GPS coordinates, styles, and sources. Import source for Phase 3, but grade values inform the normalization module design.
- Blog JS code at `bohniti.github.io` — Contains the existing French grade conversion map and numeric scoring system to port.

### Project Configuration
- `CLAUDE.md` — Technology stack decisions, version pins, and project constraints. Defines FastAPI, SQLAlchemy 2.0, GeoAlchemy2, Alembic, asyncpg, FastMCP, and all other dependencies with specific version ranges.

### Requirements
- `.planning/REQUIREMENTS.md` — ROUTE-01, ROUTE-02, ROUTE-04, ROUTE-06, INFRA-02, INFRA-07 are the requirements for this phase.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code — greenfield project. Only `CLAUDE.md` exists in the repo.

### Established Patterns
- No patterns yet. Phase 1 establishes the foundational patterns that all subsequent phases follow.

### Integration Points
- FastAPI app mounts FastMCP as an ASGI sub-app (path TBD by planner)
- Alembic migrations run against the same PostgreSQL instance used by the app
- `data/photos/` directory must be volume-mounted in Docker for persistence

</code_context>

<specifics>
## Specific Ideas

- Port the blog's existing French grade conversion map and numeric scoring — don't reinvent the scale
- The existing CSV dataset has GPS coordinates for 93% of routes (386/416) — location hierarchy should accommodate importing these
- Slash grades (6a/b) are real grades used in European climbing — the normalization module must handle them, not treat them as invalid input

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-schema*
*Context gathered: 2026-03-27*
