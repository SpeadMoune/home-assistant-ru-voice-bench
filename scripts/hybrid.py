import asyncio, sys, json, time
from hal import *
import bench
agent=sys.argv[1]; label=sys.argv[2]; out=sys.argv[3]
async def m():
    async with WS() as w:
        pl=await w.call("assist_pipeline/pipeline/list")
        pid=None
        for p in pl["pipelines"]:
            if p["name"]=="hybrid-"+label: pid=p["id"]
        if not pid:
            p=await w.call("assist_pipeline/pipeline/create",name="hybrid-"+label,language="ru",conversation_engine=agent,conversation_language="ru",prefer_local_intents=True,stt_engine=None,stt_language=None,tts_engine=None,tts_language=None,tts_voice=None,wake_word_entity=None,wake_word_id=None)
            pid=p["id"]
        f=open(out,"a")
        for cid,text,allowed,chk in bench.CASES:
            bench.reset(); time.sleep(0.5); b=bench.snap()
            w.i+=1; t0=time.time()
            await w.ws.send(json.dumps({"id":w.i,"type":"assist_pipeline/run","start_stage":"intent","end_stage":"intent","input":{"text":text},"pipeline":pid}))
            res=None; local=None; speech=""
            while True:
                r=json.loads(await w.ws.recv())
                if r.get("type")=="event":
                    ev=r["event"]
                    if ev["type"]=="intent-end":
                        d=ev["data"]; local=d.get("processed_locally"); 
                        try: speech=d["intent_output"]["response"]["speech"]["plain"]["speech"]
                        except: speech=json.dumps(d)[:200]
                    if ev["type"] in("run-end","error"):
                        if ev["type"]=="error": speech="ERROR "+json.dumps(ev["data"])[:200]
                        break
            dt=time.time()-t0
            time.sleep(1); bench.stable(); a=bench.snap()
            col=bench.diff(b,a,allowed); ok=None
            if chk:
                try: ok=bool(chk(b,a,speech)) and not col
                except: ok=False
            rec={"agent":label,"case":cid,"text":text,"ok":ok,"local":local,"dt":round(dt,2),"speech":speech,"collateral":col,"changed":{e:(b[e],a[e]) for e in b if b[e]!=a[e]}}
            f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush(); print(label,cid,ok,local,round(dt,2),speech[:80])
asyncio.run(m())
