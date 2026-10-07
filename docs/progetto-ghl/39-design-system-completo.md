# 39 — Il design system, tutto: i componenti che mancavano e il kit del marchio

> ✅ **FATTO (01/10/2026)**. Il doc 33 aveva applicato Espresso al gestionale: i grigi
> del marchio, il pieno dell'azione, la coda della nuvola sul solid, la croce su
> switch, radio e campi obbligatori. Restavano i componenti che frappe-ui non ha
> (StatTile, EmptyState, Tag, "in corso", il percorso, l'evento dell'agenda) e i segni
> sui componenti che ha (avatar, menu, liste, calendario, finestre). Ora ci sono
> tutti, e in `brand/dottorcloud/` c'è il kit grafico completo con gli script che lo rifanno.

## Com'è

```
Oggi
┌▓▓ Attesi ▓▓▓▓ ✚✚✚┐ ┌ In attesa ✚✚✚┐ ┌ Venuti ✚✚✚┐ ┌ Non venuti ✚✚✚┐
│▓▓ 5             ▓│ │ 0           │ │ 0         │ │ 0             │
└▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┘ └─────────────┘ └───────────┘ └───────────────┘
 (il primo numero della fila è il blocco verde profondo)

Laura Consenso
 ✓───────────✓───────────✚───────────④───────────✓
 Arriva      Prenota     Visita      Dopo        A casa
 Instagram   Online      2 ott,      ·           Area pazienti
 · 29 set    · 29 set    10:00                   · 30 set
```

- **StatTile** (`components/Espresso/StatTile.vue`): il numero a 28px con le cifre
  tabulari, il motivo delle croci nell'angolo, mai sotto le parole. In **Oggi** i
  quattro conti del giorno; nella **dashboard** ogni widget numero è uno StatTile, e
  il primo numero di ogni fila della griglia è il blocco verde profondo
  (`highlightedNumbers`, uno per fila).
