# 36 — Funzionalità: cosa comprende DottorCloud, e gli extra

> ✅ **FATTO (01/10/2026)**. La pagina "Piano" delle impostazioni elencava sei
> moduli tutti uguali, con uno stato ciascuno e un pulsante di prova, metà in
> inglese: la base e la clinica, che un centro ha perché si è iscritto a
> DottorCloud, stavano accanto al telefono e all'assistente come cose da
> accendere. E "Piano" si confondeva con i piani dei pazienti. Ora la pagina si
> chiama **Funzionalità**: in alto quello che DottorCloud comprende, pronto da
> usare; sotto gli extra, ognuno con quello che aggiunge e la prova gratuita; per
> ognuno i link alle pagine dove si imposta.

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
  ┌ Marketing  Attivo ──────────┐ ┌ Telefono  Attivo ───────────┐
  │ Automazioni, campagne…      │ │ Chiamate dal browser…       │
  │ Da impostare [Meta ›] …     │ │ Da impostare [Telefonia ›] …│
  └─────────────────────────────┘ └─────────────────────────────┘
  ┌ Assistente ─────────────────┐
  │ Moduli dalla carta…         │
  │ [Prova gratis per 14 giorni]│
  └─────────────────────────────┘

DIMENSIONE E CONSUMI   le agende attive questo mese, messaggi, SMS, minuti
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
- **Il nome**: "Funzionalità", non "Piano", che sono i piani dei pazienti (esercizi,
  diete). Il nome della pagina resta `Plan` nei link (`?settings=Plan`).
- **Tutto in italiano**: i moduli, le loro frasi, gli stati, le dimensioni; con la
  clinica "nuovo paziente" nel marketing (`crm/clinica/parole.py`).

## Come è fatto

| File | Cosa fa |
|---|---|
| `crm/permissions/livelli.py` | `ModuloPiano.impostazioni`: le pagine dove si imposta un modulo, nell'ordine in cui si fa |
| `crm/permissions/catalogo.py`, `crm/area`, `crm/clinica`, `crm/assistente` | Ogni modulo registra le sue pagine con sé |
| `crm/api/plan.py` | `compresi()` (puro): la base, il modulo del verticale e quello che comprende; `get_plan()` dice di ogni modulo se è compreso (`included`) e dove si imposta (`settings`) |
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
