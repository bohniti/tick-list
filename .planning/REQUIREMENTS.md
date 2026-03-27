# Requirements: Climbing Diary

**Defined:** 2026-03-26
**Core Value:** Log climbs through natural conversation with Claude and see your progression on a dashboard — no forms, no manual entry.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Logging

- [ ] **LOG-01**: User can log a climbing session via Claude conversation (location, date, partners, conditions)
- [ ] **LOG-02**: User can log individual ascents within a session (route, grade, style, result, notes)
- [ ] **LOG-03**: Ascent styles supported: onsight, flash, redpoint, repeat, attempt, toprope, hangdog
- [ ] **LOG-04**: User can attach photos to sessions or ascents (topo, send, crag, action, beta, selfie)
- [ ] **LOG-05**: Claude generates session narrative summaries ("new onsight PB at 6b+, 5 routes at Frankenjura")
- [ ] **LOG-06**: Sessions group ascents by date + location with optional partners and conditions

### Routes & Grades

- [x] **ROUTE-01**: Routes stored in local PostgreSQL with name, grade, discipline, location, pitches
- [x] **ROUTE-02**: Grade normalization across French, UIAA, YDS, Font, V-scale with numeric scoring
- [ ] **ROUTE-03**: Three-tier route resolution: local DB first, then OpenBeta GraphQL, then Claude creates new entry
- [x] **ROUTE-04**: Locations stored hierarchically (area > crag > sector) with PostGIS coordinates
- [ ] **ROUTE-05**: Spatial queries: find crags within N km of a given point
- [x] **ROUTE-06**: Disciplines supported: sport, trad, boulder, multipitch, ice, mixed

### MCP Server

- [ ] **MCP-01**: FastMCP server exposes tools to Claude for logging sessions and ascents
- [ ] **MCP-02**: MCP tools for querying logbook history with filters (date, grade, location, discipline)
- [ ] **MCP-03**: MCP tools for retrieving aggregated statistics (totals, hardest sends, streaks)
- [ ] **MCP-04**: MCP server and REST API share a single service layer — business logic written once
- [ ] **MCP-05**: Claude can answer conversational queries ("What's my hardest onsight this year?") via MCP read tools
- [ ] **MCP-06**: Tool count stays under 12 to ensure reliable LLM tool selection

### Dashboard

- [ ] **DASH-01**: Session timeline showing chronological list of sessions with date, location, ascent count, highlight send
- [ ] **DASH-02**: Expandable session detail view with full ascent list and attached photos
- [ ] **DASH-03**: Dashboard served as static files (HTML/JS/CSS) by Nginx — no build step
- [ ] **DASH-04**: Responsive layout that works on mobile browser

### REST API

- [ ] **API-01**: List sessions (paginated, filterable by date, location)
- [ ] **API-02**: Get session detail with ascents and photos
- [ ] **API-03**: List ascents (filterable by grade, style, date, discipline)
- [ ] **API-04**: List locations with coordinates
- [ ] **API-05**: Serve photo files via API endpoint
- [ ] **API-06**: Statistics endpoints: summary totals, streaks, hardest sends

### Data Import

- [ ] **IMPORT-01**: Import ~422 historical routes from unified CSV (Vertical Life + Mountain Project data)
- [ ] **IMPORT-02**: CSV import handles existing French-normalized grades, coordinates, styles, sources
- [ ] **IMPORT-03**: Import creates sessions, ascents, routes, and locations from CSV rows

### Infrastructure

- [ ] **INFRA-01**: Bearer token authentication on all API/MCP endpoints
- [x] **INFRA-02**: Docker Compose deployment: PostgreSQL 17 + PostGIS + FastAPI + Nginx
- [ ] **INFRA-03**: Nginx reverse proxy with Let's Encrypt TLS termination
- [ ] **INFRA-04**: GitHub Actions CI pipeline: ruff lint, ruff format, pytest
- [ ] **INFRA-05**: GitHub Actions CD: auto-deploy to VPS on push to main
- [ ] **INFRA-06**: Backup script: pg_dump for database + rsync for photos
- [x] **INFRA-07**: SQLAlchemy 2.0 async models + Alembic migrations with GeoAlchemy2

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Dashboard Visualizations

