import json, csv, re, sys, os, html, unicodedata
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
RAW, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(RAW))
cats = {int(k): v for k, v in d["categories"].items()}
os.makedirs(OUT, exist_ok=True)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
def cxid(cid): return f"dratti_pubcateg_{cid}"
def icxid(cid): return f"dratti_categ_{cid}"
def pxid(pid): return f"dratti_product_{pid}"
def money(x): return f"{x:.2f}"
def clean_html(h):
    h = (h or "").replace("&nbsp;", " ").strip()
    return h
def plain(h):
    t = re.sub(r"<br\s*/?>|</p>|</li>", "\n", h or "", flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    return re.sub(r"\n\s*\n+", "\n", t).strip()

def writecsv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

# ---- Categories (root 0 = Startseite des Shops, wird nicht als Kategorie angelegt)
real = {cid: c for cid, c in cats.items() if cid != 0}
parent = {}
for cid, c in cats.items():
    for s in c["subcategories"]:
        parent[s["id"]] = cid
order = list(real)  # crawl order = parents before children
pub_rows, int_rows = [], []
for i, cid in enumerate(order):
    c = real[cid]; par = parent.get(cid, 0)
    pub_rows.append([cxid(cid), c["name"], cxid(par) if par else "", (i + 1) * 10])
    int_rows.append([icxid(cid), c["name"], icxid(par) if par else "dratti_categ_root"])
writecsv("01_product_public_category.csv", ["id", "name", "parent_id/id", "sequence"], pub_rows)
writecsv("02_product_category.csv", ["id", "name", "parent_id/id"],
         [["dratti_categ_root", "Dratti-Dog", "product.product_category_all"]] + int_rows)

# ---- Attributes
def norm_choice(opt, choice):
    o = opt.lower().strip()
    if "steg" in o:
        return "Steg", ("Geteilter Steg" if "geteilt" in choice.lower() else "Normaler Steg")
    return opt.strip(), choice.strip()
attrs = {}       # attr -> {value: set(extras)}
tmpl_attrs = {}  # pid -> {attr: [values]}
price_extras = []
for pid, v in d["products"].items():
    p = v["product"]
    po = p["defaultOptionsOverrides"]["pricesOverrides"]
    types = {o["optionId"]: o["type"] for o in p["options"]}
    for oc in po["optionsChoicesWithModifiersAndTaxes"]:
        vals = []
        for ch in oc["choices"]:
            a, val = norm_choice(oc["optionId"], ch["choiceName"])
            vals.append(val)
            extra = ch.get("modifierFormatted") or ""
            m = re.search(r"([+-]?\d+(?:\.\d+)?)", extra.replace(",", "."))
            amt = float(m.group(1)) if m else 0.0
            attrs.setdefault(a, {}).setdefault(val, set()).add(amt)
            price_extras.append([pxid(pid), p["name"], a, val, money(amt)])
        if a == "Steg" and "Normaler Steg" not in vals:
            vals.insert(0, "Normaler Steg"); attrs[a].setdefault("Normaler Steg", set()).add(0.0)
            price_extras.append([pxid(pid), p["name"], a, "Normaler Steg", "0.00"])
        tmpl_attrs.setdefault(pid, {}).setdefault(a, [])
        for x in vals:
            if x not in tmpl_attrs[pid][a]: tmpl_attrs[pid][a].append(x)
def axid(a): return "dratti_attr_" + slug(a)
def vxid(a, v): return "dratti_attrval_" + slug(a) + "__" + slug(v)
arows = []
for a, vals in attrs.items():
    first = True
    for val in vals:
        arows.append([axid(a) if first else "", a if first else "", "always" if first else "", vxid(a, val), val])
        first = False
writecsv("03_product_attribute.csv", ["id", "name", "create_variant", "value_ids/id", "value_ids/name"], arows)

# ---- Products
tmpl_rows, img_rows, attr_line_rows, overview = [], [], [], []
os.makedirs(os.path.join(OUT, "bilder"), exist_ok=True)
downloads = []
for pid, v in d["products"].items():
    p = v["product"]; o = p["defaultOptionsOverrides"]; po = o["pricesOverrides"]; vo = o["variationOverrides"]
    sku = vo.get("sku") or ""
    catids = [c for c in v["categories"] if c != 0]
    default = None
    for cp in p.get("categoryPaths", []):
        if cp.get("isDefault") and len(cp["categoryPath"]) > 1: default = cp["categoryPath"][-1]["id"]
    if default not in catids: default = catids[0] if catids else None
    price = po["basePrice"]
    strike = (po.get("strikethroughPrice") or {}).get("price")
    tax = po["appliedTaxes"][0]["percent"] if po["appliedTaxes"] else None
    pics = [m for m in vo["mediaItems"] if m["type"] == "PICTURE"]
    pics.sort(key=lambda m: not m.get("isMain"))
    main = pics[0]["imageOriginalUrl"] if pics else ""
    url = "https://www.dratti-dog.de" + p["urls"]["directPageUrl"]
    local = []
    for i, m in enumerate(pics):
        fn = f"{slug(sku) or pid}_{pid}_{i+1}.jpg"
        local.append("bilder/" + fn)
        downloads.append((m["image1500pxUrl"], fn))
        if i > 0:
            img_rows.append([f"dratti_img_{pid}_{i+1}", pxid(pid), f"{p['name']} ({i+1})", m["imageOriginalUrl"]])
    qty = vo.get("quantity") or 0
    sold_out = vo.get("isSoldOut")
    tmpl_rows.append([
        pxid(pid), p["name"].strip(), sku, money(price), money(strike) if strike else "",
        icxid(default) if default else "dratti_categ_root",
        ",".join(cxid(c) for c in catids),
        "consu", "True", "True", "True" if vo.get("isShippingRequired", True) else "False",
        clean_html(p.get("description")), main])
    first = True
    for a, vals in tmpl_attrs.get(pid, {}).items():
        attr_line_rows.append([pxid(pid) if first else "", axid(a), ",".join(vxid(a, x) for x in vals)])
        first = False
    overview.append({
        "Ecwid-ID": int(pid), "SKU": sku, "Name": p["name"].strip(),
        "Preis (brutto €)": price, "Streichpreis (€)": strike or None,
        "MwSt %": tax, "Bestand": qty, "Ausverkauft": "ja" if sold_out else "nein",
        "Hauptkategorie": " / ".join(cats[default]["path"]) if default else "",
        "Alle Kategorien": " | ".join(" / ".join(cats[c]["path"]) for c in catids),
        "Optionen": "; ".join(f"{a}: {', '.join(vs)}" for a, vs in tmpl_attrs.get(pid, {}).items()),
        "Beschreibung": plain(p.get("description")),
        "Anzahl Bilder": len(pics), "Hauptbild URL": main,
        "Weitere Bild-URLs": " ".join(m["imageOriginalUrl"] for m in pics[1:]),
        "Lokale Bilder": " ".join(local), "Shop-URL": url,
    })

# drop helper column cleanly (header adjusted below)
rows = [r[:10] + [r[11], r[12]] for r in tmpl_rows]
writecsv("04_product_template.csv",
    ["id", "name", "default_code", "list_price", "compare_list_price", "categ_id/id", "public_categ_ids/id",
     "type", "sale_ok", "is_published", "description_ecommerce", "image_1920"], rows)
writecsv("05_product_image.csv", ["id", "product_tmpl_id/id", "name", "image_1920"], img_rows)
writecsv("06_product_template_attribute_lines.csv",
         ["id", "attribute_line_ids/attribute_id/id", "attribute_line_ids/value_ids/id"], attr_line_rows)
writecsv("07_aufpreise_varianten_info.csv", ["product_xmlid", "produkt", "attribut", "wert", "aufpreis_eur"], price_extras)

# ---- Excel overview
wb = Workbook(); ws = wb.active; ws.title = "Produkte"
hdr = list(overview[0].keys()); ws.append(hdr)
for r in sorted(overview, key=lambda r: (r["Hauptkategorie"], r["Name"])): ws.append([r[h] for h in hdr])
ws2 = wb.create_sheet("Kategorien"); ws2.append(["Ecwid-ID", "Kategorie (Pfad)", "Anzahl Produkte", "Kategoriebild"])
for cid in order:
    n = sum(1 for v in d["products"].values() if cid in v["categories"])
    ws2.append([cid, " / ".join(real[cid]["path"]), n, real[cid].get("image") or ""])
ws3 = wb.create_sheet("Optionen & Aufpreise"); ws3.append(["Produkt-XMLID", "Produkt", "Attribut", "Wert", "Aufpreis €"])
for r in price_extras: ws3.append(r[:4] + [float(r[4])])
for w in (ws, ws2, ws3):
    for c in w[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="3F5979")
    w.freeze_panes = "A2"; w.auto_filter.ref = w.dimensions
    for i, col in enumerate(w.columns, 1):
        w.column_dimensions[get_column_letter(i)].width = min(60, max(10, max(len(str(c.value or "")) for c in col[:60]) + 2))
for c in ws["D"][1:] + ws["E"][1:]: c.number_format = '#,##0.00 "€"'
wb.save(os.path.join(OUT, "dratti-dog_produkte_uebersicht.xlsx"))
json.dump(downloads, open(os.path.join(os.path.dirname(RAW), "downloads.json"), "w"))
print("products", len(rows), "extra images", len(img_rows), "attr lines", len(attr_line_rows), "attrs", {a: list(v) for a, v in attrs.items()})
