"""
Emovr Migration — Step 3: Load into Odoo

Reads cleaned CSVs from cleaned/ and imports them into Odoo via MCP's
import_records tool (which wraps Odoo's load() method).

Uses external IDs (__import__ prefix) for idempotent upsert:
- First run: creates records
- Subsequent runs: updates existing records (no duplicates)

Usage:
    python load.py [--dry-run] [--step STEP]

    --dry-run   Show import plan without executing
    --step      Run only a specific step (klanten, contacten, producten, all)
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CLEANED_DIR = BASE_DIR / "cleaned"
LOGS_DIR = BASE_DIR / "logs"


def slugify(text: str) -> str:
    """Convert text to a safe external ID slug."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def read_csv(filename: str) -> list[dict]:
    """Read a cleaned CSV file."""
    filepath = CLEANED_DIR / filename
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found, skipping")
        return []
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Import step builders
# Each returns: (model, fields, data, description)
# ---------------------------------------------------------------------------

def build_klanten_import() -> tuple:
    """Build import data for klanten (companies)."""
    rows = read_csv("klanten.csv")
    fields = ["id", "name", "is_company", "company_type", "lang", "customer_rank"]
    data = []
    for row in rows:
        name = row["name"]
        ext_id = f"__import__.partner_{slugify(name)}"
        data.append([ext_id, name, "True", "company", "nl_NL", "1"])
    return "res.partner", fields, data, "Klanten (bedrijven)"


def build_contacten_import() -> tuple:
    """Build import data for contact persons."""
    rows = read_csv("contactpersonen.csv")
    fields = ["id", "name", "parent_id/id", "type", "lang"]
    data = []
    for row in rows:
        name = row["name"]
        klant = row["klant"]
        ext_id = f"__import__.contact_{slugify(name)}_{slugify(klant)}"
        parent_ext_id = f"__import__.partner_{slugify(klant)}"
        data.append([ext_id, name, parent_ext_id, "contact", "nl_NL"])
    return "res.partner", fields, data, "Contactpersonen"


def build_producten_import() -> tuple:
    """Build import data for products from prijslijst."""
    rows = read_csv("prijslijst.csv")
    fields = ["id", "name", "default_code", "list_price", "type", "sale_ok", "purchase_ok"]
    data = []
    for row in rows:
        code = row["artikelnummer"]
        name = row["omschrijving"]
        prijs = row["prijs"] if row["prijs"] else "0"
        ext_id = f"__import__.product_{slugify(code)}"
        data.append([ext_id, name, code, prijs, "consu", "True", "True"])
    return "product.template", fields, data, "Producten (prijslijst)"


# ---------------------------------------------------------------------------
# Import plan & execution
# ---------------------------------------------------------------------------

IMPORT_STEPS = [
    ("klanten", build_klanten_import),
    ("contacten", build_contacten_import),
    ("producten", build_producten_import),
]


def show_plan(steps: list[tuple]) -> None:
    """Display the import plan for approval."""
    print("")
    print("=" * 70)
    print("IMPORT PLAN — Emovr Data Migratie")
    print("=" * 70)
    print("")
    print("Volgorde van laden (dependencies):")
    print("  1. res.partner (klanten)     — bedrijven eerst")
    print("  2. res.partner (contacten)   — gekoppeld aan klanten via parent_id")
    print("  3. product.template          — producten uit prijslijst")
    print("")

    total = 0
    for step_name, builder in steps:
        model, fields, data, description = builder()
        count = len(data)
        total += count
        print(f"  Stap: {description}")
        print(f"    Model: {model}")
        print(f"    Records: {count}")
        print(f"    Velden: {', '.join(fields)}")
        if count > 0 and count <= 5:
            for row in data:
                print(f"      {row[0]:50s} → {row[1]}")
        elif count > 5:
            for row in data[:3]:
                print(f"      {row[0]:50s} → {row[1]}")
            print(f"      ... en {count - 3} meer")
        print("")

    print(f"  Totaal: {total} records")
    print(f"  Methode: Odoo load() met __import__ external IDs (upsert)")
    print(f"  Context: tracking_disable=True")
    print("")
    print("  Idempotent: ja — opnieuw draaien maakt geen duplicaten")
    print("")
    print("=" * 70)


