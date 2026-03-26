# Feature Research

**Domain:** Personal climbing logbook (MCP server + web dashboard)
**Researched:** 2026-03-26
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features any climbing logbook must have. Missing these makes the product feel broken compared to 8a.nu, TheCrag, Vertical Life, or even a spreadsheet.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Log ascents with route, grade, date, style | Core purpose of a logbook. Every competitor has this. | LOW | Ascent styles: onsight, flash, redpoint, pinkpoint, toprope, attempt/hang, repeat. Must distinguish lead vs toprope. |
| Session grouping | Climbers think in sessions ("Tuesday at the crag"), not individual routes. 8a.nu and TheCrag both group by date/location. | LOW | Session = date + crag + optional partner + notes. Multiple ascents per session. |
| Grade normalization | Climbers encounter French, UIAA, YDS, Font, V-scale. Cross-system comparison is essential for stats. | MEDIUM | Already scoped in PROJECT.md. Numeric scoring enables sorting and pyramids. TheCrag uses Ewbanks internally. |
| Grade pyramid visualization | The single most-requested climbing statistic. TheCrag has it natively; Mountain Project lacks it and users build third-party tools to fill the gap. | MEDIUM | Stacked by ascent style (onsight/flash/redpoint/attempt). Horizontal bar chart, grades on Y axis. |
| Crag and route database | Users need to select from known routes, not type free text every time. Route = name + grade + crag + type (sport/trad/boulder). | MEDIUM | Three-tier resolution already scoped: local DB, OpenBeta, Claude-created. |
| Location/crag management | Crags have names, coordinates, sectors/sub-areas. Needed for map and spatial queries. | MEDIUM | PostGIS already scoped. Hierarchical: area > crag > sector > route. |
| Progression over time | "Am I getting better?" is the fundamental question. TheCrag has CPR timeline; 8a.nu shows score history. | MEDIUM | Max grade over time, volume over time, rolling averages. Chart.js line/area charts. |
| Data import from CSV | Users have history elsewhere. TheCrag, 8a.nu, Mountain Project all export CSV. Must import existing data. | LOW | Already scoped: 422-route unified CSV. Design importer to handle generic CSV too. |
| Data export | GDPR expectation. Users must be able to get their data out. TheCrag and 8a.nu both offer CSV export. | LOW | CSV export endpoint on REST API. |
| Photo attachment | Climbers photograph routes, sends, crags. Every modern app supports photos. | MEDIUM | Attach to session or ascent. Store on filesystem, reference in DB. Serve via Nginx. |
| Climbing type support | Sport, trad, bouldering at minimum. Users climb across disciplines. | LOW | Route-level attribute. Affects which tick types are valid (no "lead" for bouldering). |

### Differentiators (Competitive Advantage)

Features that make this product meaningfully different from existing logbooks. The MCP/LLM-first interaction model is the core differentiator.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Natural language logging via Claude | Zero-form data entry. Say "climbed Blue Monday 6b+ onsight at Frankenjura today" and it becomes structured data. No app has this. | HIGH | Core value prop from PROJECT.md. MCP tools parse conversation into session/ascent/route records. Claude handles ambiguity, asks clarifying questions. |
| Topo image analysis via Claude Vision | Take a photo of a topo, Claude extracts route names, grades, line positions. No competitor does automated topo parsing. | HIGH | Already scoped. Store extracted topo data for downstream analysis. Unique capability. |
| Conversational querying | "What's my hardest onsight this year?" or "How many routes did I climb in Croatia?" answered in conversation, not through UI filters. | MEDIUM | MCP read tools expose query capabilities to Claude. LLM translates natural language to structured queries. |
| Self-hosted, you own all data | 8a.nu/TheCrag/Vertical Life are cloud platforms. Your data lives on their servers. Here, it's your PostgreSQL on your VPS. | LOW | Already a constraint. Appeals to data-sovereignty-minded climbers (especially post-GDPR Europe). |
| OpenBeta integration for route enrichment | Auto-enrich routes with community data (location, description, photos) from the CC0 OpenBeta database. No other personal logbook does this. | MEDIUM | Already scoped as three-tier resolution. Contribute back upstream as future path. |
| Session narrative generation | Claude can summarize a session: "5 routes at Frankenjura, topped out on your project 6c, new onsight PB at 6b+." Logbooks don't narrate. | LOW | Low complexity because Claude does the work. MCP provides session data, Claude generates summary. Nice for journaling. |
| Smart route suggestion from context | Mention a crag name and Claude suggests routes you haven't done, or projects near your grade. Conversational trip planning. | MEDIUM | Requires good route database population. Combines local DB + OpenBeta. |
| Multi-grade-system display | Show grades in user's preferred system with one-click conversion. TheCrag does this well, but most apps lock you to one system. | LOW | Grade normalization table already needed. Dashboard toggle between French/UIAA/YDS/Font. |

