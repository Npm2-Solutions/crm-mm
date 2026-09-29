# DottorCloud — logo

Il marchio è una nuvola con il lato sinistro e la base dritti, come l'asta di una
**D**, e una croce medica ricavata in negativo. Il nome è in Inter Bold, già in
tracciati: non serve il font per aprire i file.

| File | Uso |
|---|---|
| `dottorcloud-orizzontale.svg` | Logo principale, su fondo chiaro |
| `dottorcloud-orizzontale-negativo.svg` | Su fondo scuro |
| `dottorcloud-verticale(-negativo).svg` | Quando lo spazio è quadrato o alto |
| `dottorcloud-marchio(-bianco).svg` | Solo il simbolo: avatar, timbri, spazi piccoli |
| `dottorcloud-icona-app.svg` | Icona dell'app e favicon |
| `dottorcloud-orizzontale-nero.svg` | Stampa a un colore, fax, incisioni |
| `png/` | Gli stessi, raster con fondo trasparente; icona a 1024, 512, 192 e 32 px |
| `anteprima.png` | Tutte le versioni in una tavola |

## Colori

| Nome | Hex | Dove |
|---|---|---|
| Verde acqua | `#12A594` | Marchio e "Cloud" su chiaro |
| Verde acqua scuro | `#0B6F64` | Fondo dell'icona, in sfumatura da `#17B8A4` |
| Menta | `#5FE0CC` | Marchio e "Cloud" su scuro |
| Inchiostro | `#16201E` | "Dottor" su chiaro |

## Regole

- Intorno al logo lascia uno spazio libero pari almeno all'altezza della croce.
- Il logo orizzontale non va sotto i 24 px di altezza; sotto, usa il marchio da solo.
- Non cambiare i colori, non allungare, non aggiungere ombre o contorni.

`sorgenti/` contiene gli script che generano tutto: `build.py` (geometria del
marchio e testo in tracciati, vuole `inter.woff2` accanto), `compose.py` (gli
SVG), `export.mjs` (i PNG) e `brand_js.py` (i pezzi del logo che il video anima).