- **VIZ-01**: Grade pyramid chart (horizontal bars by grade, stacked by ascent style)
- **VIZ-02**: Crag map (Leaflet + PostGIS, pins colored by session count, click for details)
- **VIZ-03**: Progression chart (hardest send per month over time, volume overlay)
- **VIZ-04**: Dashboard filters (date range, discipline, location)
- **VIZ-05**: Multi-grade display toggle (French/UIAA/YDS in dashboard)

### Advanced MCP

- **MCP-07**: Claude Vision analyzes topo images to extract route names, grades, line positions
- **MCP-08**: Analyzed topo data stored in DB for downstream analysis projects
- **MCP-09**: Route suggestion: Claude suggests unclimbed routes near your grade at a crag
- **MCP-10**: Smart context: Claude references your climbing history in conversation

### Data Management

- **DATA-01**: CSV/JSON export endpoint for full data portability
- **DATA-02**: OpenBeta enrichment: auto-lookup and cache route data from API
- **DATA-03**: OpenBeta contribution path: batch-push locally created routes upstream

## Out of Scope

| Feature | Reason |
|---------|--------|
| iOS/Android native app | Web dashboard via mobile browser; no $99/yr Apple Developer fee |
| Multi-user support | Single-user personal tool — no OAuth, no user management |
| Social features (followers, feed, sharing) | Single-user; massive scope increase for zero personal value |
| Rankings and leaderboards | Nobody to rank against in single-user tool |
| Training plans / workout tracking | Different domain; defer to specialized tools (intervals.icu) |
| Indoor gym route scanning | Requires gym partnerships and proprietary integrations |
| Real-time GPS tracking | Requires native app or watch integration |
| Garmin / Strava / intervals.icu integration | Separate MCP server, can be added as future milestone |
| Pitch-by-pitch multipitch logging | Log as single ascent with pitch count; add detail in notes |
| Aid climbing / via ferrata / DWS | Niche subtypes; can add as enum values later if needed |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOG-01 | Phase 5 | Pending |
| LOG-02 | Phase 5 | Pending |
| LOG-03 | Phase 5 | Pending |
| LOG-04 | Phase 5 | Pending |
| LOG-05 | Phase 6 | Pending |
| LOG-06 | Phase 5 | Pending |
| ROUTE-01 | Phase 1 | Complete |
| ROUTE-02 | Phase 1 | Complete |
| ROUTE-03 | Phase 2 | Pending |
| ROUTE-04 | Phase 1 | Complete |
| ROUTE-05 | Phase 2 | Pending |
| ROUTE-06 | Phase 1 | Complete |
| MCP-01 | Phase 5 | Pending |
| MCP-02 | Phase 6 | Pending |
| MCP-03 | Phase 6 | Pending |
| MCP-04 | Phase 2 | Pending |
| MCP-05 | Phase 6 | Pending |
| MCP-06 | Phase 5 | Pending |
| DASH-01 | Phase 7 | Pending |
| DASH-02 | Phase 7 | Pending |
| DASH-03 | Phase 7 | Pending |
| DASH-04 | Phase 7 | Pending |
| API-01 | Phase 4 | Pending |
| API-02 | Phase 4 | Pending |
| API-03 | Phase 4 | Pending |
| API-04 | Phase 4 | Pending |
| API-05 | Phase 4 | Pending |
| API-06 | Phase 4 | Pending |
| IMPORT-01 | Phase 3 | Pending |
| IMPORT-02 | Phase 3 | Pending |
| IMPORT-03 | Phase 3 | Pending |
| INFRA-01 | Phase 4 | Pending |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 8 | Pending |
| INFRA-04 | Phase 8 | Pending |
| INFRA-05 | Phase 8 | Pending |
| INFRA-06 | Phase 8 | Pending |
| INFRA-07 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38/38
- Unmapped: 0

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after roadmap creation*
