# Import Rapport — Emovr Mock Cycle 1
**Datum:** 13 april 2026
**Omgeving:** emovr.odoo.com (Odoo.sh, Enterprise, Odoo 19)

---

## Bronbestanden

| Bestand | Type | Inhoud |
|---------|------|--------|
| Machines&Klanten Emovr.xlsx | Excel (17 sheets) | Machinepark per klant, productie-overzichten, aanbouwdelen |
| Prijslijst Emovr 2026.xlsx | Excel (1 sheet) | 12 producten met artikelnummers en prijzen |
| Odoo offerte.docx | Word | Productomschrijvingen met technische specificaties |
| EMO-20260126-194.pdf | PDF | Voorbeeld-offerte met commerciële voorwaarden |
| Emovr TRC1.5 Flyer.pdf | PDF | Productblad met technische specs TRC 1.5 |
| emovr.nl | Website | Bedrijfsinformatie, producten, dealers, referenties |

---

## HELDER — Wat is geïmporteerd

### Klanten (13 bedrijven)
Compraan BV, GKB Buiteninrichting, SS Teknikk AS, Restauratiebedrijf Verwoerd, A Sloetjes montage, Van Gelder, Brouwer, Tuboma, Mulder Montage BV, Emovr BV, Van de Ende, B&B Diensten, Brouwer Egalisatie

### Leverancier
Stalero Assemblage (productie/assemblage, zelfde eigenaar als Emovr)

### Contactpersonen (6)
Norbert (Verwoerd), Alfred (Sloetjes), Pieter Van Der Meijden (Mulder), Marinus Slingerland (SS Teknikk), Gerwin (GKB), Tiziano Van Bruwaene (uit offerte)

### Producten (12 met prijzen en omschrijvingen)
| Artikelnr | Product | Prijs excl. BTW |
|-----------|---------|-----------------|
| 38000000 | TRC1.5 Carrier | €19.950 |
| 38040001 | Optie Kraan 500KG | €10.750 |
| 38040025 | Optie Kraan 1000KG | €17.500 |
| 38060001 | Optie Glasbok opbouw | €2.750 |
| 38030001 | Optie Dumper opbouw | €3.250 |
| 38090001 | Optie Loader opbouw | €12.500 |
| 38000032 | Optie Rongen set | €500 |
| 38000027 | Hydrauliek optie | €3.250 |
| 38100001 | Schaarlift optie 1 m | €5.500 |
| 38100101 | Schaarlift optie 3.4m | €12.250 |
| 38070001 | Optie Schuif opbouw | (onbekend) |
| 38020001 | Optie Hefmast opbouw | (onbekend) |

### Serienummers (17 carriers)
Alle TRC1.5 Carriers met serienummer aangemaakt als stock.lot met serial tracking.

### Historische verkooporders (13 met volledige inkoop→verkoop keten)
Per machine: inkooporder bij Stalero → ontvangst in magazijn → verkooporder aan klant → levering aan klant. Serienummer correct gekoppeld aan klant via Odoo traceability.

| Serienummer | Klant | Leveringsdatum |
|-------------|-------|----------------|
| EMTRC150925001 | Compraan BV | (onbekend, productiedatum gebruikt) |
| EMTRC150925002 | Emovr BV | (demo, productiedatum gebruikt) |
| EMTRC150925003 | SS Teknikk AS | 2025-12-27 |
| EMTRC150925004 | A Sloetjes montage | 2026-02-12 |
| EMTRC150925005 | GKB Buiteninrichting | 2025-12-17 |
| EMTRC150925006 | Restauratiebedrijf Verwoerd | 2026-01-05 |
| EMTRC1509250008 | Brouwer | (onbekend) |
| EMTRC1509250011 | Brouwer | (onbekend) |
| EMTRC1509250012 | Van Gelder | (onbekend) |
| EMTRC1509250014 | SS Teknikk AS | 2026-04-09 |
| EMTRC1509250016 | Brouwer Egalisatie | 2027-03-26 |
| EMTRC1509250018 | Van Gelder | (onbekend) |
| EMTRC1509250020 | Tuboma | (onbekend) |

