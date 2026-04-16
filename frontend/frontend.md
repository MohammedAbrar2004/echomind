You are building the complete frontend for EchoMind — a single-user personal 
cognitive memory system that ingests data from WhatsApp, Gmail, Google Meet, 
Google Calendar, and manual entry, then makes it queryable through a 
conversational interface.

---

## TECH STACK

- React (a complex, detailed multi component frontend is preferred)
- Tailwind CSS for utility styling
- Recharts for any data visualizations
- Also needs to have a library that can be used to visualize graphs to represent relationships
- Lucide React for icons

// All in a single deployable file (no build step needed for now — this is a 
//makeshift frontend to test UX before wiring to the FastAPI backend)


---

## AESTHETIC DIRECTION

Dark theme. Industrial-utilitarian with a touch of biopunk — like a personal 
OS for your brain. Think deep charcoal/slate backgrounds (#0f1117 range), 
electric teal/cyan as the primary accent (#00e5cc range), amber/gold for 
warnings and salience indicators, and muted warm grays for secondary text. 
Typography: use a monospace or technical font for data/metadata, and a clean 
geometric sans-serif for UI chrome. The vibe is "personal intelligence terminal" 
— not a consumer app, not a corporate dashboard. Dense information, but 
intentionally organized. Subtle grid lines or dot-grid background texture. 
Thin borders, sharp corners. No rounded-pill buttons — use sharp or very 
slightly rounded (2px) corners throughout. Micro-animations on state changes.

---

## LAYOUT

Persistent left sidebar (collapsible) with icon + label navigation.
Top bar with: system health indicators (scheduler status, last sync, failed 
jobs count), current section title, and a global search trigger.
Main content area — changes based on active section.
Optional right panel that slides in for detail views (chunk inspector, 
entity detail, answer provenance).

---

## SECTIONS (implement all with realistic placeholder/mock data)

### 1. Query  (default landing view)
- Large centered text input with mic button alongside it for audio-to-text
- On submit: show a response card with the AI's answer
- Below the answer: collapsible "Sources" panel showing which memory chunks 
  were used — each chunk card shows: source icon (WhatsApp/Gmail/Manual/etc.), 
  timestamp, salience score as a thin colored bar, and a short excerpt
- Query history in a left-anchored column (recent questions, clickable to 
  reload that result)
- Response should show which AI model was used (badge) and latency

### 2. Memory Browser
- Filterable, paginated table/card view of memory_chunks
- Filter controls: source type (multi-select chips), date range picker, 
  salience score range slider, media type (text/audio/document/image)
- Each chunk card: source badge, timestamp, salience score bar, content 
  preview (truncated), media thumbnails if applicable, "View Full" button 
  that opens the right detail panel
- Sort by: newest, oldest, highest salience, source
- Chunk count summary at top

### 3. Ingest (Manual Entry)
Three tabs within this section:
  a) Text — rich textarea with metadata fields: title (optional), 
     source label, date override, tags, people mentioned (comma-separated), 
     initial salience override slider
  b) Voice Note — a large record button with waveform visualization while 
     recording; after recording: playback + transcript preview + same metadata 
     fields as text tab
  c) Document — drag-and-drop zone accepting PDF and DOC/DOCX; after upload: 
     show filename, size, page count (mock); metadata fields: document title, 
     author, date, tags, description

All three tabs share a consistent "Submit to Memory" CTA button.

### 4. Timeline
- Unified chronological feed of all ingested data across all sources
- Each entry: source icon + color coding, timestamp, content preview, 
  salience score indicator dot (color coded: high=teal, medium=amber, low=gray)
- Filters: source toggle buttons at top, date jump (calendar picker), 
  "High salience only" toggle
- Infinite scroll or pagination
- Group entries by day with sticky date headers

### 5. Relationships
- Entity graph visualization — nodes are people/places/organizations, 
  edges are relationships/co-occurrences
- Left panel: entity list with search; clicking an entity highlights it 
  and its connections on the graph
- Node detail panel (right slide-in): entity name, type badge, mention count, 
  first seen / last seen, list of linked events/commitments, recent memory 
  chunks mentioning them
- Graph controls: zoom in/out, reset, filter by entity type, filter by 
  relationship strength (edge weight threshold slider)
- Use a simple force-directed layout (you can use D3 or a canvas-based mock)

### 6. Commitments
Three columns (kanban-ish layout):
  a) Open Tasks — extracted to-do items with source reference
  b) Upcoming Events — calendar events and detected meetings
  c) Promises / Follow-ups — things committed to by self or others
