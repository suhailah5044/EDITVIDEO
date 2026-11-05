"""Generate the HyperFrames composition (index.html) + SFX track for the
"Menolak Algebra / Kuasai Algebra" reel.

Run:  python3 build.py   -> writes index.html, assets/sfx.wav, captions.json
"""
import json, math, wave, struct, random, html
from pathlib import Path

ROOT = Path(__file__).parent
W, H = 1080, 1920
TOTAL = 27.6
VO_DUR = 27.35
TR = 0.6  # slide transition length (centered on boundary)

# ---------------------------------------------------------------- slides
# boundaries follow the voice-over beats
B = [0, 2.40, 6.33, 10.48, 13.58, 16.68, 19.25, 20.86, 22.36, TOTAL]
SLIDES = [
    # id, media, kind, object-position
    ("s1", "assets/s1.mp4", "video", "50% 45%"),   # Menolak algebra page overview
    ("s2", "assets/s2.jpg", "image", "50% 50%"),   # Menambah algebra page (still photo)
    ("s3", "assets/s3.mp4", "video", "50% 40%"),   # pointer on menolak steps
    ("s4", "assets/s4.mp4", "video", "50% 42%"),   # steps close-up
    ("s5", "assets/s5.mp4", "video", "50% 45%"),   # flipping pages
    ("s6", "assets/s6.mp4", "video", "50% 50%"),   # kandungan
    ("s7", "assets/s7.mp4", "video", "50% 45%"),   # persamaan linear page
    ("s8", "assets/s8.mp4", "video", "50% 40%"),   # set latihan + QR video
    ("s9", "assets/s9.mp4", "video", "50% 45%"),   # cover - CTA
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

# ---------------------------------------------------------------- SFX (synthesised, deterministic)
SR = 48000
buf = [0.0] * int(SR * TOTAL + SR)
rnd = random.Random(7)


def add(sig, t0, gain):
    o = int(t0 * SR)
    for i, v in enumerate(sig):
        if 0 <= o + i < len(buf):
            buf[o + i] += v * gain


def pop(f0=880.0):
    """soft bubbly 'pop' - fast downward pitch sweep + click"""
    n = int(0.11 * SR)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = f0 * (1.9 - 0.9 * min(1, t / 0.05))
        ph += 2 * math.pi * f / SR
        env = (1 - math.exp(-t * 900)) * math.exp(-t * 38)
        out.append(math.sin(ph) * env + 0.25 * math.sin(2 * ph) * env)
    return out


def whoosh(dur=0.55):
    """filtered noise swell with band sweep - for slide swipes"""
    n = int(dur * SR)
    out = []
    lp = bp = 0.0
    for i in range(n):
        x = i / n
        cut = 0.02 + 0.22 * math.sin(math.pi * x) ** 2
        w = rnd.uniform(-1, 1)
        lp += cut * (w - lp)
        bp += cut * (lp - bp)
        env = math.sin(math.pi * x) ** 1.6
        out.append((lp - bp * 0.6) * env * 3.2)
    return out


def chime(t0, gain):
    for k, (f, d) in enumerate([(1318.5, 0), (1760, 0.07), (2637, 0.14)]):
        n = int(0.9 * SR)
        sig = [math.sin(2 * math.pi * f * i / SR) * math.exp(-i / SR * 5) * (1 - math.exp(-i / SR * 400)) for i in range(n)]
        add(sig, t0 + d, gain)


pitches = [740, 830, 880, 988, 830, 932]
POP = {}
for i, c in enumerate(caps):
    f = pitches[i % len(pitches)]
    POP.setdefault(f, pop(f))
    add(POP[f], max(0, c["s"] - 0.01), 0.16 if not c["emo"] else 0.2)
W0 = whoosh()
for bt in B[1:-1]:
    add(W0, bt - 0.33, 0.30)
chime(B[-2] + 0.05, 0.08)

peak = max(abs(v) for v in buf) or 1
with wave.open(str(ROOT / "assets/sfx.wav"), "w") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    sc = 0.9 / peak if peak > 0.9 else 1.0
    wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * sc)) * 32767)) for v in buf[: int(SR * TOTAL)]))

# ---------------------------------------------------------------- HTML
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
        f'<div class="card">{media}<div class="sheen"></div></div></div>')
    slide_js.append({"id": sid, "s": round(s, 3), "e": round(e, 3), "b": B[i], "b2": B[i + 1]})

cap_html = []
for i, c in enumerate(caps):
    spans = []
    for j, w in enumerate(c["w"]):
        cls = "w k" if w["k"] else "w"
        spans.append(f'<span class="{cls}" id="c{i}w{j}">{html.escape(w["t"])}</span>')
    if c["emo"]:
        spans.append(f'<span class="w emo" id="c{i}e">{c["emo"]}</span>')
    cap_html.append(f'<div class="cap" id="c{i}">{" ".join(spans)}</div>')

