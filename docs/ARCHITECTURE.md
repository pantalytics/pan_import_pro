# Architecture

## Overview

Pantalytics Odoo Loader is an AI-powered ERP data migration tool that transforms messy client spreadsheets into clean Odoo imports. It works as a Claude Code workflow today, with a path toward becoming an Odoo custom module.

The key insight: ERP migration is **iterative, not linear**. Clients provide corrections, new versions, and additional data across multiple cycles. The architecture must support re-running imports without creating duplicates.

## Two Access Paths, One Interface

```
Consultant:  clean.py → load.py → Odoo MCP → Odoo
End user:    "Upload Excel" → Claude + Odoo MCP → Odoo
                                      ↑
                                same interface
```

The Odoo MCP is the universal interface for both developers and end users. This means the MCP must support idempotent imports (upsert via external IDs).

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

## The Iterative Migration Loop

Migration is not a pipeline — it's a loop. Clients provide corrections, new data versions, and additional context across multiple cycles (typically 3-5 mock cycles before go-live).

```
        ┌──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
   ┌──────────┐    ┌──────────┐    ┌──────────┐      │
   │  SCAN    │ →  │  CLEAN   │ →  │  DIFF    │      │
   │  Excel   │    │  → CSVs  │    │  vs      │      │
   │  Rapport │    │  + git   │    │  previous│      │
   │  3 tiers │    │  commit  │    │  version │      │
   └──────────┘    └──────────┘    └──────────┘      │
                                        │             │
                                        ▼             │
                                   ┌──────────┐      │
                                   │  PLAN    │      │
                                   │  X new   │      │
                                   │  Y update│      │
                                   │  Z skip  │      │
                                   └────┬─────┘      │
                                        │             │
                                   approval?          │
                                        │             │
                                        ▼             │
                                   ┌──────────┐      │
                                   │  IMPORT  │      │
                                   │  upsert  │      │
                                   │  via MCP │      │
                                   │  + log   │      │
                                   └────┬─────┘      │
                                        │             │
                                        ▼             │
                                   ┌──────────┐      │
                                   │  VERIFY  │ ─────┘
                                   │  client  │  correction needed?
                                   │  checks  │  new version?
                                   └──────────┘
```

### Standard Migration Cycles (from ERP best practices)

| Cycle | Focus | Who validates |
|-------|-------|---------------|
| Mock 1 | Structural issues (field mapping, dependencies, missing modules) | Consultant |
| Mock 2 | Data quality (duplicates, formats, missing data) | Consultant + client |
| Mock 3+ | Business validation (does everything make sense?) | Client / business users |
| Cutover | "Boring repeat" against production | Everyone |

## Stage Details

### Stage 1: Scan & Classify

**Input:** Raw Excel files
**Output:** Consultant-style rapport with 3-tier feedback

AI analyzes each sheet and detects:
- **Sheet type** — Is it a customer tab, product list, price list, or something else?
- **Header location** — Headers aren't always on row 1
- **Block detection** — Repeated headers within a sheet = multiple logical tables
- **Phantom rows** — Excel files often report 1M rows but only have 25 data rows
- **Free text vs data** — Notes/comments mixed in with data rows
- **Merged cells** — Cosmetic formatting that breaks table structure

#### 3-Tier Feedback (essential for client communication)

The scan output is structured as a consultant report:

1. **HELDER** — "Dit heb ik met zekerheid kunnen uitlezen" (high confidence)
   - Complete records with clear structure
   - Unambiguous field values

2. **AANNAMES** — "Hier was ik niet 100% zeker, dit heb ik zo ingeschat" (assumptions)
   - Name normalization decisions
   - Sheets skipped and why
   - Deduplication choices

3. **HULP NODIG** — "Hier kom ik niet uit zonder jouw input" (need human input)
   - Incomplete serial numbers
   - Records without required fields
   - Ambiguous relationships
   - **Required Odoo modules** not yet activated

### Stage 2: Clean (Excel → CSV)

