# Phase 1: Foundation & Schema - Research

**Researched:** 2026-03-27
**Domain:** FastAPI + FastMCP skeleton, SQLAlchemy 2.0 async models, GeoAlchemy2 PostGIS, Alembic migrations, grade normalization
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Grade Normalization**
- D-01: Reuse the existing blog's numeric scoring scale from the JS code at `bohniti.github.io`. Port and extend to cover all systems. Ensures historical consistency with existing dataset.
- D-02: French is the canonical grade system. Everything converts to French on input. Original grading system stored as metadata, but French is the single grade of record.
- D-03: Bouldering grades (Font/V-scale) use a separate numeric scoring axis from route grades (French/UIAA/YDS). No cross-discipline comparison implied.
- D-04: Full sub-grade modifier support: handle +, -, / (slash grades like 6a/b meaning "between 6a and 6b"), and optional letter suffixes. Existing dataset uses these — dropping them loses precision.
- D-05: Multipitch routes store a single route-level grade (crux/guidebook grade) plus a `pitches` integer field. Ascent logged as one entry. Notes field for per-pitch detail. Pitch-by-pitch logging is out of scope.

**Location Hierarchy**
- D-06: Location hierarchy: country > area > crag > sector. Country is the top level since climbing spans multiple countries (Austria, Italy, Croatia, Germany, Canada).
- D-07: Every level in the hierarchy gets its own PostGIS coordinate point. Enables map zoom levels: country/area pins when zoomed out, crag/sector when zoomed in.
- D-08: Claude's Discretion on table design — self-referential single table vs separate tables. (Claude recommended self-referential with parent_id and type enum.)

**Session & Ascent Model**
- D-09: Partners stored as a text array field on the session. No separate partners table.
- D-10: Conditions stored as a freeform text field on the session.
- D-11: Single `style` enum field on ascents (onsight, flash, redpoint, repeat, attempt, toprope, hangdog). Style implies the result (send vs no-send). No separate `result` field.
- D-12: Ascents have an optional 1-5 star rating field for personal route quality scores.

**Project Skeleton**
- D-13: Top-level Python package named `tick_list`. Import as `from tick_list.models import ...`.
- D-14: Flat module structure: `tick_list/models.py`, `tick_list/services.py`, `tick_list/api.py`, `tick_list/mcp.py`, `tick_list/grades.py`. Single package, no domain sub-packages.
- D-15: Static dashboard files live at `static/` at the project root.
- D-16: Configuration via Pydantic Settings + `.env` file. DATABASE_URL, API_TOKEN, etc.

**Photo Storage**
- D-17: Photos stored at `data/photos/`. Docker volume mount persists across deploys.
- D-18: UUID filenames in flat directory: `data/photos/{uuid}.jpg`.
- D-19: Generate thumbnails on upload using Pillow (400px wide).

**Database Conventions**
- D-20: UUID primary keys on all tables. No sequential integer IDs.
- D-21: Hard deletes — DELETE removes the row.
- D-22: All tables have `created_at` (server default NOW) and `updated_at` (auto-updated on change).

**Testing Approach**
- D-23: Database tests use testcontainers-python to spin up real PostgreSQL+PostGIS containers.
- D-24: Phase 1 testing priority: grade normalization round-trips and Alembic upgrade/downgrade. Skip API endpoint tests until Phase 4.

**Docker Compose Setup**
- D-25: Single `docker-compose.yml` base config + `docker-compose.override.yml` for dev extras.
- D-26: Dev workflow: PostgreSQL+PostGIS runs in Docker, FastAPI app runs locally via `uv run uvicorn`.

