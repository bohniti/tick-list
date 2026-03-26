# Pitfalls Research

**Domain:** Climbing logbook with MCP server, FastAPI, PostgreSQL+PostGIS, grade normalization, LLM-first interaction
**Researched:** 2026-03-26
**Confidence:** HIGH (most pitfalls verified across multiple sources)

## Critical Pitfalls

### Pitfall 1: MCP Tool Explosion Confuses Claude's Tool Selection

**What goes wrong:**
Designing too many fine-grained MCP tools (e.g., separate tools for `create_session`, `add_ascent`, `set_grade`, `attach_photo`, `link_route`, `search_routes`, `search_crags`, `get_grade_pyramid`, etc.) causes Claude to misselect tools, hallucinate parameters, or chain tools incorrectly. Research shows tool selection accuracy degrades significantly above 30 tools, and models virtually fail above 100.

**Why it happens:**
Developers mirror their REST API endpoints 1:1 as MCP tools. A climbing logbook has many entities (sessions, ascents, routes, crags, photos, topos) and it feels natural to expose CRUD for each. But LLMs are not API clients -- they need task-oriented tools, not entity-oriented ones.

**How to avoid:**
- Design around user intents, not database entities. A single `log_climbing_session` tool that accepts a full session with nested ascents is better than separate `create_session` + `add_ascent` tools.
- Keep total tool count under 15. Aim for 8-12 tools covering: log session, search routes, query stats, manage photos, lookup crags.
- Use rich parameter schemas with optional fields rather than separate tools for variations.
- Return only essential fields in tool responses -- full route objects with all metadata waste context window space.

**Warning signs:**
- Claude frequently calls the wrong tool or calls tools in unexpected order.
- Claude hallucinates parameter names or values.
- You find yourself writing "disambiguation" logic in tool descriptions.
- Tool descriptions start overlapping ("use this to add a route" vs "use this to create a route").

**Phase to address:**
Phase 1 (MCP server design). Tool interface design must happen before implementation. Changing tool interfaces later breaks Claude's learned patterns.

---

### Pitfall 2: Grade Conversion Treated as a Simple Lookup Table

**What goes wrong:**
Building grade normalization as a flat bidirectional mapping (French 6a = YDS 5.10a = UIAA VII-) and discovering it breaks for edge cases: sub-grades (+/-) don't align between systems, UIAA has 2 increments per numeric grade while French has 6, bouldering scales (Font/V-scale) have completely different progression curves, and grades above 5.14d/9a have no agreed UIAA equivalent.

**Why it happens:**
The most visible grade conversion charts (Wikipedia, climbing websites) present clean 1:1 tables. In reality, conversions are approximate ranges, not exact equivalences. A French 6b+ maps to a range of YDS 5.10c-5.10d, not one value. Regional softness/stiffness (Kalymnos vs Ceuse grading) adds another layer.

**How to avoid:**
- Use a numeric scoring system as the canonical internal representation (as the existing blog JS code already does). Every grade maps TO a numeric score, and display-time conversion goes FROM numeric score to the requested system.
- Accept that conversions are lossy. Store the original grade AND its system alongside the numeric score. Never discard the original.
- Define the numeric scale granularity to match French sport grades (the most granular common system: 6 sub-grades per number). Map coarser systems to the nearest score.
- Separate sport/trad grades from bouldering grades entirely -- they are different scales measuring different things.
- Handle "unknown" or custom gym grades as a nullable score.

