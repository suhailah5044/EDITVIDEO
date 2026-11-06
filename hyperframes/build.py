"""Generate the HyperFrames compositions for the "Menolak Algebra / Kuasai Algebra" reel.

Run:  python3 build.py
  -> index.html + edl.json                     (main video)
  -> hooks/hook-NN/index.html + edl.json      (20 hook variants: different intro clip + hook title)
  -> captions.json
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
    ("s2", "assets/s2.mp4", "video", "50% 50%"),   # menolak + menambah pages (video, no still photo)
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
VID_TOP = 0
VID_H = H - VID_TOP

# reference style caption box: dark rounded box, thin yellow border, small yellow kicker + white text
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


def page_html(slide_src, prefix="", hook=None):
    """slide_src: {slide id: media path}. hook: (kicker, title) replaces the first sentence's captions."""
    slides_html, slide_js = [], []
    for i, (sid, src, kind, pos) in enumerate(SLIDES):
        src = prefix + slide_src.get(sid, src)
        s = B[i] if i == 0 else B[i] - TR / 2
        e = B[i + 1] + TR / 2 if i + 1 < len(SLIDES) else TOTAL
        d = round(e - s, 3)
        hidden = "" if i == 0 else ' style="visibility:hidden"'
        media = (f'<video id="{sid}-m" class="media clip" src="{src}" muted playsinline preload="auto" '
                 f'data-start="{s:.3f}" data-duration="{d}" data-track-index="{20 + i}" '
                 f'style="object-position:{pos}"></video>')
        slides_html.append(
            f'<div class="slide clip" id="{sid}" data-start="{s:.3f}" data-duration="{d}" data-track-index="{1 + i % 2}"{hidden}>'
            f'<div class="frame">{media}</div></div>')
        slide_js.append({"id": sid, "s": round(s, 3), "e": round(e, 3)})

    g0 = 1 if hook else 0  # with a hook, the first sentence is covered by the hook title
    cap_html, cap_js = [], []
    for i, c in enumerate(caps):
        if group_of(c["s"]) < g0:
            continue
        spans = [f'<span class="w" id="c{i}w{j}">{html.escape(w["t"])}</span>' for j, w in enumerate(c["w"])]
        if c["emo"]:
            spans.append(f'<span class="w emo" id="c{i}e">{c["emo"]}</span>')
        cap_html.append(f'<div class="cap" id="c{i}">{" ".join(spans)}</div>')
        cap_js.append({"i": i, "s": c["s"], "e": c["e"], "w": [w["s"] for w in c["w"]], "emo": bool(c["emo"])})
    kick_html = "".join(f'<div class="kick" id="k{g}">{html.escape(t)}</div>'
                        for g, (_, t) in enumerate(GROUPS) if g >= g0)
    hook_html = ""
    if hook:
        kicker, title = hook
        ws = title.split()
        if len(ws) > 1 and not any(ch.isalnum() for ch in ws[-1]):  # keep a trailing emoji with its word
            ws = ws[:-2] + [ws[-2] + "\u00a0" + ws[-1]]
        tw = " ".join(f'<span class="hw">{html.escape(w)}</span>' for w in ws)
        hook_html = f'<div id="hook"><div class="hk">{html.escape(kicker)}</div><div class="ht">{tw}</div></div>'

    DATA = json.dumps({"slides": slide_js, "groups": [[g, gs] for g, (gs, _) in enumerate(GROUPS) if g >= g0],
                       "caps": cap_js, "hook": bool(hook)})
    return f"""<!doctype html>
<html lang="ms" style="overflow:hidden;margin:0">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<title>Kuasai Algebra – Menolak Algebra</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/core/dist/hyperframe.runtime.iife.js"></script>
<style>
@font-face {{ font-family:"Montserrat"; font-weight:600 900; font-style:normal; font-display:block; src:url({prefix}assets/montserrat-upright.woff2) format("woff2"); }}
:root {{ --bg:#0b0b0c; --ink:#ffffff; --gold:#f5c21b; --font:"Montserrat","Noto Color Emoji",sans-serif; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--bg); }}
#main {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font); background:var(--bg); }}

/* original footage, full screen, no filters */
.slide {{ position:absolute; left:0; top:{VID_TOP}px; width:{W}px; height:{VID_H}px; }}
.frame {{ position:absolute; inset:0; overflow:hidden; }}
.media {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}

/* caption box - reference style, kept small */
#box {{ position:absolute; left:50%; top:120px; width:820px; margin-left:-410px; padding:14px 26px 18px;
  border-radius:24px; border:3px solid var(--gold); background:rgba(12,12,12,.74);
  box-shadow:0 10px 30px rgba(0,0,0,.35); text-align:center; transform-origin:50% 0; visibility:hidden; }}
.kick {{ position:absolute; left:0; right:0; top:14px; font-weight:800; font-size:22px; letter-spacing:.16em;
  color:var(--gold); visibility:hidden; }}
.lines {{ position:relative; height:62px; margin-top:30px; }}
.cap {{ position:absolute; left:0; right:0; top:0; visibility:hidden; white-space:nowrap;
  font-weight:800; font-size:46px; line-height:62px; letter-spacing:.02em; color:#fff; }}
.w {{ display:inline-block; }}
.emo {{ font-size:42px; margin-left:4px; }}

/* hook title - same look as the caption box, one size up, max 2 lines */
#hook {{ position:absolute; left:50%; top:110px; width:900px; margin-left:-450px; padding:16px 34px 22px;
  border-radius:26px; border:3px solid var(--gold); background:rgba(12,12,12,.80);
  box-shadow:0 12px 34px rgba(0,0,0,.4); text-align:center; transform-origin:50% 0; }}
.hk {{ font-weight:800; font-size:24px; letter-spacing:.16em; color:var(--gold); }}
.ht {{ margin-top:6px; font-weight:800; font-size:48px; line-height:1.2; letter-spacing:.01em; color:#fff; text-wrap:balance; }}
.hw {{ display:inline-block; }}
</style>
</head>
<body>
<div id="main" data-composition-id="main" data-width="{W}" data-height="{H}" data-start="0" data-duration="{TOTAL}">
  {''.join(slides_html)}
  <div id="box">{kick_html}<div class="lines">{''.join(cap_html)}</div></div>
  {hook_html}
  <audio id="vo" src="{prefix}assets/vo.m4a" data-start="0" data-duration="{VO_DUR}" data-track-index="40"></audio>
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
    }}
    if (!last) tl.set(el, {{autoAlpha:0}}, s.e);
  }});

  // hook title over the intro clip
  if (D.hook) {{
    // fully readable from the very first frame (TikTok uses it as the thumbnail), then a quick pop
    tl.set("#hook", {{autoAlpha:1}}, 0);
    tl.fromTo("#hook", {{scale:1.07}}, {{scale:1, duration:.35, ease:"back.out(2.5)"}}, 0);
    tl.fromTo("#hook .hw", {{y:0}}, {{y:-6, duration:.12, ease:"power1.out", yoyo:true, repeat:1, stagger:{{each:.05, from:"start"}}}}, 0.35);
    tl.to("#hook", {{scale:1.03, duration:.22, yoyo:true, repeat:1, ease:"sine.inOut"}}, 1.45);
    tl.to("#hook", {{autoAlpha:0, y:-10, duration:.2, ease:"power1.in"}}, 2.18);
  }}

  // caption box: pops in for each sentence (new kicker), captions change inside it
  tl.set("#box", {{autoAlpha:1}}, D.groups[0][1]);
  D.groups.forEach(function(gg, n){{
    var g = gg[0], gs = gg[1];
    var end = n+1 < D.groups.length ? D.groups[n+1][1] : T;
    tl.set("#k"+g, {{autoAlpha:1}}, gs);
    tl.fromTo("#box", {{scale:.86, y:-10}}, {{scale:1, y:0, duration:.35, ease:"back.out(2.2)"}}, gs);
    tl.from("#k"+g, {{y:-8, autoAlpha:0, duration:.25, ease:"power2.out"}}, gs + .05);
    if (n+1 < D.groups.length) tl.set("#k"+g, {{autoAlpha:0}}, end);
  }});
  D.caps.forEach(function(c){{
    var id = "#c"+c.i;
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


# ---- edit decision list: original camera files, in-points and crops (used by render.js)
SOURCES = {  # slide id -> (source file, in-point seconds, crop on the rotated 2160x3840 frame or None)
    "s1": ("IMG_1591.MOV", 1.0, "1620:2880:270:420"),   # zoomed so the floor is not visible
    "s2": ("IMG_1591.MOV", 5.5, "1620:2880:270:420"),
    "s3": ("IMG_1593.MOV", 0.5, None), "s4": ("IMG_1592.MOV", 0.3, None),
    "s5": ("IMG_1594.MOV", 0.0, None), "s6": ("IMG_1596.MOV", 0.5, None),
    "s7": ("IMG_1599.MOV", 1.4, None),   # persamaan linear page (0.0-0.45s of this clip shows another book)
    "s8": ("IMG_1548.MOV", 0.3, None),
    "s9": ("IMG_1597.MOV", 1.6, None),
}


# ---- four versions of the body (everything after the intro). Every shot matches what the voice-over says:
#  s2 "bukan setakat tambah... cara tolak"      -> menambah + menolak pages
#  s3 "samakan penyebut, ikut langkah"          -> pointer on the menolak steps
#  s4 "bila dah faham tekniknya"                -> menolak steps / Teknik Mudah FastMaths
#  s5 "buku Kuasai Algebra ni berbaloi"         -> flipping through the book
#  s6 "asas algebra, operasi, kembangan"        -> Kandungan page
#  s7 "pemfaktoran dan persamaan linear"        -> Pemfaktoran / Persamaan Linear pages
#  s8 "latihan dan video tutorial"              -> Set Latihan with the video-answer QR
#  s9 "grab buku Kuasai Algebra"                -> the cover
Z = "1620:2880:270:420"
BODIES = {
    "A": dict(SOURCES),
    "B": {"s2": ("IMG_1593.MOV", 5.3, None), "s3": ("IMG_1592.MOV", 0.3, None), "s4": ("IMG_1593.MOV", 9.45, None),
          "s5": ("IMG_1598.MOV", 2.0, None), "s6": ("IMG_1596.MOV", 0.3, None), "s7": ("IMG_1594.MOV", 3.4, None),
          "s8": ("IMG_1597.MOV", 9.75, None), "s9": ("IMG_1597.MOV", 1.6, "1620:2880:270:420")},
    "C": {"s2": ("IMG_1591.MOV", 0.0, Z), "s3": ("IMG_1593.MOV", 7.9, None), "s4": ("IMG_1593.MOV", 1.0, "1080:1920:900:1300"),
          "s5": ("IMG_1594.MOV", 5.5, None), "s6": ("IMG_1596.MOV", 5.7, None), "s7": ("IMG_1597.MOV", 18.95, None),
          "s8": ("IMG_1597.MOV", 17.1, None), "s9": ("IMG_1597.MOV", 1.6, "1620:2880:400:300")},
    "D": {"s2": ("IMG_1591.MOV", 5.5, Z), "s3": ("IMG_1593.MOV", 7.9, None), "s4": ("IMG_1592.MOV", 0.3, None),
          "s5": ("IMG_1598.MOV", 2.0, None), "s6": ("IMG_1596.MOV", 0.3, None), "s7": ("IMG_1597.MOV", 18.95, None),
          "s8": ("IMG_1548.MOV", 0.3, None), "s9": ("IMG_1597.MOV", 1.6, None)},
}
BODY_ASSETS = {g: ({} if g == "A" else {sid: f"assets/body-{g}/{sid}.mp4" for sid in BODIES[g] if sid != "s1"}) for g in BODIES}


def slot_range(i):
    """start/end (s) of slide i on the timeline, including the cross-dissolve overlap."""
    s = B[i] if i == 0 else B[i] - TR / 2
    e = B[i + 1] + TR / 2 if i + 1 < len(SLIDES) else TOTAL
    return s, e


def edl(intro=None, body="A"):
    src = dict(SOURCES); src.update(BODIES[body])
    clips = [{"id": sid, "src": src[sid][0], "in": src[sid][1], "crop": src[sid][2]} for sid, *_ in SLIDES]
    if intro:
        clips[0] = {"id": "s1", "src": intro[0], "in": intro[1], "crop": intro[2]}
    return {"total": TOTAL, "tr": TR, "boundaries": B, "body": body, "clips": clips}


(ROOT / "index.html").write_text(page_html({}))
json.dump(edl(), open(ROOT / "edl.json", "w"), indent=1)

# ---------------------------------------------------------------- 20 hook variants
# Every intro is a different shot that the body of the video does not use (or a 4K close-up),
# and every hook title is different. IMG_1598 after ~6.9s shows another book -> never used.
HOOKS = [
    # (body version, source, in, crop on the rotated 2160x3840 frame, kicker, title)
    # --- videos 1-5: body A
    ("A", "IMG_1593.MOV", 5.3, None, "RAMAI SILAP DI SINI", "Tolak pecahan algebra tapi jawapan salah? 😱"),            # wide, pointer
    ("A", "IMG_1593.MOV", 7.85, "1350:2400:620:150", "BOLEH JAWAB TAK?", "3c/5b − (c−6)/2d = ?"),                     # close-up: the question
    ("A", "IMG_1593.MOV", 10.3, "1080:1920:900:1300", "TEKNIK FASTMATHS", "Cara paling pantas tolak pecahan algebra ⚡"),  # close-up: cartoon + technique
    ("A", "IMG_1593.MOV", 10.3, "1080:1920:300:1920", "TIPS MATH", "Jangan terus tolak! Buat ni dulu ⚠️"),           # close-up: backpack cartoon + darab silang
    ("A", "IMG_1598.MOV", 3.0, None, "MAK AYAH, SIMPAN VIDEO NI", "Bantu anak faham menolak algebra 📚"),               # flip-through
    # --- videos 6-10: body B
    ("B", "IMG_1596.MOV", 3.2, None, "PARENTS, TENGOK NI", "Anak pening bab menolak algebra? 🤯"),                       # kandungan, pointer
    ("B", "IMG_1596.MOV", 5.9, "1080:1920:380:300", "SEMUA DALAM SATU BUKU", "Dari asas sampai persamaan linear 🧠"),      # close-up: kandungan list
    ("B", "IMG_1597.MOV", 14.0, None, "FAHAM, BUKAN HAFAL", "Kenapa hafal formula tapi masih salah? 🤔"),               # yellow contoh page
    ("B", "IMG_1597.MOV", 18.3, None, "CIKGU PUN GUNA", "Teknik yang jarang diajar kat sekolah"),                        # yellow technique page
    ("B", "IMG_1597.MOV", 3.0, "1350:2400:300:300", "KUASAI ALGEBRA", "Satu buku, semua asas algebra 🔥"),                # close-up: cover title
    # --- videos 11-15: body C
    ("C", "IMG_1597.MOV", 0.0, None, "BUKU YANG RAMAI CARI", "Algebra jadi mudah dengan buku ni 📘"),                   # cover reveal
    ("C", "IMG_1597.MOV", 7.5, None, "ADA GROUP SUPPORT", "Tak faham? Boleh tanya terus 💬"),                           # back cover, QR groups
    ("C", "IMG_1597.MOV", 9.88, None, "CUBA JAWAB", "Boleh siapkan soalan ni dalam 1 minit? ⏱️"),                      # set latihan
    ("C", "IMG_1592.MOV", 0.5, "1080:1920:700:200", "ANAK STRUGGLE MATH?", "Tengok video ni sampai habis 👀"),           # close-up: page title
    ("C", "IMG_1592.MOV", 2.4, "1080:1920:500:900", "LANGKAH PERTAMA", "Samakan penyebut dulu, baru tolak ✍️"),          # close-up: steps
    # --- videos 16-20: body D
    ("D", "IMG_1591.MOV", 9.75, "1080:1920:0:700", "TAMBAH VS TOLAK", "Tahu tambah, tapi tolak pecahan macam mana?"),    # close-up: menambah page
    ("D", "IMG_1594.MOV", 8.2, None, "MENOLAK ALGEBRA", "3 langkah je, terus dapat jawapan ✅"),                        # straight-on spread
    ("D", "IMG_1597.MOV", 5.0, "1080:1920:900:1300", "ADA VIDEO JALAN KERJA", "Anak tak faham? Tengok video tutorial 🎥"),  # close-up: video badge
    ("D", "IMG_1599.MOV", 2.6, None, "FORM 1 HINGGA SPM", "Asas algebra yang confirm keluar exam 💯"),                  # persamaan linear page
    ("D", "IMG_1594.MOV", 3.4, None, "JANGAN SKIP", "Latihan + jawapan video, siap semua 📝"),                           # set latihan, flipping
]
assert len(HOOKS) == 20
assert len({h[5] for h in HOOKS}) == 20 and len({h[4] for h in HOOKS}) == 20, "titles/kickers must all differ"
assert len({h[1:4] for h in HOOKS}) == 20, "intros must all differ"
assert [h[0] for h in HOOKS] == ["A"] * 5 + ["B"] * 5 + ["C"] * 5 + ["D"] * 5


def overlaps(a, b):
    return a[0] == b[0] and a[1] < b[2] and b[1] < a[2]


# no intro may re-use footage that its own body already shows (the cover CTA excepted: intro shows
# the book, the ending asks to buy it)
for n, (g, src, t_in, crop, kicker, title) in enumerate(HOOKS, 1):
    intro = (src, t_in, t_in + slot_range(0)[1])
    for k, (sid, *_) in enumerate(SLIDES[1:], 1):
        bs = BODIES[g].get(sid, SOURCES[sid])
        st, en = slot_range(k)
        if sid != "s9":
            assert not overlaps(intro, (bs[0], bs[1], bs[1] + en - st)), f"hook {n}: intro repeats body shot {sid}"

for n, (g, src, t_in, crop, kicker, title) in enumerate(HOOKS, 1):
    d = ROOT / "hooks" / f"hook-{n:02d}"
    d.mkdir(parents=True, exist_ok=True)
    assets = dict(BODY_ASSETS[g]); assets["s1"] = f"assets/hooks/intro-{n:02d}.mp4"
    (d / "index.html").write_text(page_html(assets, prefix="../../", hook=(kicker, title)))
    e = edl((src, t_in, crop), g); e["hook"] = {"kicker": kicker, "title": title}
    json.dump(e, open(d / "edl.json", "w"), indent=1, ensure_ascii=False)
json.dump([{"n": n, "body": h[0], "src": h[1], "in": h[2], "crop": h[3], "kicker": h[4], "title": h[5]} for n, h in enumerate(HOOKS, 1)],
          open(ROOT / "hooks" / "hooks.json", "w"), indent=1, ensure_ascii=False)
json.dump({g: edl(None, g) for g in BODIES}, open(ROOT / "hooks" / "bodies.json", "w"), indent=1)
print("captions:", len(caps), "slides:", len(SLIDES), "hooks:", len(HOOKS))
