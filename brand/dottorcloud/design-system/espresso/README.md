# DottorCloud su Espresso — il design system del gestionale

La tavola con tutti i componenti, in chiaro e in scuro: [`anteprima.html`](./anteprima.html) (aprila nel browser).
I valori: [`tokens.json`](./tokens.json) e [`tokens.css`](./tokens.css) (variabili con gli stessi nomi di frappe-ui).
Come è applicato al gestionale, e cosa è stato sistemato applicandolo: [`frappe-ui.md`](./frappe-ui.md) (il CSS è in `frontend/src/espresso.css` e `espresso-componenti.css`). Sito e gestionale a confronto: [`sito.md`](./sito.md).

Il design system del marchio per video, slide e ads resta un livello sopra, in [`../`](../README.md).

DottorCloud è il gestionale dei centri medici di NPM2 Solutions Srl. Il gestionale è costruito con **frappe-ui** e il suo design system **Espresso**: questo sistema ne tiene la struttura, le misure compatte e i nomi delle variabili, e ci mette sopra il marchio. Logo e colori sono quelli di sempre; la nuvola del logo e la sua croce diventano i segni dei componenti.

## Principi

1. **Espresso sotto, DottorCloud sopra.** Misure, densità e componenti sono quelli di frappe-ui (controlli da 28–32px, testo a 14px, raggio 8px). Ogni personalizzazione si fa sulle sue variabili CSS (`--surface-*`, `--ink-*`, `--outline-*`, `--radius-*`, `--elevation-*`, `--focus-*`) o con poche regole in `marchio.css`: niente componenti riscritti. Il CSS pronto è in [`frappe-ui.md`](./frappe-ui.md).
2. **Riconoscibile dai dettagli.** Il marchio si vede nei punti in cui si agisce: il pieno verde dell'azione, la coda della nuvola, la croce nei controlli accesi e scelti.
3. **Il colore significa qualcosa.** Il verde acqua è il marchio e l'azione; gli accenti dicono il *tipo* di cosa (`cat-*`); gli stati dicono *come sta* (`success`, `warning`, `danger`, `info`).
4. **Ognuno vede solo quello che gli serve.** Voci, campi e azioni senza permesso non si mostrano.
5. **Leggibile.** Testo ≥4.5:1 in entrambi i temi; gli stati hanno sempre una parola o un'icona.

## I segni del marchio

1. **La nuvola-D.** Il marchio è una nuvola con il lato sinistro e la base dritti, come l'asta di una D. Nei componenti è **l'angolo in basso a sinistra quasi dritto** (`radius-tail`, 2px) mentre gli altri tre restano al raggio di Espresso. Lo hanno: il pulsante solid, la voce attiva della barra laterale e del segmentato, il giorno scelto, le carte, gli StatTile, i menu, gli avvisi, i toast, le finestre e gli eventi in agenda. Gli avatar e le piccole icone-segno sono nuvole intere (`50% 50% 50% 22%`).
2. **La croce.** La croce ricavata nel marchio è il nostro punto:
   - nel pomello dello **switch** acceso, centrata;
   - dentro il **radio** scelto, al posto del punto;
   - dopo l'etichetta dei **campi obbligatori**, al posto dell'asterisco;
   - nel **badge "in corso"** (in visita, in chiamata), al posto del pallino;
   - sulla voce scelta dei **menu**, su **oggi** nel calendario, sulla tappa corrente del **percorso**, davanti a "Nuovo paziente…" nelle ricerche e a "Adesso" in agenda;
   - nel **caricamento** di pagina (la croce che ruota);
   - come **motivo** (`dc-crosses`) solo dentro i blocchi: angolo degli StatTile. Mai sopra il testo.
3. **I blocchi.** Pochi campi di colore pieno, come nella copertina: il primo StatTile della dashboard e il toast sono `block-deep`, la barra delle righe selezionate pure, la prima visita in agenda è `brand-solid`. Uno per vista dove serve attenzione, non di più.
4. **Il logo** sta in testa alla barra laterale (orizzontale, 20px; negativo nel tema scuro) e nelle schermate vuote compare come composizione di blocchi (EmptyState).

