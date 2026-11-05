"""Edit 'Transisi Tahun 1': captions + floating ABC/Jawi/123 doodles + kid-style SFX.

Footage colours are never touched: the overlay is composited onto the original
HLG HDR video. Usage: python3 render.py RAW.mov OUT_PREFIX
"""
import math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 48000
FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_MAIN = ImageFont.truetype(FONT_DIR + "InterDisplay-Black.otf", 50)
F_LABEL = ImageFont.truetype(FONT_DIR + "InterDisplay-Bold.otf", 24)

INK = (20, 20, 24, 255)
YELLOW = (255, 199, 0, 255)
WHITE = (255, 255, 255, 255)

# Footage cuts already in the raw (scene detection): whoosh on each.
CUTS = [3.867, 5.867, 7.267, 8.733, 10.3, 17.967, 21.567, 25.467, 35.167]

# Captions. Words in [brackets] are yellow (and wiggle after landing).
CARDS = [
    dict(t0=0.05, t1=3.80, label="IBU AYAH, BACA NI!", text="Anak 6 tahun, tahun depan | masuk [Tahun~1?]"),
    dict(t0=3.90, t1=6.30, label="TIPS", text="Buat persediaan [dari sekarang]"),
    dict(t0=6.42, t1=10.15, label="MODUL TRANSISI TAHUN 1", text="Bantu anak [praktis] di rumah"),
    dict(t0=10.30, t1=13.95, label=None, text="Anak perlukan masa & [bimbingan]"),
    dict(t0=14.10, t1=17.85, label=None, text="Luangkan masa, buat [sama-sama]"),
    dict(t0=17.94, t1=21.40, label="SIAP DENGAN", text="[Video Tutorial] + [Jawapan]", twinkle=True),
    dict(t0=21.52, t1=25.22, label=None, text="[Bukan sekadar] buku latihan"),
    dict(t0=25.28, t1=28.62, label="PERSEDIAAN AWAL", text="Tahu tahap [kemahiran asas] anak"),
    dict(t0=28.74, t1=33.02, label="KEMAHIRAN ASAS",
         text="[Membaca] [Menulis] [Mengira]", word_times=[29.04, 29.96, 30.52]),
    dict(t0=33.12, t1=35.05, label=None, text="[Tak perlu tunggu] sekolah bermula"),
    dict(t0=35.16, t1=40.80, label="DAPATKAN SEKARANG", text="Tekan [beg kuning] di bawah", cta=True, twinkle=True),
]
# Everything sits above the head: in the talking shots the head starts ~y=250.
LABEL_Y = 148      # centre of the small label line
LINE1_Y = 200      # centre of first caption line (single-line captions end ~y=190)
LINE_H = 60
MAX_W = 1000
WORD_STAGGER = 0.055
WORD_IN = 0.40


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2

def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- caption sprites
def text_sprite(txt, font, fill, stroke=4):
    l, t, r, b = font.getbbox(txt, stroke_width=stroke)
    pad = 24
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), txt, font=font, fill=fill, anchor="mm",
                            stroke_width=stroke, stroke_fill=INK)
    return im

def parse(text):
    toks = []
    for part in text.replace("[", "\x00[").replace("]", "]\x00").split("\x00"):
        if part:
            on = part.startswith("[")
            toks += [(w.replace("~", " "), on) for w in part.strip("[]").split()]
    return toks

def build_card(card):
    space = F_MAIN.getlength(" ") + (14 if card.get("word_times") else 0)
    lines, cur, cw = [], [], 0
    for w, h in parse(card["text"]):
        ww = F_MAIN.getlength(w)
        add = ww + (space if cur else 0)
        if w == "|":
            lines.append((cur, cw)); cur, cw = [], 0
            continue
        if cur and cw + add > MAX_W:
            lines.append((cur, cw)); cur, cw = [], 0; add = ww
        cur.append((w, h, ww)); cw += add
    lines.append((cur, cw))
    words = []
    y = LINE1_Y if card.get("label") else LINE1_Y - 22
    for ln, lw in lines:
        x = (W - lw) / 2
        for w, h, ww in ln:
            words.append(dict(img=text_sprite(w, F_MAIN, YELLOW if h else WHITE), cx=x + ww / 2, cy=y, hl=h))
            x += ww + space
        y += LINE_H
    for i, wd in enumerate(words):
        wd["t"] = (card["word_times"][i] if card.get("word_times")
                   else card["t0"] + 0.08 + WORD_STAGGER * i)
        wd["dir"] = -1 if i % 2 else 1
    card["words"] = words
    card["label_img"] = text_sprite(card["label"], F_LABEL, YELLOW, 4) if card.get("label") else None

