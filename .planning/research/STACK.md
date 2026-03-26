# Technology Stack

**Project:** Climbing Diary (MCP Server + Dashboard)
**Researched:** 2026-03-26

## Recommended Stack

### Runtime & Tooling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12+ | Runtime | Stable, full ecosystem support. 3.13 also viable but 3.12 has widest library compat. | HIGH |
| uv | 0.11.x | Package/project manager | 10-100x faster than pip, lockfile support, replaces pip+venv+pip-tools. Industry standard for new Python projects. | HIGH |
| ruff | latest | Linter + formatter | Replaces flake8+black+isort in one tool, 100x faster. No reason to use anything else. | HIGH |
| Docker Compose | v2 | Local dev + production | Single `docker compose up` for Postgres+PostGIS+app. Matches production topology. | HIGH |

### Backend Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | 0.128.x | Web framework | Async-native, auto OpenAPI docs, Pydantic integration, SSE support. Project already specifies it. | HIGH |
| Uvicorn | 0.42.x | ASGI server | Standard FastAPI server. Install with `[standard]` extra for uvloop + httptools perf boost. | HIGH |
| Pydantic | 2.12.x | Validation/serialization | Core to FastAPI. V2 is 5-50x faster than V1 with Rust-based core. Use for all request/response models and settings. | HIGH |
| FastMCP | 3.1.x | MCP server framework | The dominant MCP library (powers 70% of MCP servers). V3 adds auth, versioning, OpenTelemetry. Mount into FastAPI via ASGI. | HIGH |

### Database

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PostgreSQL | 17 | Primary database | Latest stable. Use `postgis/postgis:17-bookworm-postgis-3.6` Docker image. PG17 improves VACUUM, JSON functions, and query planning over PG16. | HIGH |
| PostGIS | 3.6 | Spatial extension | Crag map spatial queries (crags near location, bounding box searches). Ships in the postgis/postgis Docker image. | HIGH |
| SQLAlchemy | 2.0.48 | ORM + query builder | Mature async support via `create_async_engine`. Use 2.0-style `Mapped[]` annotations for type safety. Do NOT use 2.1 beta in production. | HIGH |
| GeoAlchemy2 | 0.18.x | PostGIS integration | Adds `Geometry` and `Geography` column types to SQLAlchemy models. Required for PostGIS queries through the ORM. | HIGH |
| Alembic | 1.18.x | Database migrations | Only migration tool for SQLAlchemy. Use `--autogenerate` for initial schema, hand-edit for PostGIS-specific DDL. | HIGH |
| asyncpg | 0.31.x | Async PG driver | 5x faster than psycopg3 for async. Required by SQLAlchemy async engine. | HIGH |

### API & Auth

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| python-multipart | latest | Form/file parsing | Required by FastAPI for photo upload endpoints (UploadFile). | HIGH |
| Pillow | 12.1.x | Image processing | Resize/thumbnail uploaded topo photos and send pics before storage. Lightweight, no heavy deps. | HIGH |
| httpx | 0.28.x | Async HTTP client | For OpenBeta GraphQL API calls. Async-native, HTTP/2 support. Prefer over aiohttp (cleaner API, better maintained). | HIGH |

### Frontend (No Build Step)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Alpine.js | 3.15.x | Reactive UI | Declarative reactivity via HTML attributes. No build step, loads from CDN. Perfect for dashboard interactivity (filters, tabs, toggles) without SPA complexity. | HIGH |
| Chart.js | 4.5.x | Charts & graphs | Grade pyramid (stacked bar), progression line charts, session timeline. Loads from CDN. Responsive by default. | HIGH |
| Leaflet.js | 1.9.4 | Crag map | Interactive map with PostGIS-powered markers. Use stable 1.9.4, NOT 2.0 alpha. Plugin ecosystem (MarkerCluster) is stable on 1.x. | HIGH |
| Vanilla CSS | -- | Styling | Single-user dashboard does not need Tailwind/Bootstrap build complexity. A single `style.css` with CSS custom properties is sufficient. | MEDIUM |

