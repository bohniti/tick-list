# Phase 1: Foundation & Schema - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 01-foundation-schema
**Areas discussed:** Grade normalization, Location hierarchy, Session & ascent model, Project skeleton, Photo storage, Database conventions, Testing approach, Docker Compose setup

---

## Grade Normalization

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse blog's scale | Port existing numeric mapping from blog JS code, extend to other systems | ✓ |
| Linear integer scale | Simple 1-100 integers, may lose sub-grade nuance | |
| You decide | Claude picks a sensible scale | |

**User's choice:** Reuse blog's scale
**Notes:** Ensures historical consistency with existing dataset

---

| Option | Description | Selected |
|--------|-------------|----------|
| Store original + normalized | Keep original grade string plus normalized French + score | |
| French is canonical | Everything converts to French on input, original system as metadata | ✓ |
| You decide | Claude picks | |

**User's choice:** French is canonical
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Separate scales | Bouldering and route on different numeric axes | ✓ |
| Unified scale | One numeric axis for everything | |
| You decide | Claude picks | |

**User's choice:** Separate scales
**Notes:** Font 6A is not comparable to French 6a

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full modifier support | Handle +, -, /, letter suffixes | ✓ |
| Base grades only | Normalize to base grades only | |
| You decide | Claude picks | |

**User's choice:** Full modifier support
**Notes:** Existing data has these modifiers

---

| Option | Description | Selected |
|--------|-------------|----------|
| Single grade + pitch count | Route has one grade plus pitches integer | ✓ |
| Grade per pitch (JSONB) | Optional array of per-pitch grades | |
| You decide | Claude picks | |

**User's choice:** Single grade + pitch count
**Notes:** User asked about multipitch handling. Matches Out of Scope decision on pitch-by-pitch logging.

---

## Location Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Single table, self-referential | One locations table with parent_id and type enum | |
| Separate tables per level | Three tables: areas, crags, sectors | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide
**Notes:** Claude recommended self-referential approach

---

| Option | Description | Selected |
|--------|-------------|----------|
| Every level gets coordinates | Area, crag, sector each have PostGIS point | ✓ |
| Leaf nodes only | Only most specific location has coordinates | |
| You decide | Claude picks | |

**User's choice:** Every level gets coordinates
**Notes:** Enables map zoom levels

---

| Option | Description | Selected |
|--------|-------------|----------|
| Country as top level | Hierarchy: country > area > crag > sector | ✓ |
| Area is the top level | Area > crag > sector, country as text field | |
| You decide | Claude picks | |

**User's choice:** Country as top level
**Notes:** User climbs across multiple countries

---

## Session & Ascent Model

| Option | Description | Selected |
|--------|-------------|----------|
| Text field | Simple text/array field on session | ✓ |
| Partners table with FK | Dedicated partners table with M2M join | |
| You decide | Claude picks | |

**User's choice:** Text field for partners
**Notes:** Partners are informational, not queryable entities

---

| Option | Description | Selected |
|--------|-------------|----------|
| Freeform notes field | Text field for conditions | ✓ |
| Structured fields | Dedicated weather/temp/humidity columns | |
| You decide | Claude picks | |

**User's choice:** Freeform notes field
**Notes:** Matches conversational logging approach

---

| Option | Description | Selected |
|--------|-------------|----------|
| Single style enum | One field: onsight, flash, redpoint, etc. Style implies result | ✓ |
| Separate style + result | Two fields for how and outcome | |
| You decide | Claude picks | |

**User's choice:** Single style enum
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Optional stars field | 1-5 star rating on ascents | ✓ |
| No rating field | Skip, use notes for opinions | |
| You decide | Claude picks | |

**User's choice:** Optional stars field
**Notes:** Useful for "show me my best-rated routes" queries

---

## Project Skeleton