### Claude's Discretion
- Location table design approach (self-referential recommended but Claude has flexibility)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ROUTE-01 | Routes stored in local PostgreSQL with name, grade, discipline, location, pitches | SQLAlchemy 2.0 Mapped[] declarative, UUID PKs, GeoAlchemy2 for location FK |
| ROUTE-02 | Grade normalization across French, UIAA, YDS, Font, V-scale with numeric scoring | Blog JS gradeMap ported to Python; existing dataset defines exact UIAA-to-French mapping |
| ROUTE-04 | Locations stored hierarchically (area > crag > sector) with PostGIS coordinates | Self-referential location table with GeoAlchemy2 Geometry(POINT) and parent_id FK |
| ROUTE-06 | Disciplines supported: sport, trad, boulder, multipitch, ice, mixed | Python Enum via SQLAlchemy Enum type |
| INFRA-02 | Docker Compose deployment: PostgreSQL 17 + PostGIS + FastAPI + Nginx | postgis/postgis:17-3.6 image; dev override pattern confirmed |
| INFRA-07 | SQLAlchemy 2.0 async models + Alembic migrations with GeoAlchemy2 | Verified: alembic init -t async, GeoAlchemy2 alembic_helpers in env.py |
</phase_requirements>

---

## Summary

Phase 1 establishes the complete data layer and project skeleton. All technology choices are locked in CLAUDE.md and CONTEXT.md — research confirms they are sound and provides the specific patterns needed to implement them correctly.

The three technically tricky areas are: (1) grade normalization — the existing blog's JS `gradeMap` and `convert_to_french_fixed.py` define the exact UIAA-to-French mapping to port; the dataset contains 415 real ascents with only UIAA and YDS grades, no Font/V-scale; (2) Alembic + GeoAlchemy2 async setup — requires GeoAlchemy2 `alembic_helpers` in `env.py` and `alembic init -t async` to get the async env.py template; (3) FastMCP mounting into FastAPI — requires passing `lifespan=mcp_app.lifespan` to the FastAPI constructor to avoid session manager failures.

Docker Desktop is installed (`/Applications/Docker.app`) but not currently running. Testcontainers will require Docker running at test time. The dev workflow (D-26) keeps app code outside Docker so this is not a blocker for local development, only for running database tests.

**Primary recommendation:** Bootstrap with `uv init`, use `alembic init -t async` for the migration environment, configure GeoAlchemy2 alembic_helpers in env.py, mount FastMCP with lifespan handoff, and implement `tick_list/grades.py` as a pure-Python module porting the existing blog mappings.

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 1 |
|-----------|-------------------|
| Single process: MCP + API share one FastAPI process | FastMCP mounts as ASGI sub-app into the FastAPI app (not separate process) |
| No build step for frontend | `static/` directory created but no tooling; out of scope this phase |
| Python 3.12+ | Specify `requires-python = ">=3.12"` in pyproject.toml; system Python is 3.9 so uv manages the runtime |
| uv as package manager | `uv init` + `uv add`; no pip/venv directly |
| ruff for lint + format | Add as dev dependency; configure in pyproject.toml |
| FastAPI `>=0.128,<1` | Resolves to 0.135.2 currently |
| SQLAlchemy 2.0.48 | Use exactly; 2.1 beta explicitly excluded |
| asyncpg for async PG driver | Required by SQLAlchemy async engine |
| Docker pin: `postgis/postgis:17-bookworm-postgis-3.6` | Use this exact tag, not `latest` |
| Leaflet 1.9.4 (not 2.0 alpha) | Out of scope this phase |
| No Redis, no Celery, no SQLite | Not applicable to Phase 1 |

---

## Standard Stack

### Core
| Library | Version (verified) | Purpose | Why Standard |
|---------|-------------------|---------|--------------|
| Python | 3.12 (via uv) | Runtime | System is 3.9; uv manages the project runtime independently |
| uv | 0.8.14 (installed), 0.11.2 (latest) | Package manager | Installed and working; 0.8.x vs 0.11.x: both are compatible for this use case |
| FastAPI | 0.135.2 (latest) | Web framework | CLAUDE.md pin `>=0.128,<1` resolves here |
| FastMCP | 3.1.1 | MCP server | Mounts as ASGI sub-app into FastAPI |
| SQLAlchemy | 2.0.48 | ORM | Locked at exactly this version in CLAUDE.md |
| GeoAlchemy2 | 0.18.4 | PostGIS types | Geometry/Geography column support |
| Alembic | 1.18.4 | Migrations | Async template; GeoAlchemy2 helpers |
| asyncpg | 0.31.0 | PG async driver | Required by SQLAlchemy async engine |
| Pydantic | 2.12.5 | Validation/settings | V2 core; used for Settings class |
| pydantic-settings | 2.13.1 | .env file loading | Separate package from Pydantic V2 |
| Uvicorn | 0.42.0 | ASGI server | Install with `[standard]` extra |

