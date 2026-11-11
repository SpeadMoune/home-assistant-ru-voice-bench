import sys, requests, time, json
sys.path.insert(0,"test")
from bench import CASES
key=[l.split("=",1)[1].strip() for l in open("keys.env") if l.startswith("pro=")][0]
log=open("tts1_log.jsonl","a")
for v in ["onyx","nova"]:
    for cid,text,*_ in CASES:
        t=time.time()
        r=requests.post("https://openai.bothub.chat/v1/audio/speech",headers={"Authorization":"Bearer "+key},json={"model":"tts-1","voice":v,"input":text,"response_format":"wav"},timeout=180)
        dt=time.time()-t
        if r.status_code==200: open(f"audio/{cid}_tts1-{v}.wav","wb").write(r.content)
        log.write(json.dumps({"voice":v,"case":cid,"status":r.status_code,"dt":round(dt,2),"bytes":len(r.content)})+"\n"); log.flush()
        if r.status_code!=200: print(cid,v,r.status_code,r.text[:200])
print("ok")
