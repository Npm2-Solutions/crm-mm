# frappe-ui

Come questo sistema si applica al gestionale senza riscrivere i componenti di frappe-ui (1.0.0-beta.29, Espresso). È applicato in [`frontend/src/espresso.css`](../../../frontend/src/espresso.css), che `index.css` e l'area clienti importano dopo `marchio.css`: le variabili di frappe-ui prendono i valori del marchio, e poche regole mettono i segni del marchio dove il markup di frappe-ui lo permette. Tutto sta sotto `[data-marchio='dottorcloud']`, l'attributo che `utils/marchio.js` (`indossa()`) mette sulla pagina con la chiave del marchio acceso: un altro verticale tiene i grigi neutri di Espresso. Il pieno dell'azione (`--brand-action`: pulsante solid, switch, checkbox, radio) resta in `marchio.css`, per ogni marchio.

Le regole con un selettore di classe dipendono dal markup di frappe-ui: dopo un aggiornamento della libreria vanno ricontrollate. Sono segnate con **(markup)**.

## Cosa cambia, in breve

| Cosa | Espresso | DottorCloud | Come |
|---|---|---|---|
| Grigi | neutri | stessi valori di luminosità, tinti di verde | variabili `--surface-gray-*`, `--ink-gray-*`, `--outline-gray-*` |
| Azione (solid, switch, checkbox, radio) | `surface-gray-10` | `brand-solid` | `--brand-action` (già in marchio.css) |
| Forma del solid | `rounded-4` | coda della nuvola (2px in basso a sinistra) | regola (markup) |
| Focus | anello grigio | `focus` teal-600 / menta | `--focus-outline-default` |
| Ombre | nere | tinte di verde scuro | `--elevation-*` |
| Switch acceso | pomello bianco | pomello con la croce centrata | regola (markup) |
| Radio scelto | punto | croce | `background-image` |
| Campo obbligatorio | asterisco rosso | croce rossa | regola (markup) |
| Scheda attiva | linea `surface-gray-10` | linea `brand-solid`, icona verde | regola (markup) |
| Barra di avanzamento | `surface-gray-10` | `brand` | regola (markup) |
| Toast | `surface-gray-9` | `block-deep` con coda | regola (markup) |
| Voce attiva della barra laterale | `elevation-3` | + icona verde e coda | regola (markup) |
| Stati ambra e rosso | `ink-amber-8`, `ink-red-8` | più scuri (4.5:1) | variabili |

## Sistemato applicandolo

Il CSS proposto qui prima dell'applicazione è andato in `espresso.css` con queste correzioni, verificate nel browser (stili calcolati, in chiaro e in scuro):

- **Il grigio delle etichette** (`ink-gray-5`) un passo più scuro: `#6a716f` in chiaro, `#858c8a` in scuro. Quello di Espresso arrivava a 4.2:1 sul bianco e a 3.9:1 sul fondo delle carte scure, sotto il 4.5:1 che il principio 5 chiede; frappe-ui lo usa per etichette in peso normale, non solo in medium.
- **I grigi che il CSS proposto non toccava**, tinti come gli altri: `ink-gray-1`, `outline-gray-6…9`, `outline-elevation-1/2`, `outline-base` e `surface-elevation-3` (scuro), le ombre `elevation-md` e `elevation-xl`. Altrimenti restavano grigi neutri accanto a quelli tinti.
- **Il pieno dell'azione nel tema scuro** è la menta (`--brand-on-dark`), come dice il sistema: `marchio.css` usava il verde del logo.
- **Le icone della scheda attiva** sono spesso classi `lucide-*`, non `svg`: la regola prende entrambe (anche per la voce attiva della barra laterale).
- **L'avanzamento**: solo il riempimento figlio diretto del binario (`> .bg-surface-gray-10`), perché un contenitore `transform-gpu rounded-xl` può avere dentro un pulsante solid.
- **La croce dei campi obbligatori** anche sui campi di DottorCloud (`FieldLayout`, moduli, SLA, modelli email, motivo di perdita, griglie): portano la classe `segno-obbligatorio` al posto del solo asterisco rosso, che una regola CSS non può riconoscere.
- **Il segmentato** (TabButtons): il pulsante scelto ha la coda della nuvola. **Le schede di una voce delle impostazioni** (`SettingsHub.vue`) hanno la linea della scheda aperta nel colore dell'azione, come quelle di frappe-ui.
- **Il tooltip** resta sul grigio più scuro di Espresso (`surface-gray-10`, ora tinto): la sua freccia ha lo stesso colore e non si raggiunge da una regola sul fumetto; il tooltip non diventa comunque il pieno del marchio.

## Il resto del sistema (doc 39)

Sui componenti di frappe-ui, in `espresso.css` (sezioni 14–24, tutte **(markup)**):

| Cosa | Come |
|---|---|
| Avatar a nuvola | la radice `relative inline-block shrink-0 rounded-full` e i suoi figli; il fondo grigio del segnaposto diventa `brand-subtle`, quello del personale (`UserAvatar`, `dc-avatar--staff`) `brand-solid`; `dc-avatar--round` resta tondo |
| La coda su ciò che galleggia e sulle carte | `.menu-content`, `[data-slot='content-body'][data-panel]` (PopoverPanel: select, autocomplete, date), `div.rounded-lg.border`, `div.rounded-xl.border`, l'Alert (`grid-cols-[auto_1fr_auto] rounded-md`), gli eventi del calendario (`.event.rounded`) |
| La voce scelta con la croce | la `lucide-check` nel suffisso di `[role='option']`, e `dc-scelto` nei menu nostri: la maschera della spunta diventa quella della croce |
| Righe scelte e barra delle azioni | ListRow (`flex-col transition-all duration-300 ease-in-out bg-surface-gray-2`) su `brand-subtle`; ListSelectBanner con `class="dc-list-bar"` in blocco profondo; sul telefono `dc-riga-scelta` |
| Calendario di una data | `button[role='gridcell'][aria-selected='true']` nel pieno con la coda; oggi (`font-semibold`) nel colore del marchio con la croce sotto |
| Finestre | `.dialog-overlay` tinto di verde profondo; l'icona (`h-7 w-7 rounded-full`) in una nuvola |
| Switch | la croce del pomello cresce con un rimbalzo (`background-size`); ferma con "riduci il movimento" |
| Toast nel tema scuro | `.text-ink-base` del toast in `on-block-deep`: frappe-ui lo scrive nell'inchiostro scuro, illeggibile sul blocco |
| Spinner | `.fui-spinner` fuori dai pulsanti, senza un colore suo, in `brand-segno` |

I componenti che frappe-ui non ha sono del gestionale, in
`frontend/src/components/Espresso/`, con le classi di `espresso-componenti.css`:
`StatTile` (`dc-stat`; i numeri della dashboard con `dc-numero`), `EmptyState` e
`EmptyArt` (`dc-empty`), `CategoryTag` (`dc-tag`), `InProgressBadge` (`dc-in-corso`),
`LoaderMark` (`dc-loader-mark`); il PatientJourney non c'è (tolto dalla scheda della
persona il 01/10/2026). L'evento dell'agenda
è `dc-evento` in `ResourceScheduler.vue`, i cicli a tappe `dc-steps`, l'area di
rilascio `dc-drop`. I token che usano (stati, categorie, `brand-subtle`, `brand-solid`,
`radius-tail`) stanno in testa a `espresso-componenti.css` e prendono il marchio
acceso: un altro verticale li colora con i suoi.