### Service-datums (6 machines)
Garantiedatum, servicedatum, keuringsdatum, leveringsdatum als properties op het serienummer voor: EMTRC150925003, EMTRC150925004, EMTRC150925005, EMTRC150925006, EMTRC1509250014, EMTRC1509250016.

### Steekproef verificatie
5 van 13 machines steekproefsgewijs gecontroleerd tegen brondata: **alle 5 correct** (klant, leveringsdatum, garantiedatum, verkooporder).

---

## AANNAMES — Wat we hebben ingeschat

| Aanname | Toelichting |
|---------|-------------|
| Klantnaam-normalisatie | "Verwoert" → "Restauratiebedrijf Verwoerd", "SS Teknik AS" → "SS Teknikk AS", etc. |
| Type-normalisatie | "Trc 1.5" / "TRC1,5" → "TRC1.5" |
| Overgeslagen sheets | "rongen systeem" (alleen 'materialen'), "brouwer egalisatie" (duplicaat) |
| Machines zonder leveringsdatum | Productiedatum (2025-09-15) gebruikt als fallback. Notitie op verkooporder gezet. |
| Inkoopprijs Stalero | €10.000 als placeholder — werkelijke inkoopprijs onbekend |
| Eén carrier per verkooporder | Elke machine als aparte order. In werkelijkheid kan een klant meerdere items per bestelling hebben. |

---

## HULP NODIG — Openstaande vragen

1. **Brouwer / Brouwer Egalisatie** — Is dit hetzelfde bedrijf of twee aparte?
2. **5 machines zonder klant** — EMTRC150925009, EMTRC1509250017, EMTRC1509250013, EMTRC1509250019, EMTRC15092500 — welke klant, of is dit voorraad?
3. **2x onvolledig serienummer** EMTRC15092500 — wat zijn de volledige nummers?
4. **Serienummer-scope** — Krijgen aanbouwdelen (dumper, kraan, etc.) ook een eigen serienummer dat apart getrackt wordt?
5. **Aanbouwdeel → product mapping** — CR0.5 = Kraan 500KG of 1000KG? DU250 = Dumper opbouw?
6. **Rongen Systeem** zonder serienummer — importeren als accessoire of overslaan?
7. **Component-serienummers** (motors, DMC, scherm, acculader) — ook importeren?
8. **Status** (Geleverd/Besteld/Gereserveerd) — hoe vastleggen in Odoo?
9. **Leveringsdatums** — 7 machines missen leveringsdatum. Kunt u deze aanvullen?
10. **Inkoopprijs** — Wat is de werkelijke inkoopprijs bij Stalero?

---

## Configuratie-wijzigingen in Odoo

| Wijziging | Detail |
|-----------|--------|
| Modules geïnstalleerd | Sales, Purchase, Inventory, CRM, Field Service, Accounting |
| Lots & Serial Numbers | Aangevinkt in Inventory settings |
| TRC1.5 Carrier | is_storable=True, tracking=serial, gewicht=700kg, technische specs |
| Offertenummer | EMO-YYYYMMDD-NNN (was S00001) |
| Voorwaarden | Metaalunievoorwaarden 2019 (PDF bijlage + standaardtekst) |
| Klantprofiel | Bedrijfsomschrijving op Emovr B.V. → Notes veld |
| Lot properties | 4 datumvelden (leveringsdatum, garantiedatum, servicedatum, keuringsdatum) |
| TRC1.5 Flyer | Geüpload als productdocument |

---

## Aanbevelingen — Volgende stappen

1. **Beantwoord de 10 openstaande vragen** — dit ontgrendelt de aanbouwdelen-import
2. **Helpdesk module activeren** — voor after-sales tickets van klanten
3. **Aanbouwdelen importeren** — zodra serienummer-scope en product-mapping duidelijk zijn
4. **Leveringsdatums aanvullen** — 7 machines missen de leveringsdatum
5. **Inkoopprijs Stalero** — placeholder €10.000 vervangen door werkelijke prijs

---

*Dit rapport is automatisch gegenereerd als onderdeel van Mock Cycle 1 van de Emovr data migratie.*
