import json, sys, urllib.request, time
API="https://eu-fra3-storefront-api.ecwid.com/storefront/api/v1/84498537/catalog"
OUT=sys.argv[1]
def post(parent, offset):
    body={"categoryViewMode":"COLLAPSED","parentCategoryId":parent,"pagination":{"offset":offset,"limit":100},
          "urlParams":{"urlType":"CLEAN_URL","baseUrl":"/shop","canonicalBaseUrl":"","isCleanUrls":True,"isCanonicalUrlsEnabled":False,"isSlugsWithoutIds":False,"isTrailingSlash":False}}
    req=urllib.request.Request(API,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    for a in range(4):
        try: return json.load(urllib.request.urlopen(req,timeout=60))
        except Exception as e: print("retry",parent,offset,e); time.sleep(2*(a+1))
    raise SystemExit("failed")
cats={}; prods={}
def walk(cid, path):
    off=0
    while True:
        d=post(cid,off); e=d["expandedCategories"][0]
        if off==0:
            info=e["categoryInfo"]
            cats[cid]={"id":cid,"name":info.get("name","").strip(),"path":path,"description":info.get("description",""),
                       "image":(info.get("seo",{}).get("ogMetaTags",{}) or {}).get("image"),"raw":info,"subcategories":e["subcategories"]}
        for p in e["products"]:
            pid=p["identifier"]["productId"]
            prods.setdefault(pid,{"product":p,"categories":[]})
            if cid not in prods[pid]["categories"]: prods[pid]["categories"].append(cid)
        print(cid, off, len(e["products"]), e.get("totalProductsCount"), e.get("hasMoreProducts"))
        if off+len(e["products"])>=(e.get("totalProductsCount") or 0) or not e["products"]: break
        off+=100
    for s in e["subcategories"]:
        walk(s["id"], path+[s["name"].strip()])
walk(0,[])
json.dump({"categories":cats,"products":prods},open(OUT,"w"),ensure_ascii=False)
print(len(cats),"categories",len(prods),"products")