| Option | Description | Selected |
|--------|-------------|----------|
| climbing_diary | Matches project name | |
| tick_list | Climbing term, shorter | ✓ |
| You decide | Claude picks | |

**User's choice:** tick_list
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Flat modules | Single package with models.py, services.py, etc. | ✓ |
| Domain packages | Sub-packages per domain (sessions/, routes/) | |
| You decide | Claude picks | |

**User's choice:** Flat modules
**Notes:** Good for a single-user app of this size

---

| Option | Description | Selected |
|--------|-------------|----------|
| static/ at project root | Nginx serves directly | ✓ |
| tick_list/static/ | Inside Python package | |
| frontend/ | Separate top-level directory | |

**User's choice:** static/ at project root
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pydantic Settings + .env | Load from env vars / .env file | ✓ |
| TOML config file | config.toml loaded at startup | |
| You decide | Claude picks | |

**User's choice:** Pydantic Settings + .env
**Notes:** Standard FastAPI pattern, works with Docker Compose

---

## Photo Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Local filesystem | data/photos/ directory, Docker volume mount | ✓ |
| PostgreSQL large objects | Store bytes in DB | |
| You decide | Claude picks | |

**User's choice:** Local filesystem
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| UUID filenames | Flat directory, data/photos/{uuid}.jpg | ✓ |
| Date-based directories | data/photos/2026/03/27/{uuid}.jpg | |
| You decide | Claude picks | |

**User's choice:** UUID filenames
**Notes:** Metadata in DB, not in file paths

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, with Pillow | Generate 400px thumbnail on upload | ✓ |
| No thumbnails | Serve originals everywhere | |
| You decide | Claude picks | |

**User's choice:** Yes, with Pillow
**Notes:** Dashboard loads thumbnails in lists

---

## Database Conventions

| Option | Description | Selected |
|--------|-------------|----------|
| UUID | UUID PKs everywhere | ✓ |
| Auto-increment integers | Classic integer PKs | |
| You decide | Claude picks | |

**User's choice:** UUID
**Notes:** No sequential IDs in API responses

---

| Option | Description | Selected |
|--------|-------------|----------|
| Hard deletes | DELETE removes the row | ✓ |
| Soft deletes | Set deleted_at timestamp | |
| You decide | Claude picks | |

**User's choice:** Hard deletes
**Notes:** Single-user, backups cover accidents

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, on all tables | created_at + updated_at everywhere | ✓ |
| Only where needed | Only on sessions and ascents | |
| You decide | Claude picks | |

**User's choice:** Yes, on all tables
**Notes:** None

---

## Testing Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Testcontainers | Real PostgreSQL+PostGIS per test session | ✓ |
| SQLite in-memory | Fast but no PostGIS | |
| Shared dev DB | Use Docker Compose instance | |
| You decide | Claude picks | |

**User's choice:** Testcontainers
**Notes:** Catches migration and PostGIS issues

---

| Option | Description | Selected |
|--------|-------------|----------|
| Grade module + migrations | Focus on tricky logic and schema correctness | ✓ |
| Full coverage from day one | Test everything including endpoints | |
| You decide | Claude picks | |

**User's choice:** Grade module + migrations
**Notes:** Skip API endpoint tests until Phase 4

---

## Docker Compose Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Single file + override | Base + override for dev extras | ✓ |
| Separate files | dev.yml and prod.yml | |
| You decide | Claude picks | |

**User's choice:** Single file + override
**Notes:** Standard Docker pattern

---

| Option | Description | Selected |
|--------|-------------|----------|
| App local, DB in Docker | Run FastAPI locally, PostgreSQL in Docker | ✓ |
| Everything in Docker | App + DB both containerized | |
| You decide | Claude picks | |

**User's choice:** App local, DB in Docker
**Notes:** Faster iteration, no container rebuild

---

## Claude's Discretion

- Location table design approach (self-referential vs separate tables)

## Deferred Ideas

None — discussion stayed within phase scope
