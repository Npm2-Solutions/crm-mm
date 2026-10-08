# 36 — Funzionalità: cosa comprende DottorCloud, e gli extra

> ✅ **FATTO (01/10/2026)**. La pagina "Piano" delle impostazioni elencava sei
> moduli tutti uguali, con uno stato ciascuno e un pulsante di prova, metà in
> inglese: la base e la clinica, che un centro ha perché si è iscritto a
> DottorCloud, stavano accanto al telefono e all'assistente come cose da
> accendere. E "Piano" si confondeva con i piani dei pazienti. Ora la pagina si
> chiama **Funzionalità**: in alto quello che DottorCloud comprende, pronto da
> usare; sotto gli extra, ognuno con quello che aggiunge e la prova gratuita; per
> ognuno i link alle pagine dove si imposta.
>
> **Con il listino finale** (01/10/2026,
> [listino](../marchi/dottorcloud/listino.md#nel-crm)): la taglia conta gli
> ambulatori, la fatturazione e la firma avanzata sono extra, e i consumi sono
> quelli che l'agenzia fattura.

## Com'è

```
Funzionalità
Cosa comprende DottorCloud per il tuo centro, e gli extra da aggiungere quando servono.

COMPRESO IN DOTTORCLOUD
  Base           Persone e agenda con sale, prenotazione online…
                 Da impostare  [Servizi ›] [Orari e turni ›] [Prenotazione online ›] [Utenti ›]
  Clinica        Il gestionale del centro medico: pazienti, cartella clinica e referti…
                 Da impostare  [Moduli ›] [Consensi ›]
  Area pazienti  L'app delle persone che il centro segue…
                 Da impostare  [Area pazienti ›]

EXTRA   gratis per 14 giorni, poi l'agenzia li aggiunge al piano dal mese dopo
  ┌ Fatturazione  Attivo ───────┐ ┌ Marketing  Attivo ──────────┐
  │ Fatture illimitate, il TS…  │ │ Automazioni, campagne…      │
  │ Da impostare [Azienda…›] …  │ │ Da impostare [Meta ›] …     │
  └─────────────────────────────┘ └─────────────────────────────┘
  ┌ Telefono  Attivo ───────────┐ ┌ Assistente ─────────────────┐
  │ Chiamate dal browser…       │ │ Moduli dalla carta…         │
  │ Da impostare [Telefonia ›] …│ │ [Prova gratis per 14 giorni]│
  └─────────────────────────────┘ └─────────────────────────────┘
  ┌ Firma avanzata ─────────────┐
  │ Consenso informato e prev…  │
  │ [Prova gratis per 14 giorni]│
  └─────────────────────────────┘

DIMENSIONE E CONSUMI
  Studio, fino a 2 ambulatori · 3 ambulatori nell'agenda (avviso: oltre la taglia)
  Crediti SdI quest'anno 412 / 500 · Firme avanzate quest'anno 30 / 2000
```

- **Compreso in DottorCloud**: la base, il modulo del verticale acceso (la
  clinica, per DottorCloud) e quello che comprende (l'area pazienti). Niente da
  accendere né da provare: si accende con l'iscrizione, dalle impostazioni del
  sito che sono dell'agenzia. Uno stato compare solo se non è attivo (in prova,
  in sola lettura).
- **Extra**: gli altri moduli del piano, ognuno con la sua frase. Uno che il
  centro non ha si prova gratis per 14 giorni (come prima: l'agenzia riceve la
  richiesta e lo aggiunge al piano dal mese dopo); uno attivo dice dove si
  imposta; uno finito dice che i dati restano e che lo rinnova l'agenzia.
- **Da impostare**: i link alle pagine delle impostazioni dove si comincia, solo
  quelle che la persona vede; un link apre la pagina con la sua categoria accesa.
- **Gli extra del listino**: fatturazione (con il Sistema TS e i crediti SdI;
  accesa dove il piano non dice niente, perché ogni sito fatturava prima dei
  piani), marketing, telefono, assistente, firma avanzata (spenta finché il piano
  non la comprende).
- **La taglia** in ambulatori, le sale dell'agenda: Solo 1, Studio fino a 2,
  Centro fino a 5, Poliambulatorio fino a 10, oltre. Superarla non blocca niente.
- **I consumi** come li fattura l'agenzia, ognuno con quello che il piano
  comprende: crediti SdI dell'anno (con la fatturazione: uno a fattura inviata o
  ricevuta, tre alla PA, niente per una scartata) e firme avanzate dell'anno
  (2.000). Oltre l'80% la pagina avvisa. WhatsApp no: lo paga il centro a Meta.
  Chiamate e SMS nemmeno, dal 03/10/2026: il telefono è un canone l'anno, e
  chiamate, numeri e SMS li fattura Twilio a chi ha l'account; la spesa sta nella
  pagina di Twilio ([doc 52](./52-twilio-del-centro.md)).
- **Il nome**: "Funzionalità", non "Piano", che sono i piani dei pazienti (esercizi,
  diete). Il nome della pagina resta `Plan` nei link (`?settings=Plan`).
- **Tutto in italiano**: i moduli, le loro frasi, gli stati, le dimensioni; con la
  clinica "nuovo paziente" nel marketing (`crm/clinica/parole.py`).

## Come è fatto

| File | Cosa fa |
|---|---|
| `crm/permissions/livelli.py` | `ModuloPiano.impostazioni`: le pagine dove si imposta un modulo, nell'ordine in cui si fa |
| `crm/permissions/catalogo.py`, `crm/area`, `crm/clinica`, `crm/assistente` | Ogni modulo registra le sue pagine con sé |
| `crm/api/plan.py` | `compresi()` (puro): la base, il modulo del verticale e quello che comprende; `get_plan()` dice di ogni modulo se è compreso (`included`) e dove si imposta (`settings`), gli ambulatori (`ambulatori()`) e i consumi (`consumi()`) |
| `crm/fcrm/doctype/crm_plan/crm_plan.py` | I numeri del listino (`AMBULATORI`, `CREDITI_SDI`, `FIRME_INCLUSE`, l'avviso all'80%) e `crediti_sdi()`, puro |
| `crm/invoicing/capacita.py`, `crm/moduli/firme.py` | La fatturazione e la firma avanzata come moduli del piano; con la firma spenta niente di nuovo va al fornitore (`firme.attivo()`), quello partito torna |
| `frontend/src/utils/funzionalita.js` | `dividi()` compreso ed extra, `doveSiImposta()` i link fra le pagine che la persona vede — puro, testato |
| `frontend/src/components/Settings/PlanSettings.vue`, `FeatureSetUp.vue` | La pagina e i link; il menu visibile arriva da `Settings.vue` (`provide('menuDelleImpostazioni')`) |

Un modulo nuovo del piano: le sue pagine in `impostazioni`, la sua frase, la sua
icona in `PlanSettings.vue` (altrimenti una scatola), le traduzioni.

## Test

- `crm/tests/test_funzionalita.py`: cosa comprende il prodotto con e senza
  verticale; con la clinica la base, la clinica e l'area comprese, il marketing, il
  telefono e l'assistente extra, l'assistente da provare; ogni modulo con le sue
  pagine.
- `crm/tests/test_impostazioni.py`: le pagine che i moduli nominano esistono nel
  menu delle impostazioni.
- `tests/unit/funzionalita.test.js`: compreso ed extra nell'ordine del piano, i
  link con l'etichetta della voce (e della scheda), solo le pagine che si vedono,
  una volta.
- Nel browser, in italiano: la pagina del manager in chiaro e in scuro, sul
  telefono, il link a Telefonia; quella dell'agenzia con "Modifica".
