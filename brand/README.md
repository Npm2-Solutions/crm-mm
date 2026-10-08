# I marchi

Ogni marchio di NPM2 ha la sua cartella, con la chiave che il codice gli dà
(`crm/marchio.py`, `Marchio.chiave`): oggi c'è solo [`dottorcloud/`](./dottorcloud/).

| Marchio | Cartella | Sito | Nel gestionale |
|---|---|---|---|
| DottorCloud | [`dottorcloud/`](./dottorcloud/) | [`siti/dottorcloud/`](../siti/dottorcloud/) | `marchio.BASE`; lo porta la clinica (`crm/verticali.py`) |

## Com'è fatta la cartella di un marchio

Le stesse sottocartelle per tutti, così generatori, sito e gestionale le trovano
allo stesso posto:

| Cartella | Cosa c'è |
|---|---|
| `logo/` | Marchio, logo orizzontale e verticale, negativo, icona dell'app; SVG e PNG |
| `design-system/` | Colori, tipografia, forme, ombre, movimento, linguaggio (`tokens.css`); in `espresso/` come il gestionale li applica |
| `font/` | Il carattere, solo latino |
| `icone/`, `forme/`, `composizioni/` | Le icone più usate, i segni del marchio, le immagini fatte di blocchi |
| `sito/` | Lo strato del marchio per il suo sito (`sito-marchio.css`) |
| `generatori/` | Gli script che rifanno token, componenti, forme e PNG (`percorsi.py` dice dove stanno le cose) |
| `video/`, `ads/`, `presentazione/` | Il video, le inserzioni, le slide, con i sorgenti per rifarli |

## Un marchio nuovo

1. Una cartella `brand/<chiave>/` con le sottocartelle sopra (si parte copiando
   `dottorcloud/` e si rifanno logo e token con i generatori).
2. Il suo sito, se ne ha uno, in `siti/<chiave>/` ([`siti/README.md`](../siti/README.md)).
3. Nel gestionale: un `Marchio` registrato con `registra_marchio` dal modulo che lo
   porta (un verticale lo nomina in `Verticale.marchio`), i suoi colori sotto
   `[data-marchio='<chiave>']` in `frontend/src/espresso.css`, le sue immagini in
   `crm/public/images/<chiave>-*.svg` e le icone e le schermate d'avvio del
   telefono in `crm/public/manifest/<chiave>/` (quelle di DottorCloud restano in
   `crm/public/manifest/`, dove i telefoni che hanno già l'app le cercano). Quello che l'utente legge dice il nome del marchio
   acceso (`{brand}`), mai «DottorCloud» scritto a mano.
