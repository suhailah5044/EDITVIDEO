"""Edit 'Transisi Tahun 1' — white-box captions, zoom punches, SFX on cuts.

Usage: python3 render.py RAW.mov OUT.mp4 [--still T]
"""
import math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 48000
FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_MAIN = ImageFont.truetype(FONT_DIR + "InterDisplay-ExtraBold.otf", 52)
F_LABEL = ImageFont.truetype(FONT_DIR + "InterDisplay-Bold.otf", 26)
F_CHIP = ImageFont.truetype(FONT_DIR + "InterDisplay-ExtraBold.otf", 44)

INK = (20, 20, 24, 255)
YELLOW = (255, 199, 0, 255)
WHITE = (255, 255, 255, 255)

# Footage cuts already in the raw (scene detection) — get whoosh + zoom punch.
CUTS = [3.867, 5.867, 7.267, 8.733, 10.3, 17.967, 21.567, 25.467, 35.167]
# Extra "jump zoom" punches inside long talking shots: (start, end, zoom)
PUNCH = [(14.10, 17.967, 1.10), (28.74, 33.10, 1.06)]

# Caption cards. Text in [brackets] gets the yellow marker highlight.
CARDS = [
    dict(t0=0.05, t1=3.80, label="IBU AYAH, BACA NI!", text="Anak 6 tahun, tahun depan masuk [Tahun 1?]"),
    dict(t0=3.90, t1=6.30, label="TIPS", text="Buat persediaan [dari sekarang]"),
    dict(t0=6.42, t1=10.15, label="MODUL TRANSISI TAHUN 1", text="Bantu anak [praktis] di rumah"),
    dict(t0=10.30, t1=13.95, label=None, text="Anak perlukan masa & [bimbingan]"),
    dict(t0=14.10, t1=17.85, label=None, text="Luangkan masa, buat [sama-sama]"),
    dict(t0=17.94, t1=21.40, label="SIAP DENGAN", text="[Video Tutorial] + [Jawapan]", ding=True),
    dict(t0=21.52, t1=25.22, label=None, text="[Bukan sekadar] buku latihan"),
    dict(t0=25.28, t1=28.62, label="PERSEDIAAN AWAL", text="Tahu tahap [kemahiran asas] anak"),
    dict(t0=28.74, t1=33.02, label="KEMAHIRAN ASAS",
         chips=[("Membaca", 29.04), ("Menulis", 29.96), ("Mengira", 30.52)]),
    dict(t0=33.12, t1=35.05, label=None, text="[Tak perlu tunggu] sekolah bermula"),
    dict(t0=35.16, t1=40.80, label="DAPATKAN SEKARANG", text="Tekan [beg kuning] di bawah", cta=True, ding=True),
]
CARD_Y = 250  # top of card (keeps clear of face / product)
MAX_W = 860


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2

def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- card art
def parse(text):
    toks, hl = [], False
    for part in text.replace("[", "\x00[").replace("]", "]\x00").split("\x00"):
        if not part:
            continue
        on = part.startswith("[")
        for w in part.strip("[]").split():
            toks.append((w, on))
    return toks

def layout(toks):
    space = F_MAIN.getlength(" ")
    lines, cur, cw = [], [], 0
    for w, h in toks:
        ww = F_MAIN.getlength(w) + (18 if h else 0)
        add = ww + (space if cur else 0)
        if cur and cw + add > MAX_W - 80:
            lines.append((cur, cw)); cur, cw = [], 0; add = ww
        cur.append((w, h, ww)); cw += add
    if cur:
        lines.append((cur, cw))
    return lines, space