### Dev / Testing
| Library | Version (verified) | Purpose | When to Use |
|---------|-------------------|---------|-------------|
| pytest | 8.4.2 (installed) | Test runner | Already installed system-wide; add to dev deps |
| pytest-asyncio | 1.3.0 | Async test support | Required for async DB tests |
| testcontainers[postgres] | 4.14.2 | Real PostGIS containers | Grade roundtrip + migration tests (requires Docker running) |
| ruff | latest | Lint + format | replaces flake8+black+isort |

### Installation

```bash
# Initialize project
uv init tick-list --python 3.12
cd tick-list

# Core runtime dependencies
uv add fastapi uvicorn[standard] fastmcp sqlalchemy==2.0.48 geoalchemy2 \
    alembic asyncpg pydantic-settings

# Dev dependencies
uv add --dev pytest pytest-asyncio "testcontainers[postgres]" ruff
```

**Version verification:** Versions above confirmed against PyPI on 2026-03-27.

---

## Architecture Patterns

### Recommended Project Structure
```
tick-list/
├── tick_list/              # Main Python package (D-13, D-14)
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy ORM models
│   ├── grades.py           # Grade normalization module
│   ├── services.py         # Business logic (stub in Phase 1)
│   ├── api.py              # FastAPI routes (health endpoint)
│   ├── mcp.py              # FastMCP server definition (stub in Phase 1)
│   └── config.py           # Pydantic Settings
├── alembic/                # Alembic migration environment
│   ├── env.py              # Async env with GeoAlchemy2 helpers
│   └── versions/           # Migration scripts
├── alembic.ini
├── static/                 # Dashboard static files (D-15, empty dir)
├── data/
│   └── photos/             # Photo storage (D-17, D-18, Docker volume)
├── tests/
│   ├── conftest.py         # PostGIS container fixture
│   ├── test_grades.py      # Grade normalization tests
│   └── test_migrations.py  # Alembic upgrade/downgrade test
├── docker-compose.yml      # Base: PostgreSQL+PostGIS (D-25)
├── docker-compose.override.yml  # Dev: expose ports, volume mounts
├── pyproject.toml          # uv project config, ruff config, pytest config
├── .env.example
└── CLAUDE.md
```

### Pattern 1: SQLAlchemy 2.0 Mapped[] with GeoAlchemy2

```python
# Source: GeoAlchemy2 0.18.0 docs + SQLAlchemy 2.0 declarative docs
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry, WKBElement

class Base(DeclarativeBase):
    pass

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str]  # "country", "area", "crag", "sector"
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    coordinates: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Self-referential (D-08)
    parent: Mapped["Location | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Location"]] = relationship(back_populates="parent")
```

### Pattern 2: Async SQLAlchemy Engine Setup

```python
# Source: SQLAlchemy 2.0 async docs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://user:pass@host/db
    echo=False,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### Pattern 3: FastMCP Mounted into FastAPI

```python
# Source: https://gofastmcp.com/integrations/fastapi.md
from fastapi import FastAPI
from fastmcp import FastMCP

mcp = FastMCP(name="tick-list")
mcp_app = mcp.http_app(path="/")

app = FastAPI(lifespan=mcp_app.lifespan)  # CRITICAL: pass lifespan
app.mount("/mcp", mcp_app)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**WARNING:** Omitting `lifespan=mcp_app.lifespan` causes FastMCP session manager initialization failures. This is the most common mounting mistake.

### Pattern 4: Alembic Async env.py with GeoAlchemy2

Initialize with the async template:
```bash
alembic init -t async alembic
```

Then configure `alembic/env.py` to include GeoAlchemy2 helpers:

