#!/usr/bin/env python3
"""Compile 'Kuasai Algebra' video: footage + tutorial screen recording + VO + text overlays + pop SFX.

Usage: python3 build.py RAW_DIR WORK_DIR OUT.mp4
"""
import math, os, subprocess, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RAW, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 1080, 1920, 30
TOTAL = 36.40
SRC_SCALE = 1.15                     # footage decoded slightly larger so we can push-in without upscaling
SW, SH = int(W * SRC_SCALE) // 2 * 2, int(H * SRC_SCALE) // 2 * 2

FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_BOLD = FONT_DIR + "InterDisplay-ExtraBold.otf"
F_MATH = FONT_DIR + "InterDisplay-BoldItalic.otf"
F_NUM = FONT_DIR + "InterDisplay-Bold.otf"
WHITE = (255, 255, 255)
YELLOW = (255, 212, 0)

# ---------------------------------------------------------------- timeline
# (t_start, t_end, source, src_in, src_out, opts)
# play_dur: if set, the source span plays over this many seconds then the last frame holds.
SEGS = [
    (0.00, 1.82, "IMG_1551.MOV", 1.30, 3.12, {}),                     # hook: Set Latihan 2
    (1.82, 5.12, "IMG_1543.MOV", 0.00, 3.30, {}),                     # soalan close-up
    (5.12, 7.64, "IMG_1544.MOV", 0.40, 2.92, {}),
    (7.64, 9.90, "screen.mp4", 42.0, 80.0, {}),                        # GSTK -> darab 3t
    (9.90, 12.80, "screen.mp4", 84.0, 142.0, {"nopunch": True}),        # 12st, 9t - 4 - 3t
    (12.80, 14.10, "screen.mp4", 162.0, 168.8, {"nopunch": True, "play_dur": 0.55}),  # jawapan 6t-4 / 12st
    (14.10, 15.02, "IMG_1542.MOV", 0.00, 0.92, {}),                   # nampak susah kan
    (15.02, 17.50, "IMG_1547.MOV", 0.00, 2.48, {}),                   # pecahan algebra
    (17.50, 19.70, "IMG_1552.MOV", 2.20, 4.40, {}),                   # stuck / keliru
    (19.70, 21.84, "IMG_1549.MOV", 0.00, 1.73, {}),                   # buku Kuasai Algebra
    (21.84, 26.36, "IMG_1546.MOV", 0.00, 4.43, {}),                   # nota ringkas, contoh, latihan
    (26.36, 28.82, "IMG_1548.MOV", 0.90, 3.36, {}),                   # QR code
    (28.82, 30.92, "screen.mp4", 2.0, 42.0, {}),                       # video tutorial (lepas scan QR)
    (30.92, 32.94, "IMG_1545.MOV", 0.00, 4.04, {}),                   # Form 1 - Form 5
    (32.94, 34.40, "IMG_1552.MOV", 0.00, 1.46, {}),
    (34.40, TOTAL, "IMG_1549.MOV", 0.00, 1.73, {"play_dur": 1.73}),   # CTA cover
]

# ---------------------------------------------------------------- overlays
# Each group: (t_in, t_out, y_center, lines). line = list of runs; run = (pop_time, kind, payload, color, size)
# kind "t" = text, "f" = fraction (num, den)
def T(t, s, c=WHITE, sz=60):
    return (t, "t", s, c, sz)

def FR(t, num, den, c=YELLOW, sz=50):
    return (t, "f", (num, den), c, sz)

Y_TEXT = 470          # ~24% from top: not too high, not too low
GROUPS = [
    (0.60, 1.78, Y_TEXT, [[T(0.60, "Set Latihan "), T(0.95, "2", YELLOW)]]),
    (2.70, 7.58, Y_TEXT, [[T(2.70, "Permudahkan")],
                          [FR(3.40, "3", "4s", YELLOW, 54), T(4.62, "  −  ", YELLOW, 56), FR(4.76, "4 + 3t", "12st", YELLOW, 54)]]),
    (8.18, 9.86, 400, [[T(8.18, "Samakan penyebut")], [T(9.14, "darab 3t", YELLOW)]]),
    (10.98, 12.76, 430, [[T(10.98, "Teruskan pengiraan")]]),
    (13.00, 14.06, 400, [[T(13.00, "Jawapan paling ringkas", WHITE, 54)],
                         [FR(13.20, "6t − 4", "12st", YELLOW, 54)]]),
    (14.12, 14.98, Y_TEXT, [[T(14.12, "Nampak "), T(14.44, "susah", YELLOW), T(14.80, " kan?")]]),
    (15.40, 17.12, Y_TEXT, [[T(15.40, "Pecahan Algebra", YELLOW)]]),
    (17.22, 19.62, Y_TEXT, [[T(17.22, "Selalu "), T(17.40, "stuck?", YELLOW)]]),
    (23.12, 26.30, Y_TEXT, [[T(23.12, "Nota ringkas", WHITE, 54), T(23.58, "  •  Contoh", WHITE, 54),
                             T(24.24, "  •  Latihan", YELLOW, 54)]]),
    (27.12, 28.78, Y_TEXT, [[T(27.12, "Scan QR", YELLOW)], [T(28.14, "Video tutorial", WHITE, 54)]]),
    (29.82, 30.88, 430, [[T(29.82, "Boleh ulang tengok")]]),
    (31.16, 32.90, Y_TEXT, [[T(31.16, "Sesuai untuk", WHITE, 54)], [T(31.52, "Form 1 – Form 5", YELLOW)]]),
    (33.40, 35.10, Y_TEXT, [[T(33.40, "Nak anak "), T(33.86, "lebih faham?", YELLOW)]]),
    (35.18, TOTAL, Y_TEXT, [[T(35.18, "Check "), T(35.34, "beg kuning", YELLOW), T(35.60, " sekarang!")]]),
]

