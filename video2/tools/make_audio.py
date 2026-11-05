import numpy as np, wave, sys
SR=48000; D=23.31+0.6; out=sys.argv[1]
t=np.arange(int(SR*D))/SR
def env(n,a,r):
    e=np.ones(n); a=min(int(a*SR),n//2); r=min(int(r*SR),n//2)
    e[:a]=np.linspace(0,1,a); e[-r:]*=np.linspace(1,0,r); return e
rng=np.random.default_rng(7)
# ---------- music: warm lo-fi, 92 bpm, Fmaj7 - Em7 - Dm7 - Cmaj7 ----------
bpm=92; beat=60/bpm; bar=4*beat
chords=[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]]
f=lambda m:440*2**((m-69)/12)
mus=np.zeros_like(t)
nb=int(D/bar)+1
for b in range(nb):
    c=chords[b%4]; s=int(b*bar*SR); n=min(int(bar*SR),len(t)-s)
    if n<=0: break
    tt=np.arange(n)/SR
    pad=sum(np.sin(2*np.pi*f(m)*tt)*0.6+np.sin(2*np.pi*f(m)*2.003*tt)*0.12 for m in c)
    pad*=env(n,0.35,0.5)*0.05
    bass=np.sin(2*np.pi*f(c[0]-12)*tt)*0.09*env(n,0.02,0.4)
    mus[s:s+n]+=pad+bass
    # soft keys arpeggio on 8ths
    for k in range(8):
        ks=s+int(k*beat/2*SR); kn=int(0.45*SR)
        if ks+kn>len(t): break
        kt=np.arange(kn)/SR; m=c[[0,2,1,3,2,1,3,2][k]]+12
        mus[ks:ks+kn]+=np.sin(2*np.pi*f(m)*kt)*np.exp(-kt*7)*0.035
# drums
for i in range(int(D/beat)+1):
    s=int(i*beat*SR)
    if i%2==0:  # kick
        n=int(0.3*SR); kt=np.arange(n)/SR
        k=np.sin(2*np.pi*(50+90*np.exp(-kt*30))*kt)*np.exp(-kt*12)*0.22
        mus[s:s+n]+=k[:len(mus)-s]
    else:       # soft snare/rim
        n=int(0.18*SR); kt=np.arange(n)/SR
        sn=rng.standard_normal(n)*np.exp(-kt*28)*0.05
        mus[s:s+n]+=sn[:len(mus)-s]
    for h in (0,0.5):  # hats
        hs=s+int(h*beat*SR); n=int(0.05*SR)
        if hs+n<len(mus):
            hn=np.diff(rng.standard_normal(n+1))*np.exp(-np.arange(n)/SR*90)*0.018
            mus[hs:hs+n]+=hn
# warm low-pass (one-pole) + fades
a=np.exp(-2*np.pi*5000/SR); y=np.zeros_like(mus); acc=0
for i,x in enumerate(mus): acc=(1-a)*x+a*acc; y[i]=acc
mus=y*env(len(y),0.6,1.2)
# ---------- sfx ----------
sfx=np.zeros_like(t)
def add(arr,st,g):
    s=int(st*SR); n=min(len(arr),len(sfx)-s); sfx[s:s+n]+=arr[:n]*g
def whoosh(d=0.38):
    n=int(d*SR); x=rng.standard_normal(n); tt=np.arange(n)/n
    out=np.zeros(n); acc=0
    for i in range(n):
        fc=300+3500*np.sin(np.pi*tt[i])**2; a=np.exp(-2*np.pi*fc/SR)
        acc=(1-a)*x[i]+a*acc; out[i]=acc
    return out*np.sin(np.pi*tt)**1.5*0.5
def pop():
    n=int(0.09*SR); tt=np.arange(n)/SR
    return np.sin(2*np.pi*(900-500*tt/0.09)*tt)*np.exp(-tt*45)*0.5
def ding():
    n=int(1.2*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*1568*tt)+0.5*np.sin(2*np.pi*2349*tt)+0.25*np.sin(2*np.pi*3136*tt))*np.exp(-tt*4.5)*0.22
W=whoosh()
for st in [3.45,7.44,14.48,17.96,21.08]: add(W,st,0.55)
add(W,0.0,0.35)
for st in [3.58,4.30,4.88,5.34,5.96,7.08]: add(pop(),st,0.35)
add(ding(),21.25,0.6)
add(pop(),20.38,0.4)
def save(fn,x):
    x=np.clip(x,-1,1); w=wave.open(fn,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
save(out+'/music.wav',mus/np.max(np.abs(mus))*0.8); save(out+'/sfx.wav',sfx)
