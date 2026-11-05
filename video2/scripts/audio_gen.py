import numpy as np, wave, sys, os
SR=44100; out=sys.argv[1]
rng=np.random.default_rng(7)
def save(name,x,st=True):
    x=np.clip(x,-1,1)
    if x.ndim==1: x=np.stack([x,x],1)
    w=wave.open(os.path.join(out,name),'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
def t(d): return np.arange(int(d*SR))/SR
def env(n,a,r):
    e=np.ones(n); A=int(a*SR); e[:A]=np.linspace(0,1,A) if A else 1
    return e*np.exp(-np.arange(n)/SR/r)
def mtof(m): return 440*2**((m-69)/12)
def lp(x,k):  # one-pole lowpass
    y=np.zeros_like(x); a=k; s=0
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
# ---------- MUSIC: 112 bpm, C - G - Am - F, marimba pluck + soft bass + kick + shaker
bpm=112; beat=60/bpm; D=29.5; N=int(D*SR)
L=np.zeros(N); R=np.zeros(N)
def add(buf,x,at):
    i=int(at*SR)
    if i>=N: return
    j=min(N,i+len(x)); buf[i:j]+=x[:j-i]
def marimba(f,d=0.6):
    tt=t(d); x=np.sin(2*np.pi*f*tt)+0.35*np.sin(2*np.pi*f*4*tt)*np.exp(-tt*30)
    return x*env(len(tt),0.002,0.18)
chords=[[60,64,67],[55,59,62],[57,60,64],[53,57,60]]
bars=int(D/(beat*4))+1
for b in range(bars):
    ch=chords[b%4]; t0=b*4*beat
    # arpeggio 8th notes
    pat=[0,1,2,1,0+12,2,1,2]
    for k,p in enumerate(pat):
        idx=p%12 if p<12 else p-12
        m=ch[idx%3]+(12 if p>=12 else 0)+12
        x=marimba(mtof(m))*0.16
        pan=0.35 if k%2 else -0.35
        add(L,x*(1-pan),t0+k*beat/2); add(R,x*(1+pan),t0+k*beat/2)
    # bass
    tb=t(beat*3.6); bx=np.sin(2*np.pi*mtof(ch[0]-24)*tb)*env(len(tb),0.01,0.9)*0.28
    add(L,bx,t0); add(R,bx,t0)
    # pad
    tp=t(beat*4); pad=sum(np.sin(2*np.pi*mtof(m)*tp+0.3*np.sin(2*np.pi*0.3*tp)) for m in ch)/3
    pad*=np.minimum(1,tp/0.4)*np.minimum(1,(beat*4-tp)/0.4)*0.05
    add(L,pad,t0); add(R,pad,t0)
    for q in range(4):
        if b==0 and q<2: continue
        tk=t(0.25); f=60+90*np.exp(-tk*25)
        kick=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tk*14)*0.35
        add(L,kick,t0+q*beat); add(R,kick,t0+q*beat)
        for h in (0.5,):
            n=rng.standard_normal(int(0.05*SR)); n=n-np.concatenate([[0],n[:-1]])
            sh=n*np.exp(-np.arange(len(n))/SR*60)*0.05
            add(L,sh*0.7,t0+(q+h)*beat); add(R,sh,t0+(q+h)*beat)
        if q in (1,3):
            n=rng.standard_normal(int(0.18*SR)); n=n-np.concatenate([[0],n[:-1]])
            clap=n*np.exp(-np.arange(len(n))/SR*22)*0.06
            add(L,clap,t0+q*beat); add(R,clap,t0+q*beat)
mus=np.stack([L,R],1); mus/=np.abs(mus).max()/0.8
fo=int(1.5*SR); mus[-fo:]*=np.linspace(1,0,fo)[:,None]
save('music.wav',mus)
# ---------- SFX
# whoosh: band-swept noise
d=0.45; n=rng.standard_normal(int(d*SR)); tt=t(d)
sweep=np.zeros_like(n); s=0
for i in range(len(n)):
    k=0.02+0.25*np.sin(np.pi*tt[i]/d)**2; s+=k*(n[i]-s); sweep[i]=s
wh=sweep*np.sin(np.pi*tt/d)**2; wh/=np.abs(wh).max(); save('whoosh.wav',np.stack([wh*0.55*np.linspace(1.2,0.6,len(wh)),wh*0.55*np.linspace(0.6,1.2,len(wh))],1))
# pop
d=0.12; tt=t(d); f=900*np.exp(-tt*25)+300
pop=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*35); save('pop.wav',pop*0.6)
# ding (bell)
d=1.2; tt=t(d); f=1568
ding=(np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*2.76*tt)*np.exp(-tt*6)+0.25*np.sin(2*np.pi*f*5.4*tt)*np.exp(-tt*10))*np.exp(-tt*3.5)*np.minimum(1,tt/0.003)
save('ding.wav',ding/np.abs(ding).max()*0.45)
# tick (soft click for list items)
d=0.06; tt=t(d); tk=np.sin(2*np.pi*2200*tt)*np.exp(-tt*120); save('tick.wav',tk*0.5)
# sparkle for CTA (rising arpeggio)
sp=np.zeros(int(0.9*SR))
for k,m in enumerate([84,88,91,96]):
    x=marimba(mtof(m),0.5); i=int(k*0.07*SR); sp[i:i+len(x)]+=x[:len(sp)-i]
save('sparkle.wav',sp/np.abs(sp).max()*0.4)
print('ok')