```python
# Source: GeoAlchemy2 0.18.x alembic docs + Alembic async template
from geoalchemy2 import alembic_helpers
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool
import asyncio

# In context.configure() calls, add these three parameters:
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    include_object=alembic_helpers.include_object,
    process_revision_directives=alembic_helpers.writer,
    render_item=alembic_helpers.render_item,
)
```

**Known pitfall:** Autogenerated migrations for PostGIS geometry columns will include duplicate `create_index` statements. Remove the spatial index creation from the upgrade() function — PostGIS creates it automatically during `AddGeometryColumn`.

### Pattern 5: Pydantic Settings

```python
# Source: pydantic-settings 2.x docs
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://tick_list:secret@localhost:5432/tick_list"
    api_token: str = "changeme"
    environment: str = "development"

settings = Settings()
```

### Pattern 6: Grade Normalization Module

The existing blog defines two grade mapping structures to port:

**UIAA numeric to French** (from `convert_to_french_fixed.py` + dataset evidence):
```python
# Source: bohniti.github.io/convert_to_french_fixed.py + dataset.csv analysis
UIAA_TO_FRENCH: dict[str, str] = {
    "4": "5a", "4+": "5b",
    "5-": "5c", "5": "6a", "5+": "6a+",
    "6-": "6b", "6": "6b+", "6+": "6c",
    "7-": "6c+", "7": "7a", "7+": "7a+",
    "8-": "7b", "8": "7b+", "8+": "7c",
    "9-": "7c+", "9": "8a", "9+": "8a+",
    # Slash grades from actual dataset
    "7+/8-": "7a+", "8+/9-": "7c+", "6/6+": "6b+", "7/7+": "7a",
}
```

**YDS to French** (from convert_to_french_fixed.py + dataset evidence):
```python
YDS_TO_FRENCH: dict[str, str] = {
    "5.6": "5b", "5.7": "5c", "5.8": "6a", "5.9": "6a+",
    "5.10a": "6b", "5.10b": "6b+", "5.10c": "6c", "5.10d": "6c+",
    "5.11a": "7a", "5.11b": "7a+", "5.11c": "7b", "5.11d": "7b+",
    "5.12a": "7c", "5.12b": "7c+", "5.12c": "8a", "5.12d": "8a+",
    "5.13a": "8b", "5.13b": "8b+", "5.13c": "8c", "5.13d": "8c+",
    "5.14a": "9a", "5.14b": "9a+",
}
```

**French numeric scoring** (from `climbing-locations.js` gradeMap, adapted to French):
```python
# Source: bohniti.github.io/static/files/climbing-locations.js
# The blog's gradeMap uses UIAA notation — re-anchor the same scale to French grades
FRENCH_NUMERIC: dict[str, float] = {
    "4a": 1.0, "4b": 1.5, "4c": 2.0,
    "5a": 2.5, "5a+": 2.7, "5b": 3.0, "5b+": 3.2, "5c": 3.5, "5c+": 3.7,
    "6a": 4.0, "6a+": 4.3, "6b": 4.5, "6b+": 4.7, "6c": 5.0, "6c+": 5.3,
    "7a": 5.5, "7a+": 5.7, "7b": 6.0, "7b+": 6.3, "7c": 6.5, "7c+": 6.7,
    "8a": 7.0, "8a+": 7.3, "8b": 7.5, "8b+": 7.7, "8c": 8.0, "8c+": 8.3,
    "9a": 9.0, "9a+": 9.5,
}
```

**Note:** The existing dataset has NO Font or V-scale bouldering grades — all boulder entries use French grades. D-03 specifies a separate scoring axis for bouldering, but Phase 1 only needs to declare the structure; actual Font/V-scale entries will come from future logging. Include stub mapping tables but they won't be validated against real data until later.

### Anti-Patterns to Avoid

