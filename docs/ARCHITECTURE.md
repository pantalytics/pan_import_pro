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

## The Migration Process

Migration is iterative, not linear. The client is involved at every step. Each step produces feedback for the client (HELDER / AANNAMES / HULP NODIG) and may require their input before proceeding.

### Step 1: Know Your Client

Before touching any data, understand the business.

- **Scrape the client's website** for business context
- **Store a client profile** in Odoo (res.partner Notes field) covering:
  - What they do, what they sell, to whom
  - Business structure (who produces, who sells, who services)
  - Team size, key contacts
  - Sales channels (direct, dealers, online)
  - Business processes (purchase → sell → deliver → service)
- **Determine migration type**: greenfield (new Odoo) vs brownfield (existing data)
- **Document the goal**: what does the client want to achieve with Odoo?

This profile is the foundation. Everything else depends on it. Store it in Odoo on the company record so it's always accessible.

### Step 2: Determine Required Apps and Configuration

Using the client profile, map business processes to Odoo apps.

- **Consult the App Selection Guide** (`docs/odoo-app-guide.md`)
- Use the Decision Framework: whose asset? where is the work done?
- **Check which modules are installed** via MCP (`ir.module.module`)
- **Install missing modules** if needed (MCP can do this via `res.config.settings` + `execute()`)
- **Check configuration** (e.g., "Lots & Serial Numbers" must be enabled for serial tracking)
- **Communicate to client**: "For your business, you need Sales, Purchase, Inventory, Field Service. Here's why."

Common mistakes to avoid: see the "Fix Things Matrix" and Common Mistakes table in the App Guide.

### Step 3: Scan & Understand the Data

Read the client's source files (Excel, CSV, etc.) and understand what's in them.

- **Analyze structure**: headers, data blocks, phantom rows, merged cells, free text
- **Detect entities**: customers, products, serial numbers, dates, prices
- **Identify quality issues**: duplicates, spelling variants, missing data, incomplete records
- **Produce a 3-tier rapport**:
  - **HELDER** — "This I could read with certainty"
  - **AANNAMES** — "I wasn't 100% sure, I assumed this"
  - **HULP NODIG** — "I need your input on this"
- **Ask clarifying questions** — one at a time, multiple choice where possible

### Step 4: Clean & Normalize

Apply cleanup rules to produce normalized CSVs.

- Name normalization, header unification, deduplication
- Handle placeholders (N.V.T., ?, empty)
- Split multi-block sheets into separate tables
- **Git-commit the CSVs** so changes can be diffed between iterations
- **Show diff to client** when re-running after feedback

What is clear gets processed. What is BLOCKED (waiting for client input) stays marked as TODO.

### Step 5: Map to Odoo

Match cleaned data to Odoo models and fields.

- **Query Odoo schemas** via MCP (`odoo://{model}/fields`)
- Determine load order (dependencies: partners before contacts, products before serial numbers)
- Generate external IDs for idempotent upsert (`__import__.partner_compraan_bv`)
- **Show the import plan** to the client: "X records to create, Y to update, Z unchanged"
- **Wait for approval** — NEVER import without explicit go-ahead

### Step 6: Import (Upsert)

Execute the approved plan via Odoo MCP `import_records` (wraps `load()`).

- Import in dependency order
- Use external IDs for idempotent upsert
- Context: `tracking_disable=True` to suppress notifications
- **Import in small batches** — not everything at once
- **Verify after EACH batch** before continuing (see Step 7)
- Log all created/updated record IDs
- Report results to client

### Step 7: Verify (after every import)

**Critical step — do NOT skip.** After every import batch, verify that the data is correct before importing the next batch.

#### Automated verification (AI)
The AI samples records and cross-checks against source data:
- Pick 3-5 random imported records
- Read them back from Odoo via MCP
- Compare each field against the source CSV
- Check relational fields (does the lot point to the right partner? does the sale order have the right serial number?)
- Report: "Checked 5 records, 5 correct" or "Record X has wrong partner — expected GKB, got SS Teknikk"

Example checks:
```
Source: EMTRC150925005 → GKB Buiteninrichting → delivered 2025-12-17
Odoo:   stock.lot.name=EMTRC150925005 → partner_ids=[33] ✓
        sale.order.partner_id=GKB ✓
        stock.picking.date_done=2025-12-17 ✓
        → OK
```

#### Manual verification (client)
After AI verification passes, ask the client to spot-check:
- "Can you check serial number EMTRC150925005 in Odoo? Does it show GKB Buiteninrichting with delivery date 17 december 2025?"
- Provide direct Odoo URLs for easy checking
- Use the 3-tier feedback format for the verification report

#### What to do when verification fails
- **Stop importing** — don't continue with more data until the issue is fixed
- Diagnose the root cause (wrong ID mapping? shifted data? API behavior?)
- Fix and re-import the failed batch
- Re-verify
- Only then continue with the next batch

### Step 8: Iterate

Client checks results in Odoo. This always produces feedback.

- New corrections? → Update migration.md, re-run clean, re-import (upsert)
- New data version? → Drop new files in input/, repeat from Step 3
- Missing data? → Add to BLOCKED list, ask client
- Wrong app/model choice? → Revisit Step 2
- Configuration wrong? → Fix settings, re-import

Typically 3-5 cycles before go-live.

```
Step 1 ─→ Step 2 ─→ Step 3 ─→ Step 4 ─→ Step 5 ─→ Step 6 ─→ Step 7 ─→ Step 8
Know       Apps &    Scan &    Clean &   Map to    Import    Verify     Iterate
Client     Config    Understand Normalize Odoo      (batch)   (each      │
                                                    ↓         batch)     │
                                                    Step 7 ←──┘          │
                         ┌───────────────────────────────────────────────┘
                         │ Client feedback / corrections / new data
                         ▼
                    Back to Step 3, 4, 5, or 6 as needed
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
