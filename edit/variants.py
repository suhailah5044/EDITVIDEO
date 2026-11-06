#!/usr/bin/env python3
"""15 variants of the Kuasai Algebra video: different intro clip, hook, title and every overlay.

Usage: python3 variants.py OUT_DIR   -> writes v01.json ... v15.json and titles.md
Each JSON is passed to build.py as its 4th argument.
"""
import json, os, sys

W_, Y_ = [255, 255, 255], [255, 212, 0]

# intro clips (0.00-1.82 s): all different. Spans with QR reuse the QR masks of the main edit.
INTROS = [
    ["IMG_1551.MOV", 1.30, 3.12, {}],                                   # 1 page Latihan 2
    ["IMG_1549.MOV", 0.00, 1.73, {}],                                   # 2 cover
    ["IMG_1546.MOV", 2.40, 4.22, {}],                                   # 3 nota ringkas page
    ["IMG_1547.MOV", 0.00, 1.82, {}],                                   # 4 operasi algebra
    ["TUT", 0, 0, {"clips": [[0.00, 1.82, 150.0, 168.8, 1.30]]}],       # 5 answer being written
    ["IMG_1543.MOV", 0.00, 1.82, {}],                                   # 6 question close-up
    ["IMG_1546.MOV", 0.00, 1.82, {}],                                   # 7 kandungan
    ["IMG_1545.MOV", 0.00, 3.64, {}],                                   # 8 fast page flip (2x)
    ["TUT", 0, 0, {"clips": [[0.00, 1.82, 100.0, 142.0, None]]}],       # 9 9t - 4 - 3t forming
    ["IMG_1544.MOV", 0.40, 2.22, {}],                                   # 10 Latihan 2 angled
    ["IMG_1548.MOV", 0.90, 2.72, {}],                                   # 11 finger on (blurred) QR
    ["IMG_1552.MOV", 2.20, 4.02, {}],                                   # 12 flipping all topics
    ["IMG_1551.MOV", 3.00, 4.75, {}],                                   # 13 steady page close
    ["TUT", 0, 0, {"clips": [[0.00, 1.82, 168.8, 100.0, None]]}],       # 14 rewind
    ["IMG_1549.MOV", 0.20, 1.11, {"play_dur": 1.82}],                   # 15 cover slow-mo
]

# hook: (small yellow label, white line, yellow line)
HOOKS = [
    ("IBU AYAH, BACA NI!", "Anak selalu stuck", "pecahan algebra?"),
    ("UJI ANAK KORANG", "Boleh jawab", "soalan ni?"),
    ("JANGAN SCROLL DULU!", "Ramai salah", "langkah pertama"),
    ("FORM 1 - 5 WAJIB TAHU", "Pecahan algebra", "jadi senang!"),
    ("JAWAPAN DIA...", "Macam mana dapat", "6t − 4 per 12st?"),
    ("CUBA DULU!", "Permudahkan", "soalan ni sekarang"),
    ("MAK AYAH KENA TAHU", "Kenapa anak", "takut algebra?"),
    ("TEKNIK MUDAH", "Algebra boleh jadi", "mudah & pantas"),
    ("TENGOK SAMPAI HABIS", "Step ni yang", "ramai terlepas"),
    ("SOALAN LATIHAN 2", "Anak korang", "boleh jawab?"),
    ("SCAN & TENGOK", "Buku ni ada", "video jawapan!"),
    ("SELAK JE...", "Semua topik", "algebra ada!"),
    ("KALAU ANAK KELIRU", "Mula belajar", "dari sini dulu"),
    ("ULANG SAMPAI FAHAM", "Tak faham?", "Tengok semula!"),
    ("PARENTS, NI PENTING", "Algebra lemah?", "Mula dengan ni"),
]

# overlays per slot (one entry per variant)
B = ["Permudahkan", "Soalan dia:", "Cuba jawab:", "Permudahkan ni", "Soalan:", "Latihan 2:", "Permudahkan ya",
     "Soalan latihan", "Jom cuba!", "Permudahkan", "Soalan hari ni", "Cuba kira", "Soalan ni:", "Latihan 2",
     "Permudahkan soalan"]