- **SQLite for tests:** D-23 explicitly prohibits it. SQLite does not support PostGIS geometry columns; migration tests would silently pass on wrong schema.
- **Sequential integer IDs:** D-20 mandates UUID PKs on all tables. Leaking row counts via `/routes/423` violates single-user privacy model.
- **Storing only French grade:** D-02 says French is canonical but `grade_original` metadata must also be stored. Dropping the original loses the UIAA/YDS source grade permanently.
- **Separate UIAA/YDS/Font columns on routes:** Don't add a column per grade system. Store `grade_french` (canonical) + `grade_original` (raw input string) + `grade_system` (enum: french/uiaa/yds/font/vscale). Normalize on write.
- **Forgetting `expire_on_commit=False` on AsyncSession:** In async SQLAlchemy, accessing lazy-loaded attributes after commit raises `MissingGreenlet`. Set this on the session factory.
- **Missing lifespan handoff in FastAPI+FastMCP:** Covered in Pattern 3 above. Not passing `lifespan=mcp_app.lifespan` causes runtime failures.
- **Spatial index duplication in Alembic autogenerate:** GeoAlchemy2 autogenerates duplicate index DDL. Remove the `op.create_index` for geometry columns — PostGIS handles this.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database schema migration | Custom ALTER TABLE scripts | Alembic | Handles upgrade/downgrade, conflict detection, autogenerate from models |
| PostGIS geometry column types | Raw DDL in migration | GeoAlchemy2 + alembic_helpers | Handles AddGeometryColumn, DropGeometryColumn, SRID enforcement |
| Async DB connection pool | Manual asyncpg pool | SQLAlchemy `create_async_engine` | Pool management, connection lifecycle, transaction semantics |
| Settings from env | `os.getenv()` everywhere | `pydantic-settings BaseSettings` | Type coercion, .env file, validation, IDE support |
| MCP protocol implementation | Custom JSON-RPC | FastMCP | Protocol compliance, tool schema generation, session management |
| UUID generation | `str(uuid.uuid4())` | `UUID(as_uuid=True), default=uuid.uuid4` | Native UUID type in Postgres, efficient indexing, no string conversion |

**Key insight:** The PostGIS migration lifecycle (create extension, add geometry column, create spatial index) has enough DDL subtlety that hand-rolling it causes silent failures. GeoAlchemy2's alembic_helpers exist precisely because raw autogenerate produces broken migrations.

---

## Common Pitfalls

### Pitfall 1: Docker Not Running for Testcontainers
**What goes wrong:** `testcontainers` raises `DockerException: Error while fetching server API version` or similar.
**Why it happens:** Docker Desktop is installed but not launched. The socket at `/Users/timo/.docker/run/docker.sock` only exists when Docker Desktop is running.
**How to avoid:** Document in README that Docker must be running before `pytest`. Grade normalization tests are pure Python and don't need Docker — separate them from DB tests using pytest marks (`@pytest.mark.requires_docker`).
**Warning signs:** Tests fail immediately on import with Docker connection error, not a test assertion.

### Pitfall 2: Alembic Async Event Loop Conflict
**What goes wrong:** Running `alembic upgrade head` inside a running FastAPI app (e.g., on startup) raises `RuntimeError: This event loop is already running`.
**Why it happens:** Alembic's async template uses `asyncio.run()` which can't be called inside an existing event loop.
**How to avoid:** Run migrations as a separate CLI step before starting the app, not in the FastAPI lifespan. For dev: `uv run alembic upgrade head` then `uv run uvicorn ...`.
**Warning signs:** Only manifests if migrations are wired into `@app.on_event("startup")` — don't do that.

### Pitfall 3: GeoAlchemy2 Autogenerate Index Duplication
**What goes wrong:** `alembic upgrade head` fails with `relation "idx_locations_coordinates" already exists`.
**Why it happens:** `--autogenerate` produces `op.create_index("idx_...", ...)` for geometry columns, but PostGIS already created a GIST index during `AddGeometryColumn`.
**How to avoid:** After generating a migration with geometry columns, review the `upgrade()` function and remove any `op.create_index` calls for geometry columns. Keep the `op.drop_index` in `downgrade()` for cleanliness, or remove both.
**Warning signs:** Migration succeeds on first run (fresh DB) but fails on retry/CI.

