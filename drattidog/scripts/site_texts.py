"""Impressum-Seite (/impressum) aus dem alten Shop, Footer-Texte und Copyright für Odoo 19 (Website 1)."""
import json, urllib.request
H="https://montreal-reading-outer-arena.trycloudflare.com"; CTX={"lang":"de_DE"}; W=1; MOD="drattidog_import"
def call(model, method, **kw):
    kw.setdefault("context", CTX)
    req=urllib.request.Request(f"{H}/json/2/{model}/{method}", data=json.dumps(kw).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer proxy-injected"})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: raise SystemExit(f"{model}.{method} HTTP {e.code}: {e.read().decode()[:1500]}")
def xid(name):
    r=call("ir.model.data","search_read",domain=[["module","=",MOD],["name","=",name]],fields=["res_id"]); return r[0]["res_id"] if r else None
def upsert(model,name,vals):
    rid=xid(name)
    if rid and call(model,"search_count",domain=[["id","=",rid]]): call(model,"write",ids=[rid],vals=vals); return rid
    if rid: call("ir.model.data","unlink",ids=call("ir.model.data","search",domain=[["module","=",MOD],["name","=",name]]))
    rid=call(model,"create",vals_list=[vals])[0]
    call("ir.model.data","create",vals_list=[{"module":MOD,"name":name,"model":model,"res_id":rid,"noupdate":True}]); return rid
def website_copy(key, arch):
    base=call("ir.ui.view","search_read",domain=[["key","=",key],["website_id","=",False]],fields=["name","inherit_id","priority","mode","active"])[0]
    ex=call("ir.ui.view","search",domain=[["key","=",key],["website_id","=",W]])
    if ex: call("ir.ui.view","write",ids=ex,vals={"arch_db":arch}); return ex[0]
    return call("ir.ui.view","create",vals_list=[{"name":base["name"],"key":key,"type":"qweb","website_id":W,"arch_db":arch,
        "inherit_id":base["inherit_id"][0] if base["inherit_id"] else False,"priority":base["priority"],"mode":base["mode"],"active":base["active"]}])[0]

# 1) Impressum (Stand alter Shop; § 5 TMG -> § 5 DDG; Hinweis auf EU-OS-Plattform entfällt, Plattform seit 20.07.2025 abgeschaltet)
imp=f'''<t t-name="{MOD}.page_impressum"><t t-call="website.layout"><div id="wrap" class="oe_structure">
<section class="container py-5" style="max-width:800px">
<h1 class="mb-4">Impressum</h1>
<h2 class="h5">Angaben gemäß § 5 DDG</h2>
<p>Cornelia Weiland<br/>Dratti-Dog - Haustierbedarf<br/>Eichenbornweg 27<br/>66798 Wallerfangen<br/>Deutschland</p>
<h2 class="h5 mt-4">Kontakt</h2>
<p>Telefon: <a href="tel:+4917663378306">+49 176 63378306</a><br/>Telefax: +49 6831 1660913<br/>E-Mail: <a href="mailto:drattidog@gmail.com">drattidog@gmail.com</a></p>
<h2 class="h5 mt-4">Umsatzsteuer-ID</h2>
<p>Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz: DE340567541</p>
<h2 class="h5 mt-4">Verbraucherstreitbeilegung/Universalschlichtungsstelle</h2>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
</section></div></t></t>'''
pv=upsert("ir.ui.view","view_page_impressum",{"name":"Impressum","type":"qweb","key":f"{MOD}.page_impressum","arch_db":imp})
upsert("website.page","page_impressum",{"view_id":pv,"url":"/impressum","website_id":W,"is_published":True,"website_indexed":True})

# 2) Footer
footer='''<data inherit_id="website.layout" name="Default" active="True">
    <xpath expr="//div[@id='footer']" position="replace">
        <div id="footer" class="oe_structure oe_structure_solo border text-break" t-ignore="true" t-if="not no_footer" style="--box-border-left-width: 0px; --box-border-right-width: 0px;">
            <section class="s_text_block pt40 pb16" data-snippet="s_text_block" data-name="Container">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-2 pt24 pb24">
                            <h5>Links</h5>
                            <ul class="list-unstyled">
                                <li><a href="/">Home</a></li>
                                <li><a href="/shop">Shop</a></li>
                                <li><a href="/contactus">Kontakt</a></li>
                                <li><a href="/gewaehrleistung">Gewährleistung</a></li>
                                <li><a href="/impressum">Impressum</a></li>
                            </ul>
                        </div>
                        <div class="col-lg-5 pt24 pb24">
                            <h5>Über Dratti-Dog</h5>
                            <p>Geschirre, Leinen und Halsbänder von Dratti-Dog.
                            <br/><br/>Sofortkaufgeschirre werden im Dratti-Dog Standard angeboten. Individuelle Geschirre gibt es natürlich auch – dazu einfach per WhatsApp, Facebook, Instagram oder E-Mail Kontakt aufnehmen.</p>
                        </div>
                        <div class="col-lg-4 offset-lg-1 pt24 pb24">
                            <h5>Kontakt</h5>
                            <ul class="list-unstyled">
                                <li><i class="fa fa-user fa-fw me-2"/>Cornelia Weiland</li>
                                <li><i class="fa fa-map-marker fa-fw me-2"/>Eichenbornweg 27, 66798 Wallerfangen</li>
                                <li><i class="fa fa-phone fa-fw me-2"/><a href="tel:+4917663378306"><span class="o_force_ltr">+49 176 63378306</span></a></li>
                                <li><i class="fa fa-envelope fa-fw me-2"/><a href="mailto:drattidog@gmail.com">drattidog@gmail.com</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </xpath>
</data>'''
print("footer", website_copy("website.footer_custom", footer))

# 3) Copyright
cp='''<data inherit_id="website.layout" priority="15">
    <xpath expr="//footer//span[hasclass('o_footer_copyright_name')]" position="replace">
        <span class="o_footer_copyright_name me-2 small">Copyright © Dratti-Dog - Haustierbedarf</span>
    </xpath>
    <xpath expr="//div[hasclass('o_footer_copyright')]//div[hasclass('col-sm')]" position="attributes">
        <attribute name="class" remove="col-sm text-sm-start" add="col-md d-flex flex-column-reverse gap-2 text-md-start" separator=" "/>
    </xpath>
</data>'''
print("copyright", website_copy("website.footer_copyright_company_name", cp))
print("ok")
