# Emovr Migratie

## Status: Mock Cycle 1 — Complete (klanten, contacten, producten geïmporteerd)

## Klant
- **Bedrijf:** Emovr B.V. (res.partner ID 1 in Odoo)
- **Sector:** Elektrische carriers en aanbouwdelen voor de bouw
- **Odoo:** Enterprise (emovr.odoo.com)
- **Klantprofiel:** Opgeslagen in Odoo op res.partner ID 1 → Notes veld
- **Website:** https://www.emovr.nl
- **Locatie:** Barneveld, NL
- **Migratietype:** Greenfield + cutover (nieuw Odoo, data uit Excel)

## Bronbestanden
- `Machines&Klanten Emovr.xlsx` — Machinepark per klant + productie-overzichten
- `Prijslijst Emovr 2026.xlsx` — Productprijzen 2026

## Domeinkennis

### Bedrijfsstructuur (cruciaal)
- **Emovr B.V.** = verkoop + marketing + after-sales service. Produceert NIET zelf.
- **Stalero Assemblage** = productie/assemblage. Zelfde eigenaar (Robert van Laar, CEO).
- Emovr koopt in bij Stalero → levert door aan klanten/dealers.
- In Odoo: handels/distributiebedrijf, GEEN Manufacturing/MRP nodig.
- Stalero is aangemaakt als leverancier (res.partner ID 49, __import__.partner_stalero)

### Verkoopkanalen
- **Direct:** Emovr verkoopt rechtstreeks aan NL klanten
- **Dealers (belangrijk kanaal):** Tuboma (BE), SS-Teknikk AS (NO)

### Product
- Emovr maakt elektrische carriers (model TRC1.5) met verwisselbare aanbouwdelen
- Aanbouwdelen: Dumper (DU250), Crane (CR0.5), Glasbok (GL1.0), Hefmast (HM0.5), Loader (HM1.2), Rongen systeem, Schaarlift (SCH1.4), Hydropack
- Elke carrier heeft een uniek serienummer (formaat: EMTRC150925xxx)
- Aanbouwdelen hebben eigen serienummers (DU..., CR..., GLB..., SCH...)
- Machines kunnen status hebben: Geleverd, Besteld, Gereserveerd, Demo, Afgeleverd
- De "machines" sheet is het master-overzicht; klant-tabs zijn per-klant views van dezelfde data

## Sheet-instructies

### Klant-tabs (Compraan BV, GKB Buiteninrichting, Mulder montage BV, Restauratiebedrijf Verwoerd, A Sloetjes montage, SS Teknikk AS, Van Gelder, Brouwer, Tuboma)
- Elke tab = een klant met hun machines
- Sheets bevatten meerdere **blokken** gescheiden door herhaalde headerrijen
- Blok 1: hoofdmachine (Carrier/Emovr)
- Blok 2+: aanbouwdelen/opties bij die klant
- Headers: klant/Bedrijf | Machine/Optie's | Type | serienummer | Bouwjaar | Contactpersoon | Garantiedatum | Servicedatum | Keuringdatum | Leveringsdatum | Opmerkingen
- Vrije tekst rijen onderaan (bv. "carrier heeft nieuwe pomp...") = opmerkingen, geen data

### Sheet "machines"
- Master-overzicht van alle geproduceerde Emovr Carriers
- Let op: max_row=1048576 maar slechts ~25 echte datarijen (phantom rows)
- Kolommen A-H: machine basisinfo (type, serienummer, bouwjaar, klant, status)
- Kolommen I-O: component-serienummers (motors, DMC, scherm, acculader, HTC, afstandslader, omvormer)
- Rijen zonder serienummer in kolom C zijn lege templates — overslaan

### Sheet "Dumper optie"
- Productie-overzicht van alle Dumpers
- Kolommen: Aanbouwdeel | Type | Serienummer | Bouwjaar | Productiedatum | Klant | Status

### Sheet "Crane optie"
- Productie-overzicht van alle Cranes
- Extra kolom: Kraan nummer (leverancier-serienummer)
- Rijen zonder serienummer = lege voorraad/templates

### Sheet "Glasbok", "Hefmast", "Loader"
- Productie-overzichten per aanbouwdeel
- Zelfde structuur als Dumper optie
- Veel lege rijen (templates voor toekomstige productie)

### Sheet "rongen systeem"
- Bevat alleen "materialen" — geen bruikbare data, overslaan

### Sheet "brouwer egalisatie"
- Enkele rij met afwijkende kolomstructuur (geen headers)
- Dit is een duplicaat van machines sheet rij 16 (Brouwer egalisatie carrier)
- **Overslaan** — data staat al in "machines" sheet

## Opschoonregels

### Klantnaam normalisatie
| Gevonden variant | Genormaliseerd |
|-----------------|----------------|
| Verwoert | Restauratiebedrijf Verwoerd |
| Restauratie bedrijf Verwoerd | Restauratiebedrijf Verwoerd |
| Restauratiebedrijf Verwoerd | Restauratiebedrijf Verwoerd |
| SS Teknik AS | SS Teknikk AS |
| Sloetjes Montage | A Sloetjes montage |
| marinus Slingerland | Marinus Slingerland |
| Brouwer Egalisatie | Brouwer |

### Type normalisatie
| Gevonden variant | Genormaliseerd |
|-----------------|----------------|
| Trc 1.5 | TRC1.5 |
| TRC1,5 | TRC1.5 |
| TRC1.5 | TRC1.5 |
| CR0,5 | CR0.5 |
| GL1,0 | GL1.0 |
| GLB1,2 | GLB1.2 |
| SCH1.4 | SCH1.4 |
| DU250 | DU250 |

