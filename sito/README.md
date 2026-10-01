# Il sito di DottorCloud

Il sito pubblico di DottorCloud, per `dottorcloud.it`. Presenta il gestionale finito
come fanno il video, la presentazione e le inserzioni in [`../brand/`](../brand/): stesse
frasi, stesse schermate, stesso percorso del paziente (Arriva → Prenota → Visita → Dopo →
A casa → Il centro). Nessun piano e nessun prezzo, per scelta: un test lo controlla.

È un sito statico: HTML, un foglio di stile, poco JavaScript e un file PHP per il modulo
della demo. Nessun cookie e niente caricato da altri siti (caratteri, immagini e video
arrivano dal nostro server), quindi nessun banner per il consenso.

## Le pagine

| Indirizzo | File | Cosa c'è |
|---|---|---|
| `/` | `pagine/index.html` | Il titolo del video, l'agenda con l'app del paziente, il percorso, cinque funzioni, utenti illimitati, il video, la privacy, le domande dei centri |
| `/funzioni/` | `pagine/funzioni.html` | Tutto il prodotto, tappa per tappa, con le schermate della presentazione |
| `/per-chi/` | `pagine/per-chi.html` | Ogni ruolo (titolare, segreteria, medici, amministrazione, marketing, pazienti) e ogni tipo di centro |
| `/dati-e-privacy/` | `pagine/dati-e-privacy.html` | I dati dei pazienti, protetti; chi siamo |
| `/demo/` | `pagine/demo.html` | Il modulo "Richiedi una demo" |
| `/demo/grazie/`, `/demo/errore/` | `pagine/demo-*.html` | Dove va il modulo senza JavaScript (fuori dai motori di ricerca) |
| `/privacy/`, `/cookie/` | `pagine/privacy.html`, `pagine/cookie.html` | Informativa e cookie del sito |
| `/404.html` | `pagine/404.html` | La pagina che non c'è |

## Com'è fatto

| Dove | Cosa |
|---|---|
| `pagine/` | Una pagina per file: in cima un commento con `title`, `description`, `path`, `nav` (la voce del menu accesa) e `index: no` per tenerla fuori dai motori di ricerca; sotto, il contenuto di `<main>` |
| `parti/` | Lo scheletro (`layout.html`), la testata, il piè di pagina e la fascia finale "Vediamolo sul tuo centro" (`cta.html`) |
| `risorse/css/sito.css` | Lo stile. I colori, i raggi, le ombre e i movimenti sono i token di [`../brand/design-system/tokens.css`](../brand/design-system/), messi davanti al foglio dalla build |
| `risorse/js/sito.js` | Il menu sul telefono, le cose che arrivano mentre si scorre, il video, il capitolo acceso in Funzioni, il modulo inviato senza lasciare la pagina. Tutto funziona anche senza |
| `risorse/icone/` | Le icone Lucide usate dal sito (licenza ISC, in `LICENSE`), solo le forme: la build le mette dentro l'HTML |
| `risorse/img/` | Le schermate del video in WebP e l'immagine per i link condivisi, fatte da `immagini.py` |
| `api/richiesta-demo.php` | Il modulo della demo: controlla i campi, ferma i robot e le richieste ripetute, manda un'email a NPM2 |
| `server/nginx.ssl.conf_sito` | La nostra 404 e qualche intestazione di sicurezza per nginx su HestiaCP |
| `build.mjs` | Costruisce il sito in `dist/`, senza dipendenze |
| `deploy.sh` | Lo pubblica sul server |
| `test/sito.test.mjs` | I test: pagine, collegamenti, immagini, nessun prezzo, il modulo con PHP |

Il logo, il carattere Inter e il video non sono copiati qui: la build li prende da
`brand/` (e l'icona per il telefono da `crm/public/manifest/`).

Nelle pagine: `{{> cta}}` inserisce una parte, `{{icon calendar-days}}` un'icona,
`{{email}}`, `{{company}}`, `{{address}}` e `{{vat}}` i dati di NPM2 Solutions Srl, che
stanno una volta sola in `build.mjs`. Le immagini prendono larghezza e altezza dal file.

## Provarlo

```bash
node sito/build.mjs                        # → sito/dist
php -S localhost:8080 -t sito/dist         # http://localhost:8080 (il modulo vuole PHP)
node --test sito/test/sito.test.mjs        # i test, PHP compreso se c'è
```

`SITO_URL` cambia l'indirizzo del sito (canonico, sitemap), `SITO_ANTEPRIMA=1` lo tiene
fuori dai motori di ricerca.

## Pubblicarlo

Il sito sta sul server HestiaCP di NPM2 (`hosting.npm2solutions.com`, 91.99.201.178),
come Worgify: un utente del pannello tutto suo, `dottorcloud`, proprietario del dominio
`dottorcloud.it`. Nessuna chiave e nessuna password in questo repository.

### Da GitHub: il push su `develop` mette online

Il workflow [Pubblica il sito](../.github/workflows/sito-pubblica.yml) parte a ogni push
su `develop` che cambia `sito/` o `brand/`, o a mano da Actions → Pubblica il sito → Run
workflow. Sulla macchina di GitHub:

1. fa girare i test (pagine, collegamenti, immagini, nessun prezzo, il modulo): se uno
   fallisce non pubblica niente;
2. controlla `DEPLOY_PATH`: deve essere `/home/<utente>/web/<dominio>/public_html`, con
   l'utente della chiave (mai `root` né `admin`), perché la copia cancella quello che non
   fa parte del sito e sul server ci sono altri siti;
3. lancia `deploy.sh` per quel dominio: costruisce il sito, controlla che `public_html`
   contenga solo il nostro sito o la pagina d'attesa del pannello, copia `dist/` con
   `rsync --delete`, mette la 404 e, se manca, `private/sito.ini`;
4. controlla che il sito risponda (in https quando il DNS punta al server).

I secrets (Settings → Secrets and variables → Actions), che nessuno può rileggere ma solo
sostituire:

| Secret | Valore |
|---|---|
| `SSH_HOST` | `91.99.201.178` |
| `SSH_USER` | `dottorcloud` |
| `DEPLOY_PATH` | `/home/dottorcloud/web/dottorcloud.it/public_html` |
| `SSH_KEY` | la metà privata della chiave `dottorcloud-actions-deploy` |
| `SSH_PORT` | facoltativo, 22 se manca |

La chiave serve solo a questo ed è autorizzata solo sull'utente `dottorcloud`: GitHub
scrive nella cartella del sito e basta, senza root, senza il pannello Hetzner, senza gli
altri siti. Per cambiarla: una chiave nuova, il secret `SSH_KEY` sostituito, la vecchia
tolta dall'utente nel pannello.

### Una volta sola, dal pannello

1. **L'utente.** Da `admin`: USERS → Add User `dottorcloud`, poi Edit → *SSH Access*
   `bash` (serve a rsync).
2. **La chiave**, su un computer qualsiasi:
   `ssh-keygen -t ed25519 -N "" -C dottorcloud-actions-deploy -f dottorcloud-deploy`.
   Il contenuto di `dottorcloud-deploy.pub` va nell'utente `dottorcloud` (USERS → la
   chiave in alto → SSH Keys → Add SSH Key); tutto `dottorcloud-deploy`, righe `BEGIN` ed
   `END` comprese, va nel secret `SSH_KEY`. Poi il file privato si cancella.
