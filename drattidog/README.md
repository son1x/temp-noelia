# Dratti-Dog Shop-Export für Odoo

Quelle: https://www.dratti-dog.de/shop/ (IONOS MyWebsite Now / Ecwid, Store-ID 84498537). Stand: 12.11.2026.

**Umfang:** 249 Produkte, 17 Kategorien (hierarchisch), 472 Produktbilder, 4 Produktattribute (Optionen).

## Dateien

| Datei | Odoo-Modell | Inhalt |
|---|---|---|
| `01_product_public_category.csv` | Website › eCommerce › Kategorien (`product.public.category`) | Shop-Kategorien inkl. Unterkategorien |
| `02_product_category.csv` | Inventar/Verkauf › Produktkategorien (`product.category`) | Interne Kategorien unter „All / Dratti-Dog“ |
| `03_product_attribute.csv` | Verkauf › Konfiguration › Attribute (`product.attribute`) | Steg, Druckfarbe, Taschenfarbe, Spruch inkl. Werte |
| `04_product_template.csv` | Produkte (`product.template`) | Name, Artikelnr., Preis, Streichpreis, Kategorien, Beschreibung (HTML), Hauptbild |
| `05_product_image.csv` | Zusätzliche Produktbilder (`product.image`) | 223 weitere Bilder je Produkt |
| `06_product_template_attribute_lines.csv` | Produkte (`product.template`) | Ordnet 14 Produkten ihre Optionen zu → Varianten |
| `07_aufpreise_varianten_info.csv` | – (nur Info) | Aufpreise der Optionen, z. B. „Geteilter Steg“ +5,00 € |
| `dratti-dog_produkte_uebersicht.xlsx` | – | Gesamtübersicht zum Prüfen: Produkte, Kategorien, Optionen, Bestand, Links |
| `bilder/` | – | Alle Produktbilder lokal (1500 px), Dateiname `<SKU>_<Ecwid-ID>_<Nr>.jpg` |

## Skripte (`scripts/`)

- `fetch.py <raw.json>`: lädt alle Kategorien und Produkte über die Ecwid-Storefront-API
- `build.py <raw.json> <ausgabeordner>`: erzeugt die CSV-Dateien und die Excel-Übersicht
- `push.py <raw.json> <bilderordner> [anzahl]`: überträgt alles direkt über die Odoo-19-JSON-2-API in die Instanz: Kategorien, Attribute inkl. Aufpreise, Produkte, Bilder und Bestand. Externe IDs im Modul `drattidog_import` sorgen dafür, dass ein erneuter Lauf aktualisiert statt dupliziert. Der API-Schlüssel wird als `Authorization: Bearer`-Header erwartet.

## Import-Reihenfolge in Odoo (alternativ per CSV)

Jeweils in der Listenansicht des Modells: **⚙ › Datensätze importieren**, CSV hochladen, Trennzeichen Komma, Kodierung UTF-8. Die Spaltenköpfe sind technische Feldnamen und werden automatisch zugeordnet.

1. `01_product_public_category.csv` (Website-App muss installiert sein)
2. `02_product_category.csv`
3. `03_product_attribute.csv`
4. `04_product_template.csv`. Odoo lädt die Bilder aus der Spalte `image_1920` direkt per URL. Der Import dauert deshalb ein paar Minuten.
5. `05_product_image.csv`
6. `06_product_template_attribute_lines.csv`
7. Aufpreise laut `07_…` manuell setzen: Produkt › Attribute & Varianten › „Variantenpreise konfigurieren“. Betroffen ist im Wesentlichen „Geteilter Steg“ mit +5,00 €.

Die Spalte `id` enthält stabile externe IDs (`dratti_product_<Ecwid-ID>` usw.). Ein erneuter Import aktualisiert deshalb die vorhandenen Datensätze, statt Duplikate anzulegen.

## Wichtige Hinweise

- **Preise sind Bruttopreise (inkl. 19 % MwSt.)**, so wie im Shop angezeigt. In Odoo die Verkaufssteuer 19 % auf „Im Preis enthalten“ stellen oder die Website auf Bruttopreise konfigurieren. 12 Produkte sind im Shop mit 0 % MwSt. hinterlegt (siehe Excel, Spalte „MwSt %“).
- **Streichpreise:** 41 Produkte sind reduziert. Der alte Preis steht in `compare_list_price` (Odoo 17/18: „Vergleichspreis“). Bei älteren Odoo-Versionen diese Spalte beim Import ignorieren.
- **Feldnamen für Odoo 17/18.** `description_ecommerce` heißt in älteren Versionen anders. Spalte dann beim Import ignorieren oder auf „Beschreibung für Website“ zuordnen.
- **Bestand:** 201 von 249 Produkten sind im Shop „ausverkauft“, nur 48 haben Bestand. Bestände stehen in der Excel-Übersicht. Sie werden nicht automatisch importiert, weil Odoo Lagerbestände über die Inventur bucht.
- **„Galerie 1“, „Galerie 2“, „Adventkalender 2025“** enthalten überwiegend ausverkaufte Einzelstücke bzw. Referenzarbeiten. Vor dem Import prüfen, ob diese übernommen werden sollen. Viele Produkte liegen in mehreren Kategorien gleichzeitig.
- **Option „Steg“:** Im Shop heißt sie mal „Geteilter Steg“, mal „Geteilter steg“, teils mit Tippfehler („Notmaler steg“). Sie wurde zu einem Attribut **Steg** mit den Werten *Normaler Steg* und *Geteilter Steg* vereinheitlicht.
