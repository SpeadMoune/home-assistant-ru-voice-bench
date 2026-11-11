import json, glob, statistics, collections
R=[json.loads(l) for f in glob.glob("results_lane*.jsonl") for l in open(f)]
R+= [json.loads(l) for l in open("results_new.jsonl")]
by=collections.defaultdict(list)
for r in R: by[r["agent"].split("#")[0]].append(r)
rows=[]
for a,rs in by.items():
    sc=[r for r in rs if r["case"] not in ("C08","C20")]
    ok=sum(1 for r in sc if r["ok"]); n=len(sc)
    apierr=sum(1 for r in sc if any(c["status"]!=200 for c in r.get("calls",[])))
    med=statistics.median([r["dt"] for r in sc]) if sc else 0
    inp=[sum((c["usage"] or {}).get("prompt_tokens",0) for c in r.get("calls",[])) for r in sc]
    cost=[sum((c["usage"] or {}).get("cost",0) or 0 for c in r.get("calls",[])) for r in sc]
    cached=[sum(((c["usage"] or {}).get("prompt_tokens_details") or {}).get("cached_tokens",0) or 0 for c in r.get("calls",[])) for r in sc]
    rows.append((a,ok,n,apierr,round(med,1),int(statistics.mean(inp)) if inp else 0, round(statistics.mean(cost),6) if cost else 0, round(100*sum(cached)/max(1,sum(inp)))))
for r in sorted(rows,key=lambda x:-x[1]/max(1,x[2])): print(r)