for c in CARDS:
    build_card(c)


def scaled(im, s, alpha):
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return im

def put_sprite(frame, im, cx, cy, s=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0.01 or s <= 0.02:
        return
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    im = scaled(im, s, alpha)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------------------------------------------------------- doodles
# Faint ABC / Jawi / numbers floating in the top area, clear of the head.
F_DOODLE_LAT = FONT_DIR + "InterDisplay-Black.otf"
F_DOODLE_JAWI = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DOODLES = [  # (x, y, size, glyph, jawi?, yellow?, base_rot)
    (115, 52, 58, "A", False, False, -12), (330, 40, 52, "ب", True, True, 8),
    (560, 50, 50, "1", False, False, 10), (770, 44, 54, "+", False, True, 0),
    (965, 56, 60, "C", False, False, 14), (60, 290, 60, "ا", True, False, 0),
    (1022, 285, 58, "2", False, True, -10), (55, 420, 56, "a", False, True, 12),
    (1025, 425, 60, "ت", True, False, -8), (62, 560, 54, "3", False, False, 10),
    (1018, 565, 52, "ج", True, True, 6),
]
DOODLE_ALPHA = 0.32

def doodle_img(size, glyph, jawi, yellow):
    f = ImageFont.truetype(F_DOODLE_JAWI, int(size * 1.5)) if jawi else ImageFont.truetype(F_DOODLE_LAT, size)
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    col = YELLOW if yellow else WHITE
    ImageDraw.Draw(im).text((size, size), glyph, font=f, fill=col[:3] + (int(255 * DOODLE_ALPHA),), anchor="mm")
    return im

DOODLE_IMGS = [doodle_img(sz, g, j, y) for _, _, sz, g, j, y, _ in DOODLES]

def draw_doodles(frame, t):
    fade = clamp(t / 0.6)
    for i, ((x, y, sz, g, j, yl, rot), im) in enumerate(zip(DOODLES, DOODLE_IMGS)):
        per = 3.2 + 0.37 * i
        dy = 9 * math.sin(2 * math.pi * t / per + i)
        dx = 5 * math.cos(2 * math.pi * t / (per * 1.3) + i * 0.7)
        r = rot + 5 * math.sin(2 * math.pi * t / (per * 1.6) + i)
        a = im.rotate(r, resample=Image.BICUBIC)
        if fade < 1:
            a = scaled(a, 1.0, fade)
        frame.alpha_composite(a, (int(x + dx - a.width / 2), int(y + dy - a.height / 2)))


# ---------------------------------------------------------------- caption animation
def draw_overlays(frame, t):
    draw_doodles(frame, t)
    for c in CARDS:
        if not (c["t0"] <= t < c["t1"] + 0.2):
            continue
        k_out = clamp((t - c["t1"]) / 0.16)
        out_s, out_a = 1 - 0.35 * ease_out_cubic(k_out), 1 - k_out
        if c["label_img"] is not None:
            k = clamp((t - c["t0"]) / 0.3)
            put_sprite(frame, c["label_img"], W / 2, LABEL_Y - 18 * (1 - ease_out_cubic(k)),
                       s=(0.4 + 0.6 * ease_out_back(k, 2.2)) * out_s, alpha=clamp(k * 3) * out_a)
        for wd in c["words"]:
            d = t - wd["t"]
            if d < 0:
                continue
            k = clamp(d / WORD_IN)
            e = ease_out_cubic(k)
            s = 0.15 + 0.85 * ease_out_back(k, 2.8)           # bouncy pop
            dy = -46 * (1 - e)                                 # drop in from above
            rot = 14 * wd["dir"] * (1 - e)                     # untwist
            if wd["hl"] and d > WORD_IN:                       # jelly wiggle after landing
                u = d - WORD_IN
                damp = math.exp(-5 * u)
                rot += 8 * math.sin(2 * math.pi * 3.2 * u) * damp
                s *= 1 + 0.12 * math.sin(2 * math.pi * 3.2 * u) * damp
            if c.get("cta") and wd["hl"] and d > 1.2:          # gentle heartbeat on CTA
                s *= 1 + 0.06 * max(0.0, math.sin(2 * math.pi * 1.4 * (d - 1.2)))
            put_sprite(frame, wd["img"], wd["cx"], wd["cy"] + dy, s=s * out_s, rot=rot,
                       alpha=clamp(k * 4) * out_a)


# ---------------------------------------------------------------- audio (kid-style)
PENTA = [1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0, 2349.3, 2637.0]  # C6 pentatonic up

def sfx_track(dur):
    n = int(dur * SR) + SR
    out = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)

    def put(sig, t):
        i = int(t * SR)
        j = min(n, i + len(sig))
        if 0 <= i < n:
            out[i:j] += sig[: j - i]

    def whoosh(L=0.42):
        m = int(L * SR)
        noise = rng.standard_normal(m).astype(np.float32)
        tt = np.linspace(0, 1, m)
        y = np.zeros(m, np.float32); acc = 0.0
        cut = 0.02 + 0.25 * np.sin(np.pi * tt) ** 2
        for k in range(m):
            acc += cut[k] * (noise[k] - acc); y[k] = acc
        y = y * np.sin(np.pi * tt) ** 2.2
        return 0.22 * y / (np.abs(y).max() + 1e-9)

    def xylo(f, vol=0.09):  # wooden xylophone / marimba note
        m = int(0.4 * SR); tt = np.arange(m) / SR
        s = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 16)
             + 0.35 * np.sin(2 * np.pi * 3.93 * f * tt) * np.exp(-tt * 45))
        return (vol * s * np.minimum(1, tt / 0.002)).astype(np.float32)

    def boing(vol=0.11):  # cartoon spring
        m = int(0.45 * SR); tt = np.arange(m) / SR
        f = 260 + 220 * np.exp(-tt * 7) + 35 * np.sin(2 * np.pi * 14 * tt) * np.exp(-tt * 4)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6)
        return (vol * s * np.minimum(1, tt / 0.004)).astype(np.float32)

    def bubble(vol=0.10):  # bubbly "bloop"
        m = int(0.12 * SR); tt = np.arange(m) / SR
        f = 500 + 1300 * (tt / tt[-1]) ** 1.5
        return (vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1])).astype(np.float32)

    def twinkle(vol=0.06):  # magic sparkle run
        sig = np.zeros(int(0.9 * SR), np.float32)
        for i, f in enumerate([2093, 2637, 3136, 3520, 4186, 3520, 4186, 5274]):
            x = xylo(f, vol); o = int(i * 0.055 * SR)
            sig[o:o + len(x)] += x[: len(sig) - o]
        return sig

    for c in CUTS:
        put(whoosh(), c - 0.24)
    for c in CARDS:
        put(bubble(), c["t0"])
        for i, wd in enumerate(c["words"]):
            put(xylo(PENTA[min(i, len(PENTA) - 1)]), wd["t"] + 0.02)
            if wd["hl"]:
                put(boing(0.07), wd["t"] + WORD_IN - 0.02)
        if c.get("twinkle"):
            put(twinkle(), c["words"][-1]["t"] + 0.15)
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


