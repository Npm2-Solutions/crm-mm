# CRM — Completed Work Archive

> **This file**: Completed phases only — decision rationale, what was built, implementation detail.  
> **Current API contracts**: [SPEC.md](./SPEC.md)  
> **Upcoming work**: [PLAN.md](./PLAN.md)

---

## Phase 1 — setFieldProperty & Meta Refactor

> **Completed.** Implemented `setFieldProperty`, `setFieldProperties`, `removeFieldProperty`, `getField` for fields, sections, tabs, and child table rows.

### New pure utility files

| File | Purpose |
|---|---|
| `src/utils/expressions.js` | `_eval`, `evaluateDependsOnValue`, `evaluateExpression` — extracted from `utils/index.js` to allow import without pulling in Vue components |
| `src/utils/fieldTransforms.js` | `processField()`, `findMissingMandatory()`, `parseLinkFilters()` — pure functions, independently testable |
| `src/utils/scriptHelpers.js` | `getClassNames()`, `createDocProxy()` — extracted from `script.js` closure |

### Mutation fixes

Every place that previously mutated shared field objects now clones first:
- `Field.vue` computed: `let field = { ...props.field }`
- `SidePanelLayout.vue` `parsedField()`: `field = { ...field }`
- `Grid.vue` `getFieldObj()`: `field = { ...field }`

`JSON.parse(field.link_filters)` (6 call sites, would throw when `link_filters` was already an object) replaced everywhere with `parseLinkFilters(field.link_filters)`.

### `fieldPropertyOverrides` map structure

Added to the document cache entry alongside `fieldHtmlMap`:

```js
fieldPropertyOverrides = {
  // parent/side-panel fields
  'annual_revenue': { hidden: true },
  'status': { options: 'New\nIn Progress' },

  // sections and tabs (by name)
  'financial_section': { hidden: true },
  'advanced_tab': { hidden: true, label: 'Expert' },

  // child table columns (dot notation)
  'products.qty': { read_only: true },
  'products.discount': { hidden: true },

  // child table per-row (dot notation + colon + row.name)
  'products.rate:row_abc123': { read_only: false },
}
```

### `checkMandatory` rewritten

Old: called `getFields()` which filtered out hidden fields and only checked `mandatory_depends_on`.  
New: `findMissingMandatory()` from `fieldTransforms.js` which:
- Uses raw `doctypesMeta[doctype].fields` (all fields including hidden)
- Checks both `reqd: 1` and `mandatory_depends_on` expressions
- Respects `hidden` and `reqd` from `fieldPropertyOverrides` (script overrides win)
- Hidden fields are always skipped regardless of `reqd`

### Rendering flow (still accurate as of Phase 2)

```
script.js setFieldProperty()
  └─► ctx.fieldPropertyOverrides[target][property] = value
          │
          ├─ SidePanelLayout.vue
          │    parsedField() → Object.assign(field, overrides)
          │    parsedSection() → Object.assign(section, overrides)
          │
          ├─ FieldLayout.vue
          │    processedTabs computed → tab/section overrides merged → hidden tabs filtered
          │    │
          │    └─ Field.vue (non-grid)
          │         computed field → getFieldOverrides(fieldname) → Object.assign(field, overrides)
          │         provide('fieldPropertyOverrides', ...) → Grid.vue injects it
          │
          └─ Field.vue (isGridRow=true, inside GridRowModal)
               inject fieldPropertyOverrides from Grid.vue
               resolves: col key (products.qty) + row key (products.qty:rowName)

Grid.vue
  getFieldObj(field)
    → colKey = `${parentFieldname}.${field.fieldname}`
    → Object.assign(field, overrides[colKey])     ← column-level
    → hidden columns filtered → gridTemplateColumns recalculated

  getRowFieldObj(field, row)
    → rowKey = `${colKey}:${row.name}`
    → merged = { ...colOverrides, ...rowOverrides }  ← row wins over column
    → per-row hidden → empty cell (preserves grid alignment)
```

### Known remaining issues (as of Phase 1 completion)

| Issue | Status |
|---|---|
| `getFields()` still mutates `doctypesMeta` field objects (Select options, Link→User) | Deferred — rendering components clone first now, acceptable until Phase 4 |
| Layout APIs return redundant full field meta | Deferred — full getMeta refactor (Phase 4) |
| `getMeta` `getFields()` filters hidden fields | Intentional for now; raw `doctypesMeta` used where hidden fields needed |

---

## Phase 3A — FieldLayout Standalone Mode

> **Completed.** Added `context` prop to FieldLayout enabling standalone rendering without `useDocument`.

### Problem solved

`FieldLayout.vue` always called `useDocument(props.doctype, props.data?.name)` to get `fieldPropertyOverrides`. For a dialog with inline fields (no doctype), this called `useDocument('', undefined)` creating a garbage entry in `documentsCache`. For a dialog with a real doctype like `'CRM Lost Reason'`, it would trigger script loading unintentionally.

### Decision: Option B — `context` prop

The `context` prop carries the externally managed context object (`{ fieldPropertyOverrides, fieldHtmlMap }`). When provided, `useDocument` is skipped entirely.

**Not chosen: Option A** (`standalone` boolean) — `context` is more extensible, can carry more in future (triggerOnChange, triggerButton, etc.) without adding more props.

### What was built

**`FieldLayout.vue`**:
- Added `context: { type: Object, default: null }` prop
- When `context` is present: uses `context.fieldPropertyOverrides` for tab/section overrides instead of calling `useDocument`
- Provides `fieldLayoutContext` via inject for child Field components

**`Field.vue`**:
- Injects `fieldLayoutContext`. When present: skips `useDocument` entirely, field changes update data directly, scripting triggers are no-ops
- Guards `getMeta(doctype)` — only called when doctype is truthy. Inline mode uses `formatNumber`/`formatCurrency` fallback formatters directly

---

## Phase 2 — formDialog()

> **Completed.** Script authors can open a FieldLayout-based dialog, collect data, and act on it.

### Decision: Option C — Promise + onSubmit callback + custom actions (all three work)

Three patterns were considered:
- **Option A** (callbacks only, consistent with `createDialog`) — too verbose for simple cases
- **Option B** (`onSubmit` only) — doesn't support sequential multi-step workflows
- **Option C** (all three, Promise always resolves) — chosen. Most flexible. Promise for sequential, callback for fire-and-forget, actions for full control.

**Dialog fields are NOT scriptable (intentional).** The dialog is a data collector only. `setFieldProperty` called inside a dialog action affects the **page** fields, not the dialog's fields. Full isolation would require a separate `fieldPropertyOverrides` scope per dialog — deferred.

### What was built

| File | Description |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | Dialog shell + standalone FieldLayout + local reactive doc. Validates before resolving. |
| `frontend/src/components/Modals/FieldLayoutDialogContainer.vue` | Renders entries from the `fieldLayoutDialogs` reactive array |
| `frontend/src/utils/renderFieldLayoutDialog.js` | Pushes config to array, returns Promise. Internal `onResolve` is distinct from user's `onSubmit`. |
| `frontend/src/components/Modals/GlobalModals.vue` | Mounts `<FieldLayoutDialogContainer />` |
| `frontend/src/data/script.js` | `helpers.formDialog = renderFieldLayoutDialog` — bare helper in script scope |

### Key fixes during implementation

- **Buttons stuck in loading**: `_loading` was a `ref()` inside `computed()`. Vue doesn't auto-unwrap refs nested inside plain objects in templates. Fixed with `reactive({})` `actionLoadingMap` outside the computed.
- **Double-event bug**: `v-bind="dialog.props"` passed `onResolve` as a `@resolve` listener AND `@resolve` explicitly added it again. Fixed by stripping `onResolve` from the spread in `FieldLayoutDialogContainer`.
- **`getMeta('')` console error**: `Field.vue` called `getMeta(doctype)` unconditionally. When doctype is empty (inline mode) this triggers an API call that fails. Fixed with doctype guard.
- **`v-bind="action"` spreading internals**: Template was spreading entire action objects including `_loading` ref, wrapped `onClick`, etc. onto Button. Fixed with explicit prop bindings.

### Layout priority

1. `tabs` — full custom layout (highest)
2. `fields` — flat list, auto-wrapped
3. `doctype` + `fieldnames` — specific fields from doctype meta
4. `doctype` alone — full Quick Entry layout

