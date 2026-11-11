import time, wave, json, sys, os
import numpy as np, soundfile as sf
PH=["Свет на кухне включён.",
"Готово, люстра в гостиной на 40%.",
"Кондиционер в спальне установлен на 22,5 градуса.",
"Сейчас на улице 15,6 °C, влажность 54%.",
"Замок входной двери заперт.",
"RGB-лента в детской теперь красная.",
"Добавил в список покупок молоко и ёлочные игрушки.",
"Громкость колонки на кухне 30 процентов.",
"Пылесос запущен, уборка займёт около 25 минут.",
"Шторы в гостиной опущены наполовину."]
os.makedirs("tts_out",exist_ok=True)
res=[]
from piper import PiperVoice
for v in ["irina","dmitri"]:
    pv=PiperVoice.load(f"voices/ru_RU-{v}-medium.onnx")
    with wave.open("/tmp/w.wav","wb") as w: pv.synthesize_wav("Проверка.",w)
    for i,t in enumerate(PH):
        t0=time.time()
        with wave.open(f"tts_out/piper-{v}_{i:02d}.wav","wb") as w: pv.synthesize_wav(t,w)
        dt=time.time()-t0
        with wave.open(f"tts_out/piper-{v}_{i:02d}.wav") as w: dur=w.getnframes()/w.getframerate()
        res.append({"engine":"piper-"+v,"i":i,"dt":dt,"dur":dur})
json.dump(res,open("tts_bench.json","w"))
from collections import defaultdict
agg=defaultdict(lambda:[0,0,[]])
for r in res: a=agg[r["engine"]]; a[0]+=r["dt"]; a[1]+=r["dur"]; a[2].append(r["dt"])
for k,(dt,du,l) in agg.items(): print(k,"RTF",round(dt/du,3),"speech_s",round(du,1),"median_phrase_s",round(sorted(l)[len(l)//2],2))
