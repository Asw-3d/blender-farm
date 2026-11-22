# Blender Farm Kit — render explainer tanpa membebani VM

Isi:
- `scene/` — proyek scene yang bisa jalan di mana saja (path relatif): `scene.py` (scene + animasi), tekstur PNG, `composite.py` (overlay pill/caption + encode mp4), `make_sign.py` (regenerasi tekstur papan).
- `.github/workflows/render.yml` — GitHub Actions: render dipecah jadi N chunk yang jalan **paralel** di runner terpisah, lalu job terakhir merakit video. Picu dari tab Actions (workflow_dispatch: frame awal/akhir, jumlah chunk, persen resolusi).
- `colab/colab_render.ipynb` — notebook Google Colab (GPU T4 gratis): install Blender, upload zip scene, render, unduh frame/video.
- `render_chunk.sh` — helper lokal: `./render_chunk.sh 1 60` me-render rentang frame itu saja.

## Cara pakai GitHub Actions
1. Repo **publik** (menit Actions gratis tanpa batas untuk repo publik; privat cuma 2.000 menit/bulan).
2. Push seluruh isi folder ini ke repo (termasuk folder `.github`). File PNG tekstur sengaja TIDAK ikut — dibuat ulang dari `make_sign.py` di runner.
3. Memicu render ada dua cara:
   - **Push perubahan `render-request.json`** (atur frame/chunks/pct di situ) — jalur utama, bisa dilakukan Muse lewat konektor GitHub.
   - Manual: tab **Actions** → "Render Blender (farm)" → **Run workflow**.
4. Hasil: job terakhir meng-commit video ke folder `renders/` (`latest.mp4` + versi bertanggal) dan juga menyimpannya sebagai artifact `video-final`.

Catatan kapasitas: frame PNG 540×960 ±0,6 MB → 240 frame ±145 MB, aman di kuota artifact gratis. Resolusi 100% (1080×1920) ±2 MB/frame → ±480 MB per episode, mepet — pakai 50% + upscale, atau unduh artifact per chunk.

## Cara pakai Colab
1. Zip isi folder `scene/` jadi `blender-scene.zip`.
2. Buka `colab/colab_render.ipynb` di Colab, setel runtime GPU (T4), jalankan sel berurutan.
3. Eevee di Colab jalan lewat `xvfb-run`; bila Eevee gagal di sesi GPU, render tetap jalan di CPU Colab (tetap lebih kencang dari VM ini).

## Angka acuan (terukur di VM Muse, 1,5 CPU berbagi)
- Eevee TAA 8, 540×960: ±6 detik/frame → 240 frame ±24 menit sendirian.
- Runner GitHub Actions 4 vCPU: perkiraan 2–3× lebih cepat per frame, dan chunk jalan paralel → 240 frame di 8 chunk ≈ beberapa menit wall-clock.
- Colab T4: belum diuji — itu eksperimen pertama yang harus divalidasi (terutama Eevee headless di GPU).
