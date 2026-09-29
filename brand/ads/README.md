# Le ads

Grafiche e spot brevi per le campagne (Meta: Facebook e Instagram), pronti da
caricare. I testi da mettere nell'inserzione sono in [`testi.md`](./testi.md).

## Grafiche — [`grafiche/`](./grafiche/)

Sei idee, ognuna in tre formati: `1x1` (1080×1080, feed), `4x5` (1080×1350, feed
su telefono) e `9x16` (1080×1920, storie e reel, con le fasce in alto e in basso
libere per i pulsanti della piattaforma). Nel quadrato il sottotitolo si toglie:
lo porta il testo dell'inserzione.

| File | Titolo | Per chi |
|---|---|---|
| `tutto-*` | Tutto il tuo centro medico, in un posto solo. | Apertura, chi non ci conosce |
| `livelli-*` | Ognuno vede solo quello che gli serve. | Titolari, direttori sanitari |
| `fattura-*` | La fattura nasce dalla visita. | Amministrazione, titolari |
| `conferme-*` | I pazienti confermano da soli. | Segreterie, disdette e buchi in agenda |
| `casa-*` | Piani ed esercizi, sul telefono del paziente. | Fisioterapia, nutrizione |
| `privacy-*` | I dati dei pazienti, protetti. | Chi teme il cloud |

## Spot video — [`video/`](./video/)

Quattro spot da circa 14 secondi, ognuno su una cosa sola: aggancio col marchio e
il titolo, la scena del prodotto, chiusura con logo e "Richiedi una demo". In
`9x16` (storie, reel) e `4x5` (feed); ognuno ha la sua copertina `.jpg`.

| File | Titolo |
|---|---|
| `DottorCloud-ad-chat-*` | I pazienti confermano da soli. |
| `DottorCloud-ad-fatt-*` | La fattura si fa da sola. |
| `DottorCloud-ad-app-*` | I tuoi pazienti, con la loro app. |
| `DottorCloud-ad-ex-*` | Gli esercizi a casa, finalmente seguiti. |

Il reel verticale di un minuto è in [`../video/DottorCloud-reel.mp4`](../video/DottorCloud-reel.mp4).

## Rifarle

```bash
cd sorgenti && node grafiche.mjs            # tutte le grafiche in ../grafiche/
# una sola, da guardare nel browser: grafiche.html?c=fattura&f=4x5
cd ../../video/sorgenti && node render.mjs v ad-fatt ../../ads/video/DottorCloud-ad-fatt-9x16.mp4
```

Le grafiche prendono le schermate da `../presentazione/sorgenti/img/` (riprese dal
video) e logo e colori dal design system; titoli e sottotitoli sono in `C` dentro
`grafiche.html`. Gli spot sono tagli del video (`PLANS` e `AD` in
`../video/sorgenti/video.html`).

Valgono le stesse verifiche di [`../README.md`](../README.md): "ogni accesso
registrato" e "server in Europa" vanno confermati prima di pubblicare. Nessun
prezzo.