_fonts = {}
def font(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

def render_text(s, color, size):
    f = font(F_BOLD, size)
    bb = f.getbbox(s)
    pad = 24
    w, h = bb[2] - bb[0] + 2 * pad, int(size * 1.35) + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bb[0], pad), s, font=f, fill=color + (255,), stroke_width=3, stroke_fill=(15, 15, 15, 255))
    return img

def math_text(d, x, y, s, f, color):
    """draw a math string: letters italic, digits/operators upright. returns width."""
    cx = x
    for ch in s:
        ff = f[1] if ch.isalpha() else f[0]
        d.text((cx, y), ch, font=ff, fill=color + (255,), stroke_width=3, stroke_fill=(15, 15, 15, 255))
        cx += ff.getlength(ch)
    return cx - x

def math_len(s, f):
    return sum((f[1] if ch.isalpha() else f[0]).getlength(ch) for ch in s)

def render_frac(num, den, color, size):
    f = (font(F_NUM, size), font(F_MATH, size))
    wn, wd = math_len(num, f), math_len(den, f)
    wbar = max(wn, wd) + size * 0.4
    pad = 24
    lh = int(size * 1.2)
    w = int(wbar) + 2 * pad
    h = 2 * lh + int(size * 0.3) + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    asc = f[0].getbbox("0")[1]
    math_text(d, pad + (wbar - wn) / 2, pad - asc + 2, num, f, color)
    bar_y = pad + lh + int(size * 0.05)
    th = max(4, size // 12)
    d.rounded_rectangle([pad - 2, bar_y - 2, pad + wbar + 2, bar_y + th + 2], radius=3, fill=(20, 20, 20, 255))
    d.rounded_rectangle([pad, bar_y, pad + wbar, bar_y + th], radius=2, fill=color + (255,))
    math_text(d, pad + (wbar - wd) / 2, bar_y + th + int(size * 0.25) - asc, den, f, color)
    return img

def add_shadow(img):
    a = np.array(img)[:, :, 3]
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for blur, k, dy in ((14, 0.85, 3), (5, 0.9, 3)):
        sh = Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 255))
        shadow.putalpha(sh)
        out.alpha_composite(shadow, (0, dy))
    out.alpha_composite(img)
    return out

# prerender every run, lay out lines (centered), compute absolute positions
LAYOUT = []   # (t_in, t_out, [(pop_t, img, cx, cy)])
for t_in, t_out, yc, lines in GROUPS:
    rendered = []
    for line in lines:
        imgs = []
        for (pt, kind, payload, color, size) in line:
            im = render_text(payload, color, size) if kind == "t" else render_frac(payload[0], payload[1], color, size)
            imgs.append((pt, add_shadow(im)))
        rendered.append(imgs)
    PAD = 24
    line_h = [max(im.height for _, im in l) - 2 * PAD for l in rendered]
    gap = 6
    total_h = sum(line_h) + gap * (len(line_h) - 1)
    y = yc - total_h / 2
    items = []
    for l, lh in zip(rendered, line_h):
        lw = sum(im.width - 2 * PAD for _, im in l)
        x = W / 2 - lw / 2
        for pt, im in l:
            iw = im.width - 2 * PAD
            items.append((pt, im, x + iw / 2, y + lh / 2))
            x += iw
        y += lh + gap
    LAYOUT.append((t_in, t_out, items))

POPS = sorted({pt for _, _, items in LAYOUT for pt, *_ in items})