def overlay_frame(t):
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_overlays(fr, t)
    return fr


def main():
    """Outputs (all next to OUT):
      OUT.mp4          original HDR footage (HLG 10-bit, colours untouched) + overlay + SFX
      OUT_overlay.mov  transparent overlay only (PNG-in-MOV with alpha) for own editing
      OUT_sfx.wav      sound effects only, timed to the original video
    """
    raw, out = sys.argv[1], sys.argv[2]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", raw]).decode())
    nfr = int(round(dur * FPS))
    sfx_wav, ov_mov = out + "_sfx.wav", out + "_overlay.mov"
    write_wav(sfx_wav, sfx_track(dur)[: int(dur * SR)])

    # 1) transparent overlay track
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "png", "-pix_fmt", "rgba", ov_mov], stdin=subprocess.PIPE)
    for i in range(nfr):
        enc.stdin.write(overlay_frame(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"overlay {i/FPS:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()

    # 2) composite on the untouched HDR footage. Only the graphics are converted
    #    (sRGB -> BT.2020 HLG, white at 203 nits = HLG reference white).
    fc = ("[1:v]format=rgba,split[c][a];"
          "[a]alphaextract,format=gray10le[al];"
          "[c]format=gbrpf32le,zscale=tin=iec61966-2-1:pin=bt709:min=gbr:rin=full:"
          "t=arib-std-b67:p=bt2020:m=bt2020nc:r=tv:npl=203,format=yuv444p10le[cc];"
          "[cc][al]alphamerge[ov];"
          "[0:v]format=yuv444p10le[bg];"
          "[bg][ov]overlay=0:0:format=yuv444p10:eof_action=pass,format=yuv420p10le,"
          "setparams=color_primaries=bt2020:color_trc=arib-std-b67:colorspace=bt2020nc:range=tv[v];"
          "[0:a]aresample=48000[va];[2:a]aresample=48000[s];"
          "[va][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.97[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", ov_mov, "-i", sfx_wav,
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx265", "-preset", "medium", "-crf", "16", "-tag:v", "hvc1",
                    "-x265-params", "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited",
                    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out + ".mp4"], check=True)
    print("done", out)


if __name__ == "__main__":
    main()