## Colore

- **Grigi Espresso tinti.** I grigi di frappe-ui (`surface-gray-1…10`, `ink-gray-2…9`, `outline-gray-1…5`) hanno la stessa luminosità di Espresso ma una punta del verde del marchio (tinta 182° in OKLCH). Si usano esattamente come in Espresso: `surface-base` la pagina e le carte, `surface-gray-2` il fondo dei campi e dei pulsanti subtle, `surface-gray-3` l'hover, `ink-gray-8` il testo, `ink-gray-9` i titoli, `ink-gray-6` i metadati, `ink-gray-5` le etichette (un passo più scuro di Espresso, per arrivare a 4.5:1), `ink-gray-4` solo segnaposto e icone di contorno, `outline-gray-1` i filetti.
- **Azione.** `brand-solid` (teal-700, menta nel tema scuro) sostituisce il pieno grigio di Espresso (`surface-gray-10`) dove si agisce: pulsante solid, checkbox spuntata, radio scelto, switch acceso, giorno scelto. Sopra `on-brand-solid`. Hover `brand-solid-hover`.
- **Marchio tenue.** `brand-subtle` con `on-brand-subtle`: righe selezionate, pulsante subtle del marchio, avatar dei pazienti, contatore della scheda attiva, avvisi di novità.
- **Marchio come segno.** `brand` (il verde del logo, teal-500) solo per segni non testuali: barre di avanzamento, linea della scheda attiva nel tema scuro, croce del menu, anello "adesso". Sul bianco ha 3:1: mai per testo.
- **Focus.** `focus` (teal-600 / menta) al posto dell'anello grigio di Espresso: 2px pieni attorno al controllo.
- **Stati.** Le famiglie di Espresso (`green`, `amber`, `red`, `blue`) con testo `success`, `warning`, `danger`, `info` su `*-subtle`. `warning` e `danger` sono più scuri dei corrispondenti `ink-amber-8` / `ink-red-8` di Espresso, che su quei fondi non arrivavano a 4.5:1.
- **Categorie.** `cat-blue` documenti ed ecografie, `cat-violet` esercizi e marketing, `cat-amber` lista d'attesa, nutrizione e note interne, `cat-rose` cardiologia, allergie e registrazioni, `cat-green` fatto e WhatsApp. Pieno per barrette e pallini, `*-subtle` per i fondi, `*-text` per il testo.
- **Tema scuro.** Stessi nomi, valori propri: grigi di Espresso scuro tinti, il verde diventa menta e il testo sul verde si fa scuro (`teal-950`).

## Tipografia

- **Inter** (InterVar in frappe-ui), come il logo. Le classi sono quelle di Espresso: `text-base` (14px) per il testo del gestionale, `text-sm` (13) per metadati e barra laterale, `text-xs` (12) per badge e orari, `text-tiny` (11, maiuscolo) per le etichette di sezione, `text-p-base` per il testo su più righe, `text-lg-semibold` per i titoli delle carte, `text-xl-semibold` per le finestre. Spaziatura delle lettere leggermente aperta (+0.02em), come in Espresso.
- **In più per DottorCloud**: `page-title` (20px bold) per il titolo delle pagine principali, `metric` (28px bold, cifre tabulari) per gli StatTile, `tabular` per importi e orari in colonna.
- **Sito, slide e video**: `display-xl` e `display`, grandi e stretti come nella copertina. Mai nel gestionale.

## Misure, forme, profondità