Each card: title, source badge, due date or event date, entity tags 
(who's involved), status toggle (open/done), priority indicator.
Add a "Mark Complete" and "Snooze" action per card.

### 7. Connectors
- Card grid, one card per connector: Gmail, WhatsApp, Google Calendar, 
  Google Meet, Manual
- Each card shows: connector name + icon, status badge (Active / Inactive / 
  Error / Auth Required), last successful sync timestamp, total chunks ingested 
  from this source, ingestion mode (Push / Pull)
- For Pull connectors: editable poll interval field
- Action buttons per card: "Re-authenticate" (OAuth flow trigger), 
  "Force Sync Now", "Pause/Resume", "View Logs" (opens a modal with mock 
  recent log lines)
- WhatsApp card shows: session status, QR code placeholder if not connected, 
  list of tracked chats (editable)
- At bottom: ingestion_runs log table — timestamp, connector, chunks ingested, 
  duration, status

### 8. Salience Tuning
- Two-column layout
Left column:
  - Keyword rule builder: add keyword → assign weight multiplier → save. 
    List of existing keyword rules in a table with edit/delete.
  - Entity type weights: sliders for People, Places, Organizations, Dates, 
    Custom Tags
  - Source weights: sliders per connector (some sources count more than others)
Right column:
  - Global salience threshold slider (0.0 – 1.0) with a label showing 
    "Chunks below this score are deprioritized in retrieval"
  - "Preview Impact" button: shows a mock before/after distribution chart 
    (bar chart or histogram) of chunk salience scores against current settings
  - Decay settings: half-life slider for how fast old chunks lose salience 
    weight (in days)
  - Save / Reset to Defaults buttons

### 9. Profile & Settings
Tabbed layout within this section:

  a) Profile — name, avatar upload, timezone, language preference, 
     "About Me" free text (used as context for AI answers), role/occupation 
     field (also fed as context)

  b) AI Model — dropdown to select model (GPT-4o, GPT-4o-mini, Claude Sonnet, 
     Claude Haiku, Gemini Pro — with badges showing cost tier: $/$$/$$$ ), 
     API keys section (masked input fields per provider with show/hide toggle 
     and a "Test Key" button), response style selector (Concise / Balanced / 
     Detailed), answer persona free text ("Answer as if you are...")

  c) Preferences — toggle switches for: "Proactive commitment detection", 
     "Auto-tag entities", "Include source citations in answers", 
     "Enable voice input by default", "Dark mode" (already dark, greyed out), 
     notification preferences (stub)

  d) Tracked Entities — searchable list of entities the user explicitly 
     wants prioritized. Add entity by name + type. Each shows: name, type 
     badge, mention count, salience boost toggle. Delete option.

  e) Tracked Chats — for WhatsApp specifically: list of chat names being 
     monitored, ability to add/remove. Shows message count per chat.

  f) Security — change password (stub), session management (active sessions 
     list), data export button ("Export all memory as JSON"), danger zone 
     (Wipe all data — red button with confirmation modal)

---

## SYSTEM HEALTH BAR (persistent top bar element)

Right side of top bar shows:
- Scheduler: green dot "Running" or red dot "Stopped"  
- Last Sync: "2 min ago" (or per-connector breakdown on hover)
- Failed Jobs: count badge (amber if >0, red if >5) — clicking opens a 
  modal with the failed_jobs table showing error messages and retry buttons
- DB: green "Connected" or red "Disconnected"

---

## MOCK DATA REQUIREMENTS

Populate every section with realistic mock data so the UI feels alive:
- At least 15-20 memory chunks across WhatsApp, Gmail, and Manual sources
- 5-6 entities (people + one organization) with relationship edges between them
- 3-4 commitments across the three columns
- Connector statuses: Gmail=Active, WhatsApp=Auth Required, 
  Calendar=Inactive, Meet=Inactive, Manual=Active
- 2 failed jobs in the health bar
- Realistic salience scores (varied, not uniform)
- Query result with 3 source chunks shown

---

## IMPLEMENTATION NOTES

- All data is mock/static — no real API calls (yet). Use useState and mock 
  arrays. Leave clearly marked TODO comments where API calls will eventually go.
- The sidebar navigation should highlight the active section
- Transitions between sections should be smooth (fade or slide)
- Right detail panels should slide in from the right with an overlay
- All forms should have validation feedback (inline error states)
- Design for 1280px+ viewport width — this is a desktop-only tool
- No mobile responsiveness needed at this stage
- Use realistic timestamps, names, and content in mock data — not "Lorem ipsum"
  — use plausible WhatsApp message excerpts, email subjects, etc.
- The graph in Relationships can be a simplified SVG/canvas mock with 
  positioned nodes and drawn edges if a full D3 force simulation is too heavy 
  — just make it look good