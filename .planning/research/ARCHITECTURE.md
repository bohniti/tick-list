# Architecture Research

**Domain:** Personal climbing logbook with MCP server + REST API + dashboard
**Researched:** 2026-03-26
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
                        Clients
        ┌──────────────────┬──────────────────┐
        │                  │                  │
   Claude Desktop     Web Browser       API Consumer
   (MCP Client)      (Dashboard)       (curl, etc.)
        │                  │                  │
        │ Streamable HTTP  │ HTTP             │ HTTP
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────┐
│                      Nginx                          │
│  /mcp/* → proxy_pass :8000   (SSE-friendly)         │
│  /api/* → proxy_pass :8000                          │
│  /*     → static files (dashboard HTML/JS/CSS)      │
│  TLS via Let's Encrypt                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI + Uvicorn (:8000)               │
│                  Single Process                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │  MCP Server   │  │  REST Router │                  │
│  │  (FastMCP)    │  │  /api/v1/*   │                  │
│  │  /mcp/*       │  │              │                  │
│  │              │  │              │                  │
│  │  @mcp.tool   │  │  @router.get │                  │
│  │  log_session │  │  /sessions   │                  │
│  │  add_ascent  │  │  /ascents    │                  │
│  │  find_routes │  │  /routes     │                  │
│  │  ...         │  │  /stats      │                  │
│  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                          │
│         ▼                 ▼                          │
│  ┌─────────────────────────────────┐                 │
│  │         Service Layer           │                 │
│  │  SessionService                 │                 │
│  │  AscentService                  │                 │
│  │  RouteService                   │                 │
│  │  CragService                    │                 │
│  │  GradeService                   │                 │
│  │  TopoService                    │                 │
│  │  StatsService                   │                 │
│  └──────────────┬──────────────────┘                 │
│                 │                                    │
│                 ▼                                    │
│  ┌─────────────────────────────────┐                 │
│  │       Repository Layer          │                 │
│  │  (SQLAlchemy 2.0 async ORM)     │                 │
│  └──────────────┬──────────────────┘                 │
│                 │                                    │
└─────────────────┼────────────────────────────────────┘
                  │ asyncpg
                  ▼
┌─────────────────────────────────────────────────────┐
│         PostgreSQL 16 + PostGIS                      │
│                                                      │
│  sessions / ascents / routes / crags / topos         │
│  Spatial indexes on crag.location (POINT)            │
└─────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Nginx | TLS termination, static file serving, reverse proxy, SSE buffering config | nginx.conf with proxy_buffering off for /mcp |
| FastAPI app | ASGI host, lifespan management, dependency injection container | Single `app` with mounted MCP sub-app |
| MCP Server (FastMCP) | Expose tools for Claude to call: log sessions, add ascents, find routes, analyze topos | `FastMCP` instance mounted at `/mcp` via `app.mount()` |
| REST Router | Read-heavy API for dashboard: sessions list, stats aggregations, route search | FastAPI `APIRouter` at `/api/v1/` |
| Service Layer | Business logic: grade normalization, route resolution (DB -> OpenBeta -> create), session validation | Plain Python classes injected via `Depends()` |
| Repository Layer | Data access: SQLAlchemy async queries, spatial queries via GeoAlchemy2 | Thin classes wrapping `AsyncSession` queries |
| PostgreSQL + PostGIS | Persistent storage, spatial indexing, full-text search on route names | Docker container, Alembic migrations |
| Dashboard | Static HTML/JS/CSS: Chart.js charts, Leaflet map, vanilla JS or Alpine.js interactivity | Served by Nginx directly, fetches from `/api/v1/` |

## Recommended Project Structure

```
tick-list/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic async config
├── src/
│   └── tick_list/
│       ├── __init__.py
│       ├── app.py              # FastAPI app factory, mounts MCP, lifespan
│       ├── config.py           # Settings via pydantic-settings
│       ├── database.py         # Engine, async session factory, get_session dep
│       │
│       ├── models/             # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── base.py         # DeclarativeBase with common mixins
│       │   ├── session.py      # ClimbingSession model
│       │   ├── ascent.py       # Ascent model
│       │   ├── route.py        # Route model (with grade fields)
│       │   ├── crag.py         # Crag model (with PostGIS POINT)
│       │   └── topo.py         # Topo image + analyzed data
│       │
│       ├── schemas/            # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── session.py
│       │   ├── ascent.py
│       │   ├── route.py
│       │   ├── crag.py
│       │   └── stats.py
│       │
│       ├── repositories/       # Data access layer
│       │   ├── __init__.py
│       │   ├── base.py         # BaseRepository with common CRUD
│       │   ├── session_repo.py
│       │   ├── ascent_repo.py
│       │   ├── route_repo.py
│       │   └── crag_repo.py
│       │
│       ├── services/           # Business logic layer
│       │   ├── __init__.py
│       │   ├── session_service.py
│       │   ├── ascent_service.py
│       │   ├── route_service.py  # Three-tier resolution logic
│       │   ├── grade_service.py  # Normalization + numeric scoring
│       │   ├── topo_service.py
│       │   ├── stats_service.py
│       │   └── openbeta.py       # OpenBeta GraphQL client
│       │
│       ├── api/                # REST API routers
│       │   ├── __init__.py
│       │   ├── router.py       # Main v1 router aggregating sub-routers
│       │   ├── sessions.py
│       │   ├── ascents.py
│       │   ├── routes.py
│       │   ├── crags.py
│       │   ├── stats.py
│       │   └── deps.py         # Shared dependencies (auth, session)
│       │
│       ├── mcp/                # MCP tool definitions
│       │   ├── __init__.py
│       │   ├── server.py       # FastMCP instance + tool registration
│       │   ├── session_tools.py
│       │   ├── ascent_tools.py
│       │   ├── route_tools.py
│       │   └── topo_tools.py
│       │
│       └── utils/              # Shared utilities
│           ├── __init__.py
│           ├── grades.py       # Grade conversion tables + numeric scoring
│           └── auth.py         # Bearer token verification
│
├── dashboard/                  # Static frontend (served by Nginx)
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js             # Main entry, routing
│   │   ├── api.js             # Fetch wrapper for /api/v1/
│   │   ├── pyramid.js         # Grade pyramid chart (Chart.js)
│   │   ├── map.js             # Crag map (Leaflet + PostGIS data)
│   │   ├── progression.js     # Progression charts
│   │   └── timeline.js        # Session timeline
│   └── lib/                   # Vendored JS libs (Chart.js, Leaflet, Alpine)
│
├── scripts/
│   └── import_csv.py          # One-time CSV import script
│
├── tests/
│   ├── conftest.py            # Fixtures: async test client, test DB
│   ├── test_services/
│   ├── test_api/
│   └── test_mcp/
│
├── docker-compose.yml          # PostgreSQL + PostGIS + app
├── Dockerfile
├── alembic.ini
├── pyproject.toml
└── .github/
    └── workflows/
        └── ci.yml
```

### Structure Rationale

- **`models/` separate from `schemas/`:** ORM models define DB structure; Pydantic schemas define API contracts. They evolve independently (e.g., DB has PostGIS geometry, API returns `[lat, lon]`).
- **`repositories/` layer:** Isolates raw SQL/ORM queries. Services never import `select()` or `AsyncSession` directly. Makes testing services trivial with mock repos.
- **`services/` as the shared core:** Both MCP tools and REST endpoints call the same service methods. This is the critical architectural constraint -- no business logic in routers or tools.
- **`mcp/` and `api/` as thin adapters:** MCP tools translate Claude's natural language parameters into service calls. REST endpoints translate HTTP requests into service calls. Both are thin.
- **`dashboard/` at project root:** Not inside `src/` because it is not Python. Nginx serves it directly. No build step -- just files.

## Architectural Patterns

### Pattern 1: Shared Service Layer (the core pattern)

**What:** Both the MCP tools and REST API are thin adapters that delegate to a shared service layer. Neither contains business logic.

**When to use:** Always. This is the foundational pattern for this project.

**Trade-offs:** Slightly more indirection than putting logic in route handlers, but prevents duplication between MCP and REST, and makes testing straightforward.

**Example:**
```python
# services/session_service.py
class SessionService:
    def __init__(self, session_repo: SessionRepo, ascent_repo: AscentRepo):
        self.session_repo = session_repo
        self.ascent_repo = ascent_repo

    async def create_session(self, data: SessionCreate) -> ClimbingSession:
        session = await self.session_repo.create(data)
        return session

    async def get_sessions_with_stats(self, limit: int = 20) -> list[SessionSummary]:
        return await self.session_repo.list_with_ascent_counts(limit=limit)


# mcp/session_tools.py -- thin adapter
@mcp.tool
async def log_session(date: str, crag: str, notes: str | None = None) -> dict:
    """Log a climbing session at a crag."""
    service = get_session_service()  # resolved from app state
    session = await service.create_session(SessionCreate(
        date=date, crag_name=crag, notes=notes
    ))
    return {"id": session.id, "date": str(session.date), "crag": crag}


# api/sessions.py -- thin adapter
@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    service: SessionService = Depends(get_session_service),
) -> list[SessionSummary]:
    return await service.get_sessions_with_stats(limit=limit)
```

### Pattern 2: FastMCP Mount with Combined Lifespan

**What:** Mount the FastMCP ASGI app onto FastAPI, combining their lifespans so both the MCP session manager and the database pool initialize correctly.

**When to use:** At app startup. This is the glue that makes single-process work.

**Trade-offs:** Requires careful lifespan management. Forgetting to pass the MCP lifespan to FastAPI will silently break session management.

**Example:**
```python
# app.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.utilities.lifespan import combine_lifespans

from tick_list.mcp.server import mcp_server
from tick_list.database import engine, async_session_factory

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup: nothing extra needed if engine is lazy
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()

mcp_app = mcp_server.http_app(path="/")

app = FastAPI(
    title="Tick List API",
    lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan),
)
app.mount("/mcp", mcp_app)
```

### Pattern 3: Async Session Dependency with Request Scope

**What:** A FastAPI dependency that yields an `AsyncSession`, scoped to one request. The session is committed on success, rolled back on exception, and always closed.

**When to use:** Every REST endpoint and MCP tool that touches the database.

**Trade-offs:** One session per request is simple and correct. Avoids connection leaks. The session factory is cached per-request by FastAPI's dependency system.

**Example:**
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/ticklist",
    pool_size=5,
    max_overflow=10,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Pattern 4: Three-Tier Route Resolution

**What:** When logging an ascent, resolve the route through three tiers: (1) local DB search, (2) OpenBeta GraphQL lookup, (3) Claude creates from description/topo. Local DB is always authoritative.

**When to use:** In `RouteService.resolve_route()`, called by ascent logging tools.

**Trade-offs:** OpenBeta adds network dependency but enriches data. Tier 3 (Claude creates) means the MCP tool returns a prompt asking Claude to provide structured route data, which the tool then persists. This keeps the human-in-the-loop.

## Data Flow

### Flow 1: Logging a Climb via Claude

```
Claude Desktop (user says "I climbed 'Blue Moon' 6b+ at Arco, redpoint")
    │
    ▼
Claude calls MCP tool: log_ascent(route="Blue Moon", grade="6b+",
                                   crag="Arco", style="redpoint")
    │
    ▼
MCP tool (thin adapter)
    │ calls
    ▼
AscentService.log_ascent()
    │
    ├──→ RouteService.resolve_route("Blue Moon", "Arco", "6b+")
    │       │
    │       ├──→ RouteRepo.search(name="Blue Moon", crag="Arco")
    │       │      found? → return route
    │       │
    │       ├──→ OpenBetaClient.search("Blue Moon", near=Arco coords)
    │       │      found? → create in local DB → return route
    │       │
    │       └──→ return None (Claude will provide details to create)
    │
    ├──→ GradeService.normalize("6b+", system="french")
    │       → { french: "6b+", numeric: 17, uiaa: null, yds: null }
    │
    ├──→ AscentRepo.create(route_id, session_id, style, grade_data)
    │
    └──→ return { ascent_id, route, grade, style }
         ↓
    Claude formats response to user
```

### Flow 2: Dashboard Loading Grade Pyramid

```
Browser loads /index.html (from Nginx, static)
    │
    ├──→ GET /api/v1/stats/grade-pyramid
    │       │
    │       ▼
    │    StatsService.grade_pyramid()
    │       │
    │       ▼
    │    AscentRepo.grade_distribution_by_style()
    │       │ SQL: GROUP BY grade_french, style, count(*)
    │       ▼
    │    Returns: [{ grade: "6a", onsight: 3, redpoint: 5, flash: 1 }, ...]
    │       │
    │       ▼
    │    Browser renders stacked bar chart (Chart.js)
    │
    ├──→ GET /api/v1/crags?bounds=...
    │       │
    │       ▼
    │    CragService.within_bounds(sw_lat, sw_lng, ne_lat, ne_lng)
    │       │
    │       ▼
    │    CragRepo.spatial_query()
    │       │ SQL: ST_Within(location, ST_MakeEnvelope(...))
    │       ▼
    │    Returns: [{ name, lat, lng, route_count, best_grade }, ...]
    │       │
    │       ▼
    │    Browser renders Leaflet markers
```

### Flow 3: CSV Historical Import

```
scripts/import_csv.py (one-time run)
    │
    ├──→ Read /path/to/dataset.csv (422 routes)
    │
    ├──→ For each row:
    │       │
    │       ├──→ CragService.find_or_create(name, lat, lng)
    │       ├──→ RouteService.find_or_create(name, grade, crag_id)
    │       ├──→ GradeService.normalize(grade, source_system)
    │       └──→ AscentService.create(route_id, date, style)
    │
    └──→ Summary: "Imported 422 ascents across N crags"
```

### Key Data Flows Summary

1. **Write path (MCP tools):** Claude -> FastMCP -> Service -> Repository -> PostgreSQL
2. **Read path (REST API):** Dashboard JS -> Nginx -> FastAPI -> Service -> Repository -> PostgreSQL
3. **Import path (script):** CSV -> Script -> Service -> Repository -> PostgreSQL
4. **Static assets:** Browser -> Nginx -> dashboard/ files (no FastAPI involved)

## Scaling Considerations

This is a single-user personal tool. Scaling is not a concern. The architecture choices are driven by correctness, developer experience, and maintainability -- not throughput.

| Concern | Single User (actual) | Notes |
|---------|---------------------|-------|
| DB connections | pool_size=5 is generous | asyncpg + 5 connections handles concurrent dashboard loads fine |
| MCP concurrency | One Claude session at a time | Stateless MCP mode not needed; stateful is simpler |
| Dashboard load | Seconds of data, not millions of rows | No caching layer needed; direct DB queries are fast |
| Static files | Nginx serves directly | No CDN needed; VPS bandwidth is sufficient |

### What Could Actually Break

1. **First real issue:** Alembic migrations on PostGIS columns can be finicky. Test migrations in Docker before deploying.
2. **Second real issue:** MCP tool timeouts if OpenBeta GraphQL is slow. Add a 5-second timeout on the HTTP client.

## Anti-Patterns

### Anti-Pattern 1: Business Logic in MCP Tools or REST Handlers

**What people do:** Put grade normalization, route resolution, or validation logic directly in `@mcp.tool` functions or `@router.post` handlers.
**Why it's wrong:** Logic gets duplicated between MCP and REST. Testing requires spinning up the full transport layer. Changes must be made in two places.
**Do this instead:** MCP tools and REST handlers are thin adapters. Five lines max: parse input, call service, format output.

### Anti-Pattern 2: Passing Raw SQLAlchemy Models to Responses

**What people do:** Return ORM model instances directly from API endpoints, relying on FastAPI's auto-serialization.
**Why it's wrong:** Leaks internal DB structure (PostGIS geometry objects, relationship loading issues, `lazy=select` N+1 queries). GeoAlchemy2 `Geometry` columns do not serialize to JSON.
**Do this instead:** Always map ORM models to Pydantic response schemas in the service or router layer. Convert PostGIS points to `{"lat": float, "lng": float}`.

### Anti-Pattern 3: Letting MCP Tools Access the DB Directly

**What people do:** Import `AsyncSession` and write queries inside `@mcp.tool` functions.
**Why it's wrong:** MCP tools run in a different ASGI sub-application context. Session lifecycle, dependency injection, and error handling differ from FastAPI routes. Mixing contexts causes subtle bugs.
**Do this instead:** MCP tools call service methods. Services receive sessions via their repositories, which are initialized with a session from the shared factory.

### Anti-Pattern 4: Building a Frontend Build Pipeline

**What people do:** Introduce Vite, webpack, or npm for the dashboard because "it's more professional."
**Why it's wrong:** Adds complexity for a single-user dashboard. Vendor Alpine.js (17KB), Chart.js, and Leaflet into `dashboard/lib/`. No npm, no node_modules, no build step.
**Do this instead:** Plain HTML files, vanilla JS or Alpine.js for reactivity, CSS file for styling. Served directly by Nginx.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenBeta GraphQL | `httpx.AsyncClient` with 5s timeout | `api.openbeta.io/v2/graphql`. Sparse EU data. Cache responses in local DB once resolved. |
| Claude Vision (topos) | MCP resource/tool returning image for Claude to analyze | Claude does analysis client-side; MCP tool receives structured result to persist |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| MCP Server <-> Service Layer | Direct Python function calls | MCP tools import and call service methods. No HTTP between them. |
| REST API <-> Service Layer | FastAPI `Depends()` injection | Services injected as dependencies; sessions auto-managed. |
| Dashboard <-> REST API | HTTP fetch over `/api/v1/*` | Bearer token in `Authorization` header. JSON responses. |
| Nginx <-> FastAPI | Reverse proxy on `:8000` | `proxy_buffering off` for `/mcp` path (SSE). Standard proxy for `/api`. |
| Nginx <-> Dashboard | Direct file serving | `root /path/to/dashboard;` No proxy needed. |

## Build Order (Dependencies Between Components)

The architecture implies this build order, where each layer depends on the one before it:

```
Phase 1: Foundation
    models/ + database.py + Alembic migrations + Docker Compose (PostgreSQL+PostGIS)
    ↓ (everything depends on having a database)

Phase 2: Core Logic
    repositories/ + services/ (grade_service, route_service, session_service, ascent_service)
    utils/grades.py (conversion tables)
    ↓ (MCP and API both need services to exist)

Phase 3a: MCP Server          Phase 3b: REST API + Dashboard
    mcp/server.py                 api/router.py + endpoints
    mcp/*_tools.py                dashboard/ static files
    app.py (mount + lifespan)     Chart.js + Leaflet integration
    ↓                             ↓
    (can be built in parallel -- both consume services)

Phase 4: Import + Polish
    scripts/import_csv.py (uses services to import 422 routes)
    OpenBeta integration in RouteService
    Topo analysis flow

Phase 5: Deployment
    Dockerfile + docker-compose.yml
    Nginx config (static + proxy + SSE)
    GitHub Actions CI/CD
```

**Key dependency insight:** The service layer is the linchpin. Build and test it thoroughly before either interface layer. The MCP server and REST API can be developed in parallel once services exist.

## Sources

- [FastMCP + FastAPI Integration](https://gofastmcp.com/integrations/fastapi) -- Official FastMCP docs on mounting into FastAPI
- [FastMCP HTTP Deployment](https://gofastmcp.com/deployment/http) -- Transport options, stateless mode, Nginx config, production patterns
- [FastMCP Issue #993: from_fastapi and mounting](https://github.com/PrefectHQ/fastmcp/issues/993) -- Community discussion on mounting patterns
- [Patterns and Practices for SQLAlchemy 2.0 with FastAPI](https://chaoticengineer.hashnode.dev/fastapi-sqlalchemy) -- Async session patterns, dependency injection
- [GeoAlchemy2 Documentation](https://geoalchemy-2.readthedocs.io/) -- PostGIS integration with SQLAlchemy ORM
- [FastAPI Layered Architecture with DI](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo) -- Service + repository pattern reference
- [FastAPI 3-tier pattern with PostgreSQL](https://viktorsapozhok.github.io/fastapi-oauth2-postgres/) -- Routers/services/schemas/models structure

---
*Architecture research for: Climbing Diary (tick-list)*
*Researched: 2026-03-26*