### Anti-Features (Commonly Requested, Often Problematic)

Features to deliberately NOT build. These add complexity without serving the single-user personal tool use case.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Social features (followers, feed, sharing) | Every climbing app has social. 8a.nu, Vertical Life, KAYA all center on community. | Single-user tool. Social features require multi-user, moderation, privacy controls. Massive scope increase for zero personal value. | Export data to share; blog integration if desired (existing bohniti.github.io). |
| Rankings and leaderboards | TheCrag has global/local rankings. Motivating for competitive climbers. | Requires population data. Single-user has nobody to rank against. Gamification can distort logging honesty. | Personal milestones and PB tracking instead. Compare against your own history. |
| Training plans and workout tracking | KAYA and MyClimb offer structured training. Hangboard protocols, campus board sessions. | Different domain. Training is not logging. Scope creep into fitness app territory. Already out-of-scope per PROJECT.md (Garmin/intervals.icu separate). | Log training sessions as free-text notes on sessions. Defer structured training to specialized tools. |
| Indoor gym route scanning | TopLogger, Bould specialize in gym integration with QR codes, gym maps, route-setting APIs. | Requires gym partnerships, constantly changing routes, proprietary integrations. Entirely different product. | Log indoor sessions manually with grade + color/name. No gym integration needed. |
| Real-time GPS tracking during climbs | Redpoint auto-detects climbs via barometric sensor. Cool tech. | Requires native app or watch integration. Web dashboard can't do this. Battery drain. Overkill for logging. | Log location via crag selection. GPS coordinates come from route/crag database, not real-time tracking. |
| Guidebook sales / premium content | 27 Crags and KAYA sell digital guidebooks. Revenue model for commercial apps. | Personal tool, not a business. Guidebook licensing is complex. OpenBeta provides free route data. | Use OpenBeta for route data. Reference physical guidebooks by name in notes. |
| Native mobile app | Every competitor has iOS/Android apps. Mobile is where logging happens at the crag. | $99/yr Apple Developer fee. Maintaining two platforms. Already out-of-scope per PROJECT.md. | Mobile browser for dashboard viewing. Logging happens via Claude conversation (works in Claude mobile app). |
| Multi-pitch pitch-by-pitch logging | TheCrag tracks individual pitches with separate grades, leaders, and tick types per pitch. | Significant data model complexity. Relatively rare compared to single-pitch sport/boulder. Niche within a niche. | Log multi-pitch as single ascent with total grade and pitch count. Add pitch details in notes field. Revisit if usage pattern demands it. |
| Aid climbing / via ferrata / DWS | TheCrag supports many climbing subtypes. | Extremely niche for a personal tool. The user's profile is sport/trad/boulder. Adding these clutters the UI for no personal value. | Can be added later as climbing_type enum values if needed. Don't build UI for them now. |

## Feature Dependencies

