# La presentazione

[`DottorCloud.pptx`](./DottorCloud.pptx): 18 slide in 16:9 che rispondono alle
domande dei centri (chi vede cosa, agende e stanze, cartella clinica, fatturazione,
comunicazione, telefono, app, dati), con le **note per chi presenta** su ogni
slide. [`DottorCloud.pdf`](./DottorCloud.pdf) è la stessa, da mandare via email.

## Rifarla

```bash
cd sorgenti
npm install pptxgenjs react react-dom react-icons sharp   # in una cartella a parte, poi NODE_PATH
NODE_PATH=/percorso/node_modules node build.cjs            # → ../DottorCloud.pptx

cd pdf                                                     # PDF con Chromium
# accanto a tohtml.py servono carlito-regular.ttf e carlito-bold.ttf (Google Fonts)
python3 tohtml.py ../../DottorCloud.pptx deck.html         # pip install python-pptx pillow
node pdf.mjs                                               # → ../../DottorCloud.pdf
```

- Le immagini in `sorgenti/img/` sono le interfacce del video, riprese con
  `../video/sorgenti/grab.mjs`.
- Il PDF non passa da LibreOffice: `tohtml.py` ricostruisce ogni slide in HTML
  (testo vero, selezionabile) e disegna le ombre come immagini sfumate.