- Controlli: `control-sm` 28px (la misura base di frappe-ui), `control-md` 32px per l'azione della pagina, `control-lg` 40px su telefono e nell'area paziente, `control-xs` 24px nelle barre. Icone 16px.
- Spazi: la scala di Tailwind a passi di 4px (`space-1` … `space-8`).
- Raggi di Espresso: `radius-4` (8px, `rounded`) per controlli e righe, `radius-5` per pulsanti lg e avvisi, `radius-6` (12) per carte e menu, `radius-7` (16) per finestre e StatTile, `radius-full` per badge e switch; più `radius-tail` (2px) per la coda della nuvola.
- Ombre: le elevazioni di Espresso (`elevation-sm`, `-base`, `-lg`, `-2xl`) con l'ombra tinta del verde scuro del marchio invece del nero.

## L'area paziente

Sul telefono del paziente il sistema è lo stesso, più grande, come lo disegnano il
video, le pubblicità e la presentazione (`../../presentazione/sorgenti/img/telefono-*.png`).
Nel codice sono le classi `area-*` di `frontend/src/area/area.css`:

- titolo della pagina 28px bold stretto (`area-title`), sezioni in maiuscoletto 12px
  (`area-label`);
- carte bianche con il filo e la coda (`area-card`), righe con la nuvola del tipo, le
  parole e la freccia (`area-row`, `area-chip--amber|violet|blue|rose|green`);
- il prossimo appuntamento è il blocco `block-deep` della pagina, con le croci nel
  suo angolo e l'ora in menta (`area-deep`);
- i giorni a tessera, il giorno scelto pieno (`area-day`); la spunta in una nuvola
  che si riempie del verde dell'azione (`area-check`); il codice in sei caselle
  (`area-code`);
- controlli da 40px (`control-lg`), la barra in basso con il posto aperto nel colore
  del marchio.

## Movimento

Le curve di Espresso (120–300ms). In più: il pomello dello switch e la croce entrano con un piccolo rimbalzo (`cubic-bezier(.34,1.56,.64,1)`, 160ms); la croce del caricamento ruota di 90° e respira. Con `prefers-reduced-motion` restano solo le dissolvenze.

## Linguaggio

- Italiano semplice, frasi corte, verbi. Si dice cosa fa per il centro ("La fattura nasce dalla visita").
- Il prodotto si chiama sempre **DottorCloud**: mai il nome del framework o "il CRM" nelle schermate, nelle email e nei documenti.
- Pulsanti con verbo e oggetto: "Prenota la visita", "Annulla la visita". Mai "OK".
- Errori che dicono come rimediare ("Mancano due caratteri."). Niente punti esclamativi, niente emoji nell'interfaccia.
- Date e numeri all'italiana: `12/09/2026`, `10:30`, `€ 1.250,00`.

## Iconografia

**Lucide**, come in frappe-ui (`lucide-*`), 16px, tratto 1.5–2, nel colore del testo. Il gruppo **Icons** raccoglie le più usate nel gestionale. Nessuna icona sostituisce la croce del marchio: la croce non è `lucide-plus`, è il segno disegnato dal logo (bracci uguali, larghi un terzo).

## Logo

Orizzontale su chiaro, negativo su scuro, verticale negli spazi quadrati, marchio da solo per avatar e spazi piccoli, icona per app e favicon, nero per la stampa a un colore. Spazio libero intorno almeno quanto la croce; l'orizzontale non scende sotto i 20px di altezza nella barra laterale (24px altrove). Non cambiare colori, proporzioni, non aggiungere ombre.

## Non incluso

I componenti qui sono una resa in HTML e CSS (`componenti/componenti.css`, classi `dc-*`; ogni componente ha `anteprima.html` e `README.md`) di quelli di frappe-ui con le personalizzazioni: servono a vedere e decidere. Nel gestionale si applicano con il CSS di [`frappe-ui.md`](./frappe-ui.md), da provare pagina per pagina. Non sono stati copiati: le 117 icone Vue proprie del gestionale e i font Calibri/Carlito. Video, ads e presentazione ricostruiscono le schermate con questi stessi colori e segni, nel registro del sito ([`sito.md`](./sito.md)): i sorgenti sono in `../../video/sorgenti`, `../../ads/sorgenti` e `../../presentazione/sorgenti`.
