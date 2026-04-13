# Import Pro

AI-powered data migration into Odoo. Claude does the work, Odoo tracks the results.

## What's in this repo

| Component | What it does |
|-----------|-------------|
| **Claude Skill** (`.claude/skills/import-pro/`) | Teaches Claude how to run a data migration like a senior ERP consultant |
| **Odoo Module** (`pan_import_pro/`) | Companion app in Odoo for tracking projects, documents, questions, and import plans |

## Install the Skill

### Claude Code

Clone this repo into your project — the skill is auto-discovered:

```bash
git clone https://github.com/pantalytics/pan_import_pro.git
cd pan_import_pro
claude
```

Or copy just the skill to your global skills:

```bash
cp -r .claude/skills/import-pro ~/.claude/skills/
```

### Claude.ai

1. Download the `.claude/skills/import-pro/` folder as a zip
2. Go to Settings → Features → Skills
3. Upload the zip

### Claude API

Upload via the Skills API:

```bash
curl -X POST https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "file=@import-pro.zip"
```

## Install the Odoo Module

Copy `pan_import_pro/` to your Odoo addons path and install via Apps.

**Dependencies:** `contacts`, `documents`, `mail`

## How It Works

```
You (with Claude)              Odoo MCP              Import Pro (Odoo)
─────────────────              ────────              ─────────────────
1. Build company profile  →    write to MCP     →    res.partner.comment
2. Upload data files                                  Documents folder
3. Analyze each file      →    write analysis   →    pan.import.document
4. Ask questions          →    create questions  →    pan.import.question
5. Client answers in Odoo                             (answers via UI)
6. Read answers           ←    read via MCP     ←
7. Create import plan     →    write lines      →    pan.import.line
8. Client approves in Odoo                            (review state)
9. Import via MCP         →    import_records   →    Data in Odoo
```

## Prerequisites

- [Odoo MCP Server](https://github.com/pantalytics/odoo-mcp-pro) connected to your Odoo instance
- Claude Code, Claude.ai (Pro/Max/Team), or Claude API access

## Try It

```
You: I need to import my customer and product data into Odoo from Excel files.
Claude: [activates Import Pro skill and starts the migration process]
```

## License

LGPL-3 — [Pantalytics B.V.](https://pantalytics.com)