def execute_import(steps: list[tuple], dry_run: bool = False) -> dict:
    """Execute the import plan. Returns log data."""
    log = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "steps": [],
    }

    if dry_run:
        show_plan(steps)
        print("  DRY RUN — geen data geïmporteerd")
        return log

    show_plan(steps)

    # Ask for approval
    print("Doorgaan met importeren? [j/n]: ", end="", flush=True)
    answer = input().strip().lower()
    if answer not in ("j", "ja", "y", "yes"):
        print("Import afgebroken.")
        return log

    print("")
    print("Importeren...")
    print("")

    for step_name, builder in steps:
        model, fields, data, description = builder()
        if not data:
            print(f"  {description}: geen data, overgeslagen")
            continue

        print(f"  {description} ({len(data)} records)...", end=" ", flush=True)

        # We can't call MCP from a script directly.
        # Instead, output the import commands for the user/Claude to execute.
        step_log = {
            "step": step_name,
            "model": model,
            "description": description,
            "count": len(data),
            "fields": fields,
            "data": data,
            "status": "ready",
        }
        log["steps"].append(step_log)
        print("klaar (opgeslagen in log)")

    # Write log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"import_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"\n  Import data opgeslagen: {log_path}")
    print(f"\n  Voer de import uit met Claude Code:")
    print(f"    'Importeer de data uit {log_path}'")

    return log


def execute_import_direct(steps: list[tuple]) -> dict:
    """Execute import by calling Odoo load() directly via XML-RPC.

    This is the standalone version that doesn't need MCP.
    For MCP-based import, use the import log with Claude Code.
    """
    try:
        import xmlrpc.client
    except ImportError:
        print("ERROR: xmlrpc.client not available")
        return {}

    import os

    url = os.environ.get("ODOO_URL", "https://emovr.odoo.com")
    api_key = os.environ.get("ODOO_API_KEY", "")
    db = os.environ.get("ODOO_DB", "")
    user = os.environ.get("ODOO_USER", "")

    if not api_key:
        print("ERROR: Set ODOO_API_KEY environment variable")
        return {}

    show_plan(steps)

    print("Doorgaan met importeren? [j/n]: ", end="", flush=True)
    answer = input().strip().lower()
    if answer not in ("j", "ja", "y", "yes"):
        print("Import afgebroken.")
        return {}

    # Connect
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, api_key, {})
    if not uid:
        print("ERROR: Authenticatie mislukt")
        return {}

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    print(f"\n  Connected als uid={uid}")

    log = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
    }

    for step_name, builder in steps:
        model, fields, data, description = builder()
        if not data:
            continue

        print(f"\n  {description} ({len(data)} records)...", end=" ", flush=True)

        result = models.execute_kw(
            db, uid, api_key,
            model, "load",
            [fields, data],
            {"context": {"tracking_disable": True}},
        )

        ids = [i for i in (result.get("ids") or []) if i]
        errors = result.get("messages") or []

        step_log = {
            "step": step_name,
            "model": model,
            "description": description,
            "count": len(data),
            "ids": ids,
            "errors": errors,
            "status": "ok" if not errors else "partial",
        }
        log["steps"].append(step_log)

        if errors:
            print(f"DEELS OK ({len(ids)} ok, {len(errors)} fouten)")
            for err in errors:
                print(f"    FOUT: {err.get('message', err)}")
        else:
            print(f"OK ({len(ids)} records)")

    # Save log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"import_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"\n  Log opgeslagen: {log_path}")

    return log


def main():
    dry_run = "--dry-run" in sys.argv
    step_filter = None

    if "--step" in sys.argv:
        idx = sys.argv.index("--step")
        if idx + 1 < len(sys.argv):
            step_filter = sys.argv[idx + 1]

    # Filter steps
    if step_filter and step_filter != "all":
        steps = [(name, fn) for name, fn in IMPORT_STEPS if name == step_filter]
        if not steps:
            print(f"Unknown step: {step_filter}")
            print(f"Available: {', '.join(name for name, _ in IMPORT_STEPS)}, all")
            sys.exit(1)
    else:
        steps = IMPORT_STEPS

    if dry_run:
        execute_import(steps, dry_run=True)
    else:
        execute_import(steps)


if __name__ == "__main__":
    main()