SYMBOLS = ["+", "−", "×", "÷", "=", "a⁄b", "x²", "½", "√", "∑", "c⁄d", "%", "y", "π"]
rs = random.Random(11)
deco = []
for i in range(22):
    x, y = rs.uniform(-40, W - 40), rs.uniform(-40, H - 40)
    sz = rs.choice([54, 70, 90, 120, 150])
    rot = rs.uniform(-25, 25)
    deco.append(f'<div class="sym" id="sym{i}" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{sz}px;transform:rotate({rot:.0f}deg)">{SYMBOLS[i % len(SYMBOLS)]}</div>')

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
@font-face {{ font-family:"Jakarta"; font-weight:200 800; font-style:normal; font-display:block; src:url(assets/jakarta.woff2) format("woff2"); }}
:root {{
  --bg0:#12060b; --bg1:#3a0f17; --maroon:#9b2d24; --gold:#f6c33b; --plum:#3b1a5c;
  --ink:#ffffff; --font:"Jakarta","Noto Color Emoji",system-ui,sans-serif;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--bg0); }}
#main {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font); }}

/* ---------- background ---------- */
.bg {{ position:absolute; inset:0; overflow:hidden;
  background: radial-gradient(120% 80% at 50% 0%, #4a1420 0%, rgba(74,20,32,0) 60%),
              radial-gradient(90% 60% at 50% 100%, #2a0f3a 0%, rgba(42,15,58,0) 70%),
              linear-gradient(180deg, #1c0810 0%, var(--bg0) 55%, #0c0612 100%); }}
.blob {{ position:absolute; border-radius:50%; filter:blur(110px); opacity:.55; will-change:transform; }}
#blobA {{ width:760px; height:760px; left:-260px; top:-160px; background:radial-gradient(circle, #c23a2c 0%, rgba(194,58,44,0) 70%); }}
#blobB {{ width:700px; height:700px; right:-280px; top:620px; background:radial-gradient(circle, #f6b52e 0%, rgba(246,181,46,0) 70%); opacity:.38; }}
#blobC {{ width:900px; height:900px; left:-200px; bottom:-420px; background:radial-gradient(circle, #6b2fa8 0%, rgba(107,47,168,0) 70%); opacity:.45; }}
.sym {{ position:absolute; color:#fff; opacity:.06; font-weight:800; line-height:1; will-change:transform; }}
.rays {{ position:absolute; inset:-20%; opacity:.06;
  background: repeating-conic-gradient(from 0deg at 50% 0%, rgba(255,214,120,.0) 0deg 8deg, rgba(255,214,120,.55) 9deg 10deg, rgba(255,214,120,0) 11deg 20deg); }}
.grain {{ position:absolute; inset:0; pointer-events:none; opacity:.16; mix-blend-mode:overlay;
  background-image: radial-gradient(rgba(255,255,255,.10) 1px, transparent 1.2px), radial-gradient(rgba(0,0,0,.25) 1px, transparent 1.2px);
  background-size:3px 3px,5px 5px; background-position:0 0,1px 2px; }}
.vignette {{ position:absolute; inset:0; background:radial-gradient(120% 90% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%); }}

/* ---------- slides ---------- */
.slide {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; }}
.card {{ position:absolute; left:80px; top:190px; width:920px; height:1290px; border-radius:44px; overflow:hidden;
  background:#1a0d12; transform-origin:50% 60%;
  box-shadow: 0 50px 120px rgba(0,0,0,.6), 0 0 0 2px rgba(255,255,255,.10), 0 0 90px rgba(246,195,59,.12); }}
.media {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; will-change:transform; }}
.sheen {{ position:absolute; inset:0; pointer-events:none;
  background: linear-gradient(180deg, rgba(255,255,255,.10) 0%, rgba(255,255,255,0) 18%, rgba(0,0,0,0) 80%, rgba(0,0,0,.22) 100%); }}

/* ---------- captions (white, no box) ---------- */
#captions {{ position:absolute; left:60px; right:60px; top:1530px; height:220px; }}
.cap {{ position:absolute; left:0; right:0; top:0; text-align:center; visibility:hidden;
  font-weight:800; font-size:64px; line-height:1.18; letter-spacing:-.01em; color:var(--ink);
  text-shadow: 0 4px 18px rgba(0,0,0,.55), 0 2px 4px rgba(0,0,0,.45); }}
.w {{ display:inline-block; }}
.w.k {{ font-weight:800; }}
.emo {{ font-size:58px; margin-left:4px; text-shadow:none; }}
</style>
</head>
<body>
<div id="main" data-composition-id="main" data-width="{W}" data-height="{H}" data-start="0" data-duration="{TOTAL}">
  <div class="bg" id="bg">
    <div class="rays" id="rays"></div>
    <div class="blob" id="blobA"></div><div class="blob" id="blobB"></div><div class="blob" id="blobC"></div>
    {''.join(deco)}
    <div class="vignette"></div>
  </div>
  {''.join(slides_html)}
  <div id="captions">{''.join(cap_html)}</div>
  <div class="grain"></div>
  <audio id="vo" src="assets/vo.m4a" data-start="0" data-duration="{VO_DUR}" data-track-index="40"></audio>
  <audio id="sfx" src="assets/sfx.wav" data-start="0" data-duration="{TOTAL}" data-track-index="41" data-volume="1"></audio>
</div>
<script>
(function(){{
  var D = {DATA};
  var T = {TOTAL}, TR = {TR};
  window.__timelines = window.__timelines || {{}};
  var tl = gsap.timeline({{ paused:true }});

  // ---- living background (finite tweens spanning the whole video)
  tl.fromTo("#blobA", {{x:0,y:0,scale:1}}, {{x:260,y:380,scale:1.25,duration:T,ease:"sine.inOut"}}, 0);
  tl.fromTo("#blobB", {{x:0,y:0}}, {{x:-320,y:-420,duration:T,ease:"sine.inOut"}}, 0);
  tl.fromTo("#blobC", {{x:0,scale:1}}, {{x:300,scale:1.2,duration:T,ease:"sine.inOut"}}, 0);
  tl.fromTo("#rays", {{rotation:-6}}, {{rotation:6,duration:T,ease:"none"}}, 0);
  for (var i=0;i<22;i++) {{
    var dir = (i%2?1:-1);
    tl.to("#sym"+i, {{ y: -140 - (i%5)*40, x: dir*(30+(i%3)*25), rotation: "+="+(dir*25), duration:T, ease:"none" }}, 0);
  }}

  // ---- slides: smooth swipe between pages
  D.slides.forEach(function(s, i){{
    var card = "#"+s.id+" .card", m = "#"+s.id+"-m", last = i===D.slides.length-1;
    if (i>0) {{
      tl.set("#"+s.id, {{autoAlpha:1}}, s.s);
      tl.fromTo(card, {{x:1150, rotation:7, scale:.92}}, {{x:0, rotation:0, scale:1, duration:TR, ease:"power3.inOut"}}, s.s);
    }} else {{
      tl.from(card, {{y:120, scale:.9, autoAlpha:0, duration:.7, ease:"power3.out"}}, 0);
    }}
    // slow push-in on the media + gentle float of the card (mid-scene life)
    tl.fromTo(m, {{scale:1.04}}, {{scale:1.14, duration:s.e-s.s, ease:"none"}}, s.s);
    var floatStart = s.s + (i>0?TR:0.7), floatEnd = last ? T : s.e - TR;
    if (floatEnd - floatStart > 0.4) tl.to(card, {{y:-10, duration:(floatEnd-floatStart)/2, yoyo:true, repeat:1, ease:"sine.inOut"}}, floatStart);
    if (!last) {{
      tl.to(card, {{x:-1150, rotation:-7, scale:.92, duration:TR, ease:"power3.inOut"}}, s.e-TR);
      tl.set("#"+s.id, {{autoAlpha:0}}, s.e);
    }} else {{
      // CTA: little heartbeat on the cover
      tl.to(card, {{scale:1.035, duration:.35, yoyo:true, repeat:3, ease:"sine.inOut"}}, 24.9);
    }}
  }});

  // ---- captions: word-by-word pop, white, no box
  D.caps.forEach(function(c, i){{
    var id = "#c"+i;
    tl.set(id, {{autoAlpha:1}}, c.s);
    c.w.forEach(function(ws, j){{
      tl.from(id+"w"+j, {{y:26, scale:.82, autoAlpha:0, duration:.26, ease:"back.out(2.2)"}}, ws);
    }});
    if (c.emo) {{
      var lastW = c.w[c.w.length-1];
      tl.from(id+"e", {{scale:0, rotation:-30, autoAlpha:0, duration:.35, ease:"back.out(3)"}}, lastW + .12);
      tl.to(id+"e", {{rotation:10, duration:.25, yoyo:true, repeat:1, ease:"sine.inOut"}}, lastW + .5);
    }}
    tl.to(id, {{autoAlpha:0, y:-14, duration:.12, ease:"power1.in"}}, c.e - .12);
    tl.set(id, {{y:0}}, c.e);
  }});

  tl.to({{}}, {{duration:.01}}, T - .01); // pin the duration
  window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(page)
print("captions:", len(caps), "slides:", len(SLIDES))