> Current stable API: [SPEC.md — formDialog API](./SPEC.md#formdialog-api)  
> Full guide with examples: [feats/form-scripting/form-dialog.md](./feats/form-scripting/form-dialog.md)

---

## Pipelines — piu' funnel per le trattative

> **Completata.** Guida d'uso: [feats/pipelines/guide.md](./feats/pipelines/guide.md)

### Il problema

Un solo elenco di `CRM Deal Status` per tutto il CRM: ogni trattativa, di
qualunque natura, condivideva lo stesso funnel. Nessun modo di tenere separati,
per esempio, il funnel commerciale e quello di onboarding.

### Il modello scelto

`CRM Pipeline` (nuovo DocType) + campo `pipeline` su `CRM Deal Status` e su
`CRM Deal`.

**Lo stage e' la fonte di verita'.** `CRM Deal.pipeline` rispecchia sempre la
pipeline del suo stage (`validate_status`), quindi i due campi non possono
divergere: non esiste uno stato "deal nella pipeline A con stage della B".
Impostare una pipeline diversa su un deal esistente lo sposta sul primo stage
aperto di quella pipeline — la stessa semantica di GoHighLevel.

### Decisioni

| Decisione | Perche' |
|---|---|
| Estendere `CRM Deal Status` invece di creare uno `stage` nuovo | `status` e' cablato ovunque: SLA, dashboard, automazioni, status change log, form script, viste salvate. Sostituirlo avrebbe significato riscrivere mezzo CRM |
| Nomi degli stage unici su tutto il sito | `CRM Deal.status` e' un Link: il valore salvato *e'* il nome. Nominare gli stage con un hash avrebbe reso illeggibili dashboard, esportazioni e filtri salvati. Le pipeline nuove ricevono percio' stage con suffisso automatico (`Qualification (Onboarding)`), rinominabili subito |
| `pipeline` non obbligatorio sul deal, obbligatorio sullo stage | Il deal lo riceve sempre in `validate`; renderlo `reqd` avrebbe rotto ogni creazione via API che passa solo lo stato |
| Colonne kanban ordinate per `position` | Prima erano ordinate per `modified asc`, cioe' a caso. Con le pipeline l'ordine degli stage e' la board stessa |
| Pipeline corrente del kanban dedotta dalle colonne della vista | Nessun nuovo campo su `CRM View Settings` e nessuna sovrascrittura delle board che l'utente ha personalizzato |
| Spostamenti di massa via SQL (`delete_stage`, `delete_pipeline`) | Sono operazioni di configurazione su potenzialmente migliaia di deal: passare dai hook del documento avrebbe significato ricalcoli SLA e sharing per ognuno. Il compromesso e' che non finiscono nello status change log |

### File

| File | Ruolo |
|---|---|
| `crm/fcrm/doctype/crm_pipeline/` | DocType + helper (`get_default_pipeline`, `get_pipeline_stages`, `get_first_stage`, `get_pipeline_of_stage`) |
| `crm/api/pipeline.py` | API della schermata impostazioni: elenco, creazione, `save_stages`, cancellazioni con spostamento dei deal |
| `crm/utils/__init__.py` | `get_kanban_column_options` — colonne kanban ordinate e filtrate per pipeline (usata da `api/doc.py` e `crm_view_settings.py`) |
| `crm/patches/v1_0/create_default_pipeline.py` | Migrazione dei siti esistenti |
| `frontend/src/stores/pipelines.js` | Store: pipeline + stage in una sola chiamata |
| `frontend/src/utils/pipelines.js` | Funzioni pure (testate): stage di una pipeline, colonne kanban, pipeline di default |
| `frontend/src/components/Settings/Pipelines/` | Impostazioni → Vendite → Pipeline (lista + editor stage) |

### Non incluso

- I grafici della dashboard aggregano ancora tutte le pipeline insieme: filtrarli
  per pipeline vuol dire passare il parametro attraverso ~15 funzioni di
  `crm/api/dashboard.py` e la relativa UI. → **Risolto** con la dashboard nuova
  (sotto): i widget di vendita hanno l'opzione Pipeline.
- Le pipeline valgono per i deal, non per i lead (come in GoHighLevel).

---

## Dashboard — un cruscotto per ogni modulo

> **Completato** (24/09/2026). Documento di progetto:
> [docs/progetto-ghl/28-dashboard.md](../docs/progetto-ghl/28-dashboard.md).

166 widget in 16 categorie (`crm/dashboard/widgets/`), dieci dashboard pronte che
seguono il sito finche' nessuno le risistema, builder a griglia nel frontend.
La fatturazione si e' aggiunta dopo (25/09/2026): 19 widget e la sua dashboard.

### Decisioni

| Decisione | Perche' |
|---|---|
| Il catalogo e' codice (`@widget`), non query scritte dall'utente | Ogni widget e' rivisto e passa da un test che lo esegue su MariaDB; una query libera rompe in silenzio quando cambia uno schema |
| Ogni widget dichiara le feature che gli servono | Uno zero su un modulo non usato non significa niente e nasconde gli zeri che contano; la libreria offre prima cio' a cui il sito sa rispondere |
| I modelli sono righe, non posizioni | Vengono impaginati per chi guarda: una riga coi buchi divide la larghezza fra chi resta, una sezione vuota sparisce |
| Una dashboard da modello lo segue finche' non si salva a mano | Chi collega WhatsApp trova la sezione senza toccare niente; salvare senza cambiare niente non la stacca |
| Gli id della prima dashboard restano | Un layout salvato prima si apre coi numeri nuovi |
| Delta dei tassi in punti | Da 50% a 60,5% e' "+10,5 pts": "+21%" di un percentuale non lo legge giusto nessuno |
| Colore per nome agli stati noti | Assegnati in ordine, "No show" e "Chiamate perse" uscivano verdi; le combinazioni sono validate per daltonismo nei due temi |
| Griglia di frappe-ui con `responsive` spento | Sotto 768px di griglia passava a una colonna e restituiva quelle posizioni come nuove: il salvataggio le avrebbe tenute |
| Nella fatturazione niente "incassato" ne' "scaduto" | Il modulo non registra i pagamenti: `payment_date` vale la data della fattura se nessuno la cambia. Un "da incassare" sarebbe un numero inventato |
| Il fatturato e' l'imponibile, note di credito sottratte | E' il numero che un titolare chiama fatturato; autofatture e integrazioni sono acquisti, e una fattura scartata dallo SdI conta come non emessa |

---

## Chat — chi, dove, quando

> **Completato** (28/09/2026). Documento di progetto:
> [docs/progetto-ghl/17-timeline-unificata.md](../docs/progetto-ghl/17-timeline-unificata.md),
> sezione «La chat rifatta».

Redesign della vista «Tutto», del composer e della pagina Conversazioni, dopo
aver riletto le ragioni dei commit precedenti e averle guardate a schermo.

### Decisioni

| Decisione | Perche' |
|---|---|
| Il riempimento dice chi (loro chiaro, noi blu), il glifo dice il canale | La tinta per canale dava due verdi a un punto di luminosita' di distanza: in una chat quasi tutta WhatsApp «chi ha parlato» restava affidato al solo lato |
| Coda e nome sulla prima della serie | Una serie e' una voce; il nome solo dove il lato non basta (un collega, un altro mittente email) |
| Separatori in linea, data flottante solo mentre si scorre | A riposo la data appiccicata copriva le parole del primo messaggio |
| Date con `Intl` nella lingua dell'utente (`appLocale()`, vedi «Interfacce») | «2026-08-16» non si legge; «Yesterday» non aveva traduzione italiana. All'inizio era la lingua del browser: con un account inglese su un browser italiano le date uscivano in italiano sotto parole inglesi |
| Il composer parte dal canale dell'ultimo messaggio ricevuto | Era la regola del doc 17 e non era mai stata applicata: partiva sempre dall'email |
| Leggere e scrivere sono due stati | Rispondere su WhatsApp da «Tutto» non deve portare via «Tutto» |
| La nota tinge di ambra tutto il composer | Nessuno deve scrivere una nota interna credendo di rispondere al cliente |
| Nome e decisioni nell'intestazione del filo, pannello solo da 1400px | Aperta da link la conversazione mostrava l'id; a 1280px il pannello tagliava il nome |
| L'assegnazione tiene lo stato che trova | Passava dalla porta di «apri» e toglieva il rinvio |

---

## Interfacce — il giro di tutte le schermate

> **Completato** (28/09/2026). Ogni pagina, ogni sezione delle Impostazioni e i
> modali principali, fotografati in chiaro, in scuro e su telefono (390px) con
> Playwright, con gli errori della console e la misura dell'overflow; cinque
> revisori hanno letto gli screenshot e riportato ogni difetto al suo file.

Quello che c'era sotto era quasi sempre lo stesso: codice scritto contro una
scala di token che non era più quella di frappe-ui, o classi che non generano
CSS. Nessun controllo lo diceva, perché una classe valida che disegna il colore
sbagliato è ancora una classe valida.

### Decisioni

| Decisione | Perche' |
|---|---|
| Con i token v2 gli inchiostri colorati `-1..-4` non si usano per testo o icone | In v2 `ink-X-1` è il bianco e `-2..-4` sono le tinte 100–300: il codice arrivato dopo l'aggiornamento li usava col significato vecchio, e disegnava a 1,2–1,4:1. Si segue il Badge di frappe-ui: testo `-8` (ambra `-9`, che a `-8` resta a 3,7:1), icone `-7`, fondi `surface-X-2` |
| Su una superficie rialzata il bordo è `outline-elevation-2`, non `outline-gray-1` | In scuro `outline-gray-1` e `surface-elevation-2` (il pannello delle Impostazioni) sono lo stesso grigio: ogni divisore spariva. In chiaro i due bordi sono identici |
| Il corpo dei modali è `surface-elevation-1`, come il Dialog | La migrazione dei token aveva fatto di `surface-modal` un `elevation-2`: in scuro corpo e piede di due grigi diversi |
| `hover:bg-surface-gray-1`, mai `hover:bg-surface-sidebar` | In scuro `surface-sidebar` è trasparente: l'hover non c'era |
| `color-scheme: dark` sul tema scuro | Barre di scorrimento, calendari nativi e lettore audio si disegnano da soli e restavano chiari |
| In `LayoutHeader` la sinistra cede, la destra no | Un titolo lungo spingeva le azioni oltre il bordo: su telefono l'editor delle automazioni era largo 777px e «Salva» irraggiungibile |
| Date e numeri nella lingua dell'utente: il boot dà `window.lang`, `appLocale()` lo passa a `Intl` | Le parole seguivano l'utente Frappe e le date il browser. Un codice che `Intl` non conosce ricade sul browser invece di far fallire la formattazione. La fatturazione resta in it-IT |
| Le varianti di pagina sulle schede toccano solo i figli diretti del Tabs | `[&_[role='tab']]:px-0` prendeva anche le chip dei canali e il composer, che sono `tablist` anch'essi |
| «kanban» non è una vista di Persone | Tolta col doc 26, rispondeva ancora al suo indirizzo con le colonne di stati che nessuno compila |
| Le colonne dichiarate dal controller restano anche se il campo è nascosto | Il core nasconde `Contact.full_name` e la lista dei contatti non aveva il nome |
| `.prose-f` usa `break-words` | `break-all` spezzava ogni parola dove finiva la riga |
| Gli stati della fattura si scrivono come parole (`statusLabel`) | Restano le parole dell'Agenzia, senza i trattini bassi del database |
| Via la pagina Welcome | Uno stub di upstream che salutava «John Doe» con due pulsanti senza azione, a cui non portava niente |
| Nei modali di creazione il cursore va nel primo campo obbligatorio in cui si scrive (`useFirstFieldFocus`), aspettando che il layout sia disegnato | Il solo marcatore `<div autofocus>` toglieva a Reka il primo focus (niente più tooltip sul pulsante dell'intestazione), ma frappe-ui cerca il campo nel momento in cui il modale si apre e i campi arrivano dopo, col layout: il focus restava sul pulsante che apre il modale, dietro di esso, e Tab camminava sulla pagina sotto. Il messaggio di Chrome «Autofocus processing was blocked…» è informativo: dice che l'autofocus nativo non è partito, perché il focus lo mette il codice |

### Lasciato com'è, di proposito

- **L'ordine dei campi dei form rapidi di persona e trattativa su telefono**:
  tre colonne impilate si leggono per colonna («Salutation, Email, First
  Name…»). È un layout per sito, modificabile dai manager; intrecciare le
  colonne sparpaglierebbe i gruppi voluti (i social in una colonna). Va
  deciso sul layout predefinito, con una patch che tocchi solo i siti che non
  l'hanno cambiato.
- **Eventi sovrapposti nel calendario di frappe-ui**: si coprono lasciando
  frammenti («Tra», «Pac»). Il layout delle sovrapposizioni è di frappe-ui.
- **Segnaposto troncati nei filtri rapidi** («Telephony Med»): la striscia
  scorre in orizzontale per scelta di upstream.
- **Piedi dei dialog**: alcuni hanno pulsanti a tutta larghezza, altri a destra;
  è la convenzione di upstream, coerente dentro ogni tipo di modale.

---

## Conversazioni — leggere è un momento solo

> **Completato** (28/09/2026). Cosa succede quando si guarda, si legge, si
> risponde, si gestisce e si rimanda una conversazione, e quando il cliente
> riceve le spunte blu: la tabella completa è nel doc 17, «Leggere è un momento
> solo».

### Decisioni

| Decisione | Perche' |
|---|---|
| Letta ha tre porte: il pulsante, una risposta scritta dal CRM, «Gestita». Aprire non è una | Le spunte blu partivano all'apertura mentre il badge restava: il cliente sapeva di essere stato letto mentre il CRM diceva di no, e a un collega bastava scorrere la lista |
| Le spunte partono nello stesso momento in cui si spegne il badge, mai da sole | Un solo significato di «letto», per il team e per il cliente |
| Una conferma per numero, per l'ultimo messaggio, in coda dopo il commit | WhatsApp segna letti anche i precedenti; venti richieste di fila dentro un clic erano venti attese di Meta |
| La conferma è una nostra richiesta, non `WhatsAppMessage.send_read_receipt()` | Quel metodo risalva il messaggio in arrivo, e salvarlo ricerca il numero: poteva spostarlo su un altro record |
| La risposta di un'automazione non legge | Nessuno ha letto niente |
| Rispondere legge ma non gestisce | Si può rispondere e dovere ancora qualcosa; «In attesa di risposta» si svuota da sola, «Aperte» no |
| Ordine solo per ultimo messaggio; i non letti hanno un filtro, non la cima | Coi non letti in cima, segnarne una letta la faceva sparire sotto le altre |
| «Da leggere» rimette solo il flag e tiene il momento della lettura | Azzerare il momento trasformava il numero sulla riga in tutti i messaggi mai ricevuti |
| Il numero sulla riga solo se la conversazione è da leggere | Un numero su una riga che l'intestazione dice letta sono due risposte a una domanda |
| La riga che esce dalla vista resta, velata e col motivo, finché non si passa ad altro | Toglierla sotto il puntatore faceva slittare la lista e il clic successivo cadeva sulla persona sbagliata |
| Gestita e Rimanda hanno Annulla; l'Annulla rifiuta se nel frattempo è arrivato un messaggio | Rimettere «gestita» sopra un messaggio nuovo lo nasconderebbe |
| Gestita legge solo entrando in gestita | Assegnare una conversazione già gestita passa dallo stesso endpoint: dare via una cosa non è leggerla |
| La riga «N nuovi messaggi» si misura all'apertura e resta ferma | Leggere o rispondere non deve portare via la riga dai messaggi a cui punta |
| «Segna come letta» è blu | Su telefono è un'icona come «Letta»: il blu del contatore distingue la cosa da fare da quella fatta |
| Nell'intestazione lo stato sta sotto il nome | Accanto al nome lo schiacciava: «Gi…» con «Back tomorrow 09:00» |

### File

| File | Cosa cambia |
|---|---|
| `crm/api/conversations.py` | `mark_read` (con le spunte), `mark_unread` (solo il flag), `restore`, `send_read_receipt`, conteggi `<vista>_unread`; via `acknowledge` |
| `frontend/src/utils/conversation.js` | `keepInPlace`, `whyItLeft`, `newSince` — puri, testati |
| `frontend/src/composables/conversationState.js` | `markAnswered` per i composer, toast con Annulla, menu di «Letta» |
| `frontend/src/components/Activities/NewMessagesLine.vue` | La riga dei nuovi messaggi e la didascalia sulle spunte |

---

## Debito semgrep — 102 finding a zero

> **Completato.** La scansione completa (`semgrep scan` con le regole Frappe e
> `r/python.lang.correctness`) passa da 102 finding, tutti blocking, a 0 su 728
> target. Il debito si era accumulato perché le GitHub Actions non erano mai
> girate su questo repo: su una pull request `semgrep ci` è diff-aware e guarda
> solo il codice introdotto, quindi il pregresso non aveva mai bloccato niente.

### La cosa che contava: SSTI nel motore delle automazioni

`crm/automation/engine.py` rendeva il testo delle automazioni con
`frappe.render_template()`. Sembra innocuo finché non si guarda chi può
scrivere quel testo: `MANAGER_ROLES` in `crm/api/automation.py` è
`{"System Manager", "Sales Manager"}`, e il doctype CRM Automation dà `write` al
Sales Manager. `frappe.render_template()` passa al template i global di
safe-exec, dove `frappe.db.get_value` e compagnia **ignorano i permessi**:
`{{ frappe.db.get_value("Twilio Settings", None, "auth_token") }}` in un corpo
email leggeva qualsiasi campo di qualsiasi doctype, token delle integrazioni
compresi, da un ruolo che quei doctype non può nemmeno aprire.

Non era una funzionalità da documentare, era escalation di privilegi. Il testo
delle automazioni ha ora il suo ambiente Jinja (`_automation_jenv()`):

| Scelta | Perché |
|---|---|
| `SandboxedEnvironment` invece di `frappe.render_template` | Toglie i global `frappe.*`, che sono il vettore. Il resto di Jinja resta |
| Nessun loader | Senza loader `{% include %}` e `{% import %}` non hanno da dove pescare: un template non può tirarsi dentro un file dell'app |
| `is_safe_attribute` con `UNSAFE_ATTRIBUTES` di Frappe | Stessa lista che usa Frappe per il suo jenv: blocca `f_globals`, `gi_frame`, `format` e parenti |
| `DebugUndefined`, `autoescape=False`, filtri `json/len/int/str/flt` | Sono esattamente quelli di `frappe.render_template`: un template che funzionava prima rende identico. Cambia solo dove può arrivare |
| Singleton di modulo | L'ambiente contiene solo filtri, niente di specifico del sito, quindi è condivisibile fra richieste e fra siti |

Verificato a mano prima di committare: bloccati `{{ frappe.* }}`,
`{% include %}`, `''.__class__.__mro__`, `__globals__`, `__init__`,
`format.__globals__`; invariati i merge field documentati (`{{ first_name }}`,
`{{ tracked_link("slug") }}`, `{% if %}`, `|upper`, `|flt`). Nessuna
documentazione prometteva `frappe.*` dentro i template — `MERGE_FIELDS` in
`frontend/src/utils/automation.js` offre solo campi del record più
`tracked_link`.

### Due bug veri trovati dalle regole

- **`crm/api/doc.py`** — `get_list_data` rimuoveva le colonne nascoste dalla
  lista che stava scorrendo. L'iteratore avanza di indice: dopo una rimozione
  salta l'elemento successivo, quindi con due colonne nascoste di fila la
  seconda restava visibile. Ora il giro si fa su una copia.
- **`crm/integrations/whatsapp/signup.py`** — `SIGNUP_HINTS` chiamava `_()` a
  livello di modulo. Un modulo si importa una volta per worker e resta lì per
  ogni sito e ogni utente che passa da quel processo: quei paragrafi restavano
  congelati nella lingua caricata per prima. Ora sono lambda, come faceva già
  `crm/integrations/meta/errors.py`.

### Come si annota un `# nosemgrep`

Due cose imparate provandole, che valgono per chiunque ne aggiunga altri:

1. **La forma è `# nosemgrep: <regola> — <motivo>`.** Semgrep legge tutto quello
   che segue i due punti come una lista di id di regole separati da virgola: un
   `# nosemgrep: perché serve` non silenzia niente, perché «perché serve» non è
   il nome di nessuna regola. Con l'id davanti e il motivo dopo un trattino
   funziona, e silenzia quella regola soltanto.
2. **Sul decoratore ci va una riga sua.** `ruff-format` manda a capo le chiamate
   che superano i 110 caratteri, e il commento finisce sulla parentesi di
   chiusura — dove semgrep non lo legge più, perché il match comincia sulla riga
   del `@`. Un commento su riga propria, sopra, il formatter non lo tocca. È così
   che si erano rotte tutte e 25 le soppressioni al primo tentativo.

### Commit manuali: 14 tolti, 24 tenuti

Il criterio: si toglie solo dove si può dire *che cosa* committa al posto suo.

| Caso | Decisione |
|---|---|
| Ultima istruzione di un endpoint `methods=["POST"]` | **Tolto.** Su una POST la transazione viene committata a fine richiesta — è la stessa distinzione GET/POST già scritta in `crm/www/crm.py` |
| `crm/www/crm.py:get_context()` | **Tolto.** L'unica cosa che scrive prima è `redirect_to_set_password()`, che si alza da sola `frappe.local.flags.commit` |
| Endpoint non ristretti a POST (Twilio, Exotel, caller ID, dashboard, link tracciati) | **Tenuto.** Su una GET Frappe fa rollback: senza commit il log della chiamata o il click non resterebbero |
| Dopo un `frappe.db.rollback()` (except di Exotel, `_finish()` della trascrizione) | **Tenuto.** Lo stato d'errore svanirebbe con la transazione |
| Prima che parta qualcos'altro che deve trovare la riga (job accodato, nudge realtime, chiamata rientrante, `wire_up_delivery`) | **Tenuto.** |
| Job di background, scheduler, `after_install` | **Tenuto.** Nessuna richiesta li committa |

### Lasciato com'è, di proposito

`override_doctype_class` in `crm/hooks.py` è annotato, non rifatto. La regola
suggerisce `extend_doctype_class` e avrebbe ragione — i due override aggiungono
solo `default_list_data()` a Contact ed Email Template — ma passare a mixin
cambia come viene costruita la classe del controller, e serve un bench per
provarlo: sbagliando si rompono le liste Contatti ed Email Template.

Fuori tema ma necessario: `pre-commit run --all-files` era già rosso su develop
per tre `UP038` della ruff pinnata. È un consiglio sbagliato — costruire
l'unione costa un'allocazione a ogni chiamata, e ruff ha poi rimosso la regola —
quindi è finito negli `ignore` di `pyproject.toml` invece che nel codice.

### File

| File | Cosa cambia |
|---|---|
| `crm/automation/engine.py` | `_automation_jenv()`: la sandbox Jinja delle automazioni |
| `crm/api/site_render.py` | Annotati i cinque `render_template()` su percorsi letterali dell'app |
| `crm/api/doc.py` | Le colonne nascoste non fanno più saltare la successiva |
| `crm/integrations/whatsapp/signup.py` | `SIGNUP_HINTS` valutato al momento, non all'import |
| `crm/integrations/meta/`, `crm/integrations/whatsapp/`, `crm/telephony/`, `crm/api/` | `str(exc)` nelle stringhe tradotte, commit manuali, endpoint ospiti motivati |
| `pyproject.toml` | `UP038` fra gli ignore |

---

## Chat — scrivere, e vedere dove si scrive

> **Completato** (29/09/2026). Il compositore è la stessa riga su ogni canale,
> la chat si apre dove leggi, le nuvolette sono una forma sola. Il racconto
> completo è nel doc 17, «Scrivere, e vedere dove si scrive».

### Decisioni

| Decisione | Perche' |
|---|---|
| Nessuna riga che si trasforma in modulo: l'editor è sempre lì, una riga che cresce | Il modulo email restava aperto finché non si premeva Scarta, anche vuoto; WhatsApp aveva già la forma giusta |
| Il focus si vede sul riquadro, nel colore del canale | Cliccare nella riga WhatsApp non cambiava niente, e il colore dice anche dove andrà il messaggio (ambra = nota interna) |
| La firma si aggiunge all'invio, sopra la citazione; una riga la mostra e la toglie | Inserita al primo clic, faceva crescere la casella di quattro righe e la trasformava in bozza |
| Scarta con Annulla; gli allegati si cancellano a Annulla scaduto | Il cestino sta accanto a Invia |
| Inviare svuota subito, un errore rimette la bozza | Come in un messenger: aspettare il server con la casella chiusa non diceva cosa stava succedendo |
| Bozze di ogni canale per persona e per scheda, il compositore si riapre sulla bozza | Una bozza WhatsApp si perdeva cambiando scheda; un messaggio in arrivo su un altro canale spostava il compositore mentre si scriveva |
| Il foglio di stile dell'editor di frappe-ui importato da noi | Il bundler scartava il suo import (il pacchetto dichiara effetti collaterali solo per CSS e Vue): ogni editor aveva l'anello di focus grigio del browser |
| Rispondere parte dalla nostra casella che ha ricevuto l'email, mai dal cliente | `fromEmail = email.sender` metteva l'indirizzo del cliente come mittente |
| La riga del testo si rimette nell'editor, non solo nella bozza | L'editor scarta come eco un valore uguale all'ultimo che ha emesso: dopo un Annulla restava vuoto |
| La chat resta nascosta finché non è arrivato tutto, poi compare già al suo posto | Compariva dalla cima e scorreva, e saltava all'arrivo di WhatsApp |
| Lo scorrimento osserva anche il contenuto, non solo il contenitore | Un'email si allarga dopo il `load`, e l'ultima restava tagliata |
| La punta della nuvoletta è un `::before` con `background: inherit` e `clip-path`, l'ombra un `drop-shadow` | Un triangolo appoggiato all'angolo lasciava il gradino e l'ombra si fermava alla giunzione |

### File

| File | Cosa cambia |
|---|---|
| `frontend/src/components/Activities/ComposerShell.vue` | Il riquadro del compositore, col focus nel colore del canale |
| `frontend/src/components/CommunicationArea.vue`, `EmailEditor.vue`, `CommentBox.vue` | Email e nota come riga; firma all'invio; Scarta con Annulla; `open()` e `reply()` al posto del flag `show` |
| `frontend/src/components/Activities/WhatsAppBox.vue`, `SMSBox.vue` | Testo prima degli strumenti; crescono davvero; bozze per scheda |
| `frontend/src/utils/emailDraft.js` | Firma, citazione, indirizzi di risposta — puri, testati |
| `frontend/src/composables/growingTextarea.js`, `drafts.js`, `conversationScroll.js` | Altezza misurata, bozze condivise, dove sta la conversazione |
| `frontend/src/index.css` | Il foglio di stile dell'editor, la riga di testo, le punte delle nuvolette |

---

## Calendario — due cose, un modo solo

> **Completato** (29/09/2026). Appuntamenti ed eventi restano due modelli, ma
> si creano, si aprono e si modificano nello stesso modo. Doc 14, «Un
> calendario, due cose».

### Decisioni

| Decisione | Perche' |
|---|---|
| Non fondere `CRM Appointment` ed `Event` | L'`Event` è quello che il framework sincronizza con Google, e l'appuntamento lo rispecchia già: fonderli voleva dire migrare i dati e rifare il sync, per nessun guadagno visibile |
| Il criterio è il servizio: un appuntamento è un servizio per un cliente, un evento è tutto il resto | È la differenza che chi usa l'agenda ha già in testa, e decide quali righe servono |
| Un «Nuovo» solo, che ricorda l'ultimo tipo, e un selettore come prima riga del pannello | Due pulsanti per due cose nello stesso calendario, e il clic sul vuoto che faceva sempre un evento |
| Il clic su «tutto il giorno» è un evento | Un appuntamento ha un orario |
| L'appuntamento nel pannello laterale, prima in lettura, lo stato a un clic | La finestra modale copriva il calendario e apriva ogni campo insieme; lo stato è la cosa che si cambia più spesso |
| Eliminare propone di annullare | L'annullato resta nello storico e libera l'orario; eliminare non si annulla |
| Ogni colore salvato va al più vicino dei sette del calendario; grigio e rosso aggiunti alla sua tabella | Il calendario conosce solo sette nomi e sette esadecimali, e il resto lo disegnava verde |
| Il pannello evento salva l'esadecimale | Salvava `var(--ink-amber-7)`, che il calendario non legge e che fuori da questa pagina non significa niente |
| Grigio e rosso hanno come `color` il proprio esadecimale | Il calendario confronta un esadecimale sconosciuto con il `color` di ogni voce: così un evento appena colorato è giusto anche prima di ricaricare |
| Un filtro sugli appuntamenti nasconde gli eventi | Gli eventi non hanno servizio, professionista, sala, stato o fonte: restavano lì come se corrispondessero |
| La query `?new=appointment&party=…` resta nell'indirizzo | La pagina ha come chiave l'indirizzo completo: toglierla la ricostruiva senza il pannello appena aperto |
| La scheda «Eventi» della persona elenca anche i suoi appuntamenti | Quello che un cliente aveva prenotato si trovava solo sul calendario |

### File

| File | Cosa cambia |
|---|---|
| `frontend/src/components/Calendar/AppointmentPanel.vue` | Lettura e modifica dell'appuntamento; sostituisce `AppointmentDialog.vue` |
| `frontend/src/components/Calendar/KindSwitch.vue` | Appuntamento o evento |
| `frontend/src/pages/Calendar.vue` | Un «Nuovo», un pannello per tutto e due viste, colori, filtri, query dalla persona |
| `frontend/src/utils/calendarColors.js` | Da qualsiasi colore al colore del calendario — puro, testato |
| `crm/api/appointments.py` | `get_person_appointments`, testato in `test_scheduling.py` |
| `frontend/src/components/Activities/EventArea.vue`, `ActivityHeader.vue` | Appuntamenti della persona, «Prenota un appuntamento» |

---

## Il CRM sul telefono — ogni schermata, col dito

> **Completato** (29/09/2026). Ogni pagina, ogni cosa che si apre, ogni sezione
> delle impostazioni e i suoi dialoghi, guardati con Playwright su un telefono
> simulato (390 e 360px, chiaro e scuro) e percorsi col dito. Doc 29, «Il CRM
> sul telefono».

### Decisioni

| Decisione | Perche' |
|---|---|
| `max-md:` e non `sm:` per quello che cambia sul telefono | È la soglia di `isMobileView` (768px), che decide quali componenti si montano: con `sm:` fra 640 e 768 restava il layout da desktop dentro la forma da telefono |
| Le azioni nascoste fino al passaggio del mouse si mostrano anche al tocco | Su un telefono il passaggio non c'è: le azioni dei messaggi, il menu delle colonne del kanban e il «+» fra i passi di un'automazione non si potevano raggiungere |
| Un anello invisibile intorno ai controlli piccoli (`.touch-target`, e ogni interruttore), solo con `pointer: coarse` | Ingrandirli cambiava le righe in cui stanno; col mouse l'anello ruberebbe i clic ai vicini |
| Le impostazioni a tutto schermo, trovate con `:has(> .settings-modal)` | Il Dialog di frappe-ui non accetta una classe per il suo contenuto; da card teneva margini da monitor ed era 32px più alta dello schermo |
| Il titolo delle pagine delle impostazioni senza altezza fissa, le azioni sotto la descrizione | Con `h-5` la seconda riga del titolo finiva sulla descrizione; i pulsanti a destra schiacciavano la descrizione in una colonna di una parola |
| In una riga il testo cede (`min-w-0`) e il controllo resta; `SettingsRow` manda il controllo sotto quando non ci sta | Un titolo `truncate` senza `min-w-0` è largo quanto il suo testo e spingeva l'interruttore fuori dallo schermo |
| La riga dei pulsanti dei moduli lunghi resta in fondo allo schermo (`.dialog-footer`, e la riga `#actions` di frappe-ui riconosciuta dalle sue classi), con `overflow: clip` sul dialogo | Crea compariva solo alla fine; `overflow: hidden` di frappe-ui fa del dialogo un contenitore che scorre e un elemento `sticky` al suo interno non si ferma mai |
| Le tabelle figlie hanno una larghezza minima per colonna e scorrono di lato | A 340px sei colonne scendevano a due lettere; header e righe portano la stessa larghezza, senza un contenitore in più |
| I filtri del calendario in una riga che scorre, nascosti col pannello aperto | Su tre righe prendevano un settimo dello schermo sopra ogni giorno |
| Data e ora dei moduli al minuto (`datetimeFormat()`) | Il formato orario di sistema ha i secondi: una scadenza si leggeva «00:00:00» |
| La persona scelta nel pannello appuntamento si mostra per nome | Il Link mostrava l'id del lead appena la sua ricerca cambiava |
| Il catalogo delle prenotazioni chiesto con GET | Il metodo pubblico accetta solo GET; col POST predefinito di frappe-ui la pagina delle regole riceveva un 403 |
| Il controllo del webhook Meta risponde «nessuna app» invece di fallire | La pagina lo chiede a ogni apertura di un amministratore, anche prima che l'app esista |

### File

| File | Cosa cambia |
|---|---|
| `frontend/src/index.css` | `.touch-target`, gli anelli degli interruttori, `.settings-modal` a tutto schermo, `.dialog-footer` |
| `frontend/src/components/Settings/**`, `Layouts/SettingsLayoutBase.vue` | Titoli, intestazioni, margini, righe, griglie e schede di ogni pagina |
| `frontend/src/components/Controls/Grid.vue` | Colonne con una larghezza minima, scorrimento di lato |
| `frontend/src/components/Modals/*Modal.vue`, `FieldLayoutDialog.vue` | `.dialog-footer` |
| `frontend/src/pages/Calendar.vue`, `components/Calendar/*` | Filtri, persona per nome, campi toccabili in tutta la loro altezza |
| `frontend/src/components/Dashboard/*`, `Kanban/KanbanView.vue`, `pages/Tasks.vue` | Numeri, colonne, descrizioni |
| `frontend/src/pages/MobileLead.vue`, `MobileDeal.vue` | La scheda Eventi |
| `crm/integrations/meta/api.py` | Il webhook senza app, testato in `test_meta_webhook_check.py` |

---

## Correzioni — la conversazione vuota, i grafici, i listini

> **Completato** (29/09/2026). Tre errori che si vedevano solo tornando su una
> cosa già aperta, o andandosene in fretta. Doc 17, «Si apre dove leggi».

### Decisioni

| Decisione | Perche' |
|---|---|
| La conversazione segue i dati delle sue liste con un `watch`, non con l'`onSuccess` delle risorse | Una risorsa con `cache` è restituita tale e quale alla seconda apertura, con le callback di chi l'ha creata: muovevano la conversazione della prima visita, non più sullo schermo |
| `watch(arrived, …, { immediate: true })` | Alla seconda apertura le liste sono già piene: `arrived` è vero dall'inizio, il watcher non scattava, e la conversazione restava `invisible` |
| Le schede nell'indirizzo si confrontano in minuscolo | L'indirizzo dice `#activity`, la scheda si chiama «Activity»: la scheda era presa per un messaggio a cui scorrere, e la conversazione non veniva mai mostrata |
| Un grafico nostro (`EChart.vue`) al posto di quello di frappe-ui | Quello di frappe-ui osservava il proprio elemento mezzo secondo dopo il montaggio: smontato prima (cambio di dashboard con `?d=`), osservava `undefined` e lanciava; e non liberava mai il grafico |
| `echarts` dichiarato fra le dipendenze del frontend | Lo usavamo solo attraverso frappe-ui; ora lo importiamo, alla stessa versione che il lockfile aveva già |
| Il primo listino si seleziona da un `watch` sui dati | Stessa causa: alla seconda apertura dei Settings non si selezionava niente |

### File

| File | Cosa cambia |
|---|---|
| `frontend/src/components/Activities/Activities.vue` | La conversazione segue le sue liste e compare anche quando erano già piene |
| `frontend/src/components/Dashboard/EChart.vue`, `widgets/ChartWidget.vue` | Il grafico che vive e muore col suo elemento |
| `frontend/src/components/Settings/Scheduling/PriceListsSettings.vue` | Il primo listino selezionato anche alla seconda apertura |

---

## Home Actions — il menu dell'avatar non esegue più niente

> **Completato** (29/09/2026). Un'icona o una route salvate in Home Actions
> giravano come script nel browser di chiunque aprisse il menu dell'avatar,
> System Manager compresi, e le può scrivere un Sales Manager: escalation di
> privilegi, della stessa famiglia della SSTI nelle automazioni. Ora l'icona è
> solo un nome Feather e la route solo un percorso del sito o un link http(s),
> controllati al salvataggio, quando il menu si disegna e sui dati già salvati.

### Il buco

`UserDropdown.vue` disegnava con `innerHTML` qualunque icona cominciasse con
`<svg`, e apriva la route con `window.open` così com'era. Il campo `icon` è di
tipo Code, che Frappe salta di proposito quando sanifica l'HTML dei campi:
`<svg><image href=x onerror=…>` arrivava intatto nel database, e una route
`javascript:` pure. FCRM Settings dà `write` al Sales Manager.

Le strade per scriverci sono due, e la seconda non passa dal padre:

| Strada | Chi controlla |
|---|---|
| Salvare FCRM Settings (Home Actions, il form di Desk, `frappe.client.set_value`) | Solo `FCRMSettings.validate()`: salvando il padre, Frappe non chiama il `validate()` delle righe |
| `frappe.client.save` su una riga CRM Dropdown Item | Il permesso si guarda sul padre, ma gira solo il `validate()` della riga |

Per questo il controllo sta in `CRMDropdownItem.validate_icon_and_route()`, e lo
chiamano tutti e due.

### Decisioni

| Scelta | Perché |
|---|---|
| Una lista di nomi, non DOMPurify in profilo SVG | Niente di nostro salvava SVG: le voci standard in `hooks.py` usano `settings`, `info`, `log-out`, e né `install.py` né una patch scrivono icone. Un sanificatore SVG lato server sarebbe un secondo parser da tenere al passo con quello del browser |
| La lista è tutta feather-icons (287 nomi) | È ciò che `FeatherIcon` sa disegnare, e la descrizione del campo prometteva «feather icons»: chi usava un nome continua a vederlo. I `lucide-*` no: il menu li mette in `class=""`, e Tailwind genera solo le classi che trova nel sorgente, quindi da database non si vedrebbero comunque |
| Un file solo, `crm_dropdown_item/feather_icons.json` | Lo legge il server e lo importa `frontend/src/utils/dropdownItems.js`; un test JS verifica che coincida con `feather.icons` |
| Route: relativa, oppure `http`/`https` con un host | Lo schema si riconosce come fa il browser (WHATWG): lettera ASCII, poi lettere, cifre, `+-.`, poi `:`. I caratteri di controllo si rifiutano ovunque, perché il browser toglie tab e a capo: `java\tscript:` è `javascript:` |
| Nel menu la route la legge `new URL()` | È lo stesso parser di `window.open`, niente da emulare. Una voce con la route rifiutata non entra nel menu |
| Il messaggio d'errore non ripete il valore | Toast e msgprint disegnano HTML: ripetere l'icona rifiutata l'avrebbe eseguita lì |
| `noopener` su `window.open` | Una pagina esterna aperta dal menu non ha più `window.opener` per portare altrove la scheda del CRM |

### I dati già salvati

`crm.patches.v1_0.clean_unsafe_dropdown_items`: un'icona che non è un nome
Feather si svuota — SVG compresi, anche innocui, perché il menu il markup non lo
disegna più — e la voce prende l'icona di default. Una route con un altro schema
si svuota e la riga si nasconde, così resta in Home Actions da guardare invece di
sparire; un separatore la route non la usa, quindi si svuota soltanto. FCRM
Settings non tiene lo storico delle versioni: la patch stampa quello che toglie,
che può essere l'unica traccia di chi ha scritto cosa.

Gira prima degli `after_migrate`, dove `sync_table()` salva FCRM Settings: senza
la pulizia, quel salvataggio con la validazione nuova fermerebbe la migrate.

### Lasciato com'è, di proposito

- `icon` resta di tipo Code. Passare a Data vorrebbe dire `varchar(140)`, e la
  sincronizzazione dello schema gira *prima* delle patch post-model-sync: sui
  siti con un SVG lungo salvato la migrate si fermerebbe.
- «Open in new window» spento apre comunque una scheda nuova: `window.open` con
  target vuoto vale `_blank`. Era già così, e non è una questione di sicurezza.

### File

| File | Cosa cambia |
|---|---|
| `crm/fcrm/doctype/crm_dropdown_item/crm_dropdown_item.py` | `is_allowed_icon()`, `is_safe_route()`, `validate_icon_and_route()` |
| `crm/fcrm/doctype/crm_dropdown_item/feather_icons.json` | I nomi ammessi, per server e menu |
| `crm/fcrm/doctype/fcrm_settings/fcrm_settings.py` | Controlla ogni riga a ogni salvataggio |
| `crm/patches/v1_0/clean_unsafe_dropdown_items.py` | Pulisce quello che era stato salvato prima |
| `frontend/src/utils/dropdownItems.js` | `safeDropdownIcon()`, `safeDropdownRoute()` — puri, testati |
| `frontend/src/components/UserDropdown.vue` | Niente più `innerHTML`, route controllate, `noopener` |

---

## Inviti — la chiave del link è una credenziale

> **Completato** (29/09/2026). Chiusi tre modi di prendersi un ruolo o un
> account con gli inviti. La chiave nel link d'invito imposta la password di un
> utente nuovo e consegna un ruolo a chi accetta: ora esiste solo nell'email
> all'invitato, il ruolo è uno che chi invita può concedere, e chi ha già un
> account accede prima di accettare.

### I tre exploit

1. **Un Sales Manager diventava System Manager.** `invite_by_email` controllava
   chi può invitare chi, ma il doctype dava `create` al Sales Manager: un POST a
   `/api/resource/CRM Invitation` per il proprio indirizzo con ruolo System
   Manager, la chiave riletta dal record, `accept_invitation` — e `accept()`
   aggiungeva il ruolo con `ignore_permissions`.
2. **Un Sales User prendeva un invito in attesa.** La chiave era un campo Data
   in chiaro e il Sales User aveva `read`: elencare gli inviti via REST dava il
   link di chiunque, anche di un futuro System Manager, e con quello la sua
   password.
3. **Il link faceva entrare nell'account.** Per un utente che esisteva già
   `accept_invitation` chiamava `login_as`: chi aveva la chiave diventava
   l'invitato.

### Decisioni

| Decisione | Perché |
|---|---|
| La regola di `invite_by_email` sta in `validate`, per ogni invito in attesa (`can_grant_role`) | È il punto da cui passano REST, Desk e codice. Vale finché l'invito è in attesa: uno scaduto o accettato non consegna più niente, e il job che li fa scadere non si blocca su chi nel frattempo ha perso il ruolo |
| `email`, `role` e `invited_by` in `set_only_once` | Frappe lo impone anche con `ignore_permissions`: un invito controllato non diventa un altro invito |
| `accept()` richiede di nuovo che `invited_by` possa concedere il ruolo e sia attivo | L'invito vale tre giorni: chi l'ha mandato può aver perso il ruolo, o l'account, nel frattempo |
| Si salva lo SHA-256 della chiave | Come le chiavi di reset della password di Frappe (`User._reset_password`): leggere il record, un backup o il database non dà niente che apra l'invito |
| La chiave passa da 12 a 56 caratteri esadecimali | 12 sono 48 bit: l'hash di una chiave così si inverte per forza bruta in qualche ora |
| E il campo `key` sta su permlevel 1, che nessun ruolo ha | Difesa in profondità: REST, report view e `frappe.client` lo tolgono dai risultati, e filtrarci sopra dà PermissionError. `set_key` lo toglie dal reset dei permlevel, altrimenti un System Manager che crea un invito dal Desk lo salverebbe vuoto |
| Sales Manager senza `create` e `write`, Sales User senza accesso | Gli inviti si creano con `invite_by_email`. Al Sales Manager restano `read` e `delete`, che servono a Impostazioni → Invita utente per elencare e revocare gli inviti in attesa |
| Chi ha già un account accede, poi torna al link | Il link prova di aver avuto l'email, non di essere il titolare dell'account. Ospite → `/login?redirect-to=<link>`; un altro utente collegato → PermissionError; l'invitato collegato → ruolo aggiunto e `/crm`. Un utente nuovo imposta la password come prima |
| Accettare dal Desk per conto dell'invitato richiede `can_grant_role` | È un'altra strada per consegnare il ruolo |
| `invite_by_email` guarda solo gli inviti in attesa | Un invito scaduto impediva per sempre di invitare di nuovo quell'indirizzo dal CRM |

### Dati esistenti

La patch `expire_invitations_with_readable_keys` cancella le chiavi in chiaro e
fa scadere gli inviti in attesa che ne avevano una: ogni Sales User poteva
leggerle, quindi vanno considerate compromesse. Chi li aveva ricevuti va
invitato di nuovo da Impostazioni → Invita utente. Gli hash (64 caratteri)
restano come sono.

La patch non tocca i ruoli già dati. Per vedere se qualcuno ha usato questi
exploit prima della correzione — sono indizi, non prove: guardano i ruoli di
oggi di chi ha invitato:

```sql
-- inviti accettati per un ruolo che chi invitava non poteva dare, o a sé stessi
select i.name, i.email, i.role, i.invited_by, i.accepted_at
from `tabCRM Invitation` i
where i.status = 'Accepted'
  and (i.email = i.invited_by
       or (i.role in ('Sales Manager', 'System Manager')
           and i.invited_by != 'Administrator'
           and not exists (select 1 from `tabHas Role` r
                           where r.parenttype = 'User' and r.parent = i.invited_by
                             and r.role = 'System Manager')));

-- inviti accettati da un utente che esisteva già: il link faceva login_as
select i.name, i.email, i.role, i.accepted_at
from `tabCRM Invitation` i join `tabUser` u on u.name = i.email
where i.status = 'Accepted' and u.creation < i.creation;
```

Nel secondo caso l'Activity Log ha il login dell'invitato all'ora di
`accepted_at`, con l'IP di chi ha aperto il link.

### Lasciato com'è, di proposito

- **I permessi personalizzati.** Se un sito ha dei Custom DocPerm su CRM
  Invitation (Role Permission Manager), valgono quelli e non i permessi del
  doctype. Gli exploit restano chiusi lo stesso, perché li chiudono `validate`,
  l'hash e l'accesso obbligatorio, non i permessi.
- **I messaggi di `invite_by_email`.** La regola ora sta anche in
  `can_grant_role`, ma i messaggi tradotti («You are not allowed to invite …»)
  restano dove l'utente li vede.
- **L'hash nella risposta di un POST REST.** Chi crea un invito via REST (un
  System Manager) si vede restituire il record, hash compreso: è un hash, non
  apre niente.
- **`share` al Sales Manager.** Frappe non lascia condividere un diritto che non
  si ha, quindi non gli restituisce `write`.

### File

| File | Cosa cambia |
|---|---|
| `crm/fcrm/doctype/crm_invitation/crm_invitation.py` | `can_grant_role`, `validate`, `set_key`, il controllo in `accept()` e nell'accettazione dal Desk, la chiave che sparisce quando l'invito scade |
| `crm/fcrm/doctype/crm_invitation/crm_invitation.json` | Permessi, `set_only_once`, `key` nascosto su permlevel 1 |
| `crm/api/__init__.py` | `accept_invitation` confronta gli hash e non fa più `login_as`; `invite_by_email` guarda solo gli inviti in attesa |
| `crm/patches/v1_0/expire_invitations_with_readable_keys.py` | Le chiavi in chiaro spariscono, gli inviti in attesa che le avevano scadono |
| `crm/fcrm/doctype/crm_invitation/test_crm_invitation.py` | I tre exploit dall'inizio alla fine, ogni controllo da solo, il flusso normale |

---

## Permessi degli endpoint — prima del portale pazienti

> **Completato.** Il portale pazienti porterà utenti loggati come Website User, e
> un metodo `@frappe.whitelist()` senza controllo è chiamabile da chiunque abbia
> una sessione. Undici endpoint segnalati — due letti a mano, gli altri da un
> audit automatico — verificati uno per uno su un bench Frappe 16: dieci
> chiedevano un controllo, uno (`remove_assignments`) non era sfruttabile via
> HTTP ma si reggeva su un dettaglio di Frappe. Poi due cose trovate strada
> facendo: gli aiuti dell'editor del calendario, e chiamate, note e task che la
> gerarchia di vendita non toccava. I test sono in
> `crm/tests/test_endpoint_permissions.py`: ogni endpoint provato da chi ne ha
> diritto, da un Sales User fuori dalla gerarchia e da un Website User senza
> ruoli CRM. Tolto un controllo alla volta, almeno un test fallisce.

### La regola

Si controlla il record che si restituisce, o quello a cui appartiene (lead o
trattativa), con `frappe.has_permission(doctype, ptype, doc, throw=True)`. Le
liste passano da `frappe.get_list`, così valgono le
`permission_query_conditions` di `crm/permissions/org_hierarchy.py`.
`ignore_permissions` non arriva mai dal client. A chi aveva diritto la risposta
non cambia.

Dove il server chiamava lo stesso endpoint da un webhook, cioè come Guest, c'è
ora una funzione gemella senza controlli e l'endpoint whitelisted resta per le
richieste: `find_contact_by_phone_number()` accanto a
`get_contact_by_phone_number`, `assigned_users_of()` accanto a
`get_assigned_users`.

### Decisioni

| Endpoint | Cosa fa ora | Perché |
|---|---|---|
| `get_call_log`, `get_recording_url`, `get_transcript`, `transcribe_now` | Il controllo standard sul call log, che ora porta con sé la gerarchia (sotto) | `get_call_log` non controllava niente; registrazione e trascrizione solo il doctype, che ogni Sales User ha su ogni chiamata |
| `get_calendar`, `get_workload`, `get_scheduler_meta` | `get_list` al posto di `get_all` | CRM Appointment non ha gerarchia: ogni Sales User vede il calendario come prima, un Website User riceve `PermissionError`. `User` e `CRM Booking Connection` restano `get_all`: il Sales User non li legge e il calendario ne ha bisogno |
| `check_conflicts`, `get_available_slots`, `quote_price` | Lettura di CRM Appointment (`_check_reader()`) | `check_conflicts` risponde «X ha già un altro appuntamento in questa fascia» per qualsiasi partecipante gli si passi: diceva a chiunque quando una persona ha un appuntamento. Chi legge il calendario sa già le stesse cose; `/prenota` ha endpoint suoi |
| `get_deal_contacts` | Lettura della trattativa | |
| `get_linked_deals` | Solo le trattative che `get_list` restituisce, nell'ordine di prima | Leggere la persona non è leggere le sue trattative |
| `get_contact_by_phone_number` | Un record che l'utente non può aprire torna come nessun record, `{"mobile_no": <numero cercato>}`; la trattativa di un contatto sparisce se non è leggibile | Qui, di proposito, niente `throw`: un `PermissionError` nominerebbe il record, e un numero è la cosa che si prova in serie per sapere chi c'è nel CRM. Le schermate di chiamata fanno come per uno sconosciuto |
| `get_contact_lead_or_deal_from_number` | Non più whitelisted | La chiamano solo WhatsApp, SMS, coexistence e una patch, dal server |
| `get_linked_docs_of_document` | Lettura del documento; fra i collegati solo quelli leggibili | La trattativa di una persona può essere di un altro, come sa già `get_conversation_on_deals` |
| `get_assigned_users` | Lettura del documento | |
| `remove_assignments` | Tolto il parametro `ignore_permissions` | Annullare un'assegnazione azzera `lead_owner`/`deal_owner` e cambia chi vede il record. Via HTTP non era sfruttabile — `frappe.call` passa da `get_newargs`, che toglie `ignore_permissions` ai kwargs — ma l'endpoint non deve reggersi su quello |
| `create_deal` | `has_permission("CRM Deal", "create")` prima di tutto | Persona, organizzazione e trattativa nascono con `ignore_permissions`: il controllo viene prima di qualunque insert |
| `restore_defaults`, `restore_demo_data` | `frappe.only_for(["Sales Manager", "System Manager"])` come `clear_demo_data`, solo POST | `run_doc_method` chiede solo di poter leggere FCRM Settings, e ogni Sales User può |

### Chiamate, note e task seguono il loro lead

CRM Call Log, FCRM Note e CRM Task avevano solo i permessi di ruolo: ogni Sales
User leggeva ogni chiamata — trascrizione e `recording_url` compresi — e ogni
nota e task, da `/api/resource`, dalle liste e dal desk. Ora hanno un
`has_permission` e una `permission_query_conditions` in `org_hierarchy.py`,
costruiti dalla stessa condizione: la lista e il singolo record non possono dare
risposte diverse. Lead e trattative sono passati agli stessi mattoni (`_scope`,
`_theirs`, `_assigned`) e il loro SQL è quello di prima, byte per byte.

Chi vede tutto resta com'era: Administrator, System Manager, e il Sales Manager
fuori dall'albero o con la gerarchia spenta. Per gli altri:

| Record | Lo vede | Perché |
|---|---|---|
| Chiamata | Chi l'ha fatta, presa o registrata, e il suo ramo; chi vede uno qualsiasi dei lead o delle trattative collegati; tutti, se non è collegata a nessuno | La telefonia salva il lead in `links`, una chiamata a mano in `reference_*`: contano tutti e due. Ne basta uno, perché la chiamata compare nella timeline di ognuno. Chi era al telefono la apre sempre: una chiamata in entrata la prende chi è libero, e le note si scrivono a chiamata in corso |
| Nota | Chi l'ha scritta e il suo ramo; chi vede il lead o la trattativa di cui parla; tutti, se non parla di nessuno — salvo che la colleghi una chiamata che l'utente non vede | Una nota scritta durante una chiamata non punta a niente: è la chiamata a collegarla |
| Task | Come la nota, più l'assegnatario e il suo ramo (`assigned_to` o un ToDo aperto) | Senza, l'assegnazione di Frappe condividerebbe il task (`frappe.share`) per farglielo vedere |
| Lead condiviso | Porta con sé le sue chiamate, note e task | Una condivisione apre il lead a prescindere dalla gerarchia, nella lista e nella sua pagina |

Tre scelte per non aprire una porta di lato:

- **Una sola chiamata nascosta basta a nascondere la nota.** Chiunque può
  collegare qualsiasi cosa a una chiamata sua: se bastasse una chiamata visibile,
  collegare la nota di un altro sarebbe il modo di leggerla. Il rovescio — una
  nota collegata a due chiamate e visibile da una sola — è raro, e resta chiuso.
- **Si collega solo quello che si può leggere.** `CRMCallLog.validate` rifiuta un
  collegamento nuovo a un record che l'utente non legge; la telefonia, che collega
  per conto di nessuno, salva con `ignore_permissions`.
- **Chi mostra le note di una chiamata le filtra.** `get_call_log` e la timeline
  (`get_linked_calls`) non riportano una nota o un task solo perché la chiamata li
  collega, e `add_task_to_call_log` non modifica più un task esistente senza il
  permesso di scriverlo, come già succedeva per le note.

`check_call_log_permission()`, il controllo per endpoint del primo giro, non c'è
più: la regola sta nell'hook e gli endpoint sono tornati a chiedere a Frappe. La
coda delle richiamate e il dialer leggevano già con `get_list`, apposta, e ora
mostrano solo le chiamate che l'agente vede. Le condizioni si leggono meglio con
un esempio che a parole: `get_note_permission_query_conditions("…")` in una
console stampa l'SQL intero.

### Lasciato com'è, di proposito

- `create_deal` inserisce ancora con `ignore_permissions`: i User Permission e i
  permlevel sui campi della trattativa lì non valgono.
- `delete_bulk_docs` non controlla niente prima di scollegare i record: si regge
  sul `write` di ogni collegato e sul `delete` di Frappe.
- `_decorate` in `get_calendar` restituisce nome, email e telefono di tutti i
  partecipanti di ogni appuntamento leggibile. Oggi lo legge solo chi ha un ruolo
  CRM; se il portale darà ai pazienti la lettura degli appuntamenti di gruppo,
  ognuno vedrà gli altri.
- **CRM SMS Message** ha solo i permessi di ruolo: ogni Sales User legge ogni
  SMS. È il buco che avevano le chiamate, e si chiude allo stesso modo. Le email
  (Communication) seguono già il loro record con le regole di Frappe; WhatsApp
  Message è dell'app `frappe_whatsapp`.
- I conteggi del cruscotto contano per proprietario (`visible_owners`), non con
  queste regole: sono numeri, non record.
- `ListBulkActions.vue` passa `ignore_permissions: true` a
  `frappe.desk.form.assign_to.remove_multiple`, che non lo accetta e che
  `get_newargs` scarterebbe comunque.

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/org_hierarchy.py`, `crm/hooks.py` | La regola di chiamate, note e task; lead e trattative con gli stessi mattoni |
| `crm/fcrm/doctype/crm_call_log/crm_call_log.py` | `get_call_log` riporta solo note e task leggibili; `validate` collega solo quello che l'utente legge |
| `crm/api/activities.py` | La timeline filtra note e task delle chiamate |
| `crm/integrations/api.py` | `get_contact_by_phone_number` filtra, `find_contact_by_phone_number()` per il server; `get_contact_lead_or_deal_from_number` non whitelisted; `add_task_to_call_log` |
| `crm/api/appointments.py` | `get_list` nel calendario, `_check_reader()` negli aiuti dell'editor |
| `crm/fcrm/doctype/crm_deal/api.py`, `crm/api/contact.py` | Contatti di una trattativa, trattative di un contatto |
| `crm/api/doc.py` | Record collegati, assegnatari e `assigned_users_of()`, `remove_assignments` |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `create_deal` |
| `crm/fcrm/doctype/fcrm_settings/fcrm_settings.py` | Ripristini solo per i manager, solo POST |
| `crm/integrations/twilio/api.py`, `crm/integrations/exotel/handler.py`, `crm/api/whatsapp.py`, `crm/fcrm/doctype/crm_sms_message/crm_sms_message.py`, `crm/automation/engine.py` | Le gemelle senza controlli, per chi arriva come Guest |
| `crm/tests/test_endpoint_permissions.py` | I test |

---

## Permessi e segreti — quello che un ruolo non deve poter fare

> **Completato** (29/09/2026). Sei punti di un audit — il primo letto nel
> codice, gli altri da uno strumento automatico, tutti verificati prima di
> toccarli — più due trovati strada facendo: la chiave del webhook delle
> automazioni e le chiamate ERPNext che prendono il nome di una trattativa. Un
> commit e dei test per ciascuno: chi non deve viene fermato, chi deve continua
> a riuscire. Gli inviti, trovati nello stesso giro, sono in
> «Inviti — la chiave del link è una credenziale»; i ripristini di FCRM
> Settings in «Permessi degli endpoint».

### Decisioni

| Decisione | Perché |
|---|---|
| «Manager» è `{System Manager, Sales Manager}` in una costante per modulo | È l'insieme che usa già tutto il resto delle API. Quando arriverà `crm/permissions/livelli.py` i controlli da spostare sono: `update_quick_filters` (`crm/api/doc.py`), `get_assignment_rules_list`, `MANAGER_ROLES` di ERPNext CRM Settings, `_webhook_key` delle automazioni |
| La gerarchia di vendita la accende e la spegne solo un System Manager, controllato nel controller | Un Sales Manager nell'albero è proprio chi l'albero limita; nascondere il pulsante non bastava, `frappe.client.set_value` arriva lo stesso |
| I metodi whitelisted di ERPNext CRM Settings controllano il ruolo da soli | `run_doc_method` v1 carica il documento con un controllo di **lettura** e basta (la v2 chiede la scrittura solo sulle POST): chi legge ERPNext CRM Settings poteva far chiamare l'ERPNext remoto con le credenziali salvate |
| Agli ospiti si aprono solo liste di valori (Lead Source, Territory, Industry, CRM Service, Salutation, Gender, Currency) | Guest `select` vuol dire che chiunque abbia il link del modulo elenca quei record: mai persone, mai record del CRM. Scrivere una regola di permesso del sito è di un System Manager, che lo fa con i suoi permessi: niente più `ignore_permissions` |
| I segreti diventano campi Password, non un livello di permesso | Su un Single `frappe.client.get_single_value` e `get_value` controllano il doctype, non il campo: il livello di permesso non avrebbe fermato niente |
| Il token delle prenotazioni si confronta decifrato, connessione per connessione | Si cercava per valore, e ora la colonna tiene solo asterischi. Le connessioni attive sono poche; il confronto è a tempo costante, sui byte (`compare_digest` rifiuta le `str` non ASCII) |
| Una patch pre_model_sync toglie l'indice unique su `webhook_token` | Frappe non lo toglie quando la colonna diventa `text`, e MariaDB 10.11 lo converte in `UNIQUE … USING HASH`: le maschere di due token lunghi uguale coincidono e la seconda connessione veniva rifiutata. Provato prima di scriverla |
| La patch dei segreti sposta i valori in chiaro in __Auth e maschera la colonna | Come fa Frappe salvando una Password: gli URL e le chiavi già dati ai fornitori continuano a funzionare |
| Il token di verifica Meta non si mostra più | La schermata Meta registra il webhook da sé (*Configure it*), e dal doc 27 nessuna schermata lo mandava più; per incollarlo a mano un System Manager usa `frappe.client.get_password` |
| `CRM Global Settings` in sola lettura per il Sales User | Lo scrivono solo `update_quick_filters`, l'installazione e una patch: con create e write al Sales User il controllo sull'endpoint era a una chiamata REST di distanza |
| Le chiamate ERPNext che prendono il nome di una trattativa controllano che chi chiama la possa leggere | Leggevano con `frappe.get_doc` e `frappe.db`, che saltano i permessi: un Sales User nominava la trattativa di un altro e ne vedeva prodotti, prezzi e cliente, o la mandava a ERPNext come Prospect. `check_permission` applica anche la gerarchia |
| Per fare l'offerta basta leggere la trattativa | Non la modifica: il Prospect mandato a ERPNext porta gli stessi dati che chi chiama già legge |
| `check_customer_for_quotation` guarda la Quotation, non la trattativa | La chiama il modulo Sales Order di ERPNext, e chi lo compila può non vedere la trattativa nel CRM: deve poter leggere la Quotation e creare Sales Order, che è il passo che sta facendo |

### Lasciato com'è, di proposito

- `is_erpnext_installed` resta aperto a chi legge ERPNext CRM Settings: risponde
  con un booleano sul sito, e la pagina lo chiede.
- `CRM Twilio Settings.api_key` resta Data: è lo SID della chiave API, un
  identificativo; il segreto (`api_secret`) era già Password.
- `CRM Booking.access_token` e `CRM Appointment Participant.access_token` restano
  leggibili da chi gestisce le prenotazioni: sono i link di gestione mandati al
  cliente, e chi li legge può già modificare quella prenotazione.
- La copia del token di verifica che `upsert_account` scrive su `WhatsApp
  Account` è un campo di `frappe_whatsapp`, un'altra app.

### File

| File | Cosa cambia |
|---|---|
| `crm/api/doc.py`, `crm_global_settings.json` | Filtri rapidi: manager, sette liste; Sales User in sola lettura |
| `crm/fcrm/doctype/fcrm_settings/fcrm_settings.py`, `Hierarchy.vue` | Interruttore della gerarchia |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | Ruolo sui metodi; `api_key` decifrata; `_readable_deal` davanti alle chiamate delle offerte |
| `crm/api/form.py`, `FormBuilderPanel.vue`, `FieldCard.vue` | Liste apribili agli ospiti, System Manager, chi può aprire cosa |
| `crm/api/exchange_rate.py`, `crm/integrations/meta/`, `crm/integrations/whatsapp/`, `crm/integrations/exotel/handler.py`, `crm/telephony/providers/exotel.py` | Segreti letti con `get_password`, confronti a tempo costante |
| `crm/fcrm/doctype/crm_booking_connection/crm_booking_connection.py`, `crm/api/booking_platforms.py`, `crm/booking_platforms/sync.py` | `connection_for_token` |
| `crm/api/assignment_rule.py` | Solo manager |
| `crm/api/automation.py` | Chiave del webhook solo ai manager, confronto decifrato |
| `crm/patches/v1_0/` | `drop_unique_index_on_booking_webhook_token` (pre), `revoke_guest_select_outside_lookups`, `encrypt_integration_secrets` |
| `crm/tests/test_quick_filters.py`, `test_settings_methods.py`, `test_integration_secrets.py`, `test_assignment_rule_api.py`, `test_erpnext_deal_access.py`, e i test di FCRM Settings, form e automazioni | Per ogni fix: il ruolo che non deve fallisce, quello che deve riesce |

---

## Livelli, capacità e piano — la PR 1 del doc 30

> **Completato** (29/09/2026). Il CRM assegna **livelli** (Segreteria, Operatore,
> Manager amministrativo, e Commerciale facoltativo) invece di ruoli, e il codice
> chiede **capacità** con un nome invece di confrontare ruoli. Una capacità vale se
> il livello la dà e il suo modulo è attivo nel **piano** del centro. La matrice è
> quella del [doc 30](../docs/progetto-ghl/30-ruoli-e-permessi.md), che ha la
> sezione "La PR 1, com'è fatta". È il primo passo della fase 0 del gestionale
> medico: la clinica porterà il suo livello (Direzione sanitaria) e le sue capacità
> nello stesso registro.

### Decisioni

| Decisione | Perché |
|---|---|
| Le capacità si calcolano dai **livelli**, non dai ruoli | Il doc 30 è una matrice livello per capacità: il registro la trascrive così com'è, e `calcola()` è una funzione pura che la prova senza sito. I ruoli restano i mattoni dei permessi sui documenti |
| Chi non ha livelli conta per i livelli che i suoi ruoli implicano | Sales Manager → Manager, Sales User → Commerciale: con i ruoli di prima le risposte sono quelle di prima, e ogni `MANAGER_ROLES` sostituito continua a dire la stessa cosa |
| La migrazione dà Segreteria al Sales User, Commerciale dove la gerarchia è accesa | Il doc 30 dice Segreteria "da verificare sito per sito"; un sito che ha acceso la gerarchia ha scelto che ognuno veda il suo team, e Commerciale lo conserva |
| La migrazione non tocca chi perderebbe un ruolo | Frappe rifà i ruoli di un utente con profili dai profili, a ogni salvataggio: chi ha un ruolo di un'altra app, o un Invoicing Manager che la Segreteria non porta, resta com'è |
| I profili si chiamano `CRM …` e il registro li riscrive a ogni migrate | Il codice è la fonte, i record lo seguono; il prefisso dice quali profili sono del CRM e quali no |
| I ruoli dei profili si riscrivono sulle righe, non con `save()` | Salvare un Role Profile mette in coda un lavoro che risalva i suoi utenti e blocca il profilo finché un worker non l'ha fatto: un secondo migrate prima di allora avrebbe dovuto saltare la modifica. Gli utenti si risalvano subito, lì |
| `role_profile_name` si svuota a ogni assegnazione | È il vecchio campo singolo, che Frappe tiene uguale al primo profilo e rimette nella tabella al salvataggio se non c'è: togliere un livello lo faceva tornare |
| Le capacità "a scelta" sono righe di `CRM User Capability` | Un ruolo messo a mano su un utente con profili sparisce al salvataggio |
| Il piano: un modulo non elencato tiene il suo predefinito | Quello che il CRM faceva già resta acceso, nessun sito perde niente il giorno dopo; un modulo nuovo nasce spento, così la clinica non compare in una palestra |
| Un modulo finito diventa di sola lettura, non spento | Non si cancella mai niente (doc 30): restano le capacità che non scrivono |
| La prova di 14 giorni la fa partire il Manager, e scrive nel piano per suo conto | Il piano è dell'agenzia; l'unica cosa che il centro fa da solo è provare un modulo che non ha, e l'agenzia lo sa per email |
| Il Manager dà anche il livello Manager, ma non se lo toglie | Il doc 30: il Manager nomina gli altri Manager. Togliersi il livello da solo chiudeva fuori il centro dalla gestione degli utenti |
| Gli utenti dell'agenzia non si toccano dal CRM | Hanno System Manager, che un livello non porta: dare loro un livello glielo toglierebbe. Li gestisce l'agenzia dal Desk |
| Moduli del Desk: Segreteria e Operatore vedono quelli dell'app CRM | Come il Sales User di prima, ma fatturazione e Sistema TS compresi, che il vecchio blocco toglieva |

### Il bug della registrazione

`crm/hooks.py` registrava fatturazione e Sistema TS al momento dell'import. Fuori
dal developer mode Frappe tiene gli hook nella sua cache (`client_cache`), e un
processo che li trova lì non importa mai `hooks.py`: provato su un processo nuovo,
`estensioni._risolutori` era vuoto, "fisioterapista" non era nel registro e la
verifica del tracciato TS non era registrata. Adesso `crm/registrazione.py` registra
tutto una volta per processo, chiamato da `hooks.py`, da `before_request`, da
`before_job` e da chi legge il registro dei livelli.

### Lasciato com'è, di proposito

- I permessi dei documenti non cambiano: Front Desk e Practitioner non portano
  ancora DocPerm, e la Segreteria vede le persone come il Sales User di prima.
  L'ambito che segue la persona e le fatture tolte al Sales User sono la PR 2.
- Il frontend usa ancora `isManager()` quasi ovunque; menu, rotte e impostazioni
  passano a `puo()` con la PR 3. Oggi `puo()` lo usano la pagina Utenti, gli inviti
  e il Piano.
- ERPNext resta a `MANAGER_ROLES`: passa all'agenzia con la sua pagina, nella PR 3.
- Marketing, Amministrazione e Sola lettura sono la PR 4.

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/livelli.py`, `catalogo.py`, `utenti.py` | Il registro e il calcolo; la matrice del CRM; profili, assegnazione, migrazione |
| `crm/invoicing/capacita.py`, `crm/invoicing/__init__.py` | La colonna della fatturazione |
| `crm/registrazione.py`, `crm/hooks.py` | La registrazione in ogni processo; `after_migrate` sincronizza i profili |
| `crm/fcrm/doctype/crm_plan/`, `crm_plan_module/`, `crm_user_capability/` | Il piano; le capacità a scelta |
| `crm/api/user.py`, `crm/api/__init__.py`, `crm/api/session.py`, `crm/www/crm.py` | Livelli per utente, inviti per livello, capacità nella sessione e all'avvio |
| `crm/fcrm/doctype/crm_invitation/` | Il campo `levels`; chi invita deve poterli dare, all'invio e all'accettazione |
| `crm/api/plan.py` | Impostazioni › Piano, la prova di 14 giorni |
| Una trentina di file di `crm/api`, `crm/integrations`, `crm/fcrm/doctype`, `crm/dashboard`, `crm/www`, `crm/demo` | `MANAGER_ROLES` e i controlli scritti a mano diventano capacità |
| `crm/patches/v1_0/give_users_their_levels.py`, `crm/install.py` | Il passaggio degli utenti; i profili all'installazione |
| `frontend/src/stores/users.js`, `composables/levels.js` | `puo()`, `ambito()`, i livelli offerti |
| `frontend/src/components/Settings/Users.vue`, `InviteUserPage.vue`, `LevelPicker.vue`, `PlanSettings.vue`, `Modals/UserAccessModal.vue`, `Modals/AddExistingUserModal.vue` | Utenti, inviti, accesso, piano |
| `crm/permissions/test_livelli.py`, `test_utenti.py` | La matrice senza sito; i livelli su utenti veri |
