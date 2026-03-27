# Roadmap: Climbing Diary

## Overview

Build a personal climbing logbook where the primary interface is conversation with Claude via MCP, backed by PostgreSQL+PostGIS, a REST API, and a static web dashboard. The build order follows hard dependency constraints: schema and grade normalization first, then services, then the two interface layers (MCP tools and REST/dashboard) which can develop independently, and finally production deployment hardening.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Schema** - Database models, migrations, grade normalization, Docker Compose dev environment, project skeleton
- [ ] **Phase 2: Services & Route Resolution** - Repository and service layer, three-tier route resolution, spatial queries
- [ ] **Phase 3: Data Import** - Import 422 historical routes from unified CSV into sessions, ascents, routes, and locations
- [ ] **Phase 4: REST API & Auth** - All read endpoints for sessions, ascents, routes, locations, stats, plus bearer token auth
- [ ] **Phase 5: MCP Logging Tools** - FastMCP server with tools for logging sessions, ascents, attaching photos, and route resolution
- [ ] **Phase 6: MCP Query Tools & Narratives** - MCP tools for querying history, retrieving stats, answering conversational questions, generating session narratives
- [ ] **Phase 7: Dashboard** - Static web dashboard with session timeline, session detail, responsive layout
- [ ] **Phase 8: Deployment & CI/CD** - Nginx + Let's Encrypt, GitHub Actions pipeline, production Docker Compose, backup script

## Phase Details

### Phase 1: Foundation & Schema
**Goal**: A running PostgreSQL+PostGIS database with all tables, a grade normalization module, and a FastAPI+FastMCP skeleton that boots in Docker Compose
**Depends on**: Nothing (first phase)
**Requirements**: ROUTE-01, ROUTE-02, ROUTE-04, ROUTE-06, INFRA-02, INFRA-07
**Success Criteria** (what must be TRUE):
  1. Docker Compose starts PostgreSQL+PostGIS and the FastAPI app without errors
  2. Alembic migrations create all tables (sessions, ascents, routes, locations with PostGIS geometry) and can upgrade/downgrade cleanly
  3. Grade normalization converts between French, UIAA, YDS, Font, and V-scale with numeric scoring, and round-trips without data loss
  4. FastAPI health endpoint responds, FastMCP sub-app mounts without path conflicts
  5. Routes store name, grade, discipline, location reference, and pitch count; locations store hierarchical area/crag/sector with PostGIS coordinates; disciplines include sport, trad, boulder, multipitch, ice, mixed
**Plans:** 1/3 plans executed

Plans:
- [x] 01-01-PLAN.md — Project skeleton, dependencies, Docker Compose, FastAPI+FastMCP app
- [x] 01-02-PLAN.md — SQLAlchemy ORM models, Alembic async migrations, model/migration tests
- [ ] 01-03-PLAN.md — Grade normalization module (TDD)

### Phase 2: Services & Route Resolution
**Goal**: A shared service layer that both MCP tools and REST endpoints will consume, with three-tier route resolution and spatial queries working
**Depends on**: Phase 1
**Requirements**: ROUTE-03, ROUTE-05, MCP-04
**Success Criteria** (what must be TRUE):
  1. Three-tier route resolution works: searching local DB first, then OpenBeta GraphQL, then creating a new route from description, with a source field tracking provenance
  2. Spatial query returns crags within N km of a given lat/lon point
  3. Service layer methods are async and callable from both MCP tool handlers and REST route handlers without duplication
**Plans**: TBD

### Phase 3: Data Import
**Goal**: The 422-route historical dataset is imported and queryable, giving the dashboard real data from day one
**Depends on**: Phase 2
**Requirements**: IMPORT-01, IMPORT-02, IMPORT-03
**Success Criteria** (what must be TRUE):
  1. Running the import script populates sessions, ascents, routes, and locations from the unified CSV
  2. Import correctly handles French-normalized grades, GPS coordinates, ascent styles, and source attribution
  3. Import is idempotent: running it twice does not create duplicate records
