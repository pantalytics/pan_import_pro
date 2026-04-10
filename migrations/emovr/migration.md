# Emovr Migratie

## Status: In voorbereiding

## Klant
- **Bedrijf:** Emovr BV
- **Sector:** Elektrische carriers en aanbouwdelen voor de bouw
- **Odoo:** Enterprise (pantalytics.odoo.com)

## Bronbestanden
- `Machines&Klanten Emovr.xlsx` — Machinepark per klant + productie-overzichten
- `Prijslijst Emovr 2026.xlsx` — Productprijzen 2026

## Domeinkennis
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

## Open Vragen
- [ ] Welke Odoo-modules zijn geactiveerd? (Inventory, Sales, Field Service?)
- [ ] Moeten garantie/service/keuringsdatums als stock.lot velden of als apart model?
- [ ] Moeten de component-serienummers (motors, DMC, etc.) ook als lots?
- [ ] Is er een klant "Emovr BV" zelf nodig als partner (voor demo-machines)?
- [ ] Status (Geleverd/Besteld/Gereserveerd) — als lot status of als apart veld?
- [ ] Prijzen zonder BTW of inclusief?