C = [("Samakan penyebut", "  darab 3t"), ("Penyebut kena sama", "  × 3t"), ("Step 1:", "  darab 3t"),
     ("Samakan bawah", "  darab 3t"), ("Langkah pertama", "  × 3t"), ("Penyebut sama dulu", "  darab 3t"),
     ("Kunci dia:", "  darab 3t"), ("Samakan penyebut", "  → 12st"), ("Darab 3t", "  penyebut 12st"),
     ("Bawah kena sama", "  darab 3t"), ("Mula dengan", "  penyebut"), ("Samakan dulu", "  darab 3t"),
     ("Rahsia dia:", "  darab 3t"), ("Step pertama:", "  samakan penyebut"), ("Penyebut jadi", "  12st")]
D = ["Teruskan pengiraan", "Kira step by step", "Step 2: tolak", "Teruskan kira", "Jaga tanda tolak",
     "Gabung sebutan serupa", "Hati-hati tanda −", "Kira sampai habis", "9t − 3t = 6t", "Teruskan langkah",
     "Satu langkah lagi", "Sikit lagi!", "Tolak sebutan serupa", "Kira perlahan-lahan", "Teruskan sampai ringkas"]
E = ["Jawapan paling ringkas", "Jawapan akhir", "Siap!", "Jawapan dia", "Ini jawapannya", "Dah ringkas!",
     "Jawapan betul", "Final answer", "Tadaa!", "Jawapan:", "Siap dipermudahkan", "Inilah jawapan",
     "Paling ringkas", "Jawapan muktamad", "Done!"]
F = [("Nampak ", "susah", " kan?"), ("Rasa ", "pening", " tak?"), ("Susah ", "ke", " senang?"),
     ("Nampak ", "rumit", " kan?"), ("Anak ", "blur", " tak?"), ("Ramai ", "stuck", " kat sini"),
     ("Pening ", "kepala", " kan?"), ("Macam ", "susah", " kan?"), ("Jangan ", "panik", " dulu"),
     ("Boleh ", "faham", " tak?"), ("Nampak ", "susah", " je"), ("Senang ", "sebenarnya", "!"),
     ("Keliru ", "tak", " tadi?"), ("Laju ", "sangat", " kan?"), ("Tak ", "susah", " pun!")]
G = ["Pecahan Algebra", "Topik paling payah?", "Bab yang ramai takut", "Pecahan + Algebra", "Topik ni penting",
     "Mimpi ngeri algebra?", "Algebra Form 1", "Asas penting!", "Ramai lemah bab ni", "Topik asas algebra",
     "Pecahan algebra?", "Bab pecahan", "Bab ni kritikal", "Ni asas algebra", "Topik wajib kuasai"]
Hs = [("Selalu ", "stuck?"), ("Tak tahu ", "nak mula?"), ("Asyik ", "salah?"), ("Selalu ", "keliru?"),
      ("Blank ", "terus?"), ("Tak tahu ", "start mana?"), ("Buntu? ", "Biasa je"), ("Hilang ", "fokus?"),
      ("Selalu ", "tersilap?"), ("Tak yakin ", "nak jawab?"), ("Takut ", "algebra?"), ("Buntu ", "kat soalan?"),
      ("Confuse ", "langkah?"), ("Tak reti ", "mula?"), ("Stuck ", "lagi?")]
I = [("Nota ringkas", "  •  Contoh", "  •  Latihan"), ("Nota", "  +  Contoh", "  +  Latihan"),
     ("Nota padat", "  •  Contoh", "  •  Latihan"), ("Ringkas", "  •  Jelas", "  •  Banyak latihan"),
     ("Nota", "  •  Contoh soalan", "  •  Latihan"), ("Belajar", "  •  Faham", "  •  Praktis"),
     ("Nota ringkas", " + contoh", " + latihan"), ("Teori", "  •  Contoh", "  •  Latihan"),
     ("Semua topik", "  •  Nota", "  •  Latihan"), ("Nota mudah", "  •  Contoh", "  •  Latihan"),
     ("Nota", "  •  Teknik", "  •  Latihan"), ("Baca", "  •  Faham", "  •  Buat latihan"),
     ("Nota ringkas", " & contoh", " & latihan"), ("1 buku:", " nota, contoh", " & latihan"),
     ("Nota", "  •  Contoh", "  •  Latih tubi")]
