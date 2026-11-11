import json, re, sys
from collections import defaultdict
from num2words import num2words
import jiwer
def norm(s):
    s=s.lower().replace("ё","е")
    s=s.replace("%"," процентов ")
    s=re.sub(r"(\d+)[.,]5\b",lambda m:num2words(int(m.group(1)),lang="ru")+" с половиной",s)
    s=re.sub(r"\d+",lambda m:num2words(int(m.group(0)),lang="ru"),s)
    s=s.replace("rgb","ар джи би").replace("эр джи би","ар джи би").replace("ржб","ар джи би")
    s=re.sub(r"[^\w\s]"," ",s); s=s.replace("_"," ")
    return " ".join(s.split())
R=[json.loads(l) for l in open(sys.argv[1] if len(sys.argv)>1 else "stt_new.jsonl")]
agg=defaultdict(lambda:{"n":0,"exact":0,"ref":[],"hyp":[],"dt":[],"aud":0})
for r in R:
    g="live" if "simeon" in r["voice"] else ("noisy" if "noisy" in r["voice"] else "clean")
    a=agg[(r["engine"],g)]; a["n"]+=1; h=norm(r["hyp"]); ref=norm(r["ref"])
    a["exact"]+=h==ref; a["ref"].append(ref); a["hyp"].append(h if h else "_"); a["dt"].append(r["dt"]); a["aud"]+=r["audio_s"]
import statistics
rows={}
for (e,g),a in sorted(agg.items()):
    rows.setdefault(e,{})[g]=(round(100*jiwer.wer(a["ref"],a["hyp"]),1),a["exact"],a["n"],round(statistics.median(a["dt"]),2))
for e,d in rows.items(): print(e.ljust(36),"  ".join(f"{g}: WER {v[0]}% exact {v[1]}/{v[2]} med {v[3]}s" for g,v in d.items()))
json.dump(rows,open("stt_summary2.json","w"),ensure_ascii=False,indent=1)
