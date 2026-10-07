# 32 — Un segno per posto: il centro in alto, DottorCloud in fondo

> ✅ **FATTO (01/10/2026)**. Il logo del centro stava accanto a quello di
> DottorCloud in cima alla barra laterale, nell'area clienti e su ogni pagina
> pubblica: due loghi affiancati, quello del centro schiacciato in un quadratino.
> Ora ogni posto ha un segno solo. La barra laterale è di DottorCloud, come vuole
> il design system ([Espresso](../../brand/dottorcloud/design-system/espresso/README.md)): il
> suo logo in testa. Dove una persona ha a che fare con il centro (prenotazione,
> moduli, documenti, la sua area) in alto c'è il centro, disegnato com'è il suo
> logo, e DottorCloud firma in fondo, piccolo.

## Il problema

Il marchio del verticale (doc del marchio, `crm/marchio.py`) aveva una regola:
DottorCloud dappertutto, il logo del centro "al massimo accanto". Messa in pratica,
voleva dire:

- **nella barra laterale**: l'icona di DottorCloud, il logo del centro alto 24 px e
  largo al massimo 48 accanto, poi la scritta "DottorCloud". Un logo orizzontale,
  con il nome del centro dentro, diventava una riga illeggibile;
- **sulle pagine pubbliche** (prenotazione, moduli, documenti, lista d'attesa, il
  modulo del sito): "DottorCloud | logo del centro", poi il titolo con il nome del
  centro. Il paziente apriva la pagina del suo centro e leggeva prima il nome del
  software;
- **nell'area clienti**: lo stesso, con il nome del centro nascosto sul telefono.

Chi prenota cerca il suo centro, non il software. Le app che hanno lo stesso
problema lo risolvono tutte allo stesso modo: sulle pagine che vedono i clienti
l'attività che le offre, e in fondo un "Powered by" (Calendly, Cal.com, le pagine
di prenotazione dei gestionali medici); nell'app di chi ci lavora, il prodotto
(Cliniko, Jane, SimplePractice).

## Cosa cambia

**Un segno per posto, mai due affiancati.**

| Dove | In alto | In fondo |
|---|---|---|
| Barra laterale | il logo di DottorCloud (20 px, negativo nel tema scuro), l'utente sotto; chiusa, l'icona | — |
| Pagine pubbliche | il logo del centro, o il suo nome | "Con tecnologia DottorCloud" |
| Area clienti | il logo del centro, o il suo nome | "Con tecnologia DottorCloud" |
| Linguetta del browser, schermata di accesso, scrivania, email, telefono, PDF | DottorCloud | — |

**Il logo si disegna com'è.** Un logo si legge solo alla sua forma, quindi il
server la misura (`crm.marchio.forma_di`): dalla testa del file per un'immagine,
dalle misure o dal `viewBox` per un SVG.

- **Largo** (almeno una volta e mezza più largo che alto): contiene già il nome del
  centro e va da solo, fino a 44 px di altezza sulle pagine, 32 nell'area;
- **quadrato**: in una tessera accanto al nome del centro;
- **nessun logo**: le iniziali del centro nel colore del marchio ("Centro Aurora"
  → CA; "Studio di Fisioterapia" → SF, le parole di legame non contano);
- **né logo né nome**: il logo di DottorCloud fa le veci, e allora in fondo non
  firma una seconda volta.

Su fondo scuro un logo disegnato per la carta bianca resta su una piccola carta
bianca.

**La pagina di prenotazione** ha già il nome del centro come titolo: in alto solo il
logo (il suo, se ne ha uno, o quello del centro), senza ripetere il nome.

**Il nome del centro non è mai quello del software.** Un nome lasciato a
"DottorCloud" o al nome del framework non passa per il nome del centro
(`nome_scelto`), anche in Impostazioni > Nome e logo.

**Impostazioni > Il centro > Generale > Nome e logo** spiega dove vanno nome e
logo, accetta qualsiasi immagine (prima chiedeva solo `.ico`) e mostra, prima di
salvare, come appariranno in testa e in fondo alle pagine delle persone. La pagina
di prenotazione online mostra la stessa anteprima.

## Come è fatto

- `crm/marchio.py`: `forma_del_logo()` (pura), `misure_svg()` (pura),
  `misure_del_logo()` legge solo i file del sito e mai fuori dalla loro cartella,
  `forma_di()`; i dati del boot e delle pagine portano `centre_logo`,
  `centre_logo_shape` e `centre_name`. `page_branding()` dà anche `logo_shape`.
- `crm/templates/includes/marchio_segni.html` è il segno del centro in alto,
  `marchio_piede.html` la firma in fondo; `marchio_colori.html` il loro aspetto.
- Nel browser: `utils/marchio.js` (`formaDelLogo`, `misureSvg`, `iniziali`,
  `nomeDelCentro`, `misuraIlLogo`, gli stessi casi del server),
  `components/CentreTile.vue`, `composables/formaDelLogo.js` (l'area, costruita a
  parte, non carica gli store del CRM); `UserDropdown.vue` mette in testa alla
  barra il logo di DottorCloud.

## Test

- `crm/tests/test_marchio.py`: la forma sugli stessi casi del browser, le misure di
  un SVG, i file veri del sito (un SVG largo, un PNG quadrato) e gli indirizzi che
  non si leggono (altrove, mancanti, fuori dalla cartella); le pagine pubbliche con
  il centro in alto e la firma in fondo, la prenotazione con il solo logo, il
  marchio al posto del centro che non ha niente e senza firmare due volte.
- `tests/unit/marchio.test.js`: forma, misure, iniziali, nome del centro.
