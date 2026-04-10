# Pantalytics Odoo Loader

## What This Project Does

AI-powered ERP data migration tool. Transforms messy client Excel files into clean Odoo imports through an iterative, conversational process. Works both as Claude Code scripts and via Claude + Odoo MCP for end users.

## Key Concepts

- **Migration spec** (`migration.md`) — The central artifact per client. Captures domain knowledge, cleanup rules, and Odoo field mappings. Built iteratively through conversation.
- **Iterative loop, not linear pipeline** — Clients provide corrections, new versions, and additional data. Imports must be re-runnable without creating duplicates.
- **External IDs** — Every imported record gets a `__import__` external ID for idempotent upsert. Odoo's `load()` method handles create-or-update automatically.
- **3-tier feedback** — All output to clients uses: HELDER (confident) / AANNAMES (assumptions) / HULP NODIG (need input).
- **Odoo MCP** — Universal interface for both scripts and Claude end-users.

## Project Structure

```
migrations/<client>/
├── migration.md     # Migration spec — the "recipe"
├── clean.py         # Excel → normalized CSVs
├── load.py          # CSVs → Odoo import (TODO)
├── input/           # Original Excel files (never modify, gitignored)
├── cleaned/         # Normalized CSVs (git-committed for version control)
├── mapped/          # Odoo field-mapped files with external IDs
└── logs/            # Import logs
```

## How to Run a Migration

### Step 1: Scan & Clean
Run `clean.py` to read Excel files from `input/` and produce:
- Normalized CSVs in `cleaned/`
- A consultant-style rapport (HELDER / AANNAMES / HULP NODIG)
- Git-commit the CSVs so changes can be diffed between iterations

### Step 2: Review & Iterate
Review the rapport with the client. Update `migration.md` with answers. Re-run `clean.py`. Repeat until data is clean.

### Step 3: Prerequisite Check
Before importing, verify:
- Required Odoo modules are activated (MCP CANNOT install modules — client must do this manually in Odoo UI: Settings → Apps)
- Target models are available via MCP
- No duplicate records in Odoo

### Step 4: Import Plan (requires approval)
Generate an import plan showing:
- X records to create, Y to update, Z unchanged
- Load order (dependencies)
- External ID format

**NEVER import without explicit user approval.** Show the plan, wait for go-ahead.

### Step 5: Import via Upsert
Use Odoo's `load()` method with `__import__` external IDs:
- Exists → update
- Doesn't exist → create
- Running twice = same result (idempotent)

Load order: `res.partner` (companies) → `res.partner` (contacts) → `product.template` → `stock.lot`

### Step 6: Verify & Repeat
Client checks results. New corrections? New data version? Go back to Step 1.

## External ID Convention

```
__import__.{model_slug}_{natural_key_slug}

Examples:
__import__.partner_compraan_bv
__import__.contact_marinus_slingerland_ss_teknikk
__import__.product_38000000
__import__.lot_emtrc150925001
```

## Odoo MCP

### Available Tools
- `list_models` — See all available Odoo models
- `search_records` — Query existing records
- `get_record` — Get a specific record by ID
- `create_record` / `create_records` — Create new records
- `update_record` / `update_records` — Update existing records
- `delete_record` / `delete_records` — Delete records (for rollback)
- Resource templates: `odoo://{model}/fields` — Get field definitions

### MCP Limitations
- **Cannot install/activate Odoo modules** — must be done manually by client
- **No `load()` support yet** — needs `import_records` tool wrapping Odoo's `load()` for upsert with external IDs
- **Cannot modify Odoo settings**

### Planned MCP Enhancement
```python
import_records(
    model="res.partner",
    fields=["id", "name", "is_company"],
    data=[["__import__.partner_compraan", "Compraan BV", "True"]],
    context={"tracking_disable": True}
)
```

## Rules

- **Never modify files in `input/`** — they are the original client data
- **Never import without approval** — always show the plan first
- **Git-commit cleaned CSVs** — enables diffing between iterations
- **When in doubt, ask** — add question to migration.md rather than guessing
- **Master data first** — partners and products before transactional data
- **Use natural keys** — company name, artikelnummer, serienummer as stable identifiers
- **3-tier feedback always** — every scan output uses HELDER / AANNAMES / HULP NODIG structure
- **Log everything** — every import action with record IDs for audit/rollback

## Tech Stack

- Python 3.11+ (openpyxl, pandas)
- Odoo MCP for Odoo integration (schema + CRUD, future: `load()`)
- Odoo `load()` via XML-RPC for idempotent imports with external IDs
- Claude Code for interactive workflow
- Git for data version control

## Current State (2026-04-10)

### Done
- Project structure and docs
- Emovr migration spec (`migration.md`) with domain knowledge
- `clean.py` — scans Excel, produces CSVs with 3-tier rapport
- Test import: 3 klanten + 1 contact + 3 producten in emovr.odoo.com

### TODO
- `load.py` — upsert via `load()` with external IDs
- MCP enhancement: `import_records` tool wrapping `load()`
- Prerequisite check (detect required but missing Odoo modules)
- Diff between clean runs (what changed?)
- Full Emovr import (all klanten, producten, serienummers)
- Emovr: activate Inventory module for stock.lot
