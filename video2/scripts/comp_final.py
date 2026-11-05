import sys, os, subprocess, numpy as np
from PIL import Image, ImageFilter
src, bgv, mdir, out = sys.argv[1:5]
W,H=1080,1920; FPS=30; F=W*H*3
cuts=[0,87,165,265,382,425,512,519,540,611,736,10**9]
def seg(i): return max(k for k,c in enumerate(cuts) if c<=i)
rd=lambda f:subprocess.Popen(["ffmpeg","-v","error","-i",f,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
a,b=rd(src),rd(bgv)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-","-i",src,
  "-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf","15","-g","15","-pix_fmt","yuv420p","-c:a","copy","-shortest",out],stdin=subprocess.PIPE)
x=np.arange(W)[None,:]; y=np.arange(H)[:,None]
FADE=np.clip((850-np.arange(H))/200,0,1).astype(np.float32)[:,None,None]
strip=(np.clip((x-880)/60,0,1)*np.clip((y-640)/90,0,1)).astype(np.float32)
def lm(i):
    fn=os.path.join(mdir,f"m{i:04d}.png")
    return np.asarray(Image.open(fn),np.float32)/255 if os.path.exists(fn) else None
n=len(os.listdir(mdir)); i=0; lastbg=None
while True:
    fb=a.stdout.read(F)
    if len(fb)<F: break
    bb=b.stdout.read(F)
    if len(bb)==F: lastbg=bb
    fr=np.frombuffer(fb,np.uint8).reshape(H,W,3).astype(np.float32)/255
    bg=np.frombuffer(lastbg,np.uint8).reshape(H,W,3).astype(np.float32)/255
    s=seg(i); acc=0; wsum=0
    for j,w in ((i-1,.25),(i,.5),(i+1,.25)):
        if 0<=j<n and seg(j)==s:
            m=lm(j)
            if m is not None: acc=acc+w*m; wsum+=w
    m=acc/wsum if wsum else np.zeros((960,540),np.float32)
    M=Image.fromarray((m*255).astype(np.uint8)).resize((W,H),Image.BICUBIC).filter(ImageFilter.GaussianBlur(2.5))
    M=np.asarray(M,np.float32)/255
    if i/FPS>=24.5: M=np.maximum(M,strip)
    if 265<=i<382: M=np.clip((M-0.04)/0.30,0,1)
    else: M=np.clip((M-0.08)/0.84,0,1)
    M3=M[...,None]; gl=bg*FADE*0.5; scr=1-(1-fr)*(1-gl); o=fr*M3+scr*(1-M3)
    enc.stdin.write((np.clip(o,0,1)*255).astype(np.uint8).tobytes())
    if i%60==0: print("comp",i,flush=True)
    i+=1
enc.stdin.close(); enc.wait(); print("DONE",i)