- **EmptyState**: la piccola composizione dei blocchi della copertina (verde scuro con
  la croce, il verde del logo, la menta con la gobba, l'inchiostro), il titolo che
  dice lo stato, la frase che propone cosa fare. In tutte le liste vuote (al posto
  dell'icona) e in Oggi ("Niente in agenda in questo giorno · Apri l'agenda").
- **Tag** (`CategoryTag.vue`): che tipo di cosa è, squadrato con la coda, mai una
  pillola di stato. Il tipo dei piani (gli esercizi in viola), "Dati sanitari" sui
  documenti (rosa).
- **In corso** (`InProgressBadge.vue`): il verde tenue del marchio con la croce al
  posto del pallino. Una chiamata in corso, un ciclo di sedute attivo, un piano di
  cura in corso nell'area, i numeri "Adesso" della dashboard.
- **Il percorso** (`PersonJourney.vue`): le cinque tappe Arriva → Prenota → Viene →
  Dopo → A casa in testa alla scheda della persona. **Tolto il 01/10/2026**: in
  testa alla scheda non serviva, e ripeteva quello che la scheda dice già (gli
  appuntamenti, i documenti, i piani). Il PatientJourney resta nel design system
  (`brand/dottorcloud/design-system/espresso/componenti/PatientJourney`), non nel gestionale.
- **L'evento dell'agenda**: nella vista per professionista o ambulatorio
  l'appuntamento ha la coda, il fondo e la barretta nel colore del servizio e l'ora
  in quel colore; il **primo appuntamento** di una persona (con la clinica, la prima
  visita) è il blocco pieno del marchio; quello **in corso adesso** ha l'anello e la
  croce; l'**annullato** è grigio e barrato. Nelle viste settimana e mese gli eventi
  di frappe-ui hanno la coda.
- **I cicli di sedute** a tappe: un segmento per seduta, le usate nel verde del logo
  (fino a trenta; oltre, la barra). Anche nell'area clienti.
- **La croce che carica**: le pagine che aspettano mostrano la croce che ruota e
  respira (`LoaderMark.vue`); con "riduci il movimento" sta ferma.

E sui componenti di frappe-ui, senza riscriverli (`espresso.css`, regole segnate
"markup"):

- **Avatar a nuvola** (tre angoli tondi, la punta in basso a sinistra): le persone del
  centro sul verde tenue, chi ci lavora sul pieno del marchio (`UserAvatar`); tondo
  solo chi è fuori dal centro (`dc-avatar--round`).
- **La coda** su menu, liste aperte di select e autocomplete, calendari, popover,
  carte (`rounded-lg` o `rounded-xl` con il bordo) e avvisi.
- **La voce scelta** di una lista è segnata dalla croce, non dalla spunta (select,
  autocomplete, i menu di DottorCloud con `dc-scelto`).
- **Le righe scelte** di una lista sul verde tenue; la barra delle azioni in blocco
  è un blocco verde profondo con la coda (`dc-list-bar`); sul telefono le righe
  scelte si colorano (`dc-riga-scelta`).
- **Il calendario di una data**: il giorno scelto nel pieno con la coda, oggi nel
  colore del marchio con una piccola croce sotto.
- **Le finestre**: il velo tinto di verde profondo, l'icona in una nuvola.
- **Lo switch**: la croce entra con un piccolo rimbalzo.
- **L'attesa**: lo spinner, fuori dai pulsanti, nel colore del marchio.
- **Il toast** anche nel tema scuro: le parole chiare sul blocco (prima erano scure
  sul verde scuro), la spunta in menta.
- Il pulsante tenue del marchio (`dc-brand`) per l'azione secondaria che riguarda la
  persona.

## Il kit del marchio (`brand/dottorcloud/`)

Consegnato come `dottorcloud-kit.zip`, entra nel repo così:

| Nel kit | Nel repo | |
|---|---|---|
| `01-marchio/logo` | `brand/dottorcloud/logo` | identici, già c'erano |
| `01-marchio/font` | `brand/dottorcloud/font` | Inter variabile, latino (48 KB) |
| `01-marchio/icone` | `brand/dottorcloud/icone` | le 32 icone Lucide più usate, come immagini |
| `02-token` | `brand/dottorcloud/design-system/espresso/tokens.*` | quelli del repo, con il grigio delle etichette corretto (4.5:1) |
| `03-forme`, `04-composizioni` | `brand/dottorcloud/forme`, `brand/dottorcloud/composizioni` | croce, motivo, nuvola-D, gobba, avatar; copertina, hero e chiusura del sito, stato vuoto, og:image |
| `05-gestionale/espresso` | `brand/dottorcloud/design-system/espresso` | quello del repo è più nuovo (le correzioni del doc 33); dal kit arriva `sito.md`, sito e gestionale a confronto |
| `06-sito` | `brand/dottorcloud/sito` | lo strato CSS del sito, le due righe di HTML, gli screenshot prima e dopo |
| `07-generatori` | `brand/dottorcloud/generatori` | con i percorsi del repo (`percorsi.py`) e le correzioni portate dentro: rigenerano esattamente i file del repo |

Le logiche del marchio e come rigenerare stanno nel [README di `brand/dottorcloud/`](../../brand/dottorcloud/README.md).

## Come è fatto

| File | Cosa fa |
|---|---|
| `frontend/src/espresso-componenti.css` | I token che mancavano (stati, categorie, il tenue e il pieno del marchio, la coda) e le classi `dc-*` dei componenti; tutto sul marchio acceso, quindi un altro verticale li colora con i suoi |
| `frontend/src/espresso.css` | Sezioni 14–24: avatar, coda, voce scelta, righe e barra, calendario, finestre, toast, spinner, avvisi, `dc-brand`, eventi del calendario |
| `frontend/src/components/Espresso/` | `StatTile`, `EmptyState` + `EmptyArt`, `CategoryTag`, `InProgressBadge`, `LoaderMark` |
| `frontend/src/utils/dashboard.js` | `highlightedNumbers()`: il primo numero di ogni fila — testato |
| `frontend/src/utils/cicli.js` | `tappe()`: un segmento per seduta — testato |
| `crm/api/appointments.py` | `first_visit` sugli appuntamenti dell'agenda: il primo non annullato di una persona che non era già cliente |
| `frontend/src/App.vue` | Le date di dayjs in italiano per chi usa l'italiano ("mercoledì 30 settembre", "3 minuti fa") |

Con la clinica "Primo appuntamento" diventa "Prima visita" (`crm/clinica/parole.py`).

## Test

- `crm/tests/test_scheduling.py`: l'agenda segna la prima visita, non quella
  annullata, non le successive, non chi era cliente da prima.
- `tests/unit/dashboard.test.js`, `cicli.test.js`.
- I generatori del marchio rigenerano i 28 componenti e i token del repo senza
  differenze (solo il percorso del font, ora `brand/dottorcloud/font`).
- Nel browser, in chiaro, in scuro e sul telefono: Oggi, la dashboard, le liste con
  le righe scelte, la scheda della persona, i piani e i documenti, il toast, la
  vista per professionista dell'agenda.

## Tradotto

Oltre alle parole nuove, quelle dei file toccati che erano ancora in inglese: Oggi,
le chiamate, i documenti, la dashboard (finestre, periodi, libreria), i cicli, i
preventivi nell'area, e le coppie della clinica che non avevano la traduzione
("Paziente dal", "Nuovi pazienti", "Diventato paziente"…).
