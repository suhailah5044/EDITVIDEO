import sys, os, subprocess, numpy as np, time
from PIL import Image
from rembg import remove, new_session
src, outdir = sys.argv[1], sys.argv[2]
W,H=1080,1920; FPS=30
p=subprocess.Popen(["ffmpeg","-v","error","-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
ONLY=sys.argv[3]
sess={ONLY:new_session({"bi":"birefnet-general-lite","is":"isnet-general-use"}[ONLY])}
def model(t):
    if t<8.833 or t>=14.1: return "bi"
    return "is"
def skip(t): return (12.70<t<14.15) or (17.09<t<17.28)
i=0; t0=time.time()
while True:
    buf=p.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    t=i/FPS; fn=os.path.join(outdir,f"m{i:04d}.png")
    if not os.path.exists(fn) and (skip(t) or model(t)==ONLY):
        if skip(t): Image.new("L",(540,960),0).save(fn)
        else:
            im=Image.fromarray(np.frombuffer(buf,np.uint8).reshape(H,W,3))
            m=remove(im,session=sess[model(t)],only_mask=True).resize((540,960),Image.BILINEAR)
            m.save(fn)
    if i%30==0: print(f"frame {i} t={t:.1f} elapsed={time.time()-t0:.0f}s",flush=True)
    i+=1
print("DONE",i,flush=True)