**Warning signs:**
- Grade conversion unit tests only cover "happy path" (6a, 6b, 6c) and skip edge cases (4, 5+, 9a+).
- The conversion function is bidirectional and tries to round-trip (French -> UIAA -> French should return original, but often doesn't).
- Bouldering and sport grades share the same conversion table.

**Phase to address:**
Phase 1 (data model and core utilities). The grade normalization module is a dependency for CSV import, route creation, and all visualization. Get it right before building on top.

---

### Pitfall 3: GeoAlchemy2 + Alembic Auto-Migration Generates Broken Migrations

**What goes wrong:**
Running `alembic revision --autogenerate` with GeoAlchemy2 geometry columns produces migrations that fail on execution. Specifically: (1) duplicate spatial index creation (PostGIS auto-creates indexes on geometry columns, but Alembic also generates explicit `CREATE INDEX` statements), (2) missing `from geoalchemy2 import Geometry` imports in migration files, and (3) Alembic trying to manage PostGIS internal schemas/tables.

**Why it happens:**
Alembic's autogenerate doesn't natively understand PostGIS spatial column semantics. GeoAlchemy2 provides helper functions for this, but they must be explicitly configured in `env.py`. Most tutorials skip this step.

**How to avoid:**
- Configure GeoAlchemy2's Alembic helpers in `env.py`: use `include_object` to filter PostGIS internal objects, `render_item` to correctly render Geometry types, and `process_revision_directives` to handle spatial indexes.
- Always review generated migrations before running them. Remove duplicate spatial index operations.
- Add GeoAlchemy2 to Alembic's `script.py.mako` template imports so every migration file has the correct import.
- Test migrations against a fresh database in CI, not just against your development database.

**Warning signs:**
- First migration works (creating tables), but subsequent migrations fail.
- `alembic upgrade head` produces "relation already exists" errors for spatial indexes.
- Migrations reference `geoalchemy2.types.Geometry` but the import is missing.

**Phase to address:**
Phase 1 (database schema and migrations). Must be configured correctly before the first migration is committed.

---

### Pitfall 4: LLM Silently Invents Route Data Instead of Asking for Clarification

**What goes wrong:**
When a user says "I climbed a 6a at the crag near Arco today," Claude fills in plausible-sounding but fabricated route names, exact GPS coordinates, and sector names rather than asking "which route?" or searching the database. The logbook accumulates hallucinated data that looks real but is wrong.

**Why it happens:**
LLMs are completion engines -- they prefer generating plausible output over admitting uncertainty. Without explicit tool design that forces a search-then-confirm flow, Claude will happily fabricate a route named "Via del Sole" at made-up coordinates because that sounds like something near Arco.

**How to avoid:**
- Design the `log_climbing_session` tool to require a `route_id` (from local DB or OpenBeta lookup) OR explicit `route_name` + `grade` + `crag_name` for new routes. Never accept just a description.
- Implement the three-tier resolution as a separate `resolve_route` tool that Claude must call first: (1) search local DB, (2) search OpenBeta, (3) return "not found, please provide details."
- In tool descriptions, explicitly instruct: "If the route is not found in search results, ask the user for the route name, grade, and crag. Do NOT invent route data."
- Mark routes created from conversation (vs. imported or OpenBeta-matched) with a `source` field so hallucinated data can be identified and corrected later.

**Warning signs:**
- Routes appear in the database with suspiciously perfect data that was never confirmed with the user.
- Multiple routes at the same crag have slightly different GPS coordinates (hallucinated independently each time).
- Route names don't match any known guidebook.

**Phase to address:**
Phase 2 (route resolution and MCP tool refinement). Requires working DB search + OpenBeta integration to implement the resolution chain.

---

### Pitfall 5: FastMCP + FastAPI Mount Path Doubling and CORS Conflicts

**What goes wrong:**
Mounting FastMCP at `/mcp` results in the actual endpoint being at `/mcp/mcp` due to path prefix doubling. Separately, adding `CORSMiddleware` to the main FastAPI app conflicts with FastMCP's built-in CORS handling for OAuth routes, causing 404 errors on `.well-known` routes and broken OPTIONS preflight requests.

**Why it happens:**
FastMCP internally defines its own route prefix. When mounted as a sub-application in FastAPI, the parent mount path stacks with the internal prefix. The CORS issue stems from middleware ordering -- FastAPI's global CORS middleware intercepts requests before they reach the FastMCP sub-app.

**How to avoid:**
- Mount FastMCP at the root (`/`) or carefully test the actual resulting paths before committing.
- Use the sub-app pattern: mount REST API and FastMCP as separate sub-applications, each with their own middleware stacks, rather than adding global middleware.
- Use `combine_lifespans` to merge FastAPI's lifespan (DB connection pool setup/teardown) with FastMCP's lifespan -- do not replace one with the other.
- Test MCP connectivity with the MCP Inspector tool before building Claude Desktop integration.

**Warning signs:**
- MCP client (Claude Desktop) gets 404 errors connecting to the server.
- CORS preflight requests fail but direct requests work.
- Lifespan events (DB pool init) don't fire or fire twice.

**Phase to address:**
Phase 1 (project scaffolding). The FastAPI + FastMCP mount configuration is foundational -- get it right in the skeleton before adding tools.

---

### Pitfall 6: Async/Sync Mismatch Between FastMCP Tools and SQLAlchemy Sessions

**What goes wrong:**
FastMCP tools are async by default. If the database layer uses synchronous SQLAlchemy sessions (the `Session` class, not `AsyncSession`), calling database operations from async MCP tool handlers blocks the event loop. With a single-process architecture serving both MCP and REST, this means one slow MCP tool call blocks all REST API requests.

**Why it happens:**
SQLAlchemy 2.0 supports both sync and async, and many tutorials/examples use sync sessions. It works fine in testing (single request at a time) but fails under concurrent load. The single-process constraint in this project makes it especially dangerous since MCP and REST share the event loop.

**How to avoid:**
- Use `create_async_engine` with `asyncpg` driver and `async_sessionmaker` from the start. Do not start with sync and plan to migrate later.
- Use FastAPI's dependency injection (`Depends(get_session)`) for REST routes and a similar async session factory for MCP tool handlers.
- Configure pool settings explicitly: `pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800` as starting points for a single-user app.
- If any library forces sync (e.g., a sync-only OpenBeta client), wrap it in `asyncio.to_thread()` rather than calling it directly.

**Warning signs:**
- Dashboard loads slowly when a Claude conversation is actively logging climbs.
- "QueuePool limit exceeded" errors under light load.
- MCP tool calls time out sporadically.

**Phase to address:**
Phase 1 (database layer setup). The async engine and session factory must be established in the initial scaffolding.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded grade conversion table instead of data-driven config | Fast to implement | Every new grade or correction requires code change + deploy | Never -- use a JSON/YAML config or DB table from the start |
| Skipping Alembic and using `create_all()` | Faster initial setup | No migration path; schema changes require DB rebuild or manual SQL | Only for the first 48 hours of prototyping, then switch |
| Storing coordinates as two float columns instead of PostGIS geometry | Simpler model, no GeoAlchemy2 dependency | Cannot use spatial indexes, ST_DWithin, or any PostGIS functions; must rewrite to add crag-finding features | Never -- PostGIS is a core requirement |
| Returning full ORM objects from MCP tools (all fields) | Less code (no response shaping) | Wastes Claude's context window, may leak internal IDs or metadata | MVP only; add response schemas before dashboard phase |
| Using sync SQLAlchemy with `run_sync` wrapper | Can reuse existing sync code | Wrapper overhead, harder to debug, blocks event loop in edge cases | Never for this project's single-process architecture |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenBeta GraphQL | Treating it as reliable/always-available; building flows that fail without it | OpenBeta is optional enrichment. Every code path must work with local DB only. Cache OpenBeta results locally on first fetch. Handle API downtime with a 3-second timeout and graceful fallback. |
| Claude Vision (topo analysis) | Expecting structured JSON output from image analysis without validation | Vision output is best-effort. Always validate extracted route names/grades against known data. Store raw vision output alongside structured extraction for later correction. |
| Leaflet.js + PostGIS | Fetching all crag points as GeoJSON on page load | Use bounding-box queries: fetch only crags visible in the current map viewport. For 400 routes across Europe, this is premature optimization but becomes necessary if the dataset grows. Implement from the start as it is not much harder. |
| CSV historical import | Running import as a one-shot script with no idempotency | Make import idempotent using a composite unique key (route name + crag + date + grade). Support re-running import after bug fixes without creating duplicates. |
| FastMCP + Claude Desktop | Testing only via HTTP; not testing the actual stdio/SSE transport that Claude Desktop uses | Test with MCP Inspector and Claude Desktop early. Transport-layer issues (SSE connection drops, message framing) won't appear in HTTP unit tests. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 queries loading sessions with ascents and routes | Dashboard session timeline takes 2+ seconds | Use `selectinload` or `joinedload` on session->ascent->route relationships | At 100+ sessions (within first year of use) |
| Unindexed grade score column | Grade pyramid query scans full ascents table | Add index on `numeric_grade_score`; it is the primary filter/group-by column for visualizations | At 500+ ascents |
| PostGIS queries without spatial index | "Crags near me" query takes seconds instead of milliseconds | GiST index on geometry columns; created automatically by PostGIS if using GeoAlchemy2 correctly, but verify | At 100+ crags with point geometries |
| Loading all chart data on dashboard page load | Initial dashboard load is slow, fetches all data for all charts | Lazy-load chart data: fetch grade pyramid on tab click, not page load; use date-range filters | At 2+ years of climbing data |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Bearer token in MCP tool responses visible to Claude | Token leaks into Claude conversation history (Anthropic can see it in their logs) | Never include auth tokens in tool responses. Auth should be handled at the transport layer (HTTP headers), not in tool parameters or results. |
| Bearer token hardcoded in Docker Compose or checked into git | Token exposed in repository history | Use environment variables via `.env` file (in `.gitignore`). Use Docker secrets or env_file directive. |
| No rate limiting on REST API | Single-user app, but if exposed to internet, bots can hammer it | Nginx rate limiting (`limit_req_zone`) on the reverse proxy layer. Simple and sufficient for single-user. |
| MCP tools that accept arbitrary SQL or filter expressions | SQL injection via natural language ("show me routes where name = ''; DROP TABLE routes;--") | Never pass LLM-generated strings directly to SQL. Use parameterized queries only. MCP tools should accept typed parameters (route_id: int, grade: str) never raw query fragments. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Grade pyramid shows only French grades when user climbs across UIAA and French areas | Pyramid is confusing -- user sees unfamiliar grades for routes they know by UIAA number | Always show grades in the system the route was originally graded in, with the normalized numeric score for ordering. Allow user to set a "display preference" for the dashboard. |
| Ascent style (onsight/flash/redpoint) not prominent in visualizations | Grade pyramid without style breakdown looks flat and uninteresting; hides the difference between a 6a onsight and a 6a redpoint (which are very different achievements) | Stack the grade pyramid by ascent style using color coding. This is a table-stakes differentiator from generic logbooks. |
| Session logging requires too many confirmations | "Did you mean X? Please confirm Y. Is this correct?" turns a 30-second voice log into a 5-minute interrogation | Design for "log first, correct later." Accept plausible data optimistically, flag low-confidence entries for review on the dashboard. Batch confirmation: "I logged 5 routes at Frankenjura today -- here's what I captured, anything wrong?" |
| Map shows raw coordinate clusters with no visual hierarchy | 400 points on a European map is visual noise | Cluster markers at low zoom levels (Leaflet.markercluster). Show individual crags only when zoomed into a region. Color-code by recency or max grade. |

## "Looks Done But Isn't" Checklist

- [ ] **Grade normalization:** Handles sub-grades (6a, 6a+, 6b, 6b+, 6c, 6c+) not just base grades (6a, 6b, 6c) -- verify with conversion round-trip tests
- [ ] **Grade normalization:** Bouldering grades (Font 6A = V4-ish) are separate from sport grades (French 6a = YDS 5.10a) -- verify they don't share a conversion table
- [ ] **CSV import:** Handles the 7% of routes (36/422) without GPS coordinates gracefully -- verify they appear in session timeline but not on map
- [ ] **MCP tools:** Return human-readable confirmation messages, not raw JSON -- verify Claude can naturally summarize what was logged
- [ ] **PostGIS setup:** `CREATE EXTENSION postgis` is in the first Alembic migration -- verify fresh `alembic upgrade head` works on empty database
- [ ] **Docker Compose:** PostgreSQL data volume is a named volume, not a bind mount to a temp directory -- verify data survives `docker compose down && docker compose up`
- [ ] **Dashboard auth:** Bearer token is validated on every REST endpoint, not just the index page -- verify API calls without token return 401
- [ ] **Session timezone:** Climbing session dates are stored in UTC with user timezone context -- verify a session logged at "6pm" in Sicily shows correctly on dashboard

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Hallucinated route data in DB | LOW | Add `source` and `confidence` fields to routes. Query for `source='conversation'` entries. Review and correct on dashboard. Flag suspected hallucinations by checking if route exists in OpenBeta. |
| Wrong grade conversion mapping | MEDIUM | Fix the conversion config. Write a migration script that recalculates all `numeric_grade_score` values from the stored original grade + system. Re-verify with spot checks. |
| Broken Alembic migration history | HIGH | If migrations are broken beyond repair: dump data with `pg_dump`, recreate schema from models with fresh migration, restore data. Prevention is far cheaper. |
| MCP tool interface redesign | MEDIUM | Tool name/parameter changes require updating Claude Desktop config. But conversation history with old tool names is fine (Claude adapts). Main cost is rewriting tool handler code. |
| Sync-to-async database migration | HIGH | Requires rewriting every database call, changing session management, potentially changing the DB driver (psycopg2 -> asyncpg). Affects every layer. Start async from day one. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| MCP tool explosion | Phase 1: MCP server design | Tool count is under 15; Claude successfully logs a multi-route session in one conversation turn |
| Grade conversion as flat lookup | Phase 1: Data model + utilities | Unit tests cover all grade systems including edge cases (sub-grades, missing equivalents, bouldering vs sport) |
| GeoAlchemy2 + Alembic broken migrations | Phase 1: DB scaffolding | `alembic upgrade head` succeeds on empty DB; `alembic downgrade base` succeeds; CI runs both |
| LLM hallucinating route data | Phase 2: Route resolution | Claude calls `resolve_route` before `log_session`; "not found" response triggers clarification question, not fabrication |
| FastMCP mount path / CORS | Phase 1: Project skeleton | MCP Inspector connects successfully; REST API returns correct CORS headers; no path doubling |
| Async/sync mismatch | Phase 1: Database layer | All DB operations use `AsyncSession`; no `run_sync` wrappers in codebase; load test shows concurrent MCP + REST requests work |
| N+1 queries on dashboard | Phase 3: Dashboard API | Session timeline endpoint executes 1-2 SQL queries regardless of session count (check with SQLAlchemy echo logging) |
| Bearer token leakage | Phase 1: Auth setup | Token never appears in MCP tool response payloads; grep codebase for token value patterns |

## Sources

- [FastMCP + FastAPI Integration Guide](https://gofastmcp.com/integrations/fastapi) -- mount path, CORS, lifespan handling
- [AWS MCP Tool Design Strategy](https://docs.aws.amazon.com/prescriptive-guidance/latest/mcp-strategies/mcp-tool-strategy.html) -- tool granularity guidelines
- [Why Less is More for MCP (Speakeasy)](https://www.speakeasy.com/mcp/tool-design/less-is-more) -- tool count thresholds (30 tools = degradation)
- [The MCP Tool Trap](https://jentic.com/blog/the-mcp-tool-trap) -- tool overload consequences
- [GeoAlchemy2 Alembic Documentation](https://geoalchemy-2.readthedocs.io/en/stable/alembic.html) -- migration helpers and duplicate index issues
- [PostGIS Performance Tips](https://postgis.net/docs/performance_tips.html) -- spatial indexing, VACUUM, clustering
- [theCrag Grade Conversion Reference](https://www.thecrag.com/en/article/grades) -- grade system complexity and regional variation
- [Wikipedia: Climbing Grades](https://en.wikipedia.org/wiki/Grade_(climbing)) -- system differences, sub-grade granularity
- [Cleanlab: LLM Structured Output Benchmarks](https://cleanlab.ai/blog/structured-output-benchmark/) -- hallucination in structured extraction
- [FastAPI Async Database Sessions](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e) -- async session management patterns
- [FastMCP Issue #2961](https://github.com/PrefectHQ/fastmcp/issues/2961) -- integration configuration issues

---
*Pitfalls research for: Climbing logbook MCP server with FastAPI, PostgreSQL+PostGIS, grade normalization*
*Researched: 2026-03-26*
