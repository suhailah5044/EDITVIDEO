"""Spec-driven builder (Video 2 style).  usage: build_video.py SPEC.json RAW.mov WORKDIR OUT.mp4
Spec times for cards are SOURCE (raw) times; they are mapped to output times through the segment list."""
import json, sys, os, shutil, subprocess, wave
import numpy as np
spec_p, raw, work, out_mp4 = sys.argv[1:5]
HERE=os.path.dirname(os.path.abspath(__file__)); HF=os.path.join(HERE,'..','hf')
spec=json.load(open(spec_p)); os.makedirs(work,exist_ok=True)
segs=spec['segments']
# ---- source -> output time mapping
starts=[]; acc=0
for s in segs: starts.append(acc); acc+=s['b']-s['a']
DUR=round(acc,3)
def o(t):
    for s,st in zip(segs,starts):
        if s['a']-1e-6<=t<=s['b']+1e-6: return round(st+t-s['a'],3)
    raise ValueError(f'src time {t} not in any kept segment')
# ---- 1. base video
parts=[];vl=[];al=[]
for i,s in enumerate(segs):
    z=s.get('zoom','1.0'); ax=s.get('ax',0.5); ay=s.get('ay',0.30); d=s['b']-s['a']
    parts.append(f"[0:v]trim={s['a']}:{s['b']},setpts=PTS-STARTPTS,"
      f"scale=w='trunc(1080*({z})/2)*2':h='trunc(1920*({z})/2)*2':eval=frame:flags=lanczos,"
      f"crop=1080:1920:'(iw-1080)*{ax}':'(ih-1920)*{ay}',setsar=1,fps=30[v{i}]")
    parts.append(f"[0:a]atrim={s['a']}:{s['b']},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.015:.3f}:d=0.015[a{i}]")
    vl.append(f"[v{i}]"); al.append(f"[a{i}]")
n=len(segs)
parts+=["".join(vl)+f"concat=n={n}:v=1:a=0[vc]","".join(al)+f"concat=n={n}:v=0:a=1[ac]",
 "[vc]curves=master='0/0.02 0.25/0.30 0.5/0.56 0.8/0.84 1/0.98',eq=contrast=1.04:saturation=1.10:gamma_b=0.99,"
 "colorbalance=rs=0.01:bs=-0.01:rm=0.01,unsharp=5:5:0.45:5:5:0.0,vignette=angle=PI/6:mode=forward[vout]",
 "[ac]highpass=f=85,equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,"
 "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,aresample=48000[aout]"]
subprocess.run(["ffmpeg","-v","error","-y","-i",raw,"-filter_complex",";".join(parts),"-map","[vout]","-map","[aout]",
  "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p","-c:a","pcm_s16le",f"{work}/base.mov"],check=True)
# ---- 2. composition config (output times)
cards=[]; C=spec['cards']
for i,c in enumerate(C):
    k=dict(c); k['tin']=max(0.05,o(c['tin']))
    nxt = o(C[i+1]['tin']) if i+1<len(C) else DUR+1
    k['tout']=o(c['tout']) if 'tout' in c else round(nxt-0.14,3)
    if 'thl' in c: k['thl']=o(c['thl'])
    if 'chipT' in c: k['chipT']=[o(t) for t in c['chipT']]
    if 'pop' in c: k['pop']={'text':c['pop']['text'],'t':o(c['pop']['t'])}
    cards.append(k)
comp=os.path.join(work,'comp'); os.makedirs(comp,exist_ok=True)
for f in ['gsap.min.js','m0.ttf','m1.ttf','m2.ttf']: shutil.copy(os.path.join(HF,'video2',f),comp)
html=open(os.path.join(HF,'template.html')).read().replace('/*CONFIG*/',json.dumps({'duration':DUR,'cards':cards},ensure_ascii=False))
open(os.path.join(comp,'index.html'),'w').write(html)
json.dump({'duration':DUR,'cards':cards},open(f'{work}/timeline.json','w'),ensure_ascii=False,indent=1)
# ---- 3. overlay frames
ov=f'{work}/ov'; shutil.rmtree(ov,ignore_errors=True)
subprocess.run(["node",os.path.join(HERE,'render_overlay.js'),os.path.join(comp,'index.html'),ov,"30"],check=True)
# ---- 4. music + sfx
SR=48000; D=DUR+0.6; t=np.arange(int(SR*D))/SR; rng=np.random.default_rng(spec.get('seed',7))
def env(n,a,r):
    e=np.ones(n); a=min(int(a*SR),n//2); r=min(int(r*SR),n//2)
    e[:a]=np.linspace(0,1,a); e[len(e)-r:]*=np.linspace(1,0,r); return e
f=lambda m:440*2**((m-69)/12); bpm=spec.get('bpm',92); beat=60/bpm; bar=4*beat
chords=spec.get('chords',[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]])
mus=np.zeros_like(t)
for b in range(int(D/bar)+1):
    c=chords[b%len(chords)]; s=int(b*bar*SR); nn=min(int(bar*SR),len(t)-s)
    if nn<=0: break
    tt=np.arange(nn)/SR
    mus[s:s+nn]+=sum(np.sin(2*np.pi*f(m)*tt)*0.6+np.sin(2*np.pi*f(m)*2.003*tt)*0.12 for m in c)*env(nn,0.35,0.5)*0.05
    mus[s:s+nn]+=np.sin(2*np.pi*f(c[0]-12)*tt)*0.09*env(nn,0.02,0.4)
    for k in range(8):
        ks=s+int(k*beat/2*SR); kn=int(0.45*SR)
        if ks+kn>len(t): break
        kt=np.arange(kn)/SR; mus[ks:ks+kn]+=np.sin(2*np.pi*f(c[[0,2,1,3,2,1,3,2][k]]+12)*kt)*np.exp(-kt*7)*0.035
