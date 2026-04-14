# Import Pro

AI-powered data migration into Odoo. Two components:

1. **Claude Skill** (`.claude/skills/import-pro/`) — The migration expertise. Tells Claude how to analyze files, map data, and import into Odoo.
2. **Odoo Module** (`pan_import_pro/`) — Companion app in Odoo. Tracks projects, links to Documents and Surveys, manages import plans and logs.

## How It Works

Claude does the work (via Claude Code, Co-work, or claude.ai). The Odoo module is where the client reviews and approves.

```
Claude + Skill          Odoo MCP           Odoo
──────────────          ────────           ────
Reads files        →    Writes via MCP →   Documents (folder)
Creates survey                             Survey (questionnaire)
Proposes plan                              pan.import.plan
Imports records                            pan.import.log
```

## Odoo Module: pan_import_pro

Dependencies: `contacts`, `documents`, `mail`, `survey`

### Models

| Model | Purpose |
|-------|---------|
| `pan.import.project` | Migration project (state, folder, survey, approval) |
| `pan.import.plan` | Import plan per model (what, how many, action) |
| `pan.import.log` | Import results (created, updated, failed) |

Uses standard Odoo models for client interaction:
- `survey.survey` for questionnaires
- `documents.document` for file management

### States

Draft → In Progress → Review → Approved → Done

## Development

Local Odoo runs on `localhost:8069` via Docker.
Module is mounted from this repo into the container.
Customer-specific migration data lives in separate repos (e.g. `odoo-customer-emovr`).
