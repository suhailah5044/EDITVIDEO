"""Generate the HyperFrames composition (index.html) + SFX track for the
"Menolak Algebra / Kuasai Algebra" reel.

Run:  python3 build.py   -> writes index.html, captions.json, edl.json
"""
import json, math, wave, struct, random, html
from pathlib import Path

ROOT = Path(__file__).parent
W, H = 1080, 1920
TOTAL = 27.6
VO_DUR = 27.35
TR = 0.3  # short cross-dissolve between clips (centered on boundary)

# ---------------------------------------------------------------- slides
# boundaries follow the voice-over beats
B = [0, 2.40, 6.33, 10.48, 13.58, 16.68, 19.25, 20.86, 22.36, TOTAL]
SLIDES = [
    # id, media, kind, object-position
    ("s1", "assets/s1.mp4", "video", "50% 62%"),   # Menolak algebra page overview
    ("s2", "assets/s2.jpg", "image", "50% 50%"),   # Menambah algebra page (still photo)
    ("s3", "assets/s3.mp4", "video", "50% 55%"),   # pointer on menolak steps
    ("s4", "assets/s4.mp4", "video", "50% 55%"),   # steps close-up
    ("s5", "assets/s5.mp4", "video", "50% 45%"),   # flipping pages
    ("s6", "assets/s6.mp4", "video", "50% 50%"),   # kandungan
    ("s7", "assets/s7.mp4", "video", "50% 45%"),   # persamaan linear page
    ("s8", "assets/s8.mp4", "video", "50% 40%"),   # set latihan + QR video
    ("s9", "assets/s9.mp4", "video", "50% 60%"),   # cover - CTA
]

# ---------------------------------------------------------------- captions
words = json.load(open(ROOT / "words.json"))
FIX = {74: "pemfaktoran", 94: "grab", 95: ""}
for i, t in FIX.items():
    words[i]["w"] = t

CHUNKS = [  # (first_idx, last_idx, emoji)
    (0, 2, ""), (3, 5, ""), (6, 7, "🧮"),
    (8, 10, ""), (11, 13, "🤔"), (14, 17, ""), (18, 19, ""), (20, 22, "✅"),
    (23, 26, "📖"), (27, 29, ""), (30, 31, ""), (32, 34, ""), (35, 36, ""), (37, 38, "🎯"),
    (39, 40, ""), (41, 43, "😵"), (44, 46, ""), (47, 48, ""), (49, 52, "😍"),
    (53, 55, ""), (56, 58, ""), (59, 59, "💯"), (60, 63, ""),
    (64, 67, ""), (68, 71, ""), (72, 73, ""), (74, 76, ""), (77, 78, ""),
    (79, 81, ""), (82, 84, "🎥"),
    (85, 88, ""), (89, 92, "😩"), (93, 95, ""), (96, 98, ""), (99, 102, "🛒"),
]
KEY = {"menolak", "tambah", "tolak", "betul", "samakan", "penyebut", "jawapan", "step",
       "faham", "mudah", "Kuasai", "Algebra", "berbaloi", "kembangan", "pemfaktoran",
       "persamaan", "linear", "video", "tutorial", "struggle", "Math", "grab", "kuning", "operasi"}


def clean(t):
    t = t.strip()
    t = t.strip(".,")
    return t


caps = []
for n, (a, b, emo) in enumerate(CHUNKS):
    ws = []
    for i in range(a, b + 1):
        t = clean(words[i]["w"])
        if not t:
            continue
        if t.startswith("-") and ws:  # "mula" + "-mula"
            ws[-1]["t"] += t
            continue
        ws.append({"t": t, "s": round(words[i]["s"], 2), "k": t in KEY})
    start = ws[0]["s"]
    end_word = words[b]["e"]
    caps.append({"s": start, "e_word": end_word, "w": ws, "emo": emo})
for i, c in enumerate(caps):
    nxt = caps[i + 1]["s"] if i + 1 < len(caps) else TOTAL
    c["e"] = round(min(nxt, c["e_word"] + 0.9) if nxt - c["e_word"] > 0.9 else nxt, 2)
    if i == len(caps) - 1:
        c["e"] = TOTAL - 0.05