def ease_pop(u):
    """0..1 -> scale with overshoot"""
    if u >= 1:
        return 1.0
    c1 = 2.2
    c3 = c1 + 1
    v = u - 1
    return 1 + c3 * v ** 3 + c1 * v ** 2

def draw_overlays(frame, t):
    for t_in, t_out, items in LAYOUT:
        if not (t_in - 0.01 <= t < t_out):
            continue
        fade_out = min(1.0, (t_out - t) / 0.12)
        for pt, im, cx, cy in items:
            if t < pt:
                continue
            u = (t - pt) / 0.22
            s = 0.55 + 0.45 * ease_pop(min(u, 1.0))
            alpha = min(1.0, (t - pt) / 0.08) * fade_out
            if alpha <= 0:
                continue
            if abs(s - 1) > 1e-3:
                im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
            else:
                im2 = im
            if alpha < 1:
                im2 = im2.copy()
                a = np.array(im2.getchannel("A"), dtype=np.float32) * alpha
                im2.putalpha(Image.fromarray(a.astype(np.uint8)))
            frame.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))

# ---------------------------------------------------------------- algebra background (dark)
def algebra_bg():
    rng = random.Random(7)
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    r = np.sqrt((xx - 0.5) ** 2 + ((yy - 0.45) * 1.4) ** 2)
    base_c = np.array([22, 27, 40], np.float32)
    edge_c = np.array([8, 10, 16], np.float32)
    k = np.clip(r / 0.9, 0, 1)[..., None]
    arr = base_c * (1 - k) + edge_c * k
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    # faint graph-paper grid
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        g.line([(x, 0), (x, H)], fill=(255, 255, 255, 10), width=1)
    for y in range(0, H, 60):
        g.line([(0, y), (W, y)], fill=(255, 255, 255, 10), width=1)
    img.alpha_composite(grid)
    # scattered algebra symbols
    syms = ["x²", "÷", "a/b", "+", "−", "=", "(x+y)", "√x", "3t", "4s", "12st", "×",
            "y²", "π", "ab", "2x+1", "x/y", "%", "a²−b²", "≤", "n³"]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    placed = []
    tries = 0
    while len(placed) < 34 and tries < 4000:
        tries += 1
        x, y = rng.randint(30, W - 120), rng.randint(40, H - 80)
        if any((x - px) ** 2 + (y - py) ** 2 < 170 ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        s = rng.choice(syms)
        sz = rng.randint(38, 74)
        tile = Image.new("RGBA", (420, 200), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((20, 40), s, font=font(F_MATH, sz), fill=(255, 255, 255, rng.randint(16, 30)))
        tile = tile.rotate(rng.uniform(-18, 18), resample=Image.BICUBIC)
        layer.alpha_composite(tile, (x - 60, y - 80))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.6)))
    return img

BG = algebra_bg()
BG.convert("RGB").save(os.path.join(WORK, "algebra_bg.png"))

# rounded panel mask + shadow for the tutorial screen recording
SCR_CROP = (56, 44, 856, 560)  # x, y, w, h inside 986x654 (drop toolbar + scrollbar)
PANEL_W = 1036
PANEL_H = int(PANEL_W * SCR_CROP[3] / SCR_CROP[2]) // 2 * 2
PANEL_X = (W - PANEL_W) // 2
PANEL_Y = 610
mask = Image.new("L", (PANEL_W, PANEL_H), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, PANEL_W - 1, PANEL_H - 1], radius=28, fill=255)
shadow = Image.new("L", (W, H), 0)
ImageDraw.Draw(shadow).rounded_rectangle([PANEL_X, PANEL_Y + 14, PANEL_X + PANEL_W, PANEL_Y + PANEL_H + 14],
                                         radius=30, fill=170)
shadow = shadow.filter(ImageFilter.GaussianBlur(26))
BG_SCREEN = BG.copy()
blk = Image.new("RGBA", (W, H), (0, 0, 0, 255))
blk.putalpha(shadow)
BG_SCREEN.alpha_composite(blk)

# darker top band on footage so white/yellow text stays readable (no box)
def top_shade():
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(-1, 1, W)[None, :]
    a = np.clip(1 - yy / 0.42, 0, 1) ** 1.5 * 0.50
    vig = np.clip((np.sqrt(xx ** 2 * 0.6 + ((yy - 0.5) * 2) ** 2 * 0.5) - 0.55) / 0.6, 0, 1) * 0.30
    a = np.maximum(a, vig)
    return (1 - a)[..., None].astype(np.float32)
SHADE = top_shade()

