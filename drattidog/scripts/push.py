import json, sys, re, base64, os, urllib.request, unicodedata, time
H="https://montreal-reading-outer-arena.trycloudflare.com"
RAW, IMGDIR = sys.argv[1], sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
MOD="drattidog_import"
def call(model, method, **kw):
    req=urllib.request.Request(f"{H}/json/2/{model}/{method}", data=json.dumps(kw).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer proxy-injected"})
    for a in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=180))
        except urllib.error.HTTPError as e:
            body=e.read().decode()[:1500]
            if e.code in (502,503,504,429): time.sleep(3*(a+1)); continue
            raise SystemExit(f"{model}.{method} HTTP {e.code}: {body}")
        except Exception as e: time.sleep(3*(a+1)); err=e
    raise SystemExit(f"{model}.{method} failed: {err}")
xcache={}
def xid_get(name):
    if name in xcache: return xcache[name]
    r=call("ir.model.data","search_read",domain=[["module","=",MOD],["name","=",name]],fields=["res_id"])
    xcache[name]=r[0]["res_id"] if r else None; return xcache[name]
def upsert(model, name, vals):
    rid=xid_get(name)
    if rid and call(model,"search_count",domain=[["id","=",rid]]) :
        call(model,"write",ids=[rid],vals=vals); return rid, False
    if rid: call("ir.model.data","unlink",ids=call("ir.model.data","search",domain=[["module","=",MOD],["name","=",name]]))
    rid=call(model,"create",vals_list=[vals])[0]
    call("ir.model.data","create",vals_list=[{"module":MOD,"name":name,"model":model,"res_id":rid,"noupdate":True}])
    xcache[name]=rid; return rid, True
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode(); return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")
def b64file(p): return base64.b64encode(open(p,"rb").read()).decode()
def b64url(u): return base64.b64encode(urllib.request.urlopen(u,timeout=60).read()).decode()

d=json.load(open(RAW)); cats={int(k):v for k,v in d["categories"].items()}
parent={s["id"]:cid for cid,c in cats.items() for s in c["subcategories"]}
subimg={s["id"]:(s.get("mediaItem") or {}).get("image800pxUrl") for c in cats.values() for s in c["subcategories"]}
taxes={t["amount"]:t["id"] for t in call("account.tax","search_read",domain=[["type_tax_use","=","sale"],["name","in",["19%","0%"]]],fields=["amount"])}

# Categories
root,_=upsert("product.category","categ_root",{"name":"Dratti-Dog"})
pub,ic={}, {}
for seq,cid in enumerate([c for c in cats if c!=0]):
    c=cats[cid]; par=parent.get(cid,0)
    v={"name":c["name"],"sequence":(seq+1)*10,"parent_id":pub.get(par,False)}
    if subimg.get(cid) and not xid_get(f"pubcateg_{cid}"):
        try: v["image_1920"]=b64url(subimg[cid])
        except Exception as e: print("cat image fail",cid,e)
    pub[cid],_=upsert("product.public.category",f"pubcateg_{cid}",v)
    ic[cid],_=upsert("product.category",f"categ_{cid}",{"name":c["name"],"parent_id":ic.get(par,root)})
print("categories ok",len(pub))

# Attributes
def norm(opt,ch):
    if "steg" in opt.lower(): return "Steg",("Geteilter Steg" if "geteilt" in ch.lower() else "Normaler Steg")
    return opt.strip(), ch.strip()
popts={}
for pid,v in d["products"].items():
    for oc in v["product"]["defaultOptionsOverrides"]["pricesOverrides"]["optionsChoicesWithModifiersAndTaxes"]:
        for ch in oc["choices"]:
            a,val=norm(oc["optionId"],ch["choiceName"])
            m=re.search(r"([+-]?\d+(?:\.\d+)?)",(ch.get("modifierFormatted") or "").replace(",","."))
            popts.setdefault(pid,{}).setdefault(a,{})[val]=float(m.group(1)) if m else 0.0
        if a=="Steg": popts[pid][a].setdefault("Normaler Steg",0.0)