json.dump(caps, open(ROOT / "captions.json", "w"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- HTML
# Layout follows the reference reel: black top band with faint white algebra
# symbols + neat caption on top; ORIGINAL footage full-width in the lower part.
VID_TOP = 0            # footage is full screen
VID_H = H - VID_TOP    # 1320 px tall, full 1080 width
slides_html, slide_js = [], []
for i, (sid, src, kind, pos) in enumerate(SLIDES):
    s = B[i] if i == 0 else B[i] - TR / 2
    e = B[i + 1] + TR / 2 if i + 1 < len(SLIDES) else TOTAL
    d = round(e - s, 3)
    hidden = "" if i == 0 else ' style="visibility:hidden"'
    if kind == "video":
        media = (f'<video id="{sid}-m" class="media clip" src="{src}" muted playsinline preload="auto" '
                 f'data-start="{s:.3f}" data-duration="{d}" data-track-index="{20 + i}" '
                 f'style="object-position:{pos}"></video>')
    else:
        media = f'<img id="{sid}-m" class="media" src="{src}" style="object-position:{pos}" alt="">'
    slides_html.append(
        f'<div class="slide clip" id="{sid}" data-start="{s:.3f}" data-duration="{d}" data-track-index="{1 + i % 2}"{hidden}>'
        f'<div class="frame">{media}</div></div>')
    slide_js.append({"id": sid, "s": round(s, 3), "e": round(e, 3)})

# ---- reference style: dark rounded box, thin yellow border, small yellow kicker + white text
GROUPS = [  # (start, kicker) - one kicker per sentence of the voice-over
    (0.00, "TOPIK HARI NI"), (2.46, "PECAHAN ALGEBRA"), (6.36, "CONTOH DALAM BUKU"), (10.54, "TIPS"),
    (13.62, "KUASAI ALGEBRA"), (16.74, "APA ADA DALAM BUKU"), (20.90, "BONUS"), (22.40, "JOM DAPATKAN"),
]
def group_of(t):
    g = 0
    for k, (gs, _) in enumerate(GROUPS):
        if t >= gs - 0.01:
            g = k
    return g

cap_html = []
for i, c in enumerate(caps):
    spans = [f'<span class="w" id="c{i}w{j}">{html.escape(w["t"])}</span>' for j, w in enumerate(c["w"])]
    if c["emo"]:
        spans.append(f'<span class="w emo" id="c{i}e">{c["emo"]}</span>')
    cap_html.append(f'<div class="cap" id="c{i}">{" ".join(spans)}</div>')
kick_html = "".join(f'<div class="kick" id="k{g}">{html.escape(t)}</div>' for g, (_, t) in enumerate(GROUPS))

DATA = json.dumps({"slides": slide_js,
                   "groups": [g for g, _ in GROUPS],
                   "caps": [{"s": c["s"], "e": c["e"], "g": group_of(c["s"]), "w": [w["s"] for w in c["w"]], "emo": bool(c["emo"])} for c in caps]})

page = f"""<!doctype html>
<html lang="ms" style="overflow:hidden;margin:0">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<title>Kuasai Algebra – Menolak Algebra</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/core/dist/hyperframe.runtime.iife.js"></script>
<style>
@font-face {{ font-family:"Montserrat"; font-weight:600 900; font-style:normal; font-display:block; src:url(assets/montserrat-upright.woff2) format("woff2"); }}
:root {{ --bg:#0b0b0c; --ink:#ffffff; --font:"Montserrat","Noto Color Emoji",sans-serif; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--bg); }}
#main {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font); background:var(--bg); }}

/* original footage, full width, no filters */
.slide {{ position:absolute; left:0; top:{VID_TOP}px; width:{W}px; height:{VID_H}px; }}
.frame {{ position:absolute; inset:0; overflow:hidden; }}
.media {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
/* caption box - reference style, kept small */
#box {{ position:absolute; left:50%; top:120px; width:820px; margin-left:-410px; padding:14px 26px 18px;
  border-radius:24px; border:3px solid #f5c21b; background:rgba(12,12,12,.74);
  box-shadow:0 10px 30px rgba(0,0,0,.35); text-align:center; transform-origin:50% 0; visibility:hidden; }}
.kick {{ position:absolute; left:0; right:0; top:14px; font-weight:800; font-size:22px; letter-spacing:.16em;
  color:#f5c21b; visibility:hidden; }}
.lines {{ position:relative; height:62px; margin-top:30px; }}
.cap {{ position:absolute; left:0; right:0; top:0; visibility:hidden; white-space:nowrap;
  font-weight:800; font-size:46px; line-height:62px; letter-spacing:.02em; color:#fff; }}
.w {{ display:inline-block; }}
.emo {{ font-size:42px; margin-left:4px; }}
</style>
</head>
<body>
<div id="main" data-composition-id="main" data-width="{W}" data-height="{H}" data-start="0" data-duration="{TOTAL}">
  {''.join(slides_html)}
  <div id="box">{kick_html}<div class="lines">{''.join(cap_html)}</div></div>
  <audio id="vo" src="assets/vo.m4a" data-start="0" data-duration="{VO_DUR}" data-track-index="40"></audio>
</div>
<script>
(function(){{
  var D = {DATA};
  var T = {TOTAL}, TR = {TR};
  window.__timelines = window.__timelines || {{}};
  var tl = gsap.timeline({{ paused:true }});

  // footage: plain compilation, short cross-dissolve (no zoom, no filter)
  D.slides.forEach(function(s, i){{
    var el = "#"+s.id, last = i===D.slides.length-1;
    if (i>0) {{
      tl.set(el, {{autoAlpha:1}}, s.s);
      tl.fromTo(el, {{opacity:0}}, {{opacity:1, duration:TR, ease:"none"}}, s.s);
    }} else {{
    }}
    if (!last) {{
      tl.set(el, {{autoAlpha:0}}, s.e);
    }}
  }});

  // caption box: pops in for each sentence (new kicker), captions change inside it
  tl.set("#box", {{autoAlpha:1}}, D.groups[0]);
  D.groups.forEach(function(gs, g){{
    var end = g+1 < D.groups.length ? D.groups[g+1] : T;
    tl.set("#k"+g, {{autoAlpha:1}}, gs);
    tl.fromTo("#box", {{scale:.86, y:-10}}, {{scale:1, y:0, duration:.35, ease:"back.out(2.2)"}}, gs);
    tl.from("#k"+g, {{y:-8, autoAlpha:0, duration:.25, ease:"power2.out"}}, gs + .05);
    if (g+1 < D.groups.length) tl.set("#k"+g, {{autoAlpha:0}}, end);
  }});
  D.caps.forEach(function(c, i){{
    var id = "#c"+i;
    tl.set(id, {{autoAlpha:1}}, c.s);
    c.w.forEach(function(ws, j){{
      tl.from(id+"w"+j, {{y:14, autoAlpha:0, duration:.2, ease:"back.out(2)"}}, ws);
    }});
    if (c.emo) {{
      var lw = c.w[c.w.length-1];
      tl.from(id+"e", {{scale:0, autoAlpha:0, duration:.28, ease:"back.out(3)"}}, lw + .12);
    }}
    tl.set(id, {{autoAlpha:0}}, c.e);
  }});

  tl.to({{}}, {{duration:.01}}, T - .01);
  window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(page)

# ---- edit decision list: original camera files, in-points and crops (used by render.js)
SOURCES = {  # slide id -> (source file, in-point seconds, crop on the rotated 2160x3840 frame or None)
    "s1": ("IMG_1591.MOV", 1.0, "1620:2880:270:420"),   # zoomed so the floor is not visible
    "s2": ("IMG_1590.HEIC", 0.0, None),
    "s3": ("IMG_1593.MOV", 0.5, None), "s4": ("IMG_1592.MOV", 0.3, None),
    "s5": ("IMG_1594.MOV", 0.0, None), "s6": ("IMG_1596.MOV", 0.5, None),
    "s7": ("IMG_1599.MOV", 0.3, None), "s8": ("IMG_1548.MOV", 0.3, None),
    "s9": ("IMG_1597.MOV", 1.6, None),
}
json.dump({"total": TOTAL, "tr": TR, "boundaries": B,
           "clips": [{"id": sid, "src": SOURCES[sid][0], "in": SOURCES[sid][1], "crop": SOURCES[sid][2]} for sid, *_ in SLIDES]},
          open(ROOT / "edl.json", "w"), indent=1)
print("captions:", len(caps), "slides:", len(SLIDES))
