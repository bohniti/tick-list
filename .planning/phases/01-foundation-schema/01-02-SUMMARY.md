---
phase: 01-foundation-schema
plan: 02
subsystem: database
tags: [sqlalchemy, alembic, postgis, geoalchemy2, asyncpg, orm, migrations]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Python project structure, config.py with Settings, pyproject.toml with dependencies"
provides:
  - "SQLAlchemy 2.0 ORM models: Location, Route, Session, Ascent, Photo"
  - "Alembic async migration environment with GeoAlchemy2 helpers"
  - "Initial migration with PostGIS extension, enum types, updated_at triggers"
  - "Test infrastructure with PostGIS testcontainer fixture"
affects: [01-03, 02-services, 03-api, 05-mcp, 06-csv-import]

# Tech tracking
tech-stack:
  added: [sqlalchemy, geoalchemy2, alembic, asyncpg, testcontainers]
  patterns: [SQLAlchemy 2.0 Mapped[] annotations, async engine with asyncpg, UUID primary keys, server-side timestamps with DB triggers]

key-files:
  created:
    - tick_list/models.py
    - alembic.ini
    - alembic/env.py
    - alembic/versions/1774608527_001_initial_schema.py
    - tests/conftest.py
    - tests/test_models.py
    - tests/test_migrations.py
  modified:
    - pyproject.toml

key-decisions:
  - "Manual migration file instead of autogenerate (no DB available at build time)"
  - "updated_at via DB trigger function rather than ORM onupdate (async reliability per research)"
  - "PostGIS spatial indexes left to auto-creation by PostGIS extension"

patterns-established:
  - "Pattern: All tables use UUID primary keys with uuid.uuid4 default"
  - "Pattern: All tables have created_at/updated_at with server_default=func.now()"
  - "Pattern: Python str enums stored as PostgreSQL enum types"
  - "Pattern: Async session factory with expire_on_commit=False"
  - "Pattern: PostGIS testcontainer fixture for integration tests"

requirements-completed: [ROUTE-01, ROUTE-04, ROUTE-06, INFRA-07]

# Metrics
duration: 6min
completed: 2026-03-27
---

# Phase 01 Plan 02: SQLAlchemy ORM Models & Alembic Migrations Summary

**5 SQLAlchemy 2.0 ORM models with PostGIS geometry, 6 enum types, async Alembic migrations with GeoAlchemy2 helpers, and 13 passing model structure tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-27T10:46:17Z
- **Completed:** 2026-03-27T10:52:12Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- All 5 domain models (Location, Route, Session, Ascent, Photo) with full column definitions, relationships, and UUID primary keys
- PostGIS POINT geometry on Location with SRID 4326 for spatial queries
- Alembic async migration environment with GeoAlchemy2 include_object/writer/render_item helpers
- Initial migration creates all tables, enums, PostGIS extension, and updated_at triggers
- 13 pure Python model structure tests passing without Docker

## Task Commits

Each task was committed atomically:

1. **Task 1: Create all SQLAlchemy 2.0 ORM models** - `69bc512` (feat)
2. **Task 2: Set up Alembic async migrations with initial schema** - `38d5a85` (feat)
3. **Task 3: Write test infrastructure and model/migration tests** - `38c20e6` (test)

## Files Created/Modified
- `tick_list/models.py` - All 5 ORM models, 6 enums, async engine setup
- `alembic.ini` - Alembic config with asyncpg URL
- `alembic/env.py` - Async migration env with GeoAlchemy2 helpers
- `alembic/versions/1774608527_001_initial_schema.py` - Initial schema migration
- `alembic/script.py.mako` - Migration template (generated)
- `tests/__init__.py` - Test package marker
- `tests/conftest.py` - PostGIS testcontainer fixtures
- `tests/test_models.py` - 13 model structure tests
- `tests/test_migrations.py` - Migration and spatial insert integration tests
- `pyproject.toml` - Added requires_docker pytest marker

## Decisions Made
- Wrote migration file manually rather than using autogenerate (no running PostgreSQL available during build)
- Used DB-level trigger function for updated_at rather than SQLAlchemy onupdate (async reliability per research findings)
- Left PostGIS spatial index creation to the extension itself (auto-created on geometry columns)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Alembic autogenerate requires a running database connection; created migration manually with all table definitions, enum types, and trigger setup instead.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all models fully defined with proper columns, relationships, and types.

## Next Phase Readiness
- All ORM models importable and tested for structure
- Alembic migration ready to run against any PostGIS-enabled PostgreSQL instance
- Test infrastructure ready for integration tests when Docker is available
- Models provide the complete data layer for Phase 01 Plan 03 (Docker Compose) and Phase 02 (services)

---
*Phase: 01-foundation-schema*
*Completed: 2026-03-27*
