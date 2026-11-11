import sys, wave, time
sys.path.insert(0,"test")
from bench import CASES
from piper import PiperVoice
for v in ["irina","dmitri"]:
    pv=PiperVoice.load(f"voices/ru_RU-{v}-medium.onnx")
    for cid,text,*_ in CASES:
        with wave.open(f"audio/{cid}_piper-{v}.wav","wb") as w: pv.synthesize_wav(text,w)
print("ok")