### Pitfall 4: `WKBElement` vs `str` in Mapped[] type annotation
**What goes wrong:** Type checker errors or runtime failures when reading geometry back from DB.
**Why it happens:** GeoAlchemy2 returns `WKBElement` objects from DB reads, not plain strings or geometry objects.
**How to avoid:** Annotate geometry columns as `Mapped[WKBElement | None]` (nullable) or `Mapped[WKBElement]` (required). Import `WKBElement` from `geoalchemy2`. When inserting, pass `WKTElement("POINT(lng lat)", srid=4326)` or `func.ST_GeomFromText(...)`.
**Warning signs:** Pydantic schema validation errors when serializing location objects to API responses — WKBElement is not JSON-serializable by default; convert to WKT or lat/lon before returning.

### Pitfall 5: Grade "7/A" in Dataset (Aid Climbing Notation)
**What goes wrong:** Grade normalization raises `KeyError` or returns garbage for the single `7/A` entry in the dataset.
**Why it happens:** One route in the CSV has `grade_original="5.11a A0"` and `grade="7/A"` — this is a combined free/aid grade (YDS 5.11a with A0 aid).
**How to avoid:** In the normalization module, treat the `7/A` pattern as a special case: extract the free climbing component (`7` = UIAA -> French `7a`) and store `A0` as metadata in the notes field. Don't fail on unknown grade patterns — fall back to storing the raw string in `grade_original`.
**Warning signs:** Import script crashes on row 420 of the CSV.