**Input:** Raw Excel + cleanup rules from migration.md
**Output:** Normalized CSV files (git-committed for version control)

Transformations:
- Split multi-block sheets into separate tables
- Unify header names ("service datum" → "Servicedatum")
- Normalize entity names ("Verwoert" → "Restauratiebedrijf Verwoerd")
- Handle missing/placeholder values ("N.V.T", "?", empty → null)
- Remove duplicate data across sheets
- Detect and flag incomplete records
- Standardize date formats and type codes

**Important:** CSVs are git-committed after each clean. This enables diffing between versions when the client provides updated data.

### Stage 3: Prerequisite Check & Mapping

**Input:** Clean CSVs + Odoo model schemas (via MCP)
**Output:** Import plan for human approval

This stage:
1. **Module check** — Which Odoo models are needed? Are they available via MCP? If not: "Activate Inventory module first" (MCP cannot install modules — this must be done manually by client/admin)
2. **Duplicate check** — Does "Compraan BV" already exist in Odoo?
3. **Field mapping** — CSV column → Odoo field
4. **Dependency order** — Partners before contacts, products before serial numbers
5. **Import plan** — "3 new partners, 1 update, 9 unchanged"
6. **Wait for approval** — NEVER import without explicit user go-ahead

### Stage 4: Import (Upsert via External IDs)

**Input:** Approved plan + clean CSVs
**Output:** Records in Odoo + import log

#### External IDs: The Key to Idempotent Imports

Odoo's `load()` method supports external IDs natively. This is the same mechanism the Odoo UI import uses.

```
External ID: __import__.partner_compraan_bv
  ↓
Odoo checks ir.model.data:
  - Exists? → UPDATE the linked record
  - Doesn't exist? → CREATE + store the mapping
```

This makes imports **idempotent** — running the same import twice produces the same result, no duplicates.

#### Natural Keys for External IDs

| Entity | Natural Key | External ID Format |
|--------|-------------|-------------------|
| Klanten | Company name (normalized) | `__import__.partner_{slug}` |
| Contactpersonen | Name + parent company | `__import__.contact_{slug}` |
| Producten | Artikelnummer (default_code) | `__import__.product_{code}` |
| Serienummers | Serial number | `__import__.lot_{serial}` |

#### Technical Implementation: Odoo `load()` via API

`load()` is a public `@api.model` method, callable via XML-RPC/JSON-RPC across Odoo 16-19. It is the same method the Odoo UI import uses.

```python
# Via XML-RPC
models.execute_kw(db, uid, password, 'res.partner', 'load',
    [
        ['id', 'name', 'is_company', 'company_type'],     # fields
        [
            ['__import__.partner_compraan', 'Compraan BV', 'True', 'company'],
            ['__import__.partner_gkb', 'GKB Buiteninrichting', 'True', 'company'],
        ]
    ],
    {'context': {'tracking_disable': True}}  # suppress mail notifications
)
```

Key features of `load()`:
- Upsert via external IDs (column name `id`)
- Relational field resolution via external ID (`company_id/id`)
- Batch processing
- Detailed error reporting per row
- Context flags: `tracking_disable=True`, `defer_fields_computation=True`

#### MCP Enhancement Needed

The Odoo MCP currently supports `create_records` but not `load()`. To support idempotent imports, the MCP needs a new tool:

```python
import_records(
    model="res.partner",
    fields=["id", "name", "is_company", "company_type"],
    data=[
        ["__import__.partner_compraan", "Compraan BV", "True", "company"],
        ["__import__.partner_gkb", "GKB Buiteninrichting", "True", "company"],
    ],
    context={"tracking_disable": True}
)
```

This wraps Odoo's native `load()` method, giving both scripts and Claude end-users access to idempotent imports through one interface.

## Odoo MCP Capabilities & Limitations

### What MCP CAN do
- Search, create, update, delete records
- Introspect model schemas (`odoo://{model}/fields`)
- List available models

### What MCP CANNOT do
- Install or activate Odoo modules/apps
- Call `load()` for upsert (needs enhancement)
- Modify Odoo settings or configuration

