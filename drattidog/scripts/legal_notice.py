"""Fügt den EU-Hinweis 'Gesetzliche Gewährleistung' (DVO (EU) 2025/1960) in Odoo 19 ein:
Produktseite, Warenkorb/Checkout (Link -> Modal mit vollständigem Hinweis), eigene Seite
/gewaehrleistung und Bestellbestätigungs-Mail. Idempotent über externe IDs."""
import json, sys, base64, urllib.request, time
H="https://montreal-reading-outer-arena.trycloudflare.com"
PNG=sys.argv[1]
MOD="drattidog_import"; CTX={"lang":"de_DE"}
EU_URL="https://europa.eu/youreurope/garantien"
def call(model, method, **kw):
    kw.setdefault("context", CTX)
    req=urllib.request.Request(f"{H}/json/2/{model}/{method}", data=json.dumps(kw).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer proxy-injected"})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: raise SystemExit(f"{model}.{method} HTTP {e.code}: {e.read().decode()[:2000]}")
def xid(name):
    r=call("ir.model.data","search_read",domain=[["module","=",MOD],["name","=",name]],fields=["res_id"]); return r[0]["res_id"] if r else None
def upsert(model,name,vals):
    rid=xid(name)
    if rid and call(model,"search_count",domain=[["id","=",rid]]): call(model,"write",ids=[rid],vals=vals); return rid
    if rid: call("ir.model.data","unlink",ids=call("ir.model.data","search",domain=[["module","=",MOD],["name","=",name]]))
    rid=call(model,"create",vals_list=[vals])[0]
    call("ir.model.data","create",vals_list=[{"module":MOD,"name":name,"model":model,"res_id":rid,"noupdate":True}]); return rid
def vid(key): return call("ir.ui.view","search",domain=[["key","=",key],["website_id","=",False]])[0]

att=upsert("ir.attachment","eu_legal_guarantee_notice_de",{"name":"eu-gewaehrleistung-hinweis-de.png","type":"binary",
    "datas":base64.b64encode(open(PNG,"rb").read()).decode(),"mimetype":"image/png","public":True,"res_model":"ir.ui.view","res_id":0})
IMG=f"/web/image/{att}/eu-gewaehrleistung-hinweis-de.png"
ALT=("EU-Hinweis Gesetzliche Gewährleistung: Mindestens zwei Jahre gesetzliche Gewährleistung der Vertragsmäßigkeit "
     "für Waren, die in der Europäischen Union verkauft werden. Weitere Informationen: europa.eu/youreurope/garantien")

notice_block=f'''<div class="o_dd_legal_guarantee_notice text-center">
  <img src="{IMG}" alt="{ALT}" class="img-fluid" style="max-width:800px;width:100%" loading="lazy"/>
  <p class="mt-3 mb-0"><a href="{EU_URL}" target="_blank" rel="noopener">Weitere Informationen zu Ihren Rechten: europa.eu/youreurope/garantien</a></p>
</div>'''

# 1) Bausteine: Link (an der Stelle) + Modal (am Seitenende in #wrap, außerhalb sticky-Spalten)
link=f'''<t t-name="{MOD}.legal_guarantee_link">
  <div class="o_dd_legal_guarantee my-3">
    <a href="#" role="button" data-bs-toggle="modal" data-bs-target="#o_dd_legal_guarantee_modal" class="d-inline-flex align-items-center gap-2 text-decoration-underline">
      <img src="{IMG}" alt="" aria-hidden="true" style="height:40px;width:auto;border:1px solid #ddd"/>
      <span>Ihre gesetzlichen Gewährleistungsrechte</span>
    </a>
  </div>
</t>'''
modal=f'''<t t-name="{MOD}.legal_guarantee_modal">
    <div class="modal fade" id="o_dd_legal_guarantee_modal" tabindex="-1" aria-labelledby="o_dd_legal_guarantee_title" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="o_dd_legal_guarantee_title">Gesetzliche Gewährleistung</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Schließen"/>
          </div>
          <div class="modal-body">{notice_block}</div>
        </div>
      </div>
    </div>
</t>'''
upsert("ir.ui.view","view_legal_guarantee_link",{"name":"Dratti-Dog: EU Gewährleistungshinweis (Link)","type":"qweb","key":f"{MOD}.legal_guarantee_link","arch_db":link})
upsert("ir.ui.view","view_legal_guarantee_modal",{"name":"Dratti-Dog: EU Gewährleistungshinweis (Modal)","type":"qweb","key":f"{MOD}.legal_guarantee_modal","arch_db":modal})
MODAL_X=f'<xpath expr="//div[@id=\'wrap\']" position="inside"><t t-call="{MOD}.legal_guarantee_modal"/></xpath>'

# 2) Produktseite: vollständiger Hinweis in voller Größe direkt auf der Seite (nicht verschachtelt),
#    unter dem Produktbereich; Link beim Warenkorb-Button springt dorthin.
full=f'''<t t-name="{MOD}.legal_guarantee_full">
  <section id="o_dd_legal_guarantee_full" class="container mt-5 mb-4" style="scroll-margin-top:100px" aria-labelledby="o_dd_legal_guarantee_full_title">
    <h2 id="o_dd_legal_guarantee_full_title" class="h4 mb-3">Gesetzliche Gewährleistung</h2>
    <div style="max-width:800px">{notice_block}</div>
  </section>
</t>'''
upsert("ir.ui.view","view_legal_guarantee_full",{"name":"Dratti-Dog: EU Gewährleistungshinweis (vollständig)","type":"qweb","key":f"{MOD}.legal_guarantee_full","arch_db":full})
anchor_link='''<div class="o_dd_legal_guarantee my-3"><a href="#o_dd_legal_guarantee_full" class="text-decoration-underline">Ihre gesetzlichen Gewährleistungsrechte</a></div>'''
upsert("ir.ui.view","view_legal_guarantee_product",{"name":"Dratti-Dog: Gewährleistungshinweis Produktseite","type":"qweb",
  "inherit_id":vid("website_sale.product"),"key":f"{MOD}.legal_guarantee_product","active":True,
  "arch_db":f'<data><xpath expr="//t[@t-call=\'website_sale.cta_wrapper\']" position="after">{anchor_link}</xpath>'
            f'<xpath expr="//div[@id=\'product_detail_main\']" position="after"><t t-call="{MOD}.legal_guarantee_full"/></xpath></data>'})

# 3) Warenkorb + alle Checkout-Schritte (linke Spalte)
upsert("ir.ui.view","view_legal_guarantee_checkout",{"name":"Dratti-Dog: Gewährleistungshinweis Checkout","type":"qweb",
  "inherit_id":vid("website_sale.checkout_layout"),"key":f"{MOD}.legal_guarantee_checkout","active":True,
  "arch_db":f'<data><xpath expr="//t[@t-out=\'0\']" position="after"><t t-call="{MOD}.legal_guarantee_link"/></xpath>{MODAL_X}</data>'})

# 3b) Shop zeigt Bruttopreise (Pflicht gegenüber Verbrauchern)
call("website","write",ids=[1],vals={"show_line_subtotals_tax_selection":"tax_included"})

# 4) eigene Seite /gewaehrleistung mit vollständigem Hinweis
page_arch=f'''<t t-name="{MOD}.page_gewaehrleistung"><t t-call="website.layout"><div id="wrap" class="oe_structure">
<section class="container py-5"><h1 class="mb-4">Gesetzliche Gewährleistung</h1>{notice_block}</section></div></t></t>'''
pv=upsert("ir.ui.view","view_page_gewaehrleistung",{"name":"Gesetzliche Gewährleistung","type":"qweb","key":f"{MOD}.page_gewaehrleistung","arch_db":page_arch})
upsert("website.page","page_gewaehrleistung",{"view_id":pv,"url":"/gewaehrleistung","website_id":1,"is_published":True,"website_indexed":True})

# 5) Bestellbestätigung (E-Mail)
MARK="<!--dd-legal-guarantee-->"
tid=call("ir.model.data","search_read",domain=[["module","=","sale"],["name","=","mail_template_sale_confirmation"]],fields=["res_id"])[0]["res_id"]
body=call("mail.template","read",ids=[tid],fields=["body_html"])[0]["body_html"]
if MARK not in body:
    block=f'''{MARK}<div style="margin:24px 0 0 0;padding-top:16px;border-top:1px solid #ddd;text-align:center;">
<img t-attf-src="{{{{ object.get_base_url() }}}}{IMG}" alt="{ALT}" style="width:100%;max-width:600px;height:auto;"/>
<p style="font-size:12px;margin:8px 0 0 0;"><a href="{EU_URL}" style="color:#0E4BA0;">Weitere Informationen zu Ihren Rechten: europa.eu/youreurope/garantien</a></p></div>{MARK}'''
    i=body.rstrip().rfind("</div>")
    call("mail.template","write",ids=[tid],vals={"body_html":body[:i]+block+body[i:]})
print("ok attachment",att,"page /gewaehrleistung, mail template",tid)
