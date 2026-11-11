# usage: HA_PORT=8126 python3 e2e.py <agent> <label> <prefer_local 0/1> <audio_glob> <out>
import asyncio, json, sys, time, glob, wave, os, requests
from hal import *
import bench
agent,label,pl,pat,out=sys.argv[1],sys.argv[2],sys.argv[3]=="1",sys.argv[4],sys.argv[5]
CASE={c[0]:c for c in bench.CASES}
async def m():
    async with WS() as w:
        pls=await w.call("assist_pipeline/pipeline/list"); pid=None
        name=f"e2e-{label}"
        for p in pls["pipelines"]:
            if p["name"]==name: pid=p["id"]
        if not pid:
            p=await w.call("assist_pipeline/pipeline/create",name=name,language="ru",conversation_engine=agent,conversation_language="ru",prefer_local_intents=pl,stt_engine="stt.faster_whisper",stt_language="ru",tts_engine="tts.piper",tts_language="ru_RU",tts_voice="ru_RU-irina-medium",wake_word_entity=None,wake_word_id=None)
            pid=p["id"]
        f=open(out,"a")
        for fn in sorted(glob.glob(pat)):
            cid=os.path.basename(fn).split("_")[0]
            _,text,allowed,chk=CASE[cid]
            bench.reset(); time.sleep(0.5); b=bench.snap()
            with wave.open(fn) as wv: pcm=wv.readframes(wv.getnframes()); sr=wv.getframerate()
            w.i+=1; rid=w.i
            await w.ws.send(json.dumps({"id":rid,"type":"assist_pipeline/run","start_stage":"stt","end_stage":"tts","input":{"sample_rate":sr},"pipeline":pid}))
            T={}; handler=None; ev_data={}
            while True:
                r=json.loads(await w.ws.recv())
                if r.get("type")=="event":
                    ev=r["event"]; T[ev["type"]]=time.time(); ev_data[ev["type"]]=ev.get("data")
                    if ev["type"]=="run-start":
                        handler=ev["data"]["runner_data"]["stt_binary_handler_id"]
                        # stream audio in real-time-ish chunks of 100 ms (fast send)
                        step=sr*2//10
                        for i in range(0,len(pcm),step):
                            await w.ws.send(bytes([handler])+pcm[i:i+step]); await asyncio.sleep(0.1)
                        await w.ws.send(bytes([handler])); T["audio_end"]=time.time()
                    if ev["type"] in ("run-end","error"): break
            url=None
            try: url=ev_data["tts-end"]["tts_output"]["url"]
            except: pass
            t0=time.time(); tts_bytes=0
            if url:
                rr=requests.get(B+url if url.startswith("/") else url, headers={"Authorization":"Bearer "+access()},timeout=120); tts_bytes=len(rr.content)
            T["tts_fetched"]=time.time()
            time.sleep(1); bench.stable(); a=bench.snap()
            col=bench.diff(b,a,allowed); speech=""
            try: speech=ev_data["intent-end"]["intent_output"]["response"]["speech"]["plain"]["speech"]
            except: pass
            ok=None
            if chk:
                try: ok=bool(chk(b,a,speech)) and not col
                except: ok=False
            stt_text=(ev_data.get("stt-end") or {}).get("stt_output",{}).get("text")
            local=(ev_data.get("intent-end") or {}).get("processed_locally")
            ae=T.get("audio_end")
            rec={"label":label,"case":cid,"file":os.path.basename(fn),"ok":ok,"stt_text":stt_text,"speech":speech,"local":local,
                 "stt_s":round(T.get("stt-end",ae)-ae,2) if ae else None,
                 "intent_s":round(T.get("intent-end",0)-T.get("intent-start",0),2),
                 "tts_s":round(T["tts_fetched"]-T.get("tts-start",T["tts_fetched"]),2),
                 "total_s":round(T["tts_fetched"]-ae,2) if ae else None,"error":ev_data.get("error"),"collateral":col}
            f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
            print(label,cid,ok,rec["stt_text"],"|",rec["stt_s"],rec["intent_s"],rec["tts_s"],rec["total_s"],local,speech[:50])
asyncio.run(m())