J = [("Scan QR", "Video tutorial"), ("Ada QR", "Video jalan kerja"), ("Scan je", "Terus ada video"),
     ("QR code", "Tengok video"), ("Imbas QR", "Video jawapan"), ("Paling best:", "Video tutorial"),
     ("Bonus!", "Video jawapan"), ("Scan QR →", "Tutorial video"), ("Ada video!", "Scan QR je"),
     ("Macam ada tutor", "Scan QR je"), ("Scan", "Tengok cara kira"), ("QR code", "Video langkah demi langkah"),
     ("Video", "jalan kerja"), ("Imbas QR", "Terus faham"), ("Scan QR", "Jawapan bervideo")]
K = ["Boleh ulang tengok", "Ulang sampai faham", "Replay bila-bila", "Tak faham? Ulang!", "Tengok banyak kali",
     "Ulang je", "Pause & ulang", "Ulang sampai pandai", "Belajar ikut masa sendiri", "Tengok semula",
     "Boleh ulang lagi", "Replay sampai faham", "Ulang balik", "Ulang, faham, jawab", "Ulang bila perlu"]
L = [("Sesuai untuk", "Form 1 – Form 5"), ("Untuk pelajar", "Form 1 – 5"), ("Dari Form 1", "sampai Form 5"),
     ("Pelajar", "Form 1 – Form 5"), ("Sesuai", "Tingkatan 1 – 5"), ("Form 1", "hingga Form 5"),
     ("Untuk", "Form 1 – 5"), ("Sekolah menengah", "Form 1 – 5"), ("Boleh guna", "Form 1 – 5"),
     ("Sesuai semua", "Form 1 – 5"), ("Anak Form 1?", "Sampai Form 5 boleh"), ("Pakai dari", "Form 1 – 5"),
     ("Cover", "Form 1 – 5"), ("Target", "Form 1 – 5"), ("Satu buku", "Form 1 – 5")]
M = [("Nak anak ", "lebih faham?"), ("Nak anak ", "yakin algebra?"), ("Nak anak ", "suka math?"),
     ("Nak anak ", "faham betul?"), ("Nak anak ", "tak stuck lagi?"), ("Nak anak ", "pandai algebra?"),
     ("Nak algebra ", "jadi mudah?"), ("Nak anak ", "lebih yakin?"), ("Nak bantu ", "anak belajar?"),
     ("Nak anak ", "faham asas?"), ("Nak anak ", "siap exam?"), ("Nak anak ", "kuasai algebra?"),
     ("Nak ulang kaji ", "jadi mudah?"), ("Nak anak ", "lebih cemerlang?"), ("Nak anak ", "minat algebra?")]
N = [("Check ", "beg kuning", " sekarang!"), ("Tekan ", "beg kuning", " sekarang!"), ("Cek ", "beg kuning", " tau!"),
     ("Klik ", "beg kuning", "!"), ("Grab kat ", "beg kuning", "!"), ("Dapatkan di ", "beg kuning", "!"),
     ("Jom ke ", "beg kuning", "!"), ("Order di ", "beg kuning", "!"), ("Tekan ", "beg kuning", " ya!"),
     ("Cek ", "beg kuning", " bawah!"), ("Terus ke ", "beg kuning", "!"), ("Beli di ", "beg kuning", "!"),
     ("Ada kat ", "beg kuning", "!"), ("Klik ", "beg kuning", " cepat!"), ("Tengok ", "beg kuning", " sekarang!")]

