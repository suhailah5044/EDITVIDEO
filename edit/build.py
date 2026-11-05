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
_HERE = os.path.dirname(os.path.abspath(__file__))
F_BOLD = os.path.join(_HERE, "fonts", "Montserrat-BlackItalic.ttf")   # bold italic title style (as in the reference)
F_MATH = F_BOLD
F_NUM = F_BOLD
WHITE = (255, 255, 255)
YELLOW = (255, 212, 0)

# ---------------------------------------------------------------- timeline
# (t_start, t_end, source, src_in, src_out, opts)
# play_dur: if set, the source span plays over this many seconds then the last frame holds.
# qr: blur any QR code found in the footage.
# "TUT" segments: frozen Latihan 2 page (IMG_1551 @ PAGE_T) with the tutorial working pasted into the empty box.
PAGE_T = 3.60
SEGS = [
    (0.00, 1.82, "IMG_1551.MOV", 1.30, 3.12, {"qr": True}),          # hook: Set Latihan 2
    (1.82, 5.12, "IMG_1543.MOV", 0.00, 3.30, {"qr": True}),          # soalan close-up
    (5.12, 7.64, "IMG_1544.MOV", 0.40, 2.92, {"qr": True}),
    (7.64, 14.10, "TUT", 0, 0, {"clips": [                             # follows the VO script only
        (7.64, 9.90, 80.0, 108.0, None),        # samakan penyebut, darab 3t -> 12st, 9t
        (9.90, 12.80, 108.0, 142.0, None),      # teruskan langkah -> 9t - 4 - 3t
        (12.80, 14.10, 162.0, 168.8, 0.55),     # jawapan paling ringkas -> (6t - 4)/12st
    ], "panel_out": 13.02}),
    (14.10, 15.02, "IMG_1542.MOV", 0.00, 0.92, {"qr": True}),        # nampak susah kan
    (15.02, 17.50, "IMG_1547.MOV", 0.00, 2.48, {"qr": True}),        # pecahan algebra
    (17.50, 19.70, "IMG_1552.MOV", 2.20, 4.40, {"qr": True}),        # stuck / keliru
    (19.70, 21.84, "IMG_1549.MOV", 0.00, 1.73, {}),                  # buku Kuasai Algebra
    (21.84, 26.36, "IMG_1546.MOV", 0.00, 4.43, {"qr": True}),        # nota ringkas, contoh, latihan
    (26.36, 28.82, "IMG_1548.MOV", 0.90, 3.36, {"qr": True}),        # QR code (blurred)
    (28.82, 30.92, "TUT", 0, 0, {"clips": [(28.82, 30.92, 168.8, 84.0, None)]}),  # boleh ulang tengok (rewind)
    (30.92, 32.94, "IMG_1545.MOV", 0.00, 4.04, {"qr": True}),        # Form 1 - Form 5
    (32.94, 34.40, "IMG_1552.MOV", 0.00, 1.46, {"qr": True}),
    (34.40, TOTAL, "IMG_1549.MOV", 0.00, 1.73, {"play_dur": 1.73}),  # CTA cover
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
    # text goes into empty space so it never covers the book content
    (0.60, 1.78, 960, [[T(0.60, "Set Latihan "), T(0.95, "2", YELLOW)]]),
    (2.70, 7.58, 1150, [[T(2.70, "Permudahkan")],
                        [FR(3.40, "3", "4s", YELLOW, 54), T(4.62, "  \u2212  ", YELLOW, 56), FR(4.76, "4 + 3t", "12st", YELLOW, 54)]]),
    (8.18, 9.86, 800, [[T(8.18, "Samakan penyebut", WHITE, 54), T(9.14, "  darab 3t", YELLOW, 54)]]),
    (10.98, 12.76, 800, [[T(10.98, "Teruskan pengiraan", WHITE, 54)]]),
    (13.02, 14.06, 1290, [[T(13.02, "Jawapan paling ringkas", WHITE, 64)],
                          [FR(13.22, "6t \u2212 4", "12st", YELLOW, 128)]]),
    (14.12, 14.98, 1000, [[T(14.12, "Nampak "), T(14.44, "susah", YELLOW), T(14.80, " kan?")]]),
    (15.40, 17.12, 250, [[T(15.40, "Pecahan Algebra", YELLOW)]]),
    (17.22, 19.62, 300, [[T(17.22, "Selalu "), T(17.40, "stuck?", YELLOW)]]),
    (23.12, 26.30, 300, [[T(23.12, "Nota ringkas", WHITE, 46), T(23.58, "  \u2022  Contoh", WHITE, 46),
                          T(24.24, "  \u2022  Latihan", YELLOW, 46)]]),
    (27.12, 28.78, 950, [[T(27.12, "Scan QR", YELLOW)], [T(28.14, "Video tutorial", WHITE, 54)]]),
    (29.82, 30.88, 800, [[T(29.82, "Boleh ulang tengok", WHITE, 54)]]),
    (31.16, 32.90, 300, [[T(31.16, "Sesuai untuk", WHITE, 54)], [T(31.52, "Form 1 \u2013 Form 5", YELLOW)]]),
    (33.40, 35.10, 250, [[T(33.40, "Nak anak "), T(33.86, "lebih faham?", YELLOW)]]),
    (35.18, TOTAL, 250, [[T(35.18, "Check "), T(35.34, "beg kuning", YELLOW), T(35.60, " sekarang!")]]),
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
    pad = 24 + size // 6
    w, h = bb[2] - bb[0] + 2 * pad, int(size * 1.35) + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bb[0], pad), s, font=f, fill=color + (255,), stroke_width=max(4, size // 9), stroke_fill=(12, 12, 12, 255))
    return img

def math_text(d, x, y, s, f, color):
    """draw a math string: letters italic, digits/operators upright. returns width."""
    cx = x
    for ch in s:
        ff = f[1] if ch.isalpha() else f[0]
        d.text((cx, y), ch, font=ff, fill=color + (255,), stroke_width=max(4, f[0].size // 9), stroke_fill=(12, 12, 12, 255))
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

# ---------------------------------------------------------------- footage look
# slightly darker top band + edge vignette so the white/yellow text stays readable (no box)
def top_shade():
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(-1, 1, W)[None, :]
    a = np.clip(1 - yy / 0.42, 0, 1) ** 1.5 * 0.40
    vig = np.clip((np.sqrt(xx ** 2 * 0.6 + ((yy - 0.5) * 2) ** 2 * 0.5) - 0.55) / 0.6, 0, 1) * 0.30
    a = np.maximum(a, vig)
    return (1 - a)[..., None].astype(np.float32)
SHADE = top_shade()

GRADE = "eq=brightness=0.035:contrast=1.03:saturation=1.04,unsharp=5:5:0.35"

def read_frames(cmd, fw, fh, n):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = fw * fh * 3
    out = []
    while len(out) < n:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        out.append(np.frombuffer(buf, np.uint8).reshape(fh, fw, 3))
    p.stdout.close(); p.wait()
    return out

def decode_footage(src, a, b, play_frames):
    speed = (b - a) / (play_frames / FPS)
    vf = f"setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS},scale={SW}:{SH}:flags=lanczos,{GRADE}"
    cmd = ["ffmpeg", "-v", "quiet", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", os.path.join(RAW, src),
           "-vf", vf, "-frames:v", str(play_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return read_frames(cmd, SW, SH, play_frames)

# ---------------------------------------------------------------- QR hiding
import cv2
_qr = cv2.QRCodeDetectorAruco()

def detect_qr(fr):
    g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
    polys = []
    try:
        ok, pts = _qr.detectMulti(g)
        if ok and pts is not None:
            polys = [p.astype(np.float32).reshape(4, 2) for p in pts]
    except cv2.error:
        pass
    if not polys:
        ok, pts = cv2.QRCodeDetector().detect(g)
        if ok and pts is not None:
            polys = [pts.astype(np.float32).reshape(4, 2)]
    # sanity: plausible size
    return [p for p in polys if 40 < cv2.contourArea(p) ** 0.5 < 900]

def flow_polys(prev, cur, polys):
    """move polygons from frame prev to frame cur with sparse optical flow."""
    if not polys:
        return []
    g0 = cv2.cvtColor(prev, cv2.COLOR_RGB2GRAY)
    g1 = cv2.cvtColor(cur, cv2.COLOR_RGB2GRAY)
    out = []
    for p in polys:
        c = p.mean(0)
        big = (p - c) * 2.2 + c
        m = np.zeros(g0.shape, np.uint8)
        cv2.fillConvexPoly(m, big.astype(np.int32), 255)
        f0 = cv2.goodFeaturesToTrack(g0, 200, 0.01, 6, mask=m)
        if f0 is None or len(f0) < 6:
            out.append(p); continue
        f1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, f0, None, winSize=(31, 31), maxLevel=4)
        good = st.ravel() == 1
        if good.sum() < 6:
            out.append(p); continue
        M, _ = cv2.estimateAffinePartial2D(f0[good], f1[good], method=cv2.RANSAC)
        if M is None:
            out.append(p); continue
        out.append((p @ M[:, :2].T + M[:, 2]).astype(np.float32))
    return out

def qr_track(frames, max_gap=45):
    n = len(frames)
    det = [detect_qr(f) for f in frames]
    fwd = [None] * n; bwd = [None] * n
    cur, age = [], 0
    for i in range(n):
        if det[i]:
            cur, age = det[i], 0
        elif cur and age < max_gap:
            cur = flow_polys(frames[i - 1], frames[i], cur); age += 1
        else:
            cur = []
        fwd[i] = cur
    cur, age = [], 0
    for i in range(n - 1, -1, -1):
        if det[i]:
            cur, age = det[i], 0
        elif cur and age < max_gap:
            cur = flow_polys(frames[i + 1], frames[i], cur); age += 1
        else:
            cur = []
        bwd[i] = cur
    res = []
    for i in range(n):
        res.append(det[i] if det[i] else (fwd[i] + bwd[i]))
    return res, sum(1 for d in det if d)

def hide_qr(fr, polys):
    if not polys:
        return fr
    fr = fr.copy()
    h, w = fr.shape[:2]
    m = np.zeros((h, w), np.uint8)
    for p in polys:
        c = p.mean(0)
        cv2.fillConvexPoly(m, ((p - c) * 1.28 + c).astype(np.int32), 255)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return fr
    x0, x1 = max(0, xs.min() - 40), min(w, xs.max() + 40)
    y0, y1 = max(0, ys.min() - 40), min(h, ys.max() + 40)
    roi = fr[y0:y1, x0:x1]
    rh, rw = roi.shape[:2]
    small = cv2.resize(roi, (max(1, rw // 22), max(1, rh // 22)), interpolation=cv2.INTER_AREA)
    pix = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
    pix = cv2.GaussianBlur(pix, (0, 0), 9)
    mm = cv2.GaussianBlur(m[y0:y1, x0:x1], (0, 0), 6).astype(np.float32)[..., None] / 255.0
    fr[y0:y1, x0:x1] = (roi * (1 - mm) + pix * mm).astype(np.uint8)
    return fr


# QR keyframes per footage segment (key = segment start time), in decoded-frame coords (SW x SH = 1242x2208).
# Each run: [(frame, x0, y0, x1, y1), ...] linearly interpolated between its first and last frame.
QR_KEYS = {
    0.00: [[(0, 380, 1850, 590, 2085), (6, 436, 1900, 649, 2141), (12, 464, 1973, 688, 2197),
            (18, 498, 2085, 721, 2260), (23, 520, 2170, 760, 2300)]],
    1.82: [[(28, 1170, 2100, 1300, 2260), (30, 1150, 2050, 1260, 2230), (42, 1180, 2034, 1250, 2203),
            (48, 1057, 2000, 1250, 2200), (54, 1035, 1967, 1250, 2192), (60, 1024, 1945, 1240, 2170),
            (66, 1024, 1928, 1242, 2170), (72, 946, 1945, 1187, 2180), (78, 924, 1945, 1153, 2192),
            (84, 896, 1955, 1120, 2192), (98, 888, 1960, 1112, 2196)]],
    5.12: [[(0, 0, 1680, 240, 1990), (6, 0, 1725, 230, 2010), (12, 0, 1790, 220, 2095),
            (30, 0, 1820, 190, 2080), (54, 0, 1855, 170, 2110), (75, 0, 1880, 170, 2140)]],
    14.10: [[(0, 403, 1753, 560, 1950), (6, 392, 1736, 549, 1939), (12, 392, 1753, 537, 1950),
             (18, 358, 1770, 526, 1960), (24, 336, 1770, 504, 1975), (27, 336, 1770, 493, 1978)]],
    17.50: [[(0, 20, 1730, 180, 1970), (6, 180, 1760, 345, 2005), (10, 180, 1760, 345, 2005),
             (26, 30, 1760, 210, 2000), (34, 30, 1760, 210, 2000), (50, 20, 1760, 240, 2000),
             (65, 20, 1760, 240, 2000)]],
    26.36: [[(0, 380, 1652, 549, 1838), (6, 380, 1652, 537, 1840), (12, 397, 1652, 565, 1840),
             (18, 403, 1669, 554, 1866), (24, 392, 1680, 526, 1866), (30, 364, 1680, 504, 1866),
             (36, 370, 1669, 520, 1866), (42, 380, 1652, 510, 1840), (48, 358, 1669, 504, 1840),
             (54, 364, 1647, 532, 1815), (60, 370, 1630, 526, 1820), (66, 380, 1630, 537, 1830),
             (73, 370, 1647, 526, 1835)]],
    30.92: [[(0, 616, 1978, 773, 2163), (6, 605, 2017, 762, 2203), (9, 600, 2030, 760, 2220),
             (46, 560, 2017, 725, 2203), (48, 554, 2017, 722, 2203), (54, 459, 1928, 616, 2124),
             (60, 448, 1945, 605, 2152)]],
}

def qr_boxes(t0, n):
    out = [[] for _ in range(n)]
    for run in QR_KEYS.get(t0, []):
        for (fa, *ba), (fb, *bb) in zip(run, run[1:]):
            for f in range(fa, min(fb, n - 1) + 1):
                u = 0 if fb == fa else (f - fa) / (fb - fa)
                out[f] = [[ba[k] + (bb[k] - ba[k]) * u for k in range(4)]]
        f, *b = run[-1]
        if f < n:
            out[f] = [b]
    return out

def hide_boxes(fr, boxes):
    if not boxes:
        return fr
    fr = fr.copy()
    h, w = fr.shape[:2]
    for x0, y0, x1, y1 in boxes:
        cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 1.65, (y1 - y0) * 1.60
        bw = bh = max(bw, bh, 150)
        X0, Y0 = int(max(0, cx - bw / 2 - 30)), int(max(0, cy - bh / 2 - 30))
        X1, Y1 = int(min(w, cx + bw / 2 + 30)), int(min(h, cy + bh / 2 + 30))
        if X1 - X0 < 8 or Y1 - Y0 < 8:
            continue
        roi = fr[Y0:Y1, X0:X1]
        rh, rw = roi.shape[:2]
        m = np.zeros((rh, rw), np.uint8)
        cv2.rectangle(m, (int(cx - bw / 2 - X0), int(cy - bh / 2 - Y0)), (int(cx + bw / 2 - X0), int(cy + bh / 2 - Y0)), 255, -1)
        small = cv2.resize(roi, (max(1, rw // 26), max(1, rh // 26)), interpolation=cv2.INTER_AREA)
        pix = cv2.GaussianBlur(cv2.resize(small, (rw, rh), interpolation=cv2.INTER_LINEAR), (0, 0), 14)
        mm = cv2.GaussianBlur(m, (0, 0), 12).astype(np.float32)[..., None] / 255.0
        fr[Y0:Y1, X0:X1] = (roi * (1 - mm) + pix * mm).astype(np.uint8)
    return fr

# ---------------------------------------------------------------- tutorial pasted on the page
# only the working area of the tutorial (not the whole screen) -> follows the script, not too detailed
SCR_CROP = (458, 58, 446, 396)      # x, y, w, h inside the 986x654 screen recording
PANEL_W = 900
PANEL_H = int(PANEL_W * SCR_CROP[3] / SCR_CROP[2]) // 2 * 2
PANEL_CX, PANEL_CY = 540, 1300       # inside the empty answer box under the question
TUT_TEXT_Y = 835                     # text sits in the empty space between question and the pasted video

PAGE_POLY = [(0, 272), (1036, 288), (1079, 439), (1079, 1567), (1015, 1919), (0, 1919)]
PAGE_MASK = Image.new("L", (W, H), 0)
ImageDraw.Draw(PAGE_MASK).polygon(PAGE_POLY, fill=255)
PAGE_MASK = PAGE_MASK.filter(ImageFilter.GaussianBlur(2))

def math_bg(extra=260):
    """near-black background with scattered + - x / = symbols (taller than the frame so it can drift)."""
    rng = random.Random(11)
    h = H + extra
    yy = np.linspace(0, 1, h)[:, None]; xx = np.linspace(-1, 1, W)[None, :]
    r = np.sqrt(xx ** 2 * 0.5 + ((yy - 0.3) * 1.6) ** 2)
    k = np.clip(r, 0, 1)[..., None]
    arr = np.array([20, 22, 30], np.float32) * (1 - k) + np.array([4, 5, 8], np.float32) * k
    img = Image.fromarray(np.repeat(arr, W, axis=1).astype(np.uint8) if arr.shape[1] == 1 else arr.astype(np.uint8)).convert("RGBA")
    syms = ["+", "\u2212", "\u00d7", "\u00f7", "=", "+", "\u00f7", "\u00d7", "x\u00b2", "\u221a", "%"]
    layer = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    placed = []
    tries = 0
    while len(placed) < 60 and tries < 6000:
        tries += 1
        x, y = rng.randint(10, W - 60), rng.randint(10, h - 60)
        if any((x - px) ** 2 + (y - py) ** 2 < 120 ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        sym = rng.choice(syms)
        sz = rng.randint(44, 96)
        col = (255, 212, 0, rng.randint(55, 95)) if rng.random() < 0.3 else (255, 255, 255, rng.randint(35, 70))
        tile = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((50, 30), sym, font=font(F_BOLD, sz), fill=col)
        tile = tile.rotate(rng.uniform(-25, 25), resample=Image.BICUBIC)
        layer.alpha_composite(tile, (x - 50, y - 60))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))
    return img

import sys as _s; _s.path.insert(0, _HERE)
from algebra_bg import make_bg
MATH_BG = make_bg(extra_h=260)

def page_with_bg(page, t):
    off = int((t * 40) % 250)
    bg = MATH_BG.crop((0, off, W, off + H))
    out = bg.copy()
    out.paste(page, (0, 0), PAGE_MASK)
    return out

def page_still():
    cmd = ["ffmpeg", "-v", "quiet", "-ss", f"{PAGE_T}", "-i", os.path.join(RAW, "IMG_1551.MOV"),
           "-vf", f"scale={W}:{H}:flags=lanczos,{GRADE}", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return read_frames(cmd, W, H, 1)[0]

def decode_screen(a, b, play_frames):
    rev = b < a
    lo, hi = (b, a) if rev else (a, b)
    speed = (hi - lo) / (play_frames / FPS)
    x, y, w, h = SCR_CROP
    vf = f"crop={w}:{h}:{x}:{y},setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS},scale={PANEL_W}:{PANEL_H}:flags=lanczos," \
         f"eq=contrast=1.05:saturation=1.0"
    if rev:
        vf += ",reverse"
    cmd = ["ffmpeg", "-v", "quiet", "-ss", f"{lo:.3f}", "-t", f"{hi - lo + 0.1:.3f}", "-i", os.path.join(RAW, "screen.mp4"),
           "-vf", vf, "-frames:v", str(play_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return read_frames(cmd, PANEL_W, PANEL_H, play_frames)

PANEL_MASK = Image.new("L", (PANEL_W, PANEL_H), 0)
ImageDraw.Draw(PANEL_MASK).rounded_rectangle([0, 0, PANEL_W - 1, PANEL_H - 1], radius=22, fill=255)

def ease_back(u, k=3.2):
    u = min(max(u, 0.0), 1.0)
    v = u - 1
    return 1 + (k + 1) * v ** 3 + k * v ** 2

def paste_panel(page_img, arr, t_loc, t_out=None):
    """t_loc: time since panel entered; t_out: seconds until panel exits (None = stays)."""
    frame = page_img.copy()
    u = t_loc / 0.32
    s = 0.15 + 0.85 * ease_back(u)
    rot = -7.0 * max(0.0, 1 - u) ** 2
    alpha = min(1.0, t_loc / 0.06)
    if t_out is not None and t_out < 0.20:
        v = max(0.0, t_out / 0.20)
        s *= 0.35 + 0.65 * v
        alpha *= v
    if alpha <= 0.01:
        return frame
    panel = Image.fromarray(arr).convert("RGBA")
    panel.putalpha(PANEL_MASK)
    # thin white border like a pasted card
    card = Image.new("RGBA", (PANEL_W + 16, PANEL_H + 16), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, PANEL_W + 15, PANEL_H + 15], radius=30, fill=(255, 255, 255, 255))
    card.alpha_composite(panel, (8, 8))
    pw, ph = max(2, int(card.width * s)), max(2, int(card.height * s))
    card = card.resize((pw, ph), Image.BILINEAR)
    if abs(rot) > 0.05:
        card = card.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a_ = np.asarray(card.getchannel("A"), np.float32) * alpha
        card.putalpha(Image.fromarray(a_.astype(np.uint8)))
    sh = Image.new("L", (card.width + 120, card.height + 120), 0)
    ImageDraw.Draw(sh).rounded_rectangle([60, 78, card.width + 60, card.height + 78], radius=30, fill=int(150 * alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    blk = Image.new("RGBA", sh.size, (0, 0, 0, 255)); blk.putalpha(sh)
    x0, y0 = int(PANEL_CX - card.width / 2), int(PANEL_CY - card.height / 2)
    frame.alpha_composite(blk, (x0 - 60, y0 - 60))
    # impact flash ring just after the pop lands
    if 0.12 < t_loc < 0.45:
        k = (t_loc - 0.12) / 0.33
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rr = int(max(pw, ph) * (0.55 + 0.35 * k))
        ImageDraw.Draw(ring).rounded_rectangle([PANEL_CX - rr, PANEL_CY - rr * ph // pw, PANEL_CX + rr, PANEL_CY + rr * ph // pw],
                                               radius=40, outline=(255, 230, 120, int(200 * (1 - k))), width=10)
        frame.alpha_composite(ring.filter(ImageFilter.GaussianBlur(3)))
    frame.alpha_composite(card, (x0, y0))
    return frame

def zoom_frame(img, z):
    if z <= 1.0001:
        return img
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) / 2
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

def compose_footage(arr, t_loc, dur, punch):
    z = 1.0 + 0.045 * (t_loc / max(dur, 0.01))          # slow push-in
    if punch:
        z += 0.07 * max(0.0, 1 - t_loc / 0.22) ** 2      # quick punch on cut
    z = min(z, SRC_SCALE)
    cw = W * SRC_SCALE / z
    ch = H * SRC_SCALE / z
    x0 = (SW - cw) / 2
    y0 = (SH - ch) / 2
    im = Image.fromarray(arr).resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    return im.convert("RGBA")

# ---------------------------------------------------------------- render video
silent = os.path.join(WORK, "video_noaudio.mp4")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-profile:v", "high",
                        "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
PAGE = None
QR_DEBUG = []
for (t0, t1, src, a, b, opt) in SEGS:
    f0, f1 = round(t0 * FPS), round(t1 * FPS)
    n = f1 - f0
    if src == "TUT":
        if PAGE is None:
            pg = np.asarray(page_still(), np.float32)
            PAGE = Image.fromarray(pg.astype(np.uint8)).convert("RGBA")
        frames = []
        first = True
        for (c0, c1, sa, sb, play_dur) in opt["clips"]:
            cn = round(c1 * FPS) - round(c0 * FPS)
            play = round((play_dur or (c1 - c0)) * FPS)
            fr = decode_screen(sa, sb, play)
            fr = fr + [fr[-1]] * (cn - len(fr))
            frames += [(x, first and k == 0) for k, x in enumerate(fr[:cn])]
            first = False
        print(f"{t0:6.2f}-{t1:6.2f} TUT frames={n}/{len(frames)}", flush=True)
        t_exit = opt.get("panel_out")
        for i in range(n):
            arr = frames[min(i, len(frames) - 1)][0]
            t = (f0 + i) / FPS
            frame = paste_panel(page_with_bg(PAGE, t), arr, i / FPS, None if t_exit is None else t_exit - t)
            # page stays completely still (no zoom, no shake)
            draw_overlays(frame, t)
            enc.stdin.write(frame.convert("RGB").tobytes())
        continue
    play = round(opt.get("play_dur", t1 - t0) * FPS)
    frames = decode_footage(src, a, b, play)
    frames = frames + [frames[-1]] * (n - len(frames))
    frames = frames[:n]
    if t0 in QR_KEYS:
        bx = qr_boxes(t0, n)
        frames = [hide_boxes(f, b) for f, b in zip(frames, bx)]
    print(f"{t0:6.2f}-{t1:6.2f} {src} [{a}-{b}] frames={n} speed={(b - a) / (play / FPS):.2f}", flush=True)
    for i, arr in enumerate(frames):
        t = (f0 + i) / FPS
        frame = compose_footage(arr, i / FPS, t1 - t0, not opt.get("nopunch"))
        draw_overlays(frame, t)
        enc.stdin.write(frame.convert("RGB").tobytes())
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

def whoosh_sound(d=0.38):
    rng = np.random.default_rng(3)
    n = int(SR * d)
    noise = rng.normal(0, 1, n).astype(np.float32)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    # sweep a simple resonant band-pass from low to high
    f = 300 + 3200 * (t / d) ** 1.5
    y1 = y2 = 0.0
    for i in range(n):
        w0 = 2 * np.pi * f[i] / SR
        alpha = np.sin(w0) / (2 * 2.5)
        b0, a0, a1, a2 = alpha, 1 + alpha, -2 * np.cos(w0), 1 - alpha
        x = noise[i]
        y = (b0 * x - b0 * (noise[i - 2] if i > 1 else 0) - a1 * y1 - a2 * y2) / a0
        y2, y1 = y1, y
        out[i] = y
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    out *= env
    return (out / np.max(np.abs(out))).astype(np.float32)

def impact_sound(d=0.55):
    t = np.arange(int(SR * d)) / SR
    f = 48 + 110 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    hit = np.random.default_rng(5).normal(0, 1, t.size) * np.exp(-t * 60) * 0.5
    s_ = boom + hit
    return (s_ / np.max(np.abs(s_))).astype(np.float32)

def ting_sound(d=0.55):
    t = np.arange(int(SR * d)) / SR
    s_ = (np.sin(2 * np.pi * 1760 * t) * 1.0 + np.sin(2 * np.pi * 2640 * t) * 0.45
          + np.sin(2 * np.pi * 4410 * t) * 0.25 * np.exp(-t * 18)) * np.exp(-t * 9)
    a = int(SR * 0.003)
    s_[:a] *= np.linspace(0, 1, a)
    return (s_ / np.max(np.abs(s_))).astype(np.float32)

pop = ting_sound()
whoosh = whoosh_sound()
impact = impact_sound()
track = np.zeros(int(SR * (TOTAL + 1.0)), np.float32)
def put(snd, t, g):
    i = max(0, int(t * SR))
    track[i:i + snd.size] += snd[: max(0, track.size - i)] * g
for pt in POPS:
    put(pop, pt - 0.005, 0.22)
CUTS = [sg[0] for sg in SEGS[1:]]
for c in CUTS:
    put(whoosh, c - 0.24, 0.20)
for sg in SEGS:
    if sg[2] == "TUT":
        put(impact, sg[0] + 0.20, 0.45)        # panel lands
    if sg[2] == "TUT" and sg[5].get("panel_out"):
        put(impact, sg[5]["panel_out"] + 0.18, 0.40)   # big answer lands
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
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT, "pops:", len(POPS))