### Speciale waarden
| Waarde | Actie |
|--------|-------|
| N.V.T / N,V,T | Leeg veld |
| ? | Leeg veld |
| Lege rij | Overslaan |
| Tekst zonder tabelstructuur | Opmerking → opmerkingen veld |

### Deduplicatie
- Data uit klant-tabs en "machines" sheet overlapt — gebruik "machines" sheet als bron van waarheid voor carriers
- Gebruik klant-tabs als bron voor aanbouwdelen per klant (die staan niet in "machines")
- Gebruik "Dumper optie", "Crane optie" etc. als bron voor aanbouwdeel serienummers

## Odoo Mapping

### Load Order
1. `res.partner` (klanten + contactpersonen)
2. `product.template` (producttypes)
3. `product.pricelist.item` (prijslijst)
4. `stock.lot` (serienummers)

### res.partner — Klanten
| CSV kolom | Odoo veld | Notities |
|-----------|-----------|----------|
| name | name | Genormaliseerde klantnaam |
| — | is_company | True |
| — | company_type | company |

### res.partner — Contactpersonen
| CSV kolom | Odoo veld | Notities |
|-----------|-----------|----------|
| contactpersoon | name | |
| klant | parent_id | Lookup op klantnaam |
| — | type | contact |

### product.template — Producten
| CSV kolom | Odoo veld | Notities |
|-----------|-----------|----------|
| omschrijving | name | Uit prijslijst |
| artikelnummer | default_code | |
| prijs | list_price | |
| — | type | product |

### stock.lot — Serienummers
| CSV kolom | Odoo veld | Notities |
|-----------|-----------|----------|
| serienummer | name | |
| machine_type | product_id | Lookup op product |
| — | company_id | Emovr BV |

## Feedback Ronde 1 (2026-04-13)

### Beantwoord
- **Ontbrekende prijzen:** Prijs €0 is acceptabel — klant vult later aan in Odoo. list_price is niet verplicht.
- **Service/garantiedatums:** Als lot_properties (date velden) op stock.lot. Definition op product.product. Niet via Maintenance (dat is voor intern).
- **Prijzen:** Exclusief BTW (bron: offerte EMO-20260126-194)
- **Garantie:** 1 jaar na aflevering (bron: offerte)
- **Betaalconditie:** Betaling voor aflevering (bron: offerte)
- **Voorwaarden:** Metaalunievoorwaarden (bron: offerte)
- **Productomschrijvingen:** Uitgebreide specs geimporteerd in description_sale (bron: Odoo offerte.docx)

### BLOCKED — Wacht op klant-input
De volgende vragen moeten beantwoord worden voordat we verder kunnen.
Zodra antwoorden binnen zijn: update dit bestand, pas clean.py aan, draai opnieuw.

- [ ] **Brouwer/Brouwer Egalisatie** — zelfde bedrijf of twee aparte?
- [ ] **5 machines zonder klant** — welke klant hoort erbij, of is het voorraad?
      EMTRC150925009, EMTRC1509250017, EMTRC1509250013, EMTRC1509250019, EMTRC15092500
- [ ] **2x onvolledig serienummer** EMTRC15092500 — wat zijn de volledige nummers?
      (1x bij SS Teknikk AS, 1x zonder klant)
- [ ] **Rongen Systeem** zonder serienummer — importeren als accessoire of overslaan?
- [ ] **Component-serienummers** (motors, DMC, scherm, acculader, etc.) — ook als lots importeren?
- [ ] **Status** (Geleverd/Besteld/Gereserveerd) — hoe vastleggen in Odoo?
- [ ] **Aanbouwdeel → product mapping** — CR0.5 = Kraan 500KG of 1000KG? DU250 = Dumper opbouw?

## Odoo Omgeving Status

### Huidige staat (2026-04-10)
- **URL:** emovr.odoo.com
- **Company:** Emovr B.V. (id=1)
- **Bestaande data:** 13 klanten, 5 contactpersonen, 12 producten (alle via __import__ external IDs)

### Import Mock Cycle 1 (2026-04-13)
Geïmporteerd via import_records (Odoo load() met external IDs):
- 13 klanten (res.partner, IDs 27-39) — __import__.partner_*
- 5 contactpersonen (res.partner, IDs 40-44) — __import__.contact_*
- 12 producten (product.template, IDs 4-15) — __import__.product_*
- Idempotentie bewezen: herhaalde import updatet, geen duplicaten
- Oude test-imports (zonder external IDs) opgeruimd

### Module status (2026-04-13)
- [x] **Inventory (stock)** — geactiveerd, stock.lot beschikbaar
- [x] **Lots & Serial Numbers** — setting aangezet via MCP (res.config.settings)
- [x] **Field Service (industry_fsm)** — geactiveerd, project.task met FSM
- [x] **Maintenance** — geactiveerd (voor intern gebruik, NIET voor klant-machines)
- [x] **Sales** — actief
- [ ] **Helpdesk** — nog te activeren (voor after-sales tickets van klanten)

### Configuratie
- TRC1.5 Carrier (product.template ID 4): tracking = "serial"
- lot_properties_definition op product.product ID 4: leveringsdatum, garantiedatum, servicedatum, keuringsdatum
- 6 carriers met service-datums ingevuld via lot_properties