```
Grade Normalization
    └──requires──> Route Database (routes have grades to normalize)
                       └──requires──> Crag/Location Management (routes belong to crags)

Grade Pyramid Visualization
    └──requires──> Grade Normalization (numeric scores for ordering)
    └──requires──> Ascent Logging (data to visualize)

Progression Charts
    └──requires──> Ascent Logging (timestamped ascents)
    └──requires──> Grade Normalization (comparable numeric values)

Crag Map
    └──requires──> Crag/Location Management (coordinates)
    └──requires──> PostGIS (spatial queries)

Natural Language Logging (MCP)
    └──requires──> Ascent Logging API (structured storage)
    └──requires──> Route Database (route resolution)
    └──requires──> Grade Normalization (parse "6b+" into structured grade)

Topo Image Analysis
    └──requires──> Photo Storage (store topo images)
    └──requires──> Route Database (store extracted routes)

Conversational Querying
    └──requires──> Ascent Logging API (read endpoints)
    └──requires──> REST API (query layer)

CSV Import
    └──requires──> Route Database + Crag Management (destination tables)
    └──requires──> Grade Normalization (parse imported grades)

Session Narrative
    └──enhances──> Natural Language Logging (Claude generates after logging)

Smart Route Suggestion
    └──requires──> Route Database (well-populated)
    └──enhances──> Natural Language Logging (conversational trip planning)
```

### Dependency Notes

- **Grade Normalization is foundational:** Nearly every visualization and query depends on being able to compare grades across systems numerically. Build this early.
- **Route/Crag Database enables everything:** Routes are the core entity. Without a route database, you can't log ascents meaningfully, build pyramids, or show maps.
- **MCP logging depends on the full data layer:** Natural language logging requires the REST API, route resolution, grade parsing, and session management to all be working. It's a consumer of the data layer, not a foundation.
- **Visualizations are leaf nodes:** Grade pyramid, progression charts, and crag map all consume data but nothing depends on them. Build data layer first, visualizations second.
- **Topo analysis is independent:** Can be built after photo storage exists. Does not block other features.

## MVP Definition

### Launch With (v1)

Minimum viable product -- what validates the "log climbs through conversation" concept.

- [ ] PostgreSQL schema with sessions, ascents, routes, crags, grades -- the data foundation
- [ ] Grade normalization across French, UIAA, YDS, Font, V-scale with numeric scoring
- [ ] REST API for CRUD on all entities -- shared service layer for MCP and dashboard
- [ ] MCP server with tools: log_session, log_ascent, find_route, search_crags, get_stats
- [ ] CSV import for 422 historical routes -- immediate data for dashboard
- [ ] Dashboard: grade pyramid (stacked by style), session timeline, basic stats
- [ ] Bearer token auth on all endpoints
- [ ] Docker Compose deployment

### Add After Validation (v1.x)

Features to add once core logging and viewing works.

- [ ] Crag map with Leaflet + PostGIS spatial queries -- after crags have coordinates
- [ ] Progression charts (max grade over time, volume trends) -- after enough logged data
- [ ] Photo attachment to sessions and ascents -- after storage/serving is set up
- [ ] OpenBeta route resolution -- after local route DB proves the pattern works
- [ ] Conversational querying via MCP read tools -- after write tools are solid
- [ ] CSV export endpoint -- after schema is stable
- [ ] Multi-grade-system toggle on dashboard -- after grade normalization is proven

### Future Consideration (v2+)

Features to defer until the core product is daily-driveable.

