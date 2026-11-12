"""Übernimmt Impressums-/Adressdaten von www.dratti-dog.de/impressum in Odoo 19:
Unternehmensdaten + website-spezifische Kopien von Header, Footer und Kontaktseite (Platzhalter ersetzt)."""
import json, re, urllib.request
H="https://montreal-reading-outer-arena.trycloudflare.com"; CTX={"lang":"de_DE"}; WEBSITE=1
D=dict(owner="Cornelia Weiland", firm="Dratti-Dog - Haustierbedarf", street="Eichenbornweg 27", zip="66798",
       city="Wallerfangen", phone="+49 176 63378306", tel="+4917663378306", fax="+49 6831 1660913",
       email="drattidog@gmail.com", vat="DE340567541", web="https://www.dratti-dog.de")
def call(model, method, **kw):
    kw.setdefault("context", CTX)
    req=urllib.request.Request(f"{H}/json/2/{model}/{method}", data=json.dumps(kw).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer proxy-injected"})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: raise SystemExit(f"{model}.{method} HTTP {e.code}: {e.read().decode()[:1500]}")

# 1) Unternehmen
de=call("res.country","search",domain=[["code","=","DE"]])[0]
call("res.company","write",ids=[1],vals={"street":D["street"],"street2":False,"zip":D["zip"],"city":D["city"],"country_id":de,
     "phone":D["phone"],"email":D["email"],"vat":D["vat"],"website":D["web"]})

# 2) Platzhalter in Website-Ansichten ersetzen
def fix(a):
    a=a.replace("tel:+1 555-555-5556",f"tel:{D['tel']}").replace("+1 555-555-5556",D["phone"])
    a=a.replace("mailto:info@yourcompany.example.com",f"mailto:{D['email']}").replace("info@ihrunternehmen.beispiel.com",D["email"])
    a=a.replace("info@yourcompany.example.com",D["email"])
    # Kontaktseite: Adressblock komplett
    a=a.replace("<h5>Mein Unternehmen</h5>",f"<h5>{D['firm']}</h5>")
    a=re.sub(r'<li><i class="fa fa-map-marker fa-fw me-2"/><span class="o_force_ltr">3575 Fake Buena Vista Avenue</span></li>',
        f'<li><i class="fa fa-user fa-fw me-2"/><span>{D["owner"]}</span></li>'
        f'<li><i class="fa fa-map-marker fa-fw me-2"/><span>{D["street"]}, {D["zip"]} {D["city"]}</span></li>', a)
    a=a.replace(f'<li><i class="fa fa-1x fa-fw fa-envelope me-2"/><span>{D["email"]}</span></li>',
        f'<li><i class="fa fa-fax fa-fw me-2"/><span class="o_force_ltr">Fax {D["fax"]}</span></li>'
        f'<li><i class="fa fa-1x fa-fw fa-envelope me-2"/><a href="mailto:{D["email"]}">{D["email"]}</a></li>')
    # Footer: Adresse ergänzen
    a=a.replace(f'<li><i class="fa fa-phone fa-fw me-2"/><a href="tel:{D["tel"]}"><span class="o_force_ltr">{D["phone"]}</span></a></li>',
        f'<li><i class="fa fa-phone fa-fw me-2"/><a href="tel:{D["tel"]}"><span class="o_force_ltr">{D["phone"]}</span></a></li>'
        f'<li><i class="fa fa-map-marker fa-fw me-2"/>{D["street"]}, {D["zip"]} {D["city"]}</li>')
    return a
for key in ["website.footer_custom","website.header_text_element","website.contactus"]:
    base=call("ir.ui.view","search_read",domain=[["key","=",key],["website_id","=",False]],fields=["name","arch_db","inherit_id","priority","mode","active"])[0]
    new=fix(base["arch_db"])
    assert "555-555" not in new and "beispiel.com" not in new, key
    ex=call("ir.ui.view","search",domain=[["key","=",key],["website_id","=",WEBSITE]])
    vals={"arch_db":new}
    if ex: call("ir.ui.view","write",ids=ex,vals=vals); vid=ex[0]
    else:
        vid=call("ir.ui.view","create",vals_list=[{"name":base["name"],"key":key,"type":"qweb","website_id":WEBSITE,"arch_db":new,
             "inherit_id":base["inherit_id"][0] if base["inherit_id"] else False,"priority":base["priority"],"mode":base["mode"],"active":base["active"]}])[0]
    print(key,"-> website view",vid)
# Kontaktseite: website-spezifische Seite auf die Kopie zeigen lassen
cv=call("ir.ui.view","search",domain=[["key","=","website.contactus"],["website_id","=",WEBSITE]])[0]
if not call("website.page","search",domain=[["url","=","/contactus"],["website_id","=",WEBSITE]]):
    call("website.page","create",vals_list=[{"url":"/contactus","view_id":cv,"website_id":WEBSITE,"is_published":True}])
print("ok")
