"""Title text style like the reference: heavy italic, white + yellow, thick black outline, slight tilt, burst lines."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
F_TITLE = os.path.join(HERE, "fonts", "Montserrat-BlackItalic.ttf")
WHITE, YELLOW, INK = (255, 255, 255), (255, 212, 0), (12, 12, 12)

def burst(size, color=(255, 255, 255), n=4, flip=False):
    """little 'action lines' like the reference."""
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(n):
        ang = math.radians(200 + i * 22) if not flip else math.radians(20 + i * 22)
        r0, r1 = s * 0.18, s * (0.46 if i % 2 == 0 else 0.38)
        cx = cy = s / 2
        p0 = (cx + r0 * math.cos(ang), cy + r0 * math.sin(ang))
        p1 = (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))
        d.line([p0, p1], fill=INK + (255,), width=max(6, s // 9))
        d.line([p0, p1], fill=color + (255,), width=max(3, s // 16))
    return im

def title(runs, size, tilt=-4.0, bursts=False):
    """runs: list of (text, color). returns RGBA image with outline + shadow."""
    f = ImageFont.truetype(F_TITLE, size)
    stroke = max(4, size // 8)
    tw = int(sum(f.getlength(t) for t, _ in runs))
    asc, desc = f.getmetrics()
    pad = stroke * 3 + 20
    w, h = tw + 2 * pad, asc + desc + 2 * pad
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = pad
    for t, c in runs:
        d.text((x, pad), t, font=f, fill=c + (255,), stroke_width=stroke, stroke_fill=INK + (255,))
        x += f.getlength(t)
    if bursts:
        bs = int(size * 2.0)
        big = Image.new("RGBA", (w + 2 * bs, h + bs), (0, 0, 0, 0))
        big.alpha_composite(lay, (bs, bs // 2))
        big.alpha_composite(burst(bs), (int(bs * 0.45), int(bs * 0.05)))
        big.alpha_composite(burst(bs, flip=True), (w + int(bs * 0.55), big.height - bs - int(bs * 0.05)))
        lay = big
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    a = np.asarray(lay.getchannel("A"), np.float32)
    sh = Image.fromarray((a * 0.55).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
    s_ = Image.new("RGBA", lay.size, (0, 0, 0, 255)); s_.putalpha(sh)
    out.alpha_composite(s_, (0, 8)); out.alpha_composite(lay)
    if tilt:
        out = out.rotate(-tilt, resample=Image.BICUBIC, expand=True)
    return out
