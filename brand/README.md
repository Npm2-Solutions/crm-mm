# DottorCloud — materiale del marchio

Tutto il materiale per presentare DottorCloud, il gestionale per i centri medici di
NPM2 Solutions Srl: logo, design system, video, presentazione e ads. Ogni cartella ha i
file pronti all'uso e, in `sorgenti/`, quello che serve per rifarli.

| Cartella | Cosa c'è | Da usare |
|---|---|---|
| [`logo/`](./logo/) | Marchio, logo orizzontale e verticale, negativo, a un colore, icona dell'app; SVG e PNG | [`logo/anteprima.png`](./logo/anteprima.png) · regole in [`logo/README.md`](./logo/README.md) |
| [`design-system/`](./design-system/) | Colori, tipografia, forme, ombre, movimento, suono e linguaggio; in [`espresso/`](./design-system/espresso/) il design system del gestionale, i suoi 28 componenti e il confronto con il sito | [`design-system/anteprima.png`](./design-system/anteprima.png) · [`espresso/anteprima.html`](./design-system/espresso/anteprima.html) |
| [`font/`](./font/) | Inter variabile, solo latino (48 KB): gestionale, sito, slide, video | `Inter-Variable-latin.woff2` |
| [`icone/`](./icone/) | Le 32 icone Lucide più usate, come immagini su fondo chiaro | regole in [`icone/README.md`](./icone/README.md) |
| [`forme/`](./forme/) | I segni del marchio come file: la croce (verde, bianca, menta), la piastrella del motivo, la nuvola-D con i raggi usati, la gobba, l'avatar a nuvola; SVG e PNG | [`forme/nuvola-d.png`](./forme/nuvola-d.png) |
| [`composizioni/`](./composizioni/) | Le immagini fatte di blocchi: copertina, hero e chiusura del sito, stato vuoto, immagine di condivisione (og:image 1200×630); SVG e PNG | [`composizioni/condivisione-og.png`](./composizioni/condivisione-og.png) |
| [`sito/`](./sito/) | Lo strato del marchio per il sito (`sito-marchio.css`), le due modifiche all'HTML, gli screenshot di ogni pagina prima e dopo | [`sito/README.md`](./sito/README.md) |
| [`generatori/`](./generatori/) | Gli script Python che producono token, componenti, forme, composizioni, PNG e screenshot | sotto, "Rigenerare" |
| [`video/`](./video/) | Il video di presentazione (2:17, 1920×1080, con musica) e il reel verticale di un minuto, con copertine e testo per i social | [`video/DottorCloud.mp4`](./video/DottorCloud.mp4) · [`video/DottorCloud-reel.mp4`](./video/DottorCloud-reel.mp4) |
| [`ads/`](./ads/) | Grafiche per le inserzioni (6 idee × feed quadrato, feed verticale, storie), 4 spot da 14 s in 9:16 e 4:5, i testi per Meta | [`ads/grafiche/`](./ads/grafiche/) · [`ads/testi.md`](./ads/testi.md) |
| [`presentazione/`](./presentazione/) | 18 slide per i centri, con le note per chi presenta; la stessa in PDF per l'email | [`presentazione/DottorCloud.pptx`](./presentazione/DottorCloud.pptx) · [`presentazione/DottorCloud.pdf`](./presentazione/DottorCloud.pdf) |

## Le logiche, in breve

Un marchio solo, due registri: il **gestionale** è Espresso di frappe-ui (controlli da
28–32px, testo 14px) con i colori e i segni del marchio; il **sito, le slide e i video**
usano gli stessi colori e segni in grande, con i blocchi pieni della copertina
([`design-system/espresso/sito.md`](./design-system/espresso/sito.md)).

