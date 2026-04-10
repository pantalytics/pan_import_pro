# Pantalytics Odoo Loader

AI-powered ERP data migration tool that transforms messy Excel files into clean Odoo imports.

## The Problem

ERP migrations typically involve messy, inconsistent spreadsheets that a human consultant manually interprets. This process is slow, error-prone, and hard to reproduce. Over 80% of ERP transformations miss their targets, largely due to poor data quality — not technology limitations.

## The Solution

Pantalytics Odoo Loader uses AI (Claude) to do what a human ERP consultant does:

1. **Scan** — Read messy Excel files and understand the structure
2. **Clean** — Normalize data into consistent tables (CSVs)
3. **Map** — Match clean data to Odoo model fields
4. **Load** — Import into Odoo via MCP

The key innovation is the **migration spec** (`migration.md`) — a human-readable document that captures all domain knowledge, cleanup rules, and mapping decisions. It's built iteratively through conversation with the client.

## How It Works

```
Messy Excel  →  AI Scan  →  Q&A with client  →  Clean CSVs  →  Odoo Import
                                  ↕
                          migration.md
                      (accumulates knowledge)
```

### The Migration Spec

Instead of keeping migration knowledge in a consultant's head, we capture it in a structured file:

- **Domain knowledge** — What the business does, what the data represents
- **Sheet instructions** — How to interpret each sheet/tab
- **Cleanup rules** — Name normalization, deduplication, handling of missing data
- **Odoo mapping** — Which Excel data goes to which Odoo model/field

Each conversation with the client improves the spec. The spec is reproducible, auditable, and transferable.

## Project Structure

```
pantalytics-odoo-loader/
├── migrations/              # One folder per client migration
│   └── emovr/               # Example: Emovr migration
│       ├── migration.md     # The migration spec (domain knowledge + rules)
│       ├── input/           # Original messy Excel files
│       ├── cleaned/         # Normalized intermediate CSVs
│       ├── mapped/          # Odoo-ready import files
│       └── logs/            # Import logs and issues
├── docs/                    # Documentation
│   └── ARCHITECTURE.md      # Technical architecture
├── CLAUDE.md                # Claude Code project instructions
└── README.md
```

## Quick Start

1. Create a migration folder: `migrations/<client-name>/`
2. Drop Excel files in `input/`
3. Run Claude Code in the migration folder
4. Claude scans the files, asks questions, builds the migration spec
5. Review cleaned CSVs and Odoo mapping
6. Approve and import

## Technology

- **Claude API** — AI analysis, data understanding, iterative Q&A
- **Odoo MCP** — Direct connection to Odoo for schema introspection and data loading
- **Python** — Excel parsing (openpyxl/pandas), data transformation
- **Claude Code** — Interactive migration workflow

## Context

Built by [Pantalytics](https://pantalytics.com) as described in our whitepaper [AI in ERP: A Practical Guide](https://pantalytics.com/en/post/ai-in-erp-practical-guide). AI doesn't change the rules of your ERP — it changes the speed.

## License

Proprietary - Pantalytics B.V.
