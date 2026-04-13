# Odoo App Selection Guide

A structured knowledge base for mapping business scenarios to the correct Odoo apps.
Used by the AI migration tool to avoid importing data into the wrong models.

## The Decision Framework

Two questions cut through most app selection confusion:
1. **Whose asset?** Yours (internal) or the customer's?
2. **Where is the work done?** Your location, their location, or remote?

## Quick Reference: The "Fix Things" Matrix

The most common source of confusion. Use this 2x2:

| | **Your equipment** | **Customer's equipment** |
|---|---|---|
| **Your location** | **Maintenance** | **Repairs** |
| **Customer's location** | (rare) | **Field Service** |
| **Remote** | — | **Helpdesk** |

Helpdesk acts as the front door: a ticket can escalate to Repairs (ship it to us), Field Service (we come to you), or a refund/return.

---

## App Profiles

### CRM

**When to use:**
- Sales pipeline with leads progressing through stages
- Lead scoring, prospecting, win/loss tracking
- Multiple salespeople nurturing opportunities

**When NOT to use:**
- You just need to send quotes and invoices (use Sales)
- You only need to store contacts (that's res.partner, not CRM)

**Key models:** `crm.lead`, `crm.team`, `utm.source`
**Typical company:** B2B with multi-stage sales cycles, companies with dedicated sales teams
**Related apps:** Sales (converts won opportunities into quotations), Marketing Automation

---

### Sales

**When to use:**
- Create quotations, confirm sales orders, invoice customers
- Pricelists, discounts, subscription billing
- Multi-channel selling (webshop, Amazon, POS)

**When NOT to use:**
- You only need pipeline/lead tracking (use CRM)
- You only purchase, never sell (use Purchase)

**Key models:** `sale.order`, `sale.order.line`, `sale.order.template`, `product.pricelist`
**Typical company:** Any company that sells products or services
**Related apps:** CRM (feeds opportunities), Inventory (fulfillment), Accounting (invoicing)

---

### Purchase

**When to use:**
- Send RFQs to vendors, manage purchase orders
- Vendor pricelists, blanket orders, call-for-tenders
- Automated reordering rules tied to inventory levels

**When NOT to use:**
- You only buy occasionally without formal PO workflow
- Internal requisitions only (use Approvals)

**Key models:** `purchase.order`, `purchase.order.line`, `product.supplierinfo`
**Typical company:** Manufacturers sourcing components, retailers replenishing stock
**Related apps:** Inventory (receiving), Accounting (vendor bills), Manufacturing (component sourcing)

---

### Inventory

**When to use:**
- Physical stock tracking (quantities, locations, multi-warehouse)
- Lot or serial number traceability (food, pharma, electronics, machines)
- Shipping, receiving, dropship flows

**When NOT to use:**
- You sell only services with no physical goods
- You only need a product catalog (product master lives in Sales too)

**Key models:** `stock.move`, `stock.picking`, `stock.lot`, `stock.quant`, `stock.warehouse`, `stock.location`, `product.template`, `product.product`
**Typical company:** Distributors, e-commerce, manufacturers, any company with a warehouse
**Related apps:** Manufacturing (consumes stock), Purchase (replenishes), Sales (triggers delivery)

---

### Manufacturing

**When to use:**
- Produce finished goods from raw materials using bills of materials
- Work orders, work centers, shop floor tracking
- Subcontract production to third parties

**When NOT to use:**
- You only assemble kits at point of sale (Inventory kits may suffice)
- You resell finished goods without transformation (use Inventory alone)

**Key models:** `mrp.production`, `mrp.bom`, `mrp.bom.line`, `mrp.workcenter`, `mrp.workorder`
**Typical company:** Factories, artisan producers, food processors
**Related apps:** Inventory (stock consumption), Purchase (components), Quality (inspection)

---

### Project

**When to use:**
- Internal or client projects with tasks, stages, deadlines
- Timesheets for billing or internal time tracking
- Project profitability tracking

**When NOT to use:**
- Your "projects" are on-site service visits (use Field Service)
- You only need a simple to-do list (overkill)

**Key models:** `project.project`, `project.task`, `account.analytic.line` (timesheets)
**Typical company:** Consulting firms, agencies, software teams
**Related apps:** Timesheets, Sales (billable projects), Field Service (extends Project)

---

### Field Service

**When to use:**
- Dispatch technicians to customer sites for installations, repairs, inspections
- Itinerary planning, on-site worksheets, mobile task management
- **Customer's equipment, at customer's location**

**When NOT to use:**
- Support is handled remotely (use Helpdesk)
- You maintain your own internal equipment (use Maintenance)
- Work is done at your facility on customer goods (use Repairs)

**Key models:** `project.task` (with `is_fsm=True`), worksheet templates, `product.product` (materials used)
**Typical company:** HVAC contractors, telecom installers, elevator service, machine manufacturers with after-sales service
**Related apps:** Helpdesk (ticket triggers field visit), Project (Field Service extends it), Sales (bill for work)

---

### Helpdesk

**When to use:**
- Customer support tickets via email, chat, web forms
- SLAs, customer satisfaction ratings, ticket metrics
- After-sales hub: can trigger returns, repairs, refunds, field service tasks

**When NOT to use:**
- Primarily on-site technician work (use Field Service, triggered from Helpdesk)
- Internal IT ticketing only (works but is customer-facing by design)

**Key models:** `helpdesk.ticket`, `helpdesk.team`, `helpdesk.sla`
**Typical company:** SaaS vendors, equipment dealers with after-sales obligations
**Related apps:** Field Service (dispatch from ticket), Repairs (repair order from ticket), Sales (refunds/credit notes)

---

### Repairs

**When to use:**
- Customers send you broken products and you fix them at your facility
- Track parts used, warranty status, return logistics
- **Customer's product, your location**

**When NOT to use:**
- You go to the customer's site to fix things (use Field Service)
- You maintain your own machines (use Maintenance)

**Key models:** `repair.order`, `repair.line`, `stock.lot` (serial tracking)
**Typical company:** Electronics repair shops, equipment dealers with service centers
**Related apps:** Helpdesk (ticket triggers repair), Inventory (parts and returns), Sales (invoicing)

---

### Maintenance

**When to use:**
- Schedule preventive maintenance on your own internal equipment
- Maintenance calendar with recurring requests
- **Your equipment, your location**

**When NOT to use:**
- You service customer equipment (use Field Service or Repairs)
- You need customer-facing ticketing (use Helpdesk)
- You track warranty/service dates on sold products (NOT this)

**Key models:** `maintenance.equipment`, `maintenance.request`, `maintenance.team`, `maintenance.equipment.category`
**Typical company:** Factories, facilities managers, fleet operators — anyone with capital equipment needing scheduled upkeep
**Related apps:** Manufacturing (equipment tied to work centers), Inventory (spare parts)

---

### Accounting

**When to use:**
- Full general ledger, journal entries, financial statements
- Tax declarations, bank reconciliation, multi-currency
- Localized accounting (40+ country localizations)

**When NOT to use:**
- You only need basic invoicing (Invoicing app is lighter)
- You outsource all accounting to an external firm

**Key models:** `account.move`, `account.account`, `account.journal`, `account.tax`, `account.payment`
**Typical company:** Any company beyond the smallest
**Related apps:** Sales (invoices), Purchase (vendor bills), Inventory (stock valuation), Payroll

---

### Quality

**When to use:**
- Quality checks on incoming/outgoing shipments or manufacturing
- Min/max tolerance measurements
- Quality alerts and corrective actions

**When NOT to use:**
- You only need visual inspection notes (use chatter/notes on picking)

**Key models:** `quality.check`, `quality.alert`, `quality.point`
**Typical company:** Manufacturers, food/pharma companies with compliance requirements
**Related apps:** Manufacturing (quality at work orders), Inventory (quality at receipts)

---

### Planning

**When to use:**
- Schedule employee shifts and work schedules
- Visual drag-and-drop resource planning
- Forecast workload capacity

**When NOT to use:**
- You plan project tasks, not shifts (use Project)
- You dispatch field technicians (use Field Service)

**Key models:** `planning.slot`, `planning.role`
**Typical company:** Retail, hospitality, manufacturing with shift workers
**Related apps:** HR (employees), Field Service, Manufacturing

---

### Rental

**When to use:**
- Rent out products with delivery and return tracking
- Manage rental periods, pricing, and availability
- Track which assets are currently out on rental

**When NOT to use:**
- You sell products outright (use Sales)
- You lease vehicles long-term (use Fleet)

**Key models:** `sale.order` (with rental fields), `sale.order.line`
**Typical company:** Equipment rental, car rental, tool hire companies
**Related apps:** Sales (extends it), Inventory (stock availability)

---

### Fleet

**When to use:**
- Manage company vehicles, leasing contracts, insurance
- Track fuel costs, maintenance, odometer readings
- Assign vehicles to employees

**When NOT to use:**
- You rent vehicles to customers (use Rental)
- You maintain factory equipment (use Maintenance)

**Key models:** `fleet.vehicle`, `fleet.vehicle.log.fuel`, `fleet.vehicle.log.services`
**Typical company:** Companies with company cars or delivery fleets
**Related apps:** HR (employee vehicle assignment), Accounting (cost tracking)

---

## Common Mistakes

| Mistake | Why it's wrong | Correct app |
|---------|---------------|-------------|
| Maintenance for sold products | Maintenance = YOUR equipment, not customer's | Field Service or Helpdesk |
| Field Service for remote support | Field Service = on-site visits | Helpdesk |
| CRM for contact management | CRM = sales pipeline, not an address book | res.partner (core) |
| Manufacturing for kit assembly | MRP is for production with work orders | Inventory (kits) |
| Project for field technician work | Project = office/desk work | Field Service |

---

## How to Use This Guide During Migration

Before importing data into any Odoo model:

1. Understand the client's business process (what do they do, for whom, where?)
2. Use the Decision Framework and Fix Things Matrix to identify the right app
3. Verify the required module is installed (`ir.module.module` via MCP)
4. Check the model's fields via MCP (`odoo://{model}/fields`) before mapping
5. If unsure — ask the client, don't guess

## Generating This Guide from Odoo

The app descriptions in this guide can be refreshed from any Odoo instance:

```python
# Via MCP: get all apps with descriptions
search_records(
    model="ir.module.module",
    domain=[["summary", "!=", ""], ["application", "=", true]],
    fields=["name", "shortdesc", "summary", "category_id", "state", "description"],
    order="shortdesc asc"
)
```

This gives you each app's official summary and description, plus whether it's installed.

## Sources

### Odoo Official Documentation (18.0/19.0)
- [Field Service](https://www.odoo.com/documentation/18.0/applications/services/field_service.html)
- [Helpdesk](https://www.odoo.com/documentation/18.0/applications/services/helpdesk.html)
- [After-Sales Services](https://www.odoo.com/documentation/18.0/applications/services/helpdesk/advanced/after_sales.html)
- [Maintenance](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/maintenance.html)
- [Repairs](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/repairs/repair_orders.html)
- [Manufacturing](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/manufacturing.html)
- [Inventory](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory.html)
- [Sales](https://www.odoo.com/documentation/18.0/applications/sales/sales.html)
- [CRM](https://www.odoo.com/documentation/18.0/applications/sales/crm.html)
- [Purchase](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase.html)
- [Project](https://www.odoo.com/documentation/18.0/applications/services/project.html)

### Odoo Community & Learning
- [Odoo Forum: When to use Maintenance, Repairs, Field Services](https://www.odoo.com/forum/help-1/when-would-we-use-maintenance-repairs-and-field-services-apps-284702)
- [Odoo Academy / eLearning](https://www.odoo.com/slides)
- [Odoo App Store](https://www.odoo.com/app) — official app descriptions

### Odoo Instance (live data)
- `ir.module.module` — app descriptions, install status, categories
- `odoo://{model}/fields` — field definitions per model via MCP