def build_card(card):
    """Returns RGBA image of the static card + anchor info."""
    pad_x, pad_y, lh = 44, 30, 66
    label_h = 44 if card.get("label") else 0
    if card.get("chips"):
        chip_w = [F_CHIP.getlength(c) + 56 for c, _ in card["chips"]]
        inner_w = sum(chip_w) + 18 * (len(chip_w) - 1) + 20
        body_h = 78
        lines = None
    else:
        lines, space = layout(parse(card["text"]))
        inner_w = max(w for _, w in lines)
        body_h = lh * len(lines)
    if card.get("label"):
        inner_w = max(inner_w, F_LABEL.getlength(card["label"]) + 40)
    cw = int(min(MAX_W + 40, inner_w + 2 * pad_x))
    ch = int(pad_y * 2 + label_h + (14 if label_h else 0) + body_h)
    sh = 30  # shadow margin
    img = Image.new("RGBA", (cw + 2 * sh, ch + 2 * sh), (0, 0, 0, 0))
    # soft shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((sh, sh + 8, sh + cw, sh + ch + 8), 30, fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((sh, sh, sh + cw, sh + ch), 30, fill=WHITE)
    y = sh + pad_y
    if card.get("label"):
        lw = F_LABEL.getlength(card["label"]) + 36
        lx = sh + (cw - lw) / 2
        d.rounded_rectangle((lx, y, lx + lw, y + label_h), label_h // 2, fill=INK)
        d.text((lx + lw / 2, y + label_h / 2 + 1), card["label"], font=F_LABEL, fill=YELLOW, anchor="mm")
        y += label_h + 14
    chip_boxes = []
    if lines:
        for words, lw_ in lines:
            x = sh + (cw - lw_) / 2
            for i, (w, h, ww) in enumerate(words):
                if h:
                    nxt = i + 1 < len(words) and words[i + 1][1]
                    d.rounded_rectangle((x, y + 6, x + ww + (space + 12 if nxt else 0), y + lh - 4), 10, fill=YELLOW)
                d.text((x + (9 if h else 0), y + lh / 2 + 1), w, font=F_MAIN, fill=INK, anchor="lm")
                x += ww + space
            y += lh
    else:
        x = sh + (cw - inner_w) / 2
        for (c, _), w_ in zip(card["chips"], chip_w):
            chip_boxes.append((int(x), int(y), int(x + w_), int(y + body_h), c))
            x += w_ + 18
    return img, chip_boxes

def chip_img(text, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=YELLOW)
    d.text((w / 2, h / 2 + 1), text, font=F_CHIP, fill=INK, anchor="mm")
    return im

def arrow_img():
    im = Image.new("RGBA", (120, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((44, 0, 76, 80), 14, fill=YELLOW, outline=INK, width=4)
    d.polygon([(10, 70), (110, 70), (60, 136)], fill=YELLOW, outline=INK)
    d.line([(10, 70), (60, 136), (110, 70)], fill=INK, width=4)
    return im

for c in CARDS:
    c["img"], c["chips_xy"] = build_card(c)
    if c.get("chips"):
        c["chip_imgs"] = [chip_img(t, x1 - x0, y1 - y0) for x0, y0, x1, y1, t in c["chips_xy"]]
ARROW = arrow_img()


def scaled(im, s, alpha):
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    return im


def draw_overlays(frame, t):
    for c in CARDS:
        if not (c["t0"] <= t < c["t1"] + 0.2):
            continue
        k_in = clamp((t - c["t0"]) / 0.32)
        k_out = clamp((t - c["t1"]) / 0.18)
        s = 0.7 + 0.3 * ease_out_back(k_in)
        s *= 1 - 0.08 * k_out
        if c.get("cta") and k_in >= 1:
            s *= 1 + 0.025 * math.sin((t - c["t0"]) * 2 * math.pi * 1.6)
        alpha = clamp(k_in * 2.5) * (1 - k_out)
        if alpha <= 0:
            continue
        base = c["img"]
        if c.get("chips"):
            base = base.copy()
            for (x0, y0, x1, y1, _), (_, tc), ci in zip(c["chips_xy"], c["chips"], c["chip_imgs"]):
                kc = clamp((t - tc) / 0.25)
                if kc <= 0:
                    continue
                cs = 0.5 + 0.5 * ease_out_back(kc, 2.4)
                im = scaled(ci, cs, clamp(kc * 3))
                base.alpha_composite(im, (int((x0 + x1) / 2 - im.width / 2), int((y0 + y1) / 2 - im.height / 2)))
        im = scaled(base, s, alpha)
        cx, cy = W // 2, CARD_Y + c["img"].height // 2
        frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
        if c.get("cta"):
            ka = clamp((t - c["t0"] - 0.35) / 0.3)
            if ka > 0:
                bob = 18 * abs(math.sin((t - c["t0"]) * math.pi * 2.2))
                a = scaled(ARROW, 0.9, ka * (1 - k_out))
                frame.alpha_composite(a, (W // 2 - a.width // 2, int(CARD_Y + c["img"].height - 10 + bob)))


# ---------------------------------------------------------------- camera
SHOTS = [0.0] + CUTS + [99.0]

def zoom_at(t):
    i = max(j for j in range(len(SHOTS) - 1) if SHOTS[j] <= t)
    s0, s1 = SHOTS[i], SHOTS[i + 1]
    z = 1.0 + 0.035 * clamp((t - s0) / max(0.1, min(s1, 40.8) - s0))  # slow push-in
    if i > 0:  # punch on cut: start tight, settle
        k = clamp((t - s0) / 0.35)
        z += 0.07 * (1 - ease_out_cubic(k))
    for a, b, pz in PUNCH:
        if a <= t < b:
            z *= pz
    return z

def flash_at(t):
    v = 0.0
    for c in CUTS:
        if 0 <= t - c < 0.1:
            v = max(v, 0.22 * (1 - (t - c) / 0.1))
    return v


# ---------------------------------------------------------------- audio
def sfx_track(dur):
    n = int(dur * SR) + SR
    out = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)

    def put(sig, t):
        i = int(t * SR)
        j = min(n, i + len(sig))
        if i < n:
            out[max(0, i):j] += sig[max(0, -i): j - i]

    def whoosh(L=0.42):
        m = int(L * SR)
        noise = rng.standard_normal(m).astype(np.float32)
        tt = np.linspace(0, 1, m)
        # sweeping one-pole lowpass
        y = np.zeros(m, np.float32); acc = 0.0
        cut = 0.02 + 0.25 * np.sin(np.pi * tt) ** 2
        for k in range(m):
            acc += cut[k] * (noise[k] - acc); y[k] = acc
        env = np.sin(np.pi * tt) ** 2.2
        y = y * env
        return 0.32 * y / (np.abs(y).max() + 1e-9)

    def pop():
        m = int(0.09 * SR); tt = np.arange(m) / SR
        f = 950 * np.exp(-tt * 18) + 380
        ph = 2 * np.pi * np.cumsum(f) / SR
        return (0.22 * np.sin(ph) * np.exp(-tt * 38)).astype(np.float32)

    def ding():
        m = int(0.9 * SR); tt = np.arange(m) / SR
        s = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d)
                for f, a, d in [(1568, 1, 5), (3136, .35, 8), (2350, .2, 7), (4700, .1, 12)])
        return (0.16 * s * np.minimum(1, tt / 0.004)).astype(np.float32)

    def tick():
        m = int(0.05 * SR); tt = np.arange(m) / SR
        return (0.18 * np.sin(2 * np.pi * 1700 * tt) * np.exp(-tt * 70)).astype(np.float32)

    for c in CUTS:
        put(whoosh(), c - 0.24)
    for c in CARDS:
        put(pop(), c["t0"])
        if c.get("ding"):
            put(ding(), c["t0"] + 0.05)
        for _, tc in c.get("chips", []):
            put(tick(), tc)
    return out


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- main
GRADE = "null"  # footage kept original

def process(frame_arr, t):
    img = Image.fromarray(frame_arr, "RGB")
    rgba = img.convert("RGBA")
    draw_overlays(rgba, t)
    return rgba.convert("RGB")


def main():
    raw, out = sys.argv[1], sys.argv[2]
    if "--still" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--still") + 1].split(",")]
        for t in times:
            buf = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", raw, "-vf", GRADE,
                                  "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 capture_output=True, check=True).stdout
            process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), t).save(f"{out}_{t:05.2f}.jpg", quality=88)
        return
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", raw]).decode())
    sfx_wav = out + ".sfx.wav"
    write_wav(sfx_wav, sfx_track(dur))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", raw, "-vf", GRADE + f",fps={FPS}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    afilt = ("[0:a]aresample=48000[v];"
             "[2:a]volume=0.9,aresample=48000[s];"
             "[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", raw, "-i", sfx_wav,
                            "-filter_complex", afilt.replace("[0:a]", "[1:a]"),
                            "-map", "0:v", "-map", "[a]",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-movflags", "+faststart",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    fsz = W * H * 3
    i = 0
    while True:
        b = dec.stdout.read(fsz)
        if len(b) < fsz:
            break
        enc.stdin.write(process(np.frombuffer(b, np.uint8).reshape(H, W, 3), i / FPS).tobytes())
        i += 1
        if i % 150 == 0:
            print(f"{i/FPS:.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("done", out)


if __name__ == "__main__":
    main()
