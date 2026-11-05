"""Generate the HyperFrames composition (index.html) + SFX track for the
"Menolak Algebra / Kuasai Algebra" reel.

Run:  python3 build.py   -> writes index.html, captions.json
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

cap_html = []
for i, c in enumerate(caps):
    spans = [f'<span class="w" id="c{i}w{j}">{html.escape(w["t"])}</span>' for j, w in enumerate(c["w"])]
    if c["emo"]:
        spans.append(f'<span class="w emo" id="c{i}e">{c["emo"]}</span>')
    cap_html.append(f'<div class="cap" id="c{i}">{" ".join(spans)}</div>')

# faint algebra symbols in the black band (like the reference)
SYM = [("×", 90, 70, 46), ("( )", 470, 40, 40), ("x²", 900, 60, 48), ("+", 160, 230, 44), ("5x", 610, 170, 40),
       ("=", 760, 280, 46), ("÷", 60, 420, 44), ("−", 980, 400, 50), ("a⁄b", 330, 520, 40), ("y", 860, 520, 44),
       ("√", 250, 120, 42), ("½", 690, 470, 40), ("π", 990, 200, 40), ("%", 420, 300, 36)]
deco = "".join(f'<div class="sym" id="sym{i}" style="left:{x}px;top:{y}px;font-size:{z}px">{html.escape(t)}</div>'
               for i, (t, x, y, z) in enumerate(SYM))

DATA = json.dumps({"slides": slide_js, "caps": [{"s": c["s"], "e": c["e"], "w": [w["s"] for w in c["w"]], "emo": bool(c["emo"])} for c in caps]})

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

/* black band + algebra symbols */
.band {{ position:absolute; left:0; top:0; width:{W}px; height:{VID_TOP + 140}px;
  background:radial-gradient(90% 70% at 50% 35%, #1b1b1d 0%, #0b0b0c 70%); }}
.sym {{ position:absolute; color:#fff; opacity:.13; font-weight:800; line-height:1; will-change:transform; }}

/* original footage, full width, no filters */
.slide {{ position:absolute; left:0; top:{VID_TOP}px; width:{W}px; height:{VID_H}px; }}
.frame {{ position:absolute; inset:0; overflow:hidden; }}
.media {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.fade {{ position:absolute; left:0; top:{VID_TOP - 2}px; width:{W}px; height:170px; pointer-events:none;
  background:linear-gradient(180deg, var(--bg) 0%, rgba(11,11,12,.55) 45%, rgba(11,11,12,0) 100%); }}

/* captions: neat, upright, white, no box, top band */
#captions {{ position:absolute; left:70px; right:70px; top:150px; height:120px; }}
.cap {{ position:absolute; left:0; right:0; top:0; text-align:center; visibility:hidden;
  font-weight:800; font-size:54px; line-height:1.22; letter-spacing:.035em; color:var(--ink);
  text-shadow:0 2px 3px rgba(0,0,0,.75), 0 0 12px rgba(0,0,0,.45), 0 4px 22px rgba(0,0,0,.5); }}
.w {{ display:inline-block; }}
.emo {{ font-size:50px; margin-left:6px; text-shadow:none; }}
</style>
</head>
<body>
<div id="main" data-composition-id="main" data-width="{W}" data-height="{H}" data-start="0" data-duration="{TOTAL}">
  {''.join(slides_html)}
  <div id="captions">{''.join(cap_html)}</div>
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

  // captions: word-by-word pop
  D.caps.forEach(function(c, i){{
    var id = "#c"+i;
    tl.set(id, {{autoAlpha:1}}, c.s);
    c.w.forEach(function(ws, j){{
      tl.from(id+"w"+j, {{y:18, scale:.85, autoAlpha:0, duration:.22, ease:"back.out(2.4)"}}, ws);
    }});
    if (c.emo) {{
      var lw = c.w[c.w.length-1];
      tl.from(id+"e", {{scale:0, autoAlpha:0, duration:.3, ease:"back.out(3)"}}, lw + .12);
    }}
    tl.to(id, {{autoAlpha:0, duration:.12, ease:"power1.in"}}, c.e - .12);
  }});

  tl.to({{}}, {{duration:.01}}, T - .01);
  window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(page)
print("captions:", len(caps), "slides:", len(SLIDES))
