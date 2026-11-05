import subprocess, sys
S = sys.argv[1]
# (src_start, src_end, zoom_expr(t local), anchor_x, anchor_y)
segs = [
 (0.05, 3.08, "1.05+0.11*exp(-5*t)+0.012*t", 0.0, 0.30),   # hook punch-in
 (3.17, 6.07, "1.00+0.012*t",               0.0, 0.30),
 (6.33, 7.94, "1.07+0.010*t",               0.0, 0.30),
 (7.94, 13.58,"1.00+0.010*t",               0.5, 0.30),
 (13.78,15.18,"1.10",                        0.5, 0.30),
 (15.18,18.62,"1.00+0.008*t",               0.5, 0.30),
 (18.62,20.62,"1.07",                        1.0, 0.30),
 (20.92,23.33,"1.04+0.04*exp(-5*t)",        1.0, 0.30),
 (23.52,24.40,"1.12",                        1.0, 0.30),
]
parts=[]; vl=[]; al=[]
for i,(a,b,z,ax,ay) in enumerate(segs):
    parts.append(
      f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,"
      f"scale=w='trunc(1080*({z})/2)*2':h='trunc(1920*({z})/2)*2':eval=frame:flags=lanczos,"
      f"crop=1080:1920:'(iw-1080)*{ax}':'(ih-1920)*{ay}',setsar=1,fps=30[v{i}]")
    d=b-a
    parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.015:.3f}:d=0.015[a{i}]")
    vl.append(f"[v{i}]"); al.append(f"[a{i}]")
n=len(segs)
parts.append("".join(vl)+f"concat=n={n}:v=1:a=0[vc]")
parts.append("".join(al)+f"concat=n={n}:v=0:a=1[ac]")
# grade: lift shadows, gentle contrast, fresh but natural colour, mild sharpening (no smoothing)
parts.append("[vc]curves=master='0/0.02 0.25/0.30 0.5/0.56 0.8/0.84 1/0.98',"
             "eq=contrast=1.04:saturation=1.10:gamma_r=1.0:gamma_b=0.99,"
             "colorbalance=rs=0.01:bs=-0.01:rm=0.01,"
             "unsharp=5:5:0.45:5:5:0.0,"
             "vignette=angle=PI/6:mode=forward[vout]")
# voice chain: clean low end, presence, gentle compression
parts.append("[ac]highpass=f=85,equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,"
             "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,aresample=48000[aout]")
fc=";".join(parts)
cmd=["ffmpeg","-v","error","-y","-i",f"{S}/raw/raw.mov","-filter_complex",fc,"-map","[vout]","-map","[aout]",
     "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p","-c:a","pcm_s16le",f"{S}/build/base.mov"]
subprocess.run(cmd,check=True)