3. **Il dominio.** Entrati come `dottorcloud`: WEB → Add Web Domain `dottorcloud.it`, con
   l'alias `www.dottorcloud.it`. Il primo giro del workflow sostituisce la pagina d'attesa.
4. **Il DNS.** È su Teliko (`dns1.teliko.net`): il record A di `dottorcloud.it` va portato
   a 91.99.201.178; `www` è un CNAME di `dottorcloud.it` e lo segue. Quando punta qui,
   nel dominio: SSL → Let's Encrypt, Force SSL, e il rimando di `www` al dominio.
5. **nginx**, la nostra 404 e le intestazioni di sicurezza di `server/`: da root, una
   volta, `sito/deploy.sh dottorcloud.it --nginx` con `SITO_SSH=root@hosting.npm2solutions.com`
   e `HESTIA_USER=dottorcloud`. Senza, il sito funziona con la 404 del pannello.
6. **L'email del modulo.** In `private/sito.ini` (fuori da `public_html`, il workflow lo
   crea la prima volta e poi non lo tocca): `destinatario` riceve le richieste, `mittente`
   le manda (`sito@dottorcloud.it`). Perché non finiscano nello spam, il record TXT di
   `dottorcloud.it`, oggi `v=spf1`, diventa
   `v=spf1 ip4:91.99.201.178 ip6:2a01:4f8:1c1f:b10d::1 ~all`. `archivio` tiene anche una
   copia di ogni richiesta in un file, se si vuole. Poi una richiesta di prova dal sito.

### A mano, da un computer

`deploy.sh` fa la stessa cosa da un computer con Node, rsync e SSH:

```bash
SITO_SSH=dottorcloud@91.99.201.178 SITO_SSH_KEY=dottorcloud-deploy sito/deploy.sh dottorcloud.it
sito/deploy.sh dottorcloud.it --prova    # cosa cambierebbe, senza cambiare niente
```

Da root ha anche `--crea` (aggiunge il dominio se manca e il certificato quando il DNS
punta qui) e `--nginx`. Un'anteprima fuori dai motori di ricerca:
`sito/deploy.sh dottorcloud.preview.npm2solutions.com` (`*.preview` punta già qui).

## Cambiarlo

- **Un testo**: nella pagina in `pagine/`; titolo e descrizione per Google nel commento in cima.
- **Una pagina nuova**: un file in `pagine/` con il suo `path`; la sitemap si aggiorna da
  sola, il menu è in `parti/header.html` e `parti/footer.html`.
- **Un'immagine**: la schermata in `brand/presentazione/sorgenti/img/`, il nome e la
  larghezza in `immagini.py` (`pip install pillow`, poi `python3 sito/immagini.py`), e
  nella pagina `<img src="/img/nome.webp" alt="…">`.
- **Un'icona**: da [lucide.dev](https://lucide.dev), solo le forme dentro `<svg>`, in
  `risorse/icone/<nome>.svg`.

## Prima di pubblicarlo

- Come per il resto del materiale ([`../brand/README.md`](../brand/README.md)), sono da
  confermare "ogni accesso registrato", "i dati non escono dall'Unione europea", "senza
  addestramento sui dati" per l'IA, la registrazione delle chiamate e l'avviso automatico
  dalla lista d'attesa. L'assistente IA ha l'etichetta "Presto".
- L'informativa privacy e la pagina dei cookie vanno lette da chi segue la privacy di NPM2:
  il fornitore della posta, i tempi di conservazione.
- Nel piè di pagina ci sono ragione sociale, sede e partita IVA; se si vogliono, numero REA
  e capitale sociale vanno aggiunti in `parti/footer.html`.
- Il dominio è `dottorcloud.it` (`SITO_URL` in `build.mjs`).