**Plans**: TBD

### Phase 4: REST API & Auth
**Goal**: Authenticated REST API serves all data needed by the dashboard and external consumers
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, INFRA-01
**Success Criteria** (what must be TRUE):
  1. All API endpoints require a valid bearer token; requests without a token get 401
  2. Sessions endpoint returns paginated list filterable by date and location; session detail includes ascents and photo references
  3. Ascents endpoint returns list filterable by grade, style, date, and discipline
  4. Locations endpoint returns list with coordinates; stats endpoint returns summary totals, streaks, and hardest sends
  5. Photo files are served via a dedicated API endpoint
**Plans**: TBD

### Phase 5: MCP Logging Tools
**Goal**: User can log climbing sessions and ascents through natural conversation with Claude using MCP tools
**Depends on**: Phase 2
**Requirements**: LOG-01, LOG-02, LOG-03, LOG-04, LOG-06, MCP-01, MCP-06
**Success Criteria** (what must be TRUE):
  1. Claude can log a complete climbing session (location, date, partners, conditions) and individual ascents (route, grade, style, result, notes) via MCP tools
  2. All ascent styles are supported: onsight, flash, redpoint, repeat, attempt, toprope, hangdog
  3. Sessions correctly group ascents by date and location with optional partners and conditions
  4. Photos can be attached to sessions or ascents via MCP tools
  5. Total MCP tool count stays under 12 to ensure reliable LLM tool selection
**Plans**: TBD

### Phase 6: MCP Query Tools & Narratives
**Goal**: Claude can answer questions about climbing history and generate session summaries via MCP read tools
**Depends on**: Phase 5
**Requirements**: LOG-05, MCP-02, MCP-03, MCP-05
**Success Criteria** (what must be TRUE):
  1. Claude can query logbook history with filters (date, grade, location, discipline) via MCP tools
  2. Claude can retrieve aggregated statistics (totals, hardest sends, streaks) via MCP tools
  3. Claude can answer conversational questions like "What's my hardest onsight this year?" using MCP read tools
  4. Claude generates session narrative summaries (e.g., "new onsight PB at 6b+, 5 routes at Frankenjura")
**Plans**: TBD

### Phase 7: Dashboard
**Goal**: Users can view their climbing history and session details on a responsive web dashboard
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Session timeline shows chronological list of sessions with date, location, ascent count, and highlight send
  2. Clicking a session expands to show full ascent list and attached photos
  3. Dashboard is served as static HTML/JS/CSS files by Nginx with no build step required
  4. Layout is responsive and usable on mobile browsers
**Plans**: TBD
**UI hint**: yes

### Phase 8: Deployment & CI/CD
**Goal**: Application runs in production on a VPS with TLS, automated deployment, and database backups
**Depends on**: Phase 7
**Requirements**: INFRA-03, INFRA-04, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):
  1. Nginx reverse proxy terminates TLS with Let's Encrypt certificates
  2. GitHub Actions CI runs ruff lint, ruff format check, and pytest on every push
  3. Pushing to main triggers automatic deployment to the VPS
  4. Backup script performs pg_dump for the database and rsync for photos, and can be scheduled via cron
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
Note: Phases 4, 5, and 7 form parallel tracks after Phase 2 (REST API track vs MCP track), but are numbered sequentially for simplicity.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Schema | 1/3 | In Progress|  |
| 2. Services & Route Resolution | 0/? | Not started | - |
| 3. Data Import | 0/? | Not started | - |
| 4. REST API & Auth | 0/? | Not started | - |
| 5. MCP Logging Tools | 0/? | Not started | - |
| 6. MCP Query Tools & Narratives | 0/? | Not started | - |
| 7. Dashboard | 0/? | Not started | - |
| 8. Deployment & CI/CD | 0/? | Not started | - |
