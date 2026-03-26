# Climbing Diary

## What This Is

A personal climbing logbook and unified fitness data platform. You log climbs by talking to Claude — mentioning routes, grades, topos, photos — and an MCP server persists structured data into PostgreSQL. A web dashboard visualizes your climbing history: grade pyramid, crag map, progression charts, session timeline. Single-user, self-hosted, you own all your data.

## Core Value

Log climbs through natural conversation with Claude and see your progression on a dashboard — no forms, no manual entry.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Log climbing sessions and ascents via Claude conversation through MCP tools
- [ ] Claude vision analyzes topo images to extract route names, grades, and line positions
- [ ] Store analyzed topo data in the database for downstream analysis projects
- [ ] Attach photos (topos, send pics, crag overviews) to sessions and ascents
- [ ] Three-tier route resolution: local DB → OpenBeta GraphQL → Claude creates from description/topo
- [ ] Grade normalization across French, UIAA, YDS, Font, V-scale systems with numeric scoring for cross-system comparison
- [ ] PostgreSQL + PostGIS as source of truth with spatial queries (crags near a location)
- [ ] REST API serving both MCP server and web dashboard from shared service layer
- [ ] Web dashboard: grade pyramid (stacked by ascent style), crag map (Leaflet + PostGIS), progression charts, session timeline
- [ ] Import ~422 historical routes from unified CSV (Vertical Life + Mountain Project data, already French-normalized with coordinates)
- [ ] Bearer token authentication for single-user access
- [ ] Docker Compose deployment to VPS with Nginx + Let's Encrypt
- [ ] CI/CD via GitHub Actions (lint, test, deploy on push to main)

### Out of Scope

- iOS/Android native app — web dashboard via mobile browser, no $99/year Apple Developer fee
- Multi-user support — single-user personal tool
- intervals.icu / Garmin / Strava integration — separate MCP server, can be added later
- Real-time sync from Garmin watch during climbing sessions
- Real-time chat or WebSocket features

## Context

### Prior work

A unified climbing dataset already exists at `/Users/timo/Development/bohniti.github.io/static/files/dataset.csv` — 422 routes from Vertical Life (404) and Mountain Project (12), with:
- Unified French grading (converted from UIAA, YDS)
- GPS coordinates for 93% of routes (386/416)
- Styles (onsight, redpoint, flash, fell)
- Sources, dates (2017–present), sectors, countries
- Blog visualization at `bohniti.github.io` with Leaflet map, Plotly charts, grade distribution

The existing French grade conversion map and numeric scoring system from the blog JS code can inform the Python grade normalization utility.

### OpenBeta

CC0-licensed climbing route database at `api.openbeta.io`. Strong US coverage (Mountain Project era), sparse European coverage (Sicily, Austria, Fränkische Schweiz). Used as optional enrichment — local DB is always source of truth. Future path: contribute European routes back upstream.

### Climbing profile

Climbs across Europe (Fränkische Schweiz, Sicily, Croatia, Austria) and North America (Squamish). Sport, trad, bouldering, multipitch. Grade range roughly 3a–7a+ French. Primary grading systems encountered: French and UIAA.

### Tech environment

- Python 3.11+, uv, ruff, pytest
- FastAPI + Uvicorn for web framework
- FastMCP for MCP server
- SQLAlchemy 2.0 + Alembic for ORM/migrations
- PostgreSQL 16 + PostGIS for storage
- Vanilla JS or Alpine.js + Chart.js + Leaflet.js for dashboard (no build step)
- Docker Compose for local dev and production
- Nginx + Let's Encrypt for reverse proxy
- VPS deployment via systemd

## Constraints

- **Single process**: MCP server and REST API share one FastAPI process, one service layer, one DB connection pool
- **No build step for frontend**: Dashboard is static files (HTML/JS/CSS) served by Nginx — no webpack, no bundler
- **Self-hosted**: Runs on a personal VPS, not a cloud platform
- **Privacy**: Single-user, bearer token auth, no OAuth complexity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PostgreSQL + PostGIS over SQLite | Spatial queries for crag map, relational schema for sessions→ascents→routes, handles dashboard workload | — Pending |
| Claude as primary UI, dashboard as read-only visualization | Natural language is faster than forms for logging; dashboard is for reflection not data entry | — Pending |
| OpenBeta as optional enrichment, not dependency | European coverage too sparse to rely on; local DB is source of truth | — Pending |
| Store analyzed topo data in DB | Enables future downstream analysis projects beyond just the logbook | — Pending |
| Unified CSV as historical import source | Already normalized from multiple platforms (Vertical Life, Mountain Project) with grades and coordinates | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-26 after initialization*
