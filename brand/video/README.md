# Il video

[`DottorCloud.mp4`](./DottorCloud.mp4): 2:17, 1920×1080, 30 fps, con musica ed
effetti. [`DottorCloud.jpg`](./DottorCloud.jpg) è la copertina, già messa come
primo fotogramma. [`testo-social.txt`](./testo-social.txt) è il testo da
accompagnare; [`storyboard.md`](./storyboard.md) racconta scena per scena.

## Rifarlo

Tutto sta in `sorgenti/`: il video è una pagina HTML animata fotogramma per
fotogramma (`video.html`), la musica e gli effetti sono sintetizzati da
`audio.py`.

```bash
cd sorgenti
pip install numpy imageio-ffmpeg        # ffmpeg incluso
python3 audio.py                        # → audio.wav
node render.mjs                         # → raw.mp4, cattura a 3840×2160 e riduce a 1080p
node shoot.mjs 12.5 40                  # fotogrammi singoli in stills/, per controllare
```

Poi copertina e primo fotogramma (con l'ffmpeg di `imageio-ffmpeg`):

```bash
ffmpeg -ss 136.3 -i raw.mp4 -frames:v 1 -q:v 2 ../DottorCloud.jpg
ffmpeg -i raw.mp4 -i ../DottorCloud.jpg \
  -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)',format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset slow -crf 18 -c:a copy -movflags +faststart ../DottorCloud.mp4
```

- **Scene e tempi**: `PLAN` in `video.html` (durata della coreografia, transizione,
  rallentamento, pausa finale) e la sua copia in `audio.py`: vanno cambiate
  insieme.
- **Il logo** arriva da `brand.js`, generato da `../logo/sorgenti/brand_js.py`.
- **Le immagini della presentazione** si riprendono dalle scene con
  `node grab.mjs` (scrive in `../../presentazione/sorgenti/img/`).
- Serve Chromium con Playwright (`/opt/node22/lib/node_modules/playwright`: se è
  altrove, cambia l'import in cima agli script).
