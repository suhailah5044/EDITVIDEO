"""Dark 'algebra' background in the style of the reference (dark charcoal, glossy light streak,
sparse large faint symbols, a few tinted yellow). Usage: python3 algebra_bg.py OUT_DIR"""
import random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_SYM = FONT_DIR + "InterDisplay-ExtraBold.otf"
F_SYM_I = FONT_DIR + "InterDisplay-BoldItalic.otf"


def make_bg(seed=4, extra_h=0):
    h = H + extra_h
    rng = random.Random(seed)
    yy = np.linspace(0, 1, h)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    # charcoal base, slightly lighter towards the upper middle
    r = np.sqrt((xx - 0.55) ** 2 + ((yy - 0.35) * 1.2) ** 2)
    k = np.clip(r / 0.95, 0, 1)[..., None]
    base = np.array([38, 40, 44], np.float32) * (1 - k) + np.array([14, 15, 17], np.float32) * k
    img = Image.fromarray(base.astype(np.uint8)).convert("RGBA")

    # glossy light streak sweeping from the top-right corner (like the reference)
    def bez(p0, p1, p2, n=80):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]
    curve = bez((600, -30), (800, 330), (1110, 470))
    streak = Image.new("L", (W, h), 0)
    d = ImageDraw.Draw(streak)
    for w_, a_ in ((150, 22), (80, 45), (36, 90), (12, 170)):
        d.line(curve, fill=a_, width=w_, joint="curve")
    streak = streak.filter(ImageFilter.GaussianBlur(14))
    sharp = Image.new("L", (W, h), 0)
    ImageDraw.Draw(sharp).line(bez((610, -30), (815, 318), (1110, 455)), fill=200, width=4, joint="curve")
    streak = Image.fromarray(np.maximum(np.asarray(streak), np.asarray(sharp.filter(ImageFilter.GaussianBlur(1.2)))))
    white = Image.new("RGBA", (W, h), (235, 238, 240, 255))
    white.putalpha(streak)
    img.alpha_composite(white)
    # soft dark shape under the streak (the 'fold' in the reference)
    fold = Image.new("L", (W, h), 0)
    ImageDraw.Draw(fold).ellipse([-500, 260, 1400, 1500], fill=60)
    fold = fold.filter(ImageFilter.GaussianBlur(120))
    blk = Image.new("RGBA", (W, h), (0, 0, 0, 255)); blk.putalpha(fold)
    img.alpha_composite(blk)

    # sparse, large, faint algebra symbols
    syms = [("x", True), ("y", True), ("+", False), ("−", False), ("×", False), ("÷", False),
            ("=", False), ("x²", True), ("√", False), ("π", False), ("a", True), ("b", True),
            ("( )", False), ("2", False), ("3t", True), ("4s", True)]
    layer = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    cols, rows = 4, max(5, h // 330)
    order = list(range(len(syms))); rng.shuffle(order)
    n = 0
    for r_ in range(rows):
        for c in range(cols):
            if rng.random() < 0.38:
                continue
            sym, italic = syms[order[n % len(order)]]; n += 1
            x = int((c + 0.5) * W / cols + rng.uniform(-90, 90))
            y = int((r_ + 0.5) * h / rows + rng.uniform(-110, 110))
            sz = rng.randint(70, 120)
            yellow = rng.random() < 0.22
            col = (220, 180, 20, rng.randint(55, 85)) if yellow else (255, 255, 255, rng.randint(22, 42))
            f = ImageFont.truetype(F_SYM_I if italic else F_SYM, sz)
            tile = Image.new("RGBA", (360, 300), (0, 0, 0, 0))
            ImageDraw.Draw(tile).text((60, 40), sym, font=f, fill=col)
            tile = tile.rotate(rng.uniform(-14, 14), resample=Image.BICUBIC)
            layer.alpha_composite(tile, (x - 120, y - 120))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.2)))

    # fine film grain like a real video frame
    g = np.random.default_rng(seed).normal(0, 4, (h, W, 1)).astype(np.float32)
    arr = np.clip(np.asarray(img.convert("RGB"), np.float32) + g, 0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")


if __name__ == "__main__":
    out = sys.argv[1]
    make_bg().convert("RGB").save(os.path.join(out, "algebra_bg_plain.png"))
