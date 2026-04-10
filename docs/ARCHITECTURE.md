# Architecture

## Overview

Pantalytics Odoo Loader is an AI-powered data migration pipeline that transforms messy client spreadsheets into clean Odoo imports. It works as a Claude Code workflow today, with a path toward becoming an Odoo custom module.

## Core Concept: The Migration Spec

The central artifact is `migration.md` — a human-readable file that captures everything an ERP consultant would know about a migration. It serves as both documentation and executable specification.

```
migration.md = domain knowledge + cleanup rules + field mapping
```

This file is:
- **Iteratively built** through conversation with the client
- **Reproducible** — run the same spec again if the import fails
- **Auditable** — every decision is documented with rationale
- **Transferable** — another consultant can pick it up

## Pipeline Stages

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │ →  │  Scan &      │ →  │  Clean   │ →  │  Map to  │ →  │  Load    │
│  Excel   │    │  Classify    │    │  Tables  │    │  Odoo    │    │  Data    │
└──────────┘    └──────────────┘    └──────────┘    └──────────┘    └──────────┘
                      ↕                  ↕               ↕
                 migration.md       migration.md    migration.md
                 (sheet rules)      (cleanup rules) (field mapping)
```

### Stage 1: Scan & Classify

**Input:** Raw Excel files
**Output:** Sheet inventory + structure analysis

AI analyzes each sheet and detects:
- **Sheet type** — Is it a customer tab, product list, price list, or something else?
- **Header location** — Headers aren't always on row 1
- **Block detection** — Repeated headers within a sheet = multiple logical tables
- **Phantom rows** — Excel files often report 1M rows but only have 25 data rows
- **Free text vs data** — Notes/comments mixed in with data rows
- **Merged cells** — Cosmetic formatting that breaks table structure

The AI generates questions for the client when it can't determine intent.

### Stage 2: Clean (Excel → CSV)

**Input:** Raw Excel + cleanup rules from migration.md
**Output:** Normalized CSV files

Transformations:
- Split multi-block sheets into separate tables
- Unify header names ("service datum" → "Servicedatum")
- Normalize entity names ("Verwoert" → "Restauratiebedrijf Verwoerd")
- Handle missing/placeholder values ("N.V.T", "?", empty → null)
- Remove duplicate data across sheets
- Detect and flag incomplete records (e.g., serienummers missing digits)
- Standardize date formats
- Standardize type codes ("Trc 1.5" = "TRC1,5" = "TRC1.5" → "TRC1.5")

### Stage 3: Map (CSV → Odoo fields)

**Input:** Clean CSVs + Odoo model schemas (via MCP)
**Output:** Import-ready files with Odoo field names

The AI:
1. Queries Odoo MCP for available models and their field definitions
2. Matches CSV columns to Odoo fields
3. Resolves relational fields (e.g., customer name → res.partner ID)
4. Determines load order based on dependencies
5. Presents the mapping plan for human approval

### Stage 4: Load

**Input:** Mapped data + approved plan
**Output:** Records created in Odoo

Execution:
1. Load in dependency order (partners before orders, products before lots)
2. Use Odoo's `model.load()` or MCP `create_records` for bulk operations
3. Track all created record IDs for potential rollback
4. Log successes and failures per record
5. Report summary to user

## Data Flow Example

```
Input (messy):
┌─────────────────────────────────────────────────────┐
│ Sheet "Compraan BV"                                  │
│ Row 1: klant/Bedrijf | Machine | Type  | serienummer │
│ Row 2: Compraan BV   | Carrier | Trc 1.5 | EMTRC... │
│ Row 5: klant/Bedrijf | Optie's | Type  | serienummer │ ← repeated header!
│ ...                                                   │
└─────────────────────────────────────────────────────┘

Cleaned (intermediate):
┌─────────────────────────────────────────────────┐
│ klanten.csv                                      │
│ name                                             │
│ Compraan BV                                      │
│ GKB Buiteninrichting                             │
│ ...                                              │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ machines.csv                                     │
│ klant,type,machine,serienummer,bouwjaar,status   │
│ Compraan BV,TRC1.5,Carrier,EMTRC150925001,2025,  │
│ ...                                              │
└─────────────────────────────────────────────────┘

Mapped (Odoo-ready):
┌─────────────────────────────────────────────────┐
│ res_partner.csv                                  │
│ name,is_company,company_type                     │
│ Compraan BV,True,company                         │
│ ...                                              │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ stock_lot.csv                                    │
│ name,product_id/name                             │
│ EMTRC150925001,TRC1.5 Carrier                    │
│ ...                                              │
└─────────────────────────────────────────────────┘
```

## Odoo Model Mapping (Emovr case)

| Domain Entity | Odoo Model | Key Fields |
|--------------|------------|------------|
| Klanten (Compraan BV, GKB, etc.) | `res.partner` | name, is_company=True |
| Contactpersonen (Gerwin, Alfred) | `res.partner` | name, parent_id, type=contact |
| Producten (Carrier, Dumper, Crane) | `product.template` | name, type, list_price |
| Serienummers | `stock.lot` | name, product_id |
| Prijslijst | `product.pricelist.item` | product_tmpl_id, fixed_price |

Load order: `res.partner` → `product.template` → `product.pricelist.item` → `stock.lot`

## Error Handling

### Data Quality Flags

Each record in the cleaned stage gets a quality assessment:

- **OK** — Complete, consistent, ready to import
- **WARNING** — Missing optional fields, can import with defaults
- **ERROR** — Missing required fields or inconsistent data, needs human input
- **SKIP** — Duplicate or irrelevant (e.g., template rows, free text notes)

### Rollback Strategy

- All created record IDs are logged to `logs/import_<timestamp>.json`
- If import fails partway, the log shows which records were created
- Records can be deleted via Odoo MCP `delete_records` using logged IDs

## Future: Odoo Custom Module

The current Claude Code workflow can evolve into a native Odoo module:

- **Wizard-based UI** — TransientModel with state-driven multi-step flow
- **Binary field** for file upload, `fields.Json` for mapping config
- **Claude API integration** via Python `anthropic` SDK
- **OWL frontend** for preview and Q&A interface
- **Background processing** via `queue_job` for large files

This requires Odoo.sh or self-hosted (not Odoo Online/SaaS).

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Engine | Claude API (Anthropic) | Data analysis, mapping, Q&A |
| Odoo Connection | Odoo MCP | Schema introspection, record CRUD |
| Excel Parsing | openpyxl, pandas | Read and transform spreadsheets |
| Workflow | Claude Code | Interactive migration sessions |
| Data Format | CSV (intermediate) | Clean, inspectable intermediate state |