**Implication:** The migration rapport must include a prerequisites section listing required modules with activation instructions for the client.

## Data Flow Example

```
Input (messy):
┌─────────────────────────────────────────────────────┐
│ Sheet "Compraan BV"                                  │
│ Row 1: klant/Bedrijf | Machine | Type  | serienummer │
│ Row 2: Compraan BV   | Carrier | Trc 1.5 | EMTRC... │
│ Row 5: klant/Bedrijf | Optie's | Type  | serienummer │ ← repeated header!
└─────────────────────────────────────────────────────┘

Cleaned (intermediate, git-committed):
┌─────────────────────────────────────────────────┐
│ klanten.csv                                      │
│ name                                             │
│ Compraan BV                                      │
│ GKB Buiteninrichting                             │
└─────────────────────────────────────────────────┘

Mapped (Odoo-ready with external IDs):
┌──────────────────────────────────────────────────────────┐
│ id,name,is_company,company_type                           │
│ __import__.partner_compraan,Compraan BV,True,company      │
│ __import__.partner_gkb,GKB Buiteninrichting,True,company  │
└──────────────────────────────────────────────────────────┘
```

## Odoo Model Mapping (Emovr case)

| Domain Entity | Odoo Model | Natural Key | Key Fields |
|--------------|------------|-------------|------------|
| Klanten | `res.partner` | name | is_company=True, customer_rank=1 |
| Contactpersonen | `res.partner` | name + parent | parent_id, type=contact |
| Producten | `product.template` | default_code | name, list_price, type=consu |
| Serienummers | `stock.lot` | name | product_id |
| Prijslijst | `product.pricelist.item` | product + pricelist | fixed_price |

Load order: `res.partner` → `product.template` → `product.pricelist.item` → `stock.lot`

## Error Handling

### Data Quality Flags

Each record in the cleaned stage gets a quality assessment:
- **OK** — Complete, consistent, ready to import
- **WARNING** — Missing optional fields, can import with defaults
- **ERROR** — Missing required fields or inconsistent data, needs human input
- **SKIP** — Duplicate or irrelevant (e.g., template rows, free text notes)

### Rollback Strategy

- External IDs in `ir.model.data` provide a complete audit trail
- All records with `__import__` prefix can be queried and deleted if needed
- Import logs track what was created/updated per run

## Future: Odoo Custom Module

The current Claude Code workflow can evolve into a native Odoo module:

- **Wizard-based UI** — TransientModel with state-driven multi-step flow
- **Binary field** for file upload, `fields.Json` for mapping config
- **Claude API integration** via Python `anthropic` SDK
- **Clarifying questions** as wizard form fields (simpler than chat UI)
- **Background processing** via `queue_job` for large files

Requirements: Odoo.sh or self-hosted (NOT Odoo Online/SaaS — custom modules cannot be installed there).

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Engine | Claude API (Anthropic) | Data analysis, mapping, Q&A |
| Odoo Connection | Odoo MCP | Schema introspection, record CRUD, import |
| Import Method | Odoo `load()` via MCP | Idempotent upsert with external IDs |
| Excel Parsing | openpyxl, pandas | Read and transform spreadsheets |
| Workflow | Claude Code | Interactive migration sessions |
| Data Format | CSV (intermediate) | Clean, inspectable, git-versionable |
| Version Control | Git | Track data changes between iterations |

## Key Design Principles

1. **Iterative, not linear** — The whole process is a loop. Imports must be re-runnable.
2. **Idempotent** — Running the same import twice = same result, no duplicates.
3. **Approval before action** — Never import without explicit human go-ahead.
4. **3-tier feedback** — Always communicate confidence: clear / assumptions / need help.
5. **External IDs as anchors** — Every imported record gets a stable `__import__` ID.
6. **Git as version control** — Cleaned CSVs are committed so changes can be diffed.
7. **Master data first** — Partners and products before transactional data.
8. **Script everything** — Manual steps don't scale and introduce variance between cycles.
