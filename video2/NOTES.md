# VIDEO 2 — Buku transisi ke dua (HyperFrames)

RAW: Google Drive `Buku transisi ke dua.mov`
(https://drive.google.com/file/d/1SZRmzMxt1-v_fK63HBrlytqpdDGmGC4T/view), 29.03s, 1080x1920, 30fps.

## Status
- Preview 1 (latar kereta asal) dihantar → user minta tukar.
- Mockup v4 (latar gelap penuh) → user tukar fikiran.
- **Mockup v5 (`mockup_v5_approved.jpg`) → user ALLOW**: background kereta ASAL kekal; huruf ABC / alif ba ta
  pudar HANYA di bahagian atas & tepi (`glyphtop/index.html`), di belakang subjek (guna mask), tak tutup muka/buku/caption.
- Preview 2 dihantar (draft, -14 LUFS). Tunggu review user.
- Belum final render. **Hantar gambar/preview dulu & minta izin sebelum render.**

## Keputusan yang dah approve
- Background: gelap, huruf/nombor pudar besar (A B C 1 2 3, ا ب ت, + × −), penuh,
  sedikit kabur, drift sangat perlahan (BUKAN goyang). Ikut gaya video sebelum ni
  (screenshot: latar gelap + jalur cahaya serong + simbol pudar). Fail: `background/index.html`.
- Caption: putih + kuning (#FFD60A), Inter Black, saiz sederhana, band atas (top 330–370px).
  Tiada kotak kuning, tiada anak panah. Cip 4M kekal dalam kotak + bunyi "ting".
- SFX: swipe, boop, xylo, ting, chime (`scripts/sfx2.py`). Muzik `scripts/audio_gen.py`,
  ducked 0.13 bawah suara.
- Potongan (masa sumber): buang 12.733–14.167 ("Boleh buat persediaan awal", berulang)
  dan 17.067–17.300 (jeda). Jumlah 27.4s.

## Pipeline (bina semula)
1. Muat turun RAW → `ffmpeg -vf "eq=brightness=0.025:contrast=1.06:saturation=1.08:gamma=1.04,colorbalance=rm=0.02:bm=-0.02,unsharp=5:5:0.45,vignette=PI/5"` → `assets/graded.mp4`
2. `cd glyphtop && npx hyperframes render -q delivery -o glyph_top.mp4` (29.1s, latar hitam; screen-blend)
3. Mask (rembg): `python3 scripts/masks.py graded.mp4 masks is` lalu `... masks bi`
   (birefnet-general-lite untuk semua kecuali 8.83–14.1s = isnet). Jalankan satu model satu masa (OOM jika dua).
4. `python3 scripts/comp_final.py graded.mp4 glyph_top.mp4 masks assets/composited.mp4`
5. `npx hyperframes check` → snapshot → `npx hyperframes render -q draft` (preview), lalu ffmpeg `loudnorm=I=-14`.