- **I colori.** Il verde del logo `#12a594` segna, non scrive: logo, indicatori,
  croce, barre (sul bianco ha 3:1). Il verde scuro `#0b6f64` è l'azione: pulsanti
  pieni, caselle spuntate, switch accesi; nel tema scuro l'azione è la menta
  `#5fe0cc`. I grigi sono quelli di Espresso tinti verso il verde del marchio (182° in
  OKLCH). Stati e categorie hanno un pieno, un fondo tenue e un colore del testo, ogni
  coppia a 4.5:1 in chiaro e in scuro
  ([`controllo-contrasti.txt`](./design-system/espresso/controllo-contrasti.txt)).
- **La nuvola-D**: tre angoli tondi e quello in basso a sinistra quasi dritto, come il
  lato della D del marchio. Gestionale: il raggio di Espresso con la coda di 2px;
  sito: 14px sui pulsanti, 20–28px su carte e blocchi, coda di 4px; avatar e segni
  piccoli `border-radius: 50% 50% 50% 22%`.
- **La croce** ricavata nel logo (bracci uguali, larghi un terzo): è il punto del
  marchio. Nel gestionale: switch acceso, radio scelto, campo obbligatorio, "in
  corso", voce scelta, oggi nel calendario. Non è l'icona `plus`.
- **Il motivo delle croci**: croci da 20px a passo 40px, solo dentro i blocchi o negli
  angoli, mai sotto il testo.
- **La gobba**: il mezzo disco che sporge sopra un blocco, come la nuvola del logo.
  Una per composizione.
- **I blocchi**: verde scuro, verde del logo, menta, inchiostro. Sul sito dietro al
  prodotto e ai lati della chiusura; nel gestionale solo il primo numero di una fila,
  il toast e la barra delle righe scelte.

Le composizioni sono geometria pura (`generatori/genera_forme.py`, i colori da
`tokens.json`): una lastra verde scuro con il motivo delle croci in menta, un blocco
del verde del logo che esce dal bordo, un blocco menta con la gobba, un blocco
d'inchiostro stretto; il testo o il logo sempre fuori dai blocchi.

## Rigenerare

```bash
cd brand/generatori
python3 genera_token.py          # design-system/espresso/tokens.json, con il controllo dei contrasti
python3 genera_css.py            # design-system/espresso/tokens.css
python3 genera_componenti.py     # design-system/espresso/componenti/*
python3 genera_forme.py          # forme/*.svg, composizioni/*.svg
python3 rendi_png.py             # i PNG di forme e composizioni (playwright)
python3 screenshot_sito.py <cartella-sito> <uscita> "/:home:1366,/:home-telefono:390"
```

Le cartelle sono in `generatori/percorsi.py`. I generatori rifanno esattamente i file
del repo: chi cambia un componente cambia il generatore, non solo l'anteprima. Il CSS
dei componenti (`componenti/componenti.css`) e quello applicato al gestionale
(`frontend/src/espresso.css`, `espresso-componenti.css`) sono scritti a mano.

## Il messaggio

Il gestionale che tiene tutto il centro medico in un posto solo, con ognuno che
vede solo quello che gli serve. Il video e la presentazione seguono il percorso del
paziente: **Arriva → Prenota → Visita → Dopo → A casa**, più **Il centro** dietro
le quinte (permessi, persone, dati protetti).

## Prima di usarlo con i clienti

- Cartella clinica, area paziente, piani, esercizi e lista d'attesa vengono dal
  design (`docs/gestionale-medico/`) e sono mostrati come funzionanti: solo
  l'assistente IA ha l'etichetta "Presto".
- Da confermare: "ogni accesso registrato", "i dati non escono dall'Unione
  europea", "senza addestramento sui dati" per l'IA, la registrazione delle
  chiamate e l'avviso automatico dalla lista d'attesa.
- Il centro "Aurora", i pazienti e l'indirizzo `aurora.dottorcloud.it` sono
  inventati; le schermate sono ricostruite nello stile del prodotto, non catturate
  dall'app.
- Nessun prezzo, per scelta.