**CDN delivery pattern:** Load Alpine, Chart.js, and Leaflet from `unpkg.com` or `cdn.jsdelivr.net` with pinned versions. Include SRI hashes for integrity. For self-hosted production, vendor the files into `/static/vendor/` so the dashboard works offline.

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | latest | Test runner | Standard. Use with `pytest-asyncio` for async test functions. | HIGH |
| pytest-asyncio | latest | Async test support | Required for testing async FastAPI endpoints and DB operations. | HIGH |
| httpx (TestClient) | -- | API testing | FastAPI's `TestClient` uses httpx under the hood. Test endpoints without starting a server. | HIGH |
| testcontainers-python | latest | DB testing | Spins up real PostgreSQL+PostGIS in Docker for integration tests. No mocking spatial queries. | MEDIUM |

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Nginx | latest | Reverse proxy + static | Serves dashboard static files directly, proxies `/api` and `/mcp` to Uvicorn. Handles TLS termination. | HIGH |
| Let's Encrypt (certbot) | latest | TLS certificates | Free automated TLS. Use certbot with nginx plugin or DNS challenge. | HIGH |
| GitHub Actions | -- | CI/CD | Lint (ruff), test (pytest), build Docker image, deploy to VPS on push to main. | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| ORM | SQLAlchemy 2.0 | Tortoise ORM | Smaller ecosystem, worse PostGIS support, less mature async story |
| ORM | SQLAlchemy 2.0 | SQLModel | Thin wrapper over SQLAlchemy -- adds indirection without value for a project that already needs GeoAlchemy2 |
| HTTP Client | httpx | aiohttp | httpx has cleaner API, better typing, and is the FastAPI testing standard |
| Frontend framework | Alpine.js | HTMX | HTMX is better for server-rendered HTML. This project serves a JSON API + static dashboard, so Alpine.js fits better for client-side data binding |
| Frontend framework | Alpine.js | React/Vue/Svelte | Requires build step, far too heavy for a personal single-page dashboard |
| Charts | Chart.js | Plotly.js | Plotly is 3MB+ minified vs Chart.js at ~200KB. Overkill for the chart types needed (bar, line, doughnut) |
| Charts | Chart.js | D3.js | D3 is low-level -- requires writing rendering code. Chart.js gives declarative charts out of the box |
| Map | Leaflet 1.9 | MapLibre GL | WebGL-based, heavier. Leaflet is lighter and sufficient for marker-based crag maps |
| Map | Leaflet 1.9 | Leaflet 2.0 alpha | Alpha quality, plugin ecosystem not yet compatible. Stick with 1.9.4 stable. |
| PG Driver | asyncpg | psycopg3 | asyncpg is significantly faster for async workloads. psycopg3 is fine but slower. |
| DB | PostgreSQL 17 | PostgreSQL 16 | PG17 is stable and the Docker images are available. No reason to use older version for greenfield. |
| MCP | FastMCP 3.x | mcp (official SDK) | FastMCP wraps the official SDK with better DX -- decorators, auto-schema. The official SDK is lower-level. |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| SQLite | No spatial queries, no concurrent access, doesn't match production topology |
| Django | Overkill ORM/admin/template baggage for an API-first project with a static JS frontend |
| Flask | No async support, no auto-docs, no Pydantic integration. FastAPI is strictly better here. |
| Webpack/Vite/esbuild | Project constraint: no build step for frontend. CDN + vanilla is correct. |
| Redis | No caching layer needed for single-user. PostgreSQL handles everything. |
| Celery | No background job queue needed. Single-user, single-process. Import CSV is a one-time script. |
| MongoDB | Relational data (sessions -> ascents -> routes) maps perfectly to PostgreSQL. Document DB adds complexity for no benefit. |
| Next.js / Nuxt / SvelteKit | Server-side rendering framework for a dashboard that is static files + API calls is absurd overhead. |

## Installation

```bash
# Initialize project with uv
uv init tick-list
cd tick-list

# Core dependencies
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings
uv add sqlalchemy[asyncio] asyncpg geoalchemy2 alembic
uv add fastmcp
uv add httpx pillow python-multipart

# Dev dependencies
uv add --dev pytest pytest-asyncio ruff
uv add --dev testcontainers  # optional: for integration tests with real PG+PostGIS
```

### Docker Compose (dev)

```yaml
services:
  db:
    image: postgis/postgis:17-bookworm-postgis-3.6
    environment:
      POSTGRES_DB: climbing
      POSTGRES_USER: climbing
      POSTGRES_PASSWORD: climbing
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Frontend (CDN with pinned versions)

```html
<!-- Alpine.js -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.1/dist/cdn.min.js"></script>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>

<!-- Leaflet -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

## Version Pinning Strategy

- **Python deps:** Pin in `pyproject.toml` with `>=x.y,<x+1` ranges. `uv.lock` provides exact reproducibility.
- **Frontend CDN:** Pin exact versions in HTML `src` attributes. Vendor into `/static/vendor/` for production.
- **Docker images:** Pin to specific tags (e.g., `postgis/postgis:17-bookworm-postgis-3.6`) not `latest`.
- **CI:** Pin tool versions in GitHub Actions (e.g., `astral-sh/setup-uv@v5` with explicit uv version).

## Sources

- [FastMCP PyPI](https://pypi.org/project/fastmcp/) - v3.1.1, HIGH confidence
- [FastMCP 3.0 GA announcement](https://www.jlowin.dev/blog/fastmcp-3-launch) - HIGH confidence
- [FastAPI PyPI](https://pypi.org/project/fastapi/) - v0.128.x, HIGH confidence
- [SQLAlchemy releases](https://github.com/sqlalchemy/sqlalchemy/releases) - v2.0.48, HIGH confidence
- [GeoAlchemy2 docs](https://geoalchemy-2.readthedocs.io/) - v0.18.4, HIGH confidence
- [Alembic docs](https://alembic.sqlalchemy.org/en/latest/) - v1.18.4, HIGH confidence
- [asyncpg PyPI](https://pypi.org/project/asyncpg/) - v0.31.0, HIGH confidence
- [Pydantic releases](https://github.com/pydantic/pydantic/releases) - v2.12.5, HIGH confidence
- [Uvicorn PyPI](https://pypi.org/project/uvicorn/) - v0.42.x, HIGH confidence
- [Alpine.js GitHub](https://github.com/alpinejs/alpine/releases) - v3.15.x, HIGH confidence
- [Chart.js npm](https://www.npmjs.com/package/chart.js) - v4.5.1, HIGH confidence
- [Leaflet.js download](https://leafletjs.com/download.html) - v1.9.4 stable, HIGH confidence
- [postgis/postgis Docker Hub](https://hub.docker.com/r/postgis/postgis) - PG17+PostGIS 3.6, HIGH confidence
- [uv PyPI](https://pypi.org/project/uv/) - v0.11.x, HIGH confidence
- [Pillow PyPI](https://pypi.org/project/pillow/) - v12.1.1, HIGH confidence
- [httpx PyPI](https://pypi.org/project/httpx/) - v0.28.1, HIGH confidence
