import numpy as np, wave, sys, os
SR=44100; out=sys.argv[1]; rng=np.random.default_rng(11)
def save(n,x):
    x=np.clip(x,-1,1); x=np.stack([x,x],1) if x.ndim==1 else x
    w=wave.open(os.path.join(out,n),'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
def t(d): return np.arange(int(d*SR))/SR
def norm(x,g): return x/np.abs(x).max()*g
# swipe: short airy noise with rising bandpass-ish (diff of lowpassed)
d=0.32; tt=t(d); n=rng.standard_normal(len(tt)); y=np.zeros_like(n); s=0
for i in range(len(n)):
    k=0.03+0.5*(tt[i]/d)**2; s+=k*(n[i]-s); y[i]=s
y=y-np.convolve(y,np.ones(40)/40,'same'); y*=np.sin(np.pi*tt/d)**1.5
save('swipe.wav',np.stack([norm(y,.5)*np.linspace(.6,1.2,len(y)),norm(y,.5)*np.linspace(1.2,.6,len(y))],1))
# boop: bubbly upward pitch
d=0.16; tt=t(d); f=380+700*(tt/d)**0.6
save('boop.wav',norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*18)*np.minimum(1,tt/0.004),.55))
# xylophone run (modul reveal)
def bar(fr,d=0.45):
    tt=t(d); return (np.sin(2*np.pi*fr*tt)+0.3*np.sin(2*np.pi*fr*3.93*tt)*np.exp(-tt*40))*np.exp(-tt*9)*np.minimum(1,tt/0.002)
xs=np.zeros(int(0.9*SR))
for k,m in enumerate([72,76,79,84]):
    b=bar(440*2**((m-69)/12)); i=int(k*0.06*SR); xs[i:i+len(b)]+=b[:len(xs)-i]
save('xylo.wav',norm(xs,.42))
# ting (4M chips) - clear small bell
d=0.5; tt=t(d); f=2093
ting=(np.sin(2*np.pi*f*tt)+0.4*np.sin(2*np.pi*f*2.0*tt)*np.exp(-tt*12))*np.exp(-tt*7)*np.minimum(1,tt/0.002)
save('ting.wav',norm(ting,.4))
# chime CTA: two-note shimmering
d=1.3; tt=t(d); ch=np.zeros_like(tt)
for k,(f,dl) in enumerate([(1318.5,0),(1975.5,0.12)]):
    i=int(dl*SR); tk=tt[:len(tt)-i]
    ch[i:]+=(np.sin(2*np.pi*f*tk)+0.3*np.sin(2*np.pi*f*2.01*tk))*np.exp(-tk*3)*np.minimum(1,tk/0.003)
save('chime.wav',norm(ch,.38))
print("ok")
