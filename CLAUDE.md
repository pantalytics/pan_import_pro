# Import Pro

AI-powered data migration into Odoo. Two components:

1. **Claude Skill** (`.claude/skills/import-pro/`) — The migration expertise. Tells Claude how to analyze files, map data, and import into Odoo.
2. **Odoo Module** (`pan_import_pro/`) — Companion app in Odoo. Tracks projects, documents, questions, and import plans.

## How It Works

Claude does the work (via Claude Code, Co-work, or claude.ai). The Odoo module is where results land and clients review.

```
Claude + Skill          Odoo MCP           Import Pro (Odoo)
──────────────          ────────           ─────────────────
Reads files        →    Writes via MCP →   pan.import.project
Analyzes data                              pan.import.document
Asks questions                             pan.import.question
Maps to Odoo                               pan.import.line
Imports records                            Results visible in Odoo
```

## Odoo Module: pan_import_pro

Dependencies: `contacts`, `documents`, `mail`

### Models

| Model | Purpose |
|-------|---------|
| `pan.import.project` | Migration project with state tracking |
| `pan.import.document` | Per-document analysis and instructions |
| `pan.import.question` | Questions (Claude asks, client answers) |
| `pan.import.line` | Import plan (create/update/skip per record) |

### States

Draft → In Progress → Review → Approved → Done

## Development

Local Odoo runs on `localhost:8069` via Docker.
Module is mounted from this repo into the container.
Customer-specific migration data lives in separate repos (e.g. `odoo-customer-emovr`).
