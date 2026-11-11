import sys, asyncio, json, time, os
from hal import *
P=os.environ["PROXY_PORT"]
KEYS={l.split("=",1)[0]:l.split("=",1)[1].strip() for l in open("keys.env") if "=" in l}
MAIN="deepseek-v4.1-flash claude-haiku-5.5 gpt-oss-120b gpt-6-luna qwen3.8-flash gpt-5.4-nano gpt-5.4-mini qwen3.6-35b-a3b gemma-4-26b-a4b-it gpt-oss-20b qwen3.5-9b".split()
GEM="gemini-3.5-flash-lite gemini-3.8-flash".split()
YA="yandexgpt yandexgpt-lite".split()
ECO="deepseek-v4.1-flash qwen3.8-flash gpt-5.4-nano gemma-4-26b-a4b-it gpt-oss-20b".split()
PLAN=[("pro",f"http://127.0.0.1:{P}/v1",MAIN,""),("pro",f"http://localhost:{P}/v1",GEM,""),("pro",f"http://127.0.0.1:{P}/v1/",YA,""),("eco",f"http://127.0.0.1:{P}/v1",ECO,"ECO ")]
c,r=rest("GET","/api/config/config_entries/entry?domain=llama_cpp")
for e in r: rest("DELETE","/api/config/config_entries/entry/"+e["entry_id"])
agents={}
for kn,url,models,pref in PLAN:
    c,r=rest("POST","/api/config/config_entries/flow",json={"handler":"llama_cpp"})
    fid=r["flow_id"]; c,r=rest("POST",f"/api/config/config_entries/flow/{fid}",json={"base_url":url,"api_key":KEYS[kn]})
    if r.get("step_id")!="model": print("FAIL user",url,r); continue
    c,r=rest("POST",f"/api/config/config_entries/flow/{fid}",json={"chat_model":models[0]})
    if r.get("type")!="create_entry": print("FAIL model",models[0],r); continue
    eid=r["result"]["entry_id"]
    for m in models[1:]:
        for attempt in range(3):
            c,r=rest("POST","/api/config/config_entries/subentries/flow",json={"handler":[eid,"conversation"]})
            c,r2=rest("POST","/api/config/config_entries/subentries/flow/"+r["flow_id"],json={"chat_model":m,"recommended":True,"llm_hass_api":["assist"]})
            if r2.get("type")=="create_entry": break
            print("retry",m,str(r2)[:200]); time.sleep(3)
    time.sleep(2)
    async def reg():
        async with WS() as w: return await w.call("config/entity_registry/list")
    ents=asyncio.run(reg())
    c,er=rest("GET","/api/config/config_entries/entry?domain=llama_cpp")
    ent=[x for x in er if x["entry_id"]==eid][0]
    stream=None
    for e in ents:
        if e.get("config_entry_id")==eid and e["entity_id"].startswith("conversation."):
            agents[e["entity_id"]]=(kn, e.get("config_subentry_id"))
    print(kn,url,"entry",eid,"subentries",ent.get("num_subentries"))
# map subentry -> model
c,er=rest("GET","/api/config/config_entries/entry?domain=llama_cpp")
out={}
async def subs():
    async with WS() as w:
        res={}
        for x in er:
            for s in await w.call("config_entries/subentries/list",entry_id=x["entry_id"]):
                res[s["subentry_id"]]=s
        return res
S=asyncio.run(subs())
for a,(kn,sid) in agents.items():
    t=S.get(sid,{}).get("title")
    out[a]=(("ECO " if kn=="eco" else "")+str(t))
json.dump(out,open(f"agents_{os.environ['HA_PORT']}.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False))
