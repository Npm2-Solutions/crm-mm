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

## Classi DottorCloud da usare nei componenti nostri

Dove frappe-ui non ha il componente (o serve la forma del marchio) si passa una classe:

- `dc-avatar` su `<Avatar>`: la persona nella nuvola (`border-radius: 50% 50% 50% 22%`).
- `dc-tag dc-tag--<categoria>` su `<Badge>`: le etichette di categoria.
- `dc-brand` su `<Button variant="subtle">`: il pulsante tenue del marchio.
- StatTile, AgendaEvent, PatientJourney, EmptyState: componenti del gestionale (`components/Dashboard/`, l'agenda, la scheda paziente) da costruire con i token di questo sistema.