attr_vals={}
for a in sorted({a for o in popts.values() for a in o}):
    vals=[]; [vals.append(x) for o in popts.values() for x in o.get(a,{}) if x not in vals]
    aid,_=upsert("product.attribute",f"attr_{slug(a)}",{"name":a,"create_variant":"always","display_type":"radio"})
    for i,x in enumerate(vals):
        attr_vals[(a,x)],_=upsert("product.attribute.value",f"attrval_{slug(a)}__{slug(x)}",{"name":x,"attribute_id":aid,"sequence":i})
    attr_vals[a]=aid
print("attributes ok")

# Products
wh_loc=call("stock.warehouse","search_read",domain=[],fields=["lot_stock_id"],limit=1)[0]["lot_stock_id"][0]
items=list(d["products"].items())[:LIMIT] if LIMIT else list(d["products"].items())
n_new=0
for k,(pid,v) in enumerate(items):
    p=v["product"]; o=p["defaultOptionsOverrides"]; po=o["pricesOverrides"]; vo=o["variationOverrides"]
    catids=[c for c in v["categories"] if c!=0]
    default=next((cp["categoryPath"][-1]["id"] for cp in p.get("categoryPaths",[]) if cp.get("isDefault") and len(cp["categoryPath"])>1),None)
    if default not in catids: default=catids[0] if catids else None
    tax=po["appliedTaxes"][0]["percent"] if po["appliedTaxes"] else 19.0
    strike=(po.get("strikethroughPrice") or {}).get("price") or 0.0
    pics=sorted([m for m in vo["mediaItems"] if m["type"]=="PICTURE"],key=lambda m: not m.get("isMain"))
    sku=vo.get("sku") or ""
    files=[os.path.join(IMGDIR,f"{slug(sku) or pid}_{pid}_{i+1}.jpg") for i in range(len(pics))]
    name=f"product_{pid}"; exists=bool(xid_get(name))
    vals={"name":p["name"].strip(),"default_code":sku,"list_price":po["basePrice"],"compare_list_price":strike,
          "categ_id":ic.get(default,root),"public_categ_ids":[[6,0,[pub[c] for c in catids]]],
          "type":"consu","is_storable":True,"sale_ok":True,"is_published":True,
          "description_ecommerce":(p.get("description") or "").replace("&nbsp;"," "),
          "taxes_id":[[6,0,[taxes[tax]]]] if tax in taxes else [[6,0,[taxes[19.0]]]]}
    if not exists and files: vals["image_1920"]=b64file(files[0])
    tid,new=upsert("product.template",name,vals); n_new+=new
    if new:
        for i,f in enumerate(files[1:],2):
            upsert("product.image",f"img_{pid}_{i}",{"name":f"{p['name'].strip()} ({i})","product_tmpl_id":tid,"image_1920":b64file(f)})
    # attributes
    if pid in popts:
        lines=call("product.template.attribute.line","search_read",domain=[["product_tmpl_id","=",tid]],fields=["attribute_id"])
        have={l["attribute_id"][0] for l in lines}
        cmds=[[0,0,{"attribute_id":attr_vals[a],"value_ids":[[6,0,[attr_vals[(a,x)] for x in vals_]]]}] for a,vals_ in popts[pid].items() if attr_vals[a] not in have]
        if cmds: call("product.template","write",ids=[tid],vals={"attribute_line_ids":cmds})
        for ptav in call("product.template.attribute.value","search_read",domain=[["product_tmpl_id","=",tid]],fields=["attribute_id","product_attribute_value_id","price_extra"]):
            a=next(a for a in popts[pid] if attr_vals[a]==ptav["attribute_id"][0])
            val=next(x for x in popts[pid][a] if attr_vals[(a,x)]==ptav["product_attribute_value_id"][0])
            if abs(ptav["price_extra"]-popts[pid][a][val])>0.001: call("product.template.attribute.value","write",ids=[ptav["id"]],vals={"price_extra":popts[pid][a][val]})
    # stock (only for products without variants, only on first creation)
    qty=vo.get("quantity") or 0
    if new and qty>0 and pid not in popts:
        prod=call("product.product","search",domain=[["product_tmpl_id","=",tid]])[0]
        q=call("stock.quant","create",vals_list=[{"product_id":prod,"location_id":wh_loc,"inventory_quantity":qty}])
        call("stock.quant","action_apply_inventory",ids=q)
    print(k+1,len(items),"NEW" if new else "upd",tid,p["name"].strip(),flush=True)
print("done, new:",n_new)
