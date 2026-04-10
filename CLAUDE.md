# Pantalytics Odoo Loader

## What This Project Does

AI-powered ERP data migration tool. Transforms messy client Excel files into clean Odoo imports through an iterative, conversational process.

## Key Concepts

- **Migration spec** (`migration.md`) — The central artifact. A human-readable file per client that captures domain knowledge, cleanup rules, and Odoo field mappings. Built iteratively through conversation.
- **Three-stage pipeline** — Input (messy Excel) → Cleaned (normalized CSVs) → Mapped (Odoo-ready import files)
- **Odoo MCP** — Used to introspect Odoo model schemas and create records. Connected to `pantalytics.odoo.com`.

## Project Structure

```
migrations/<client>/
├── migration.md     # Migration spec — the "recipe"
├── input/           # Original Excel files (never modify)
├── cleaned/         # Normalized CSVs (intermediate)
├── mapped/          # Odoo field-mapped files (ready to import)
└── logs/            # Import logs with created record IDs
```

## How to Run a Migration

### Step 1: Scan
Read the Excel files in `input/`. Analyze each sheet: detect headers, data blocks, phantom rows, free text. Generate an initial `migration.md` with findings and questions for the client.

### Step 2: Clean
Apply the cleanup rules from `migration.md` to produce normalized CSVs in `cleaned/`. Rules include:
- Entity name normalization (dedup spelling variants)
- Header unification
- Split multi-block sheets into separate tables
- Handle placeholders (N.V.T., ?, empty)
- Remove duplicates across sheets
- Flag incomplete records

### Step 3: Map
Query Odoo MCP for model schemas (`odoo://{model}/fields`). Match cleaned CSV columns to Odoo fields. Determine load order based on model dependencies. Write mapped files to `mapped/`.

### Step 4: Load
Import via Odoo MCP `create_records` in dependency order. Log all created record IDs. Report results.

## Working with the Migration Spec

The `migration.md` file is the most important artifact. Treat it like a living document:

- Add domain knowledge as the client explains their data
- Document every cleanup rule with rationale
- Record field mapping decisions
- Note ambiguities that need client clarification
- Update when answers come in

## Odoo MCP Tools

Available tools for Odoo interaction:
- `list_models` — See all available Odoo models
- `search_records` — Query existing records
- `get_record` — Get a specific record by ID
- `create_record` / `create_records` — Create new records
- `update_record` / `update_records` — Update existing records
- `delete_record` / `delete_records` — Delete records (for rollback)
- Resource templates: `odoo://{model}/fields` — Get field definitions for mapping

## Rules

- Never modify files in `input/` — they are the original client data
- Always write cleaned CSVs to `cleaned/`, never overwrite input
- Always ask before importing to Odoo — show the plan first
- Log every import with record IDs for rollback capability
- When in doubt about data meaning, add a question to migration.md rather than guessing
- Use pandas for data transformation, openpyxl for Excel reading
- Prefer `model.load()` style imports (via MCP create_records) over individual creates

## Tech Stack

- Python 3.11+ (openpyxl, pandas)
- Claude API (anthropic SDK) for AI analysis
- Odoo MCP for Odoo integration
- Claude Code for interactive workflow