for i in range(int(D/beat)+1):
    s=int(i*beat*SR)
    if i%2==0:
        nn=int(0.3*SR); kt=np.arange(nn)/SR; x=np.sin(2*np.pi*(50+90*np.exp(-kt*30))*kt)*np.exp(-kt*12)*0.22
    else:
        nn=int(0.18*SR); kt=np.arange(nn)/SR; x=rng.standard_normal(nn)*np.exp(-kt*28)*0.05
    mus[s:s+nn]+=x[:max(0,len(mus)-s)]
    for h in (0,0.5):
        hs=s+int(h*beat*SR); nn=int(0.05*SR)
        if hs+nn<len(mus): mus[hs:hs+nn]+=np.diff(rng.standard_normal(nn+1))*np.exp(-np.arange(nn)/SR*90)*0.018
a=np.exp(-2*np.pi*5000/SR); y=np.zeros_like(mus); q=0
for i,x in enumerate(mus): q=(1-a)*x+a*q; y[i]=q
mus=y*env(len(y),0.6,1.2); mus=mus/np.max(np.abs(mus))*0.8
sfx=np.zeros_like(t)
def add(arr,st,g):
    s=int(st*SR); nn=min(len(arr),len(sfx)-s); sfx[s:s+nn]+=arr[:nn]*g
def whoosh(d=0.38):
    nn=int(d*SR); x=rng.standard_normal(nn); tt=np.arange(nn)/nn; out=np.zeros(nn); q=0
    for i in range(nn):
        aa=np.exp(-2*np.pi*(300+3500*np.sin(np.pi*tt[i])**2)/SR); q=(1-aa)*x[i]+aa*q; out[i]=q
    return out*np.sin(np.pi*tt)**1.5*0.5
def pop():
    nn=int(0.09*SR); tt=np.arange(nn)/SR; return np.sin(2*np.pi*(900-500*tt/0.09)*tt)*np.exp(-tt*45)*0.5
def ding():
    nn=int(1.2*SR); tt=np.arange(nn)/SR
    return (np.sin(2*np.pi*1568*tt)+0.5*np.sin(2*np.pi*2349*tt)+0.25*np.sin(2*np.pi*3136*tt))*np.exp(-tt*4.5)*0.22
W=whoosh(); add(W,0.0,0.35)
for i,c in enumerate(cards):
    if i>0: add(W,max(0,c['tin']-0.10),0.55)
    for tc in c.get('chipT',[]): add(pop(),tc,0.35)
    if c['type']=='list': add(pop(),c['tin']+0.03,0.35)
    if 'pop' in c: add(pop(),c['pop']['t'],0.4)
    if c['type']=='cta': add(ding(),c['tin']+0.07,0.6)
def save(fn,x):
    x=np.clip(x,-1,1); w=wave.open(fn,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
save(f'{work}/music.wav',mus); save(f'{work}/sfx.wav',sfx)
# ---- 5. final mix
subprocess.run(["ffmpeg","-v","error","-y","-i",f"{work}/base.mov","-framerate","30","-i",f"{ov}/f%05d.png",
 "-i",f"{work}/music.wav","-i",f"{work}/sfx.wav","-filter_complex",
 "[0:v][1:v]overlay=format=auto,format=yuv420p[v];[0:a]asplit=2[voice][sc];[2:a]volume=0.32,aresample=48000[mu];"
 "[mu][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350:makeup=1[duck];[3:a]volume=0.8,aresample=48000[fx];"
 "[voice][duck][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]",
 "-map","[v]","-map","[a]","-c:v","libx264","-preset","slow","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",
 "-c:a","aac","-b:a","192k","-t",str(DUR),out_mp4],check=True)
print('done',out_mp4,DUR)