### Pitfall 6: pytest-asyncio 1.3.0 Configuration Required
**What goes wrong:** `PytestUnraisableExceptionWarning` or `DeprecationWarning` about `asyncio_default_fixture_loop_scope` filling test output.
**Why it happens:** pytest-asyncio 1.x requires explicit `asyncio_default_fixture_loop_scope` setting; it's not optional.
**How to avoid:** Set in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```
**Warning signs:** Tests pass but warnings fill terminal output from the first run.

### Pitfall 7: `updated_at` Not Updating on ORM Changes
**What goes wrong:** `updated_at` column stays frozen at creation time despite record updates.
**Why it happens:** `onupdate=func.now()` on a SQLAlchemy column only fires when using Core `update()` statements, not ORM attribute assignment. For async ORM operations, use a `__setattr__` override or a SQLAlchemy `event.listen` on the `before_flush` event.
**How to avoid:** Use a `@event.listens_for(Base, "before_update", propagate=True)` hook on the Base class to set `updated_at = datetime.utcnow()` before every update, OR use a PostgreSQL trigger. For Phase 1, a trigger is simpler and more reliable.
**Warning signs:** `updated_at` equals `created_at` after updates in tests.

---

## Runtime State Inventory

Step 2.5: SKIPPED — Phase 1 is greenfield. No existing runtime state (no database, no running services, no OS registrations). The project currently contains only `CLAUDE.md`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Runtime (CLAUDE.md) | Managed by uv | uv will download 3.12 | — |
| uv | Package manager | ✓ | 0.8.14 | — |
| Docker Desktop | Testcontainers DB tests | Installed, not running | 29.2.1 (when running) | Skip DB tests until Docker started |
| PostgreSQL client (psql) | Manual DB inspection | ✓ | 16.13 | — |
| ruff | Lint/format | ✗ | — | Install via `uv add --dev ruff` |
| pytest | Tests | ✓ (system) | 8.4.2 | Will also be in uv dev deps |

**Missing dependencies with no fallback:**
- Docker must be running to execute testcontainers-based DB tests. Grade normalization tests (pure Python) do not require Docker and will always pass.

**Missing dependencies with fallback:**
- ruff: install as dev dependency, no fallback needed.

**Note:** System Python is 3.9.6. uv will manage the 3.12 runtime independently. All `uv run` commands use the project's virtual environment, not the system Python.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (installed) + pytest-asyncio 1.3.0 (add as dev dep) |
| Config file | `pyproject.toml` — Wave 0 creates it |
| Quick run command | `uv run pytest tests/test_grades.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROUTE-02 | French/UIAA/YDS/Font/V-scale conversions round-trip without data loss | unit | `uv run pytest tests/test_grades.py -x` | Wave 0 |
| ROUTE-02 | Slash grades (6a/b, 7+/8-) parse correctly | unit | `uv run pytest tests/test_grades.py::test_slash_grades -x` | Wave 0 |
| ROUTE-02 | Numeric scoring order is monotonically increasing | unit | `uv run pytest tests/test_grades.py::test_numeric_ordering -x` | Wave 0 |
| INFRA-07 | Alembic upgrade head creates all tables | integration (Docker) | `uv run pytest tests/test_migrations.py::test_upgrade -x` | Wave 0 |
| INFRA-07 | Alembic downgrade returns to empty schema | integration (Docker) | `uv run pytest tests/test_migrations.py::test_downgrade -x` | Wave 0 |
| INFRA-02 | docker-compose up starts without errors | smoke | manual / `docker compose up --wait` | Wave 0 |
| ROUTE-01 | Route model has name, grade, discipline, location FK, pitches | unit | `uv run pytest tests/test_models.py -x` | Wave 0 |
| ROUTE-04 | Location self-referential FK and PostGIS coordinate insert/query | integration (Docker) | `uv run pytest tests/test_migrations.py::test_location_insert -x` | Wave 0 |
| ROUTE-06 | All 6 disciplines storable as enum values | unit | `uv run pytest tests/test_models.py::test_discipline_enum -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_grades.py -x` (pure Python, fast)
- **Per wave merge:** `uv run pytest tests/ -x` (requires Docker running for migration tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — PostGIS testcontainer fixture + async session fixture
- [ ] `tests/test_grades.py` — grade normalization unit tests (no Docker needed)
- [ ] `tests/test_migrations.py` — Alembic upgrade/downgrade + spatial insert tests
- [ ] `tests/test_models.py` — model structure / enum value tests (no Docker needed)
- [ ] `pyproject.toml` — project config with `[tool.pytest.ini_options]` section

---

## Code Examples

Verified patterns from official sources:

### Testcontainers PostGIS Fixture

```python
# Source: testcontainers-python docs + PostGIS module
import pytest
from testcontainers.postgres import PostgresContainer

POSTGIS_IMAGE = "postgis/postgis:17-3.6"

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer(POSTGIS_IMAGE) as container:
        yield container

@pytest.fixture
async def db_session(postgres_container):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()
```

### Grade Normalization (pure Python)

```python
# tick_list/grades.py
# Source: ported from bohniti.github.io/static/files/climbing-locations.js
#         and bohniti.github.io/convert_to_french_fixed.py

def normalize_to_french(grade: str, system: str = "auto") -> str:
    """Convert a grade string to French notation."""
    grade = grade.strip()
    if system == "uiaa" or system == "auto" and _is_uiaa(grade):
        return UIAA_TO_FRENCH.get(grade, grade)
    if system == "yds" or system == "auto" and grade.startswith("5."):
        return YDS_TO_FRENCH.get(grade, grade)
    return grade  # already French or unknown

def grade_to_numeric(french_grade: str) -> float:
    """Convert a French grade to numeric score for ordering."""
    # Handle slash grades: "6a/b" -> midpoint of 6a and 6b
    if "/" in french_grade and not french_grade.startswith("5."):
        parts = french_grade.split("/")
        scores = [FRENCH_NUMERIC.get(p.strip(), 0.0) for p in parts]
        return sum(scores) / len(scores)
    return FRENCH_NUMERIC.get(french_grade, 0.0)
```

### Docker Compose Base

```yaml
# docker-compose.yml — base config (D-25)
services:
  db:
    image: postgis/postgis:17-3.6
    environment:
      POSTGRES_USER: tick_list
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: tick_list
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tick_list"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

```yaml
# docker-compose.override.yml — dev extras (D-25, D-26)
services:
  db:
    ports:
      - "5432:5432"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `event_loop` fixture in pytest-asyncio | `asyncio_default_fixture_loop_scope` config | pytest-asyncio 1.0 (2025) | Must update conftest.py fixture patterns |
| `alembic init` (sync template) | `alembic init -t async` | Alembic 1.x | async template generates proper async env.py |
| `fastmcp.FastMCP().run()` standalone | Mount as ASGI sub-app via `http_app()` | FastMCP 3.x | Single process; no separate MCP process |
| `app.add_event_handler("startup", ...)` | `lifespan` context manager | FastAPI 0.95+ | Required for proper FastMCP lifespan handoff |
| `Mapped[Optional[WKBElement]]` | `Mapped[WKBElement | None]` | Python 3.10+ / SA 2.0 | Modern union syntax; use this form |

**Deprecated/outdated:**
- `from sqlalchemy.ext.declarative import declarative_base`: Use `class Base(DeclarativeBase): pass` in SQLAlchemy 2.0.
- `@app.on_event("startup")`: Deprecated in FastAPI 0.95+. Use `@asynccontextmanager` lifespan instead.
- `pytest-asyncio` event_loop fixture: Removed in 1.0. Use `asyncio_default_fixture_loop_scope` config.

---

## Open Questions

1. **FastMCP tool context / session injection pattern**
   - What we know: FastMCP 3.x tools are plain decorated functions; context can be injected via `Context` parameter.
   - What's unclear: The exact `Context` import and usage for accessing a DB session inside an MCP tool. This will matter in Phase 5 (MCP logging tools) but the skeleton in Phase 1 needs only stub tools.
   - Recommendation: Leave `tick_list/mcp.py` as a stub with one placeholder tool in Phase 1. Defer context injection pattern to Phase 5 research.

2. **`updated_at` trigger vs ORM event**
   - What we know: SQLAlchemy's `onupdate=func.now()` does not reliably fire for ORM-level updates in async mode.
   - What's unclear: Whether a PostgreSQL trigger or an ORM `before_update` event listener is simpler for this project.
   - Recommendation: Use a PostgreSQL trigger in the Alembic migration. Add to the initial migration: `CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER...`. This is database-level and always correct regardless of how the update is issued.

---

## Sources

### Primary (HIGH confidence)
- PyPI: fastmcp 3.1.1, fastapi 0.135.2, sqlalchemy 2.0.48, geoalchemy2 0.18.4, alembic 1.18.4, asyncpg 0.31.0, pydantic 2.12.5, pydantic-settings 2.13.1, uvicorn 0.42.0, pytest-asyncio 1.3.0, testcontainers 4.14.2 — verified 2026-03-27
- `https://gofastmcp.com/integrations/fastapi.md` — FastMCP ASGI mounting pattern including lifespan requirement
- `https://github.com/sqlalchemy/alembic/blob/main/alembic/templates/async/env.py` — Alembic async template
- `/Users/timo/Development/bohniti.github.io/convert_to_french_fixed.py` — UIAA-to-French mapping
- `/Users/timo/Development/bohniti.github.io/static/files/climbing-locations.js` — numeric grade scoring scale
- `/Users/timo/Development/bohniti.github.io/static/files/dataset.csv` — 415-row real dataset; grade range, discipline types, coordinate coverage (93%)

### Secondary (MEDIUM confidence)
- WebSearch: GeoAlchemy2 alembic_helpers `include_object`, `writer`, `render_item` — consistent across multiple docs versions (0.14 through 0.18)
- WebSearch: pytest-asyncio 1.0 breaking changes — `asyncio_default_fixture_loop_scope` required setting
- WebSearch: testcontainers-python PostGIS container using custom image — `PostgresContainer("postgis/postgis:17-3.6")`

### Tertiary (LOW confidence)
- SQLAlchemy `updated_at` via ORM event vs trigger — common community pattern but not verified against official SQLAlchemy 2.0 async docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI on 2026-03-27
- Architecture patterns: HIGH — FastMCP mounting from official docs; GeoAlchemy2 Mapped[] from official docs
- Grade normalization: HIGH — directly extracted from existing blog code and real dataset
- Pitfalls: MEDIUM — combination of official docs (alembic autogenerate pitfall) and verified community patterns (pytest-asyncio config, Docker socket)
- updated_at trigger recommendation: LOW — common pattern but not officially documented for async SQLAlchemy

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable libraries; FastMCP version may move faster)
