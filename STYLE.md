# STYLE VIDEO 2 — Template Editing

Style rujukan untuk semua video seterusnya. Contoh siap: `video2/preview_video2.mp4`.

## Fail template

| Fail | Guna |
|---|---|
| `video2/composition/index.html` | Komposisi HyperFrames (HTML + GSAP): text, motion graphics, background ABC |
| `video2/tools/transcribe.py` | Transcribe suara (faster-whisper, Bahasa Melayu, timing setiap perkataan) |
| `video2/tools/build_base.py` | Potong jeda, punch-in zoom, colour grade, proses suara |
| `video2/tools/make_audio.py` | Muzik lo-fi + sound effects (whoosh, pop, ding) |
| `video2/tools/render_overlay.js` | Render komposisi kepada frame PNG lutsinar (Playwright) |

Untuk video baru: guna semula fail ni. Tukar text, timing dan kedudukan zoom ikut RAW baru.

## 1. Background ABC

- Simbol subjek samar: `A B C a`, `ب ت`, `1 2 3 + − × ?`
- Warna putih & kuning, opacity rendah (20–30%)
- Muncul dengan pop kecil di awal, kemudian terapung & bergoyang perlahan sepanjang video
- Hanya di ruang atas (kawasan text). Simbol di tepi, tak bertindih dengan text
- Gradient gelap lembut di bahagian atas supaya text jelas

## 2. Text & Typography

- Font **Montserrat** bold (800/900)
- Baris kecil: **putih** ~46px. Baris utama: **kuning** `#FFD21F` ~66px
- Letak di ruang atas sahaja — jangan tutup muka atau produk
- Satu kad untuk satu idea. Garisan kuning (highlight) pada kata kunci, ikut timing suara
- Jangan terlalu banyak text

## 3. Motion Graphics

- Kad text masuk dengan pop (back-out), keluar dengan fade ke atas
- Senarai (contoh subjek): badge kuning + chip putih ✓ yang muncul tepat bila disebut
- Nombor penting (contoh "2027?") muncul dengan pop
- CTA "BEG KUNING" + ikon bakul kuning yang melantun di hujung
- Light flash lembut pada setiap pertukaran bahagian

## 4. Footage

- Hook kuat dalam 3 saat pertama (zoom masuk cepat)
- Buang jeda janggal & perkataan berulang. Kekalkan ayat asal
- Punch-in zoom bertukar setiap ayat untuk tutup jump cut
- Bingkai ikut kedudukan muka (jangan potong muka)

## 5. Colour Grade

- Cerah, segar, natural — angkat shadow, contrast lembut, saturation +10%
- Tajam sedikit. Jangan overexpose, jangan smoothing, jangan ubah muka
- Warna produk kekal asal. Vignette lembut

## 6. Audio

- Suara asli sahaja, dominan (EQ + compressor ringan)
- Muzik lo-fi perlahan (~92 bpm), automatik turun (ducking) bila bercakap
- Whoosh setiap tukar kad, pop halus untuk chip, ding pada CTA
- Loudness akhir -14 LUFS

## 7. Output

- 9:16, 1080×1920, 30fps, HD
- **PREVIEW dahulu. Jangan final render sehingga diluluskan.**

---

## Prompt untuk video seterusnya

```
VIDEO [nombor] — Ikut STYLE.md

RAW video: [link Google Drive — "Anyone with the link"]
Produk: [nama produk]
Hook (kalau ada): [ayat hook]
CTA: [contoh: Dapatkan di beg kuning]
Tambahan / beza: [kalau ada]
```