# ---------------------------------------------------------------- frame sources
def decode(src, a, b, n_out, play_frames):
    """yield exactly n_out RGB frames: span [a,b] of src stretched over play_frames, then hold last."""
    path = os.path.join(RAW, src)
    speed = (b - a) / (play_frames / FPS)
    is_screen = src.startswith("screen")
    if is_screen:
        x, y, w, h = SCR_CROP
        vf = f"setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS},crop={w}:{h}:{x}:{y},scale={PANEL_W}:{PANEL_H}:flags=lanczos," \
             f"eq=contrast=1.04:saturation=1.05"
        fw, fh = PANEL_W, PANEL_H
    else:
        vf = f"setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS},scale={SW}:{SH}:flags=lanczos," \
             f"eq=brightness=0.015:contrast=1.07:saturation=1.10:gamma=1.02,unsharp=5:5:0.45"
        fw, fh = SW, SH
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", path,
           "-vf", vf, "-frames:v", str(play_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = fw * fh * 3
    last = None
    got = 0
    for i in range(n_out):
        if got < play_frames:
            buf = p.stdout.read(size)
            if len(buf) == size:
                last = np.frombuffer(buf, np.uint8).reshape(fh, fw, 3)
                got += 1
            else:
                got = play_frames
        yield last, is_screen
    p.stdout.close()
    p.wait()

def compose_footage(arr, t_loc, dur, punch):
    z = 1.0 + 0.045 * (t_loc / max(dur, 0.01))          # slow push-in
    if punch:
        z += 0.07 * max(0.0, 1 - t_loc / 0.22) ** 2      # quick punch on cut
    z = min(z, SRC_SCALE)
    cw, ch = SW / z * (W / SW) * (SW / W), 0
    cw = W * SRC_SCALE / z
    ch = H * SRC_SCALE / z
    x0 = (SW - cw) / 2
    y0 = (SH - ch) / 2
    im = Image.fromarray(arr).resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    a = np.asarray(im, np.float32) * SHADE
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")

def compose_screen(arr, t_loc, punch):
    frame = BG_SCREEN.copy()
    s = 1.0
    if punch:
        u = min(1.0, t_loc / 0.28)
        s = 0.86 + 0.14 * ease_pop(u)
    panel = Image.fromarray(arr).convert("RGBA")
    panel.putalpha(mask)
    if s != 1.0:
        panel = panel.resize((int(PANEL_W * s), int(PANEL_H * s)), Image.BILINEAR)
    frame.alpha_composite(panel, (int(W / 2 - panel.width / 2), int(PANEL_Y + PANEL_H / 2 - panel.height / 2)))
    return frame

# ---------------------------------------------------------------- render video
silent = os.path.join(WORK, "video_noaudio.mp4")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                        "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
fidx = 0
for (t0, t1, src, a, b, opt) in SEGS:
    f0, f1 = round(t0 * FPS), round(t1 * FPS)
    n = f1 - f0
    play = round(opt.get("play_dur", t1 - t0) * FPS)
    punch = not opt.get("nopunch")
    print(f"{t0:6.2f}-{t1:6.2f} {src} [{a}-{b}] frames={n} speed={(b - a) / (play / FPS):.2f}", flush=True)
    for i, (arr, is_screen) in enumerate(decode(src, a, b, n, play)):
        t_loc = i / FPS
        t = (f0 + i) / FPS
        frame = compose_screen(arr, t_loc, punch) if is_screen else compose_footage(arr, t_loc, t1 - t0, punch)
        draw_overlays(frame, t)
        enc.stdin.write(frame.convert("RGB").tobytes())
        fidx += 1
enc.stdin.close()
enc.wait()

# ---------------------------------------------------------------- audio: VO + pop SFX
SR = 48000
def pop_sound():
    d = 0.16
    t = np.arange(int(SR * d)) / SR
    f = 95 + 210 * np.exp(-t * 38)                          # pitch drop "pam"
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 26)
    click = np.random.default_rng(1).normal(0, 1, t.size) * np.exp(-t * 400) * 0.25
    s = body + click
    s[: int(SR * 0.002)] *= np.linspace(0, 1, int(SR * 0.002))
    return (s / np.max(np.abs(s))).astype(np.float32)

pop = pop_sound()
track = np.zeros(int(SR * (TOTAL + 0.5)), np.float32)
for pt in POPS:
    i = int((pt - 0.01) * SR)
    track[i:i + pop.size] += pop * 0.30
sfx = os.path.join(WORK, "sfx.wav")
pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
import wave
with wave.open(sfx, "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", os.path.join(RAW, "vo.mov"), "-i", sfx,
                "-filter_complex",
                "[1:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
                "loudnorm=I=-14:TP=-1.5:LRA=9,apad[vo];"
                "[2:a]aresample=48000,volume=0.9[fx];"
                "[vo][fx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95,"
                f"atrim=0:{TOTAL},afade=t=out:st={TOTAL - 0.25}:d=0.25[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, "pops:", len(POPS))