- [ ] Topo image analysis via Claude Vision -- high complexity, needs solid photo storage first
- [ ] Session narrative generation -- nice-to-have, low effort once MCP read tools exist
- [ ] Smart route suggestion from context -- needs well-populated route database
- [ ] Downstream topo data analysis projects -- explicitly future per PROJECT.md

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Ascent logging (MCP tools) | HIGH | HIGH | P1 |
| Session management | HIGH | LOW | P1 |
| Route/crag database | HIGH | MEDIUM | P1 |
| Grade normalization | HIGH | MEDIUM | P1 |
| CSV import (historical data) | HIGH | LOW | P1 |
| REST API (shared service layer) | HIGH | MEDIUM | P1 |
| Grade pyramid visualization | HIGH | MEDIUM | P1 |
| Session timeline | MEDIUM | LOW | P1 |
| Bearer token auth | HIGH | LOW | P1 |
| Docker Compose deployment | HIGH | MEDIUM | P1 |
| Crag map (Leaflet + PostGIS) | MEDIUM | MEDIUM | P2 |
| Progression charts | MEDIUM | MEDIUM | P2 |
| Photo attachment | MEDIUM | MEDIUM | P2 |
| OpenBeta integration | MEDIUM | MEDIUM | P2 |
| Conversational querying | MEDIUM | MEDIUM | P2 |
| CSV export | LOW | LOW | P2 |
| Multi-grade-system toggle | LOW | LOW | P2 |
| Topo image analysis | MEDIUM | HIGH | P3 |
| Session narratives | LOW | LOW | P3 |
| Smart route suggestion | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch -- validates the core concept
- P2: Should have, add when core is working
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | 8a.nu / Vertical Life | TheCrag | Mountain Project | This Project |
|---------|----------------------|---------|------------------|--------------|
| Ascent logging | Form-based, app + web | Form-based, web-first | Simple tick list | Natural language via Claude conversation |
| Grade systems | French-centric, some conversion | All systems, Ewbanks internal, full conversion | YDS-centric | All major systems, numeric scoring, user-preferred display |
| Grade pyramid | Basic in Vertical Life app | Native, stacked by style | Not native (third-party tools) | Native, stacked by ascent style |
| Performance rating | 8a.nu score (proprietary) | CPR (scientifically modeled) | None | Numeric grade scoring (simpler than CPR, sufficient for single user) |
| Route database | Large, community-contributed | Largest, wiki-style | Large, US-focused | Local DB + OpenBeta enrichment, Claude-created fallback |
| Topo/photos | Topos per route, photo uploads | Interactive topo drawing, community photos | User photos, basic topo | Claude Vision topo analysis, photo attachment |
| Map | Crag locations | Detailed crag maps | Area maps | PostGIS-powered crag map with spatial queries |
| Import/export | CSV export, no bulk import | CSV/XLS import and export | CSV export | CSV import (flexible) and export |
| Social | Followers, rankings, challenges | Rankings, CPR leaderboards, community | Comments, star ratings | None (single-user, by design) |
| Data ownership | Their servers, GDPR export on request | Their servers, CSV export | Their servers (REI-owned) | Self-hosted PostgreSQL, you own everything |
| Interaction model | Tap/click forms | Tap/click forms | Tap/click forms | Conversational AI (MCP + Claude) |

## Sources

- [TheCrag: Ticking and logbook](https://www.thecrag.com/en/article/ticking)
- [TheCrag: Tick Types](https://www.thecrag.com/en/article/ticktypes)
- [TheCrag: Climber Performance Rating](https://www.thecrag.com/en/article/cpr)
- [TheCrag: Import logbook](https://www.thecrag.com/en/article/importlogbook)
- [TheCrag: Export logbook](https://www.thecrag.com/en/article/exportlogbook)
- [8a.nu / Vertical Life](https://www.8a.nu/)
- [Mountain Project tick pyramid discussion](https://www.mountainproject.com/forum/topic/114054803/ticks-as-a-route-pyramid)
- [Pompon.io: Climbing pyramid visualization tool](https://rpomponio.github.io/posts/climbing-pyramids/index.html)
- [Best climbing apps 2025 - Bould](https://www.usebould.com/best-climbing-apps)
- [Redpoint app](https://redpoint-app.com/)
- [KAYA climbing app](https://kayaclimb.com/import-logbook)
- [Climbing.com: Best climbing apps](https://www.climbing.com/gear/6-must-have-climbing-apps/)

---
*Feature research for: Personal climbing logbook (MCP server + web dashboard)*
*Researched: 2026-03-26*