# posting titles (TikTok caption) - one per video
TITLES = [
    "Anak selalu stuck pecahan algebra? Tengok cara ni \U0001F447",
    "Uji anak korang: boleh jawab soalan pecahan algebra ni?",
    "Ramai salah langkah pertama soalan ni!",
    "Pecahan algebra jadi senang untuk Form 1 - 5",
    "Macam mana nak dapat jawapan (6t - 4)/12st?",
    "Cuba permudahkan soalan ni sekarang!",
    "Kenapa ramai anak takut algebra?",
    "Algebra dengan teknik mudah & pantas",
    "Step yang ramai terlepas bila permudahkan pecahan algebra",
    "Soalan Latihan 2: anak korang boleh jawab?",
    "Buku algebra yang ada video jawapan setiap latihan",
    "Semua topik algebra dalam satu buku",
    "Kalau anak keliru algebra, mula dari sini",
    "Tak faham? Ulang tengok video tutorial sampai faham",
    "Parents, kalau anak lemah algebra, mula dengan ni",
]


def T(t, s, c, sz):
    return [t, "t", s, c, sz]


def FR(t, num, den, c, sz):
    return [t, "f", [num, den], c, sz]


def variant(i):
    lab, h1, h2 = HOOKS[i]
    groups = [
        # hook at the top, strongest line in yellow
        [0.05, 2.62, 330, [[T(0.05, lab, Y_, 42)], [T(0.25, h1, W_, 74)], [T(0.55, h2, Y_, 82)]]],
        [2.70, 7.58, 1150, [[T(2.70, B[i], W_, 60)],
                            [FR(3.40, "3", "4s", Y_, 54), T(4.62, "  −  ", Y_, 56), FR(4.76, "4 + 3t", "12st", Y_, 54)]]],
        [8.18, 9.86, 800, [[T(8.18, C[i][0], W_, 54), T(9.14, C[i][1], Y_, 54)]]],
        [10.98, 12.76, 800, [[T(10.98, D[i], W_, 54)]]],
        [13.02, 14.06, 1290, [[T(13.02, E[i], W_, 64)], [FR(13.22, "6t − 4", "12st", Y_, 128)]]],
        [14.12, 14.98, 1000, [[T(14.12, F[i][0], W_, 60), T(14.44, F[i][1], Y_, 60), T(14.80, F[i][2], W_, 60)]]],
        [15.40, 17.12, 250, [[T(15.40, G[i], Y_, 60)]]],
        [17.22, 19.62, 300, [[T(17.22, Hs[i][0], W_, 60), T(17.40, Hs[i][1], Y_, 60)]]],
        [23.12, 26.30, 300, [[T(23.12, I[i][0], W_, 46), T(23.58, I[i][1], W_, 46), T(24.24, I[i][2], Y_, 46)]]],
        [27.12, 28.78, 950, [[T(27.12, J[i][0], Y_, 60)], [T(28.14, J[i][1], W_, 54)]]],
        [29.82, 30.88, 800, [[T(29.82, K[i], W_, 54)]]],
        [31.16, 32.90, 300, [[T(31.16, L[i][0], W_, 54)], [T(31.52, L[i][1], Y_, 60)]]],
        [33.40, 35.10, 250, [[T(33.40, M[i][0], W_, 60), T(33.86, M[i][1], Y_, 60)]]],
        [35.18, 36.40, 250, [[T(35.18, N[i][0], W_, 60), T(35.34, N[i][1], Y_, 60), T(35.60, N[i][2], W_, 60)]]],
    ]
    return {"intro": INTROS[i], "groups": groups}


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    lines = ["# 15 video Kuasai Algebra: hook & tajuk\n"]
    for i in range(15):
        json.dump(variant(i), open(os.path.join(out, f"v{i + 1:02d}.json"), "w"), ensure_ascii=False, indent=1)
        lab, h1, h2 = HOOKS[i]
        lines.append(f"## Video {i + 1:02d}\n- Hook: **{lab}** / {h1} **{h2}**\n- Tajuk posting: {TITLES[i]}\n")
    open(os.path.join(out, "titles.md"), "w").write("\n".join(lines))
    print("ok")
