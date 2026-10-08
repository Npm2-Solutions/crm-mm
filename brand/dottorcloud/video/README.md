# Il video

[`DottorCloud.mp4`](./DottorCloud.mp4): 2:17, 1920×1080, 30 fps, con musica ed
effetti. [`DottorCloud.jpg`](./DottorCloud.jpg) è la copertina, già messa come
primo fotogramma. [`testo-social.txt`](./testo-social.txt) è il testo da
accompagnare; [`storyboard.md`](./storyboard.md) racconta scena per scena.

[`DottorCloud-reel.mp4`](./DottorCloud-reel.mp4): la versione verticale per reel e
storie, 1080×1920, circa un minuto. Tiene le scene che si leggono su un telefono
(WhatsApp, cartella, fattura, area paziente, esercizi, livelli, privacy) con il
testo in alto e l'interfaccia sotto; lascia fuori l'agenda e il marketing, troppo
larghi per uno schermo verticale. Gli spot brevi per le ads sono in
[`../ads/`](../ads/).

## Rifarlo

Tutto sta in `sorgenti/`: il video è una pagina HTML animata fotogramma per
fotogramma (`video.html`), la musica e gli effetti sono sintetizzati da
`audio.py` sullo stesso piano delle scene.

```bash
cd sorgenti
pip install numpy imageio-ffmpeg                  # ffmpeg incluso
node render.mjs                                    # → ../DottorCloud.mp4 (+ .jpg)
node render.mjs v reel ../DottorCloud-reel.mp4     # il reel verticale
node render.mjs v ad-chat ../../ads/video/DottorCloud-ad-chat-9x16.mp4
node shoot.mjs 12.5 40                             # fotogrammi singoli in stills/
node shoot.mjs v reel 5 20                         # … anche per gli altri tagli
```

`render.mjs [formato] [piano] [file]`: formato `h` (1920×1080), `v` (1080×1920) o
`p` (1080×1350); piano `full`, `reel`, `ad-chat`, `ad-fatt`, `ad-app`, `ad-ex`.
Cattura al doppio della risoluzione e riduce (il testo non trema), costruisce
l'audio dal piano, prende la copertina dall'ultimo fotogramma fermo e la mette
come primo fotogramma.

- **Scene e tempi**: `PLANS` in `video.html` (durata della coreografia,
  transizione, rallentamento, pausa finale); l'audio li legge dal piano che
  `render.mjs` gli passa.
- **Formati verticali**: `layoutPortrait()` in `video.html` mette il testo in alto
  e ridimensiona l'interfaccia sotto; i testi degli spot sono in `AD`.
- **Il logo** arriva da `brand.js`, generato da `../logo/sorgenti/brand_js.py`.
- **Le immagini della presentazione** si riprendono dalle scene con
  `node grab.mjs` (scrive in `../../presentazione/sorgenti/img/`).
- Serve Chromium con Playwright (`/opt/node22/lib/node_modules/playwright`: se è
  altrove, cambia l'import in cima agli script).
