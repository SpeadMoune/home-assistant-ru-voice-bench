import sys, json, time, glob, os, wave, numpy as np
sys.path.insert(0,".")
from bench import CASES
REF={c[0]:c[1] for c in CASES}
eng=sys.argv[1]; OUT="stt_new.jsonl"
done=set()
if os.path.exists(OUT):
    for l in open(OUT):
        r=json.loads(l); done.add((r["engine"],r["case"],r["voice"]))
files=sorted(glob.glob("a16/C*.wav"))
def load(fn):
    with wave.open(fn) as w: return np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
def dur(fn):
    with wave.open(fn) as w: return w.getnframes()/w.getframerate()
if eng.startswith("fw-"):
    from faster_whisper import WhisperModel
    m=WhisperModel(eng[3:],device="cpu",compute_type="int8",cpu_threads=2)
    def tr(fn):
        segs,_=m.transcribe(load(fn),language="ru",beam_size=5,vad_filter=False)
        return " ".join(s.text for s in segs).strip()
elif eng.startswith("oa-"):
    import onnx_asr
    LOCAL={'nemo-parakeet-tdt-0.6b-v3':'./models/parakeet-v3'}
    m=onnx_asr.load_model(eng[3:], LOCAL.get(eng[3:]))
    def tr(fn):
        r=m.recognize(fn)
        return r if isinstance(r,str) else str(r)
elif eng=="whisper-1":
    import requests
    key=[l.split("=",1)[1].strip() for l in open("keys.env") if l.startswith("pro=")][0]
    def tr(fn):
        r=requests.post("https://openai.bothub.chat/v1/audio/transcriptions",headers={"Authorization":"Bearer "+key},files={"file":open(fn,"rb")},data={"model":"whisper-1","language":"ru"},timeout=180)
        try: return r.json().get("text","ERR "+r.text[:200])
        except: return "ERR "+r.text[:200]
todo=[f for f in files if (eng,)+tuple(os.path.basename(f)[:-4].split("_",1)) not in done]
if not todo: print(eng,"nothing"); sys.exit()
if eng!="whisper-1": tr(files[0])
out=open(OUT,"a")
for fn in todo:
    cid,voice=os.path.basename(fn)[:-4].split("_",1)
    t=time.time(); 
    try: txt=tr(fn)
    except Exception as e: txt="ERR "+str(e)[:200]
    dt=time.time()-t
    out.write(json.dumps({"engine":eng,"case":cid,"voice":voice,"ref":REF[cid],"hyp":txt,"dt":round(dt,3),"audio_s":round(dur(fn),2)},ensure_ascii=False)+"\n"); out.flush()
print(eng,"done",len(todo))
