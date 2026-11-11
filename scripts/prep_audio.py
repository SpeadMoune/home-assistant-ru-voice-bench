import glob, os, subprocess, numpy as np, soundfile as sf
os.makedirs("a16",exist_ok=True)
rng=np.random.default_rng(42)
def pink(n):
    w=rng.standard_normal(n); f=np.fft.rfft(w); k=np.arange(len(f)); k[0]=1; f=f/np.sqrt(k); x=np.fft.irfft(f,n); return x/np.std(x)
for fn in sorted(glob.glob("audio/*.wav")+glob.glob("audio_live/*.wav")):
    base=os.path.basename(fn)[:-4]; out=f"a16/{base}.wav"
    if not os.path.exists(out): subprocess.run(["ffmpeg","-loglevel","error","-y","-i",fn,"-ar","16000","-ac","1","-sample_fmt","s16",out])
    if "simeon" in base: continue
    nout=f"a16/{base}-noisy.wav"
    if os.path.exists(nout): continue
    x,sr=sf.read(out); sp=x[np.abs(x)>0.01]; ps=np.sqrt(np.mean(sp**2))
    y=x+pink(len(x))*ps/(10**(10/20)); y=y/max(1,np.max(np.abs(y))*1.01)
    sf.write(nout,y,sr,subtype="PCM_16")
print(len(glob.glob("a16/*.wav")))
