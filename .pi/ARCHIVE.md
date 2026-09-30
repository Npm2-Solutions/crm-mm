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
| Un livello non si dà a chi perderebbe un ruolo di un'altra app | `assegna_livelli` rifiuta e dice quali ruoli: pagina Utenti, invito accettato da chi ha già un account e migrazione passano tutti da lì. Il vecchio codice aggiungeva ruoli e basta, i profili li rifanno |
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

---

## Il sito senza Builder, le fatture a chi deve

> **Completato** (29/09/2026). La seconda PR della fase 0 del gestionale medico.
> Senza Frappe Builder la parte Sito non esiste per nessuno; le fatture le leggono
> Segreteria, Manager e, delle sue prestazioni, l'Operatore; il Commerciale e il
> Sales User di prima non più, neanche nella cronologia della persona.

### Decisioni

| Decisione | Perché |
|---|---|
| Le capacità possono avere un **requisito** (`requisito="builder"`), controllato da una funzione registrata | Installare Builder è un lavoro sul bench, dell'agenzia: senza, `sito.gestisci` non è di nessuno, agenzia compresa, e menu, impostazioni e rotte lo sanno dall'avvio |
| Le rotte dichiarano `meta.richiede` e la guardia del router la controlla | Una pagina tolta dal menu si apriva ancora dall'indirizzo; è il meccanismo della PR 3 del doc 30, qui per sito e fatture |
| Il Sales User perde la lettura di CRM Invoice, del suo registro e delle fatture passive | Una riga di fattura dice cosa è stato fatto ("seduta di psicoterapia"): è un dato sanitario. I cataloghi (servizi fatturabili, erogatori, qualifiche) restano leggibili: non dicono niente di nessuno |
| L'Invoicing User emette (create, write, submit) e non annulla | La Segreteria emette e incassa (doc 30); annullare e le note di credito restano all'Invoicing Manager |
| La trasmissione a SdI e Sistema TS chiede `fatture.invia` | È "a scelta" per la Segreteria: emettere non vuol dire spedire. Chi lavora solo dal Desk con un ruolo della fatturazione, fuori dai livelli, trasmette come prima (`verifica_nel_crm`) |
| L'Operatore ha un permesso di lettura su CRM Invoice, ristretto per record alle fatture con una sua riga | `permission_query_conditions` e `has_permission` in `crm/invoicing/permessi.py`, dalla stessa regola; l'ambito restringe e non allarga, e non tocca chi è fuori dai livelli |
| La cronologia chiede le fatture con `get_list`, e a chi non le legge non le chiede affatto | Prima `get_all` saltava i permessi |
| I ruoli dei livelli si creano prima della sincronizzazione dei DocType (`before_install`, patch `pre_model_sync`) | CRM Invoice nomina Practitioner, e una DocPerm su un ruolo che non esiste ancora fallisce. I ruoli che Frappe crea da sé (Sales User, Sales Manager, System Manager) restano a Frappe |
| La pagina Fatture nasconde "Impostazioni" a chi non configura la fatturazione | La Segreteria lavora nella pagina, la configurazione è del Manager |

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/livelli.py`, `catalogo.py`, `utenti.py` | Requisiti; `verifica_nel_crm`; `assicura_ruoli` prima della sincronizzazione |
| `crm/invoicing/doctype/crm_invoice/`, `crm_invoice_log/`, `crm_supplier_invoice/` | Permessi |
| `crm/invoicing/permessi.py`, `crm/hooks.py` | Le fatture dell'Operatore |
| `crm/invoicing/api.py`, `crm/tessera_sanitaria/api.py` | `fatture.invia` per trasmettere |
| `crm/api/activities.py` | La cronologia con i permessi |
| `crm/dashboard/features.py` | "website" richiede Builder |
| `crm/install.py`, `crm/patches/v1_0/create_level_roles.py` | I ruoli prima della sincronizzazione |
| `frontend/src/router.js`, `Layouts/AppSidebar.vue`, `Settings/Settings.vue`, `pages/Invoices.vue` | Rotte protette, menu e impostazioni per capacità |
| `crm/tests/test_invoice_access.py`, `crm/permissions/test_livelli.py` | I test |

## L'anagrafica fiscale sola

> **Completato** (29/09/2026). La terza PR della fase 0 del gestionale medico.
> Codice fiscale e indirizzo si scrivono una volta, nell'anagrafica fiscale della
> persona o dell'organizzazione: la fattura la legge, quella confermata la
> completa, e la pagina della persona la mostra a chi può vederla.

### Decisioni

| Decisione | Perché |
|---|---|
| `CRM Billing Profile` è un DocType della fatturazione, fuori da `CRM Lead` | Serve a tutti i settori, non solo alla clinica; e il marketing, che le persone le vede, il codice fiscale non ha bisogno di vederlo: un documento a parte ha permessi suoi |
| Uno per persona **e** uno per organizzazione (`party_type` + `party`, indice unico `unique_party`) | Il consulente fattura aziende quanto il fisioterapista fattura persone; lo stesso codice, un campo in più (la ragione sociale). Una trattativa o un contatto portano a uno dei due |
| La bozza prende solo i campi vuoti, l'indirizzo intero | Quello sulla fattura è quello confermato alla cassa; una via da un posto e una città da un altro è un indirizzo dove non abita nessuno. Il paese da solo (IT di predefinito) non è un indirizzo |
| La fattura confermata completa solo dove è vuoto, dentro un savepoint, senza mai sollevare | Un valore diverso è una decisione, non un buco; e una fattura che non si emette perché un'anagrafica non si aggiorna sarebbe difficile da spiegare |
| Non completa se la fattura è intestata a un altro: confronto delle parole dei nomi | Il genitore che paga per il figlio. Le parole e non i campi, perché i moduli web mettono tutto il nome nel primo campo |
| La ragione sociale va e torna solo per aziende ed enti | Scritta una volta nell'anagrafica di una persona finirebbe sulla ricevuta del medico |
| I formati che la fattura rifiuterebbe dopo si bloccano subito; le incoerenze con la persona si segnalano | Carattere di controllo, partita IVA di un formato noto, codice destinatario, CAP e provincia italiani. Nome, cognome e sesso contro il codice fiscale sbagliano coi cognomi doppi: avviso, non blocco |
| Data di nascita e sesso letti dal codice fiscale, in sola lettura | Mai scritti a mano, mai fuori passo; la clinica li leggerà da qui |
| L'anagrafica segue la persona: `org_hierarchy.visible_leads` per la lista, `has_permission` del record per il documento | La stessa regola della lista delle persone, condivisioni comprese |
| Una patch fa completare le anagrafiche alle fatture già emesse, dalla più recente | Il paziente fatturato il mese scorso non deve ridire il suo codice fiscale il giorno in cui l'anagrafica arriva |
| Nel pannello laterale uno slot `after` di `SidePanelLayout` | La sezione non è un campo della persona ma scorre con le altre; lo slot non cambia niente altrove |
| L'anagrafica se ne va con la persona o l'organizzazione (`on_trash`), e non compare fra i documenti da scollegare | Fa parte del record: lasciata indietro fermava la cancellazione, perché Frappe non cancella quello a cui qualcosa punta, e un diritto all'oblio che si ferma al codice fiscale non lo è |

### File

| File | Cosa cambia |
|---|---|
| `crm/invoicing/engine/anagrafica.py` | Le regole, pure: cosa prende la bozza, cosa restituisce la confermata, stessa persona, formati, dati dal codice |
| `crm/invoicing/anagrafica.py` | Di chi è l'anagrafica, i due versi, gli avvisi, `get_billing_profile` e `save_billing_profile` |
| `crm/invoicing/doctype/crm_billing_profile/` | Il DocType e il controller |
| `crm/invoicing/doctype/crm_invoice/crm_invoice.py` | `compila_da_controparte` legge, `on_submit` completa |
| `crm/invoicing/engine/codice_fiscale.py` | `formato_iva_noto` |
| `crm/invoicing/permessi.py`, `crm/permissions/org_hierarchy.py`, `crm/hooks.py` | L'anagrafica segue la persona |
| `crm/patches/v1_0/billing_details_from_past_invoices.py` | Il recupero dalle fatture già emesse |
| `crm/api/doc.py` | I documenti che se ne vanno col loro record non si propongono da scollegare |
| `frontend/src/components/BillingProfileSection.vue`, `SidePanelLayout.vue`, `pages/Lead.vue`, `MobileLead.vue`, `Organization.vue`, `MobileOrganization.vue` | La sezione "Billing details" |
| `crm/invoicing/tests/test_anagrafica.py`, `crm/tests/test_billing_profile.py` | I test: 24 senza sito, 20 sul sito |


## Il registro dei consensi

> **Completato** (29/09/2026). La quarta PR della fase 0 del gestionale medico.
> Chi ha accettato cosa, su quali parole, quando e come: un registro che cresce
> soltanto, con quello di `/prenota`, la sezione sulla pagina della persona e i
> testi nelle impostazioni.

### Decisioni

| Decisione | Perché |
|---|---|
| Nel CRM, in un modulo nuovo `crm/moduli` (Frappe module "Moduli"), non nella clinica | Il consenso al marketing serve a una palestra quanto a una clinica; i modelli e le firme della fase 2 andranno nello stesso modulo |
| I tipi si registrano in codice (`registro.registra_tipo`) e diventano record (`CRM Consent Type`) al migrate, senza mai sovrascrivere | Il codice chiede per chiave ("marketing"); il testo è del centro, controllato dal suo DPO, e una migrazione non deve rimettere quello di serie. Come le capacità, ogni modulo porta i suoi |
| Due nature: consenso (si revoca) e presa visione (l'informativa, non si revoca) | L'informativa è informazione, non un consenso: non c'è niente da ritirare |
| Una risposta non si modifica: la revoca si timbra sulla stessa riga, un nuovo sì è una riga nuova | Una prova del consenso (art. 7(1) GDPR) che si può modificare non prova niente. Lo stato è l'ultima risposta |
| Ogni risposta tiene la sua copia del testo e la versione | Riscrivere il testo non riscrive quello che qualcuno ha accettato |
| La spunta dell'informativa di `/prenota` si registra con le parole della pagina, nella lingua del visitatore, più l'indirizzo dell'informativa | La pagina è bilingue e il testo del tipo no: si tiene quello che la persona ha letto davvero. Da una pagina in cache che non le manda, il testo del tipo |
| Il marketing su `/prenota` solo se il centro lo accende, facoltativo e mai spuntato | Un consenso si dà, non si trova già dato |
| Un "no" di chi aveva detto sì è una revoca | Non due righe che si contraddicono |
| Il marketing si specchia su `CRM Lead.marketing_consent` | Liste e automazioni leggono i campi della persona: è il mattone dei richiami col consenso della fase 1 |
| Registrare e revocare a mano chiede `consensi.raccogli`, anche al commerciale | Chi sente "non scrivetemi più" lo deve poter scrivere: revocare è facile quanto dare (art. 7(3)) |
| Le risposte seguono la persona e se ne vanno con lei | La stessa regola dell'anagrafica fiscale: fanno parte della persona |

### File

| File | Cosa cambia |
|---|---|
| `crm/moduli/registro.py` | Le regole, pure: tipi, nature, canali, stato attuale |
| `crm/moduli/__init__.py` | I due tipi del CRM: informativa e marketing |
| `crm/moduli/consensi.py` | Registrare, revocare, lo stato, i permessi, le chiamate del pannello e delle impostazioni |
| `crm/moduli/doctype/crm_consent_type/`, `crm_consent/` | I DocType |
| `crm/api/service_booking.py`, `crm/www/prenota.html` | Le spunte di `/prenota` nel registro, la casella del marketing |
| `crm/fcrm/doctype/crm_scheduling_settings/`, `crm/api/appointments.py`, `Settings/Booking/BookingPageSettings.vue` | "Ask for marketing consent" |
| `crm/fcrm/doctype/crm_lead/` | `marketing_consent` |
| `crm/permissions/catalogo.py` | `consensi.vedi`, `consensi.raccogli`, `consensi.configura` |
| `crm/hooks.py`, `crm/install.py`, `crm/registrazione.py`, `crm/modules.txt`, `crm/api/doc.py` | Il cablaggio |
| `frontend/src/components/ConsentsSection.vue`, `Settings/ConsentsSettings.vue` | La sezione sulla persona, la pagina dei testi |
| `crm/moduli/tests/test_registro.py`, `crm/tests/test_consents.py` | I test: 9 senza sito, 16 sul sito |

## Lo scheletro della clinica

> **Completato** (29/09/2026). La quinta PR della fase 0 del gestionale medico.
> Un modulo `crm/clinica` acceso dal piano, la scheda paziente che nasce dalla
> prima regola che scatta, il recupero sui dati che ci sono già, il livello
> Direzione sanitaria, e un confine controllato da un test.

### Decisioni

| Decisione | Perché |
|---|---|
| L'interruttore "centro medico" è il modulo "clinica" del piano, spento di serie | Una chiave sola per tutto: capacità, regole, consensi e job della clinica si accendono con il piano, e lo accende l'agenzia |
| `clinica_accesa()` registra i moduli prima di chiedere al piano | Il registro conta come acceso un modulo che nessuno ha dichiarato: un worker che non avesse importato gli hook avrebbe acceso la clinica ovunque |
| Una porta sola, `assicura_paziente`, per tutte le regole | La prima che scatta scrive la scheda, le altre non fanno niente; due richieste insieme si fermano sull'indice unico, non su una seconda scheda |
| Regole di oggi: appuntamento svolto, fattura sanitaria, importazione, a mano | Il primo dato clinico arriva con la sezione Clinica (PR 6), l'accettazione con la fase 1 |
| Chi non si è presentato resta contatto, anche su un appuntamento completato | Meglio un paziente in meno che un no-show contato come paziente |
| Un servizio fatturato come non sanitario non fa pazienti | Come la sua fattura: un corso di yoga in un centro misto non è una visita |
| Il recupero segue il tempo, non l'ordine della tabella | "Paziente dal" deve essere il primo fatto: una fattura di gennaio e un appuntamento di marzo fanno un paziente da gennaio. A parità decide la tabella |
| Il recupero parte da solo, una volta, quando il piano accende la clinica | Nessuno deve segnare a mano i pazienti di prima; ritrovarli di nuovo è un'azione del Manager (`find_patients`) |
| Niente campo "paziente" sulla persona | Chi è paziente è un dato sanitario: sulla persona lo leggerebbero anche marketing e commerciale. La scheda è un documento a sé, con i suoi permessi |
| I consensi della clinica (dossier, referti online) chiedono `pazienti.vedi` per essere visti, anche in lista | Una risposta sul dossier dice già che la persona è paziente |
| Una regola che fallisce non ferma l'appuntamento né la fattura | Si scrive nel log; sarebbe la cosa sbagliata al contrario |
| La persona che è paziente non si cancella | La cartella va conservata anche se la persona chiede l'oblio; lo si dice a parole |
| Il ruolo Medical Director si crea prima della sincronizzazione (la patch dei ruoli dei livelli, rilanciata) | La scheda paziente lo nomina nei permessi |

### File

| File | Cosa cambia |
|---|---|
| `crm/clinica/__init__.py` | `registra()`: modulo del piano, ruolo e livello Direzione sanitaria, capacità, consensi della clinica |
| `crm/clinica/regole.py` | Le regole, pure: presente o no, la prima nel tempo |
| `crm/clinica/paziente.py` | La porta unica, il recupero, le chiamate della pagina |
| `crm/clinica/eventi.py` | Appuntamento, fattura, piano, cancellazione |
| `crm/clinica/doctype/clinic_patient/` | La scheda paziente |
| `crm/moduli/registro.py`, `consensi.py`, `crm_consent_type` | Il modulo del piano e la capacità di un tipo di consenso |
| `crm/hooks.py`, `crm/registrazione.py`, `crm/modules.txt`, `crm/patches.txt` | Il cablaggio |
| `frontend/src/components/PatientSection.vue`, `pages/Lead.vue`, `MobileLead.vue` | La sezione "Patient" sulla persona |
| `crm/clinica/tests/` | Confine e regole senza sito (13), la scheda sul sito (16) |

## La sezione Clinica sulla persona

> **Completato** (29/09/2026). La sesta PR della fase 0 del gestionale medico.
> La scheda "Clinic" con la visita semplice (testo e allegati privati), la regola
> 1 del paziente, chi legge cosa, il lucchetto nella cronologia e il registro
> degli accessi tenuto due anni.

### Decisioni

| Decisione | Perché |
|---|---|
| `Clinic Record` è submittable: bozza dell'autore, firmata e poi solo aggiunte | Una cartella si integra, non si riscrive; "annulla" non c'è, c'è "Add to it" |
| Chi legge: l'autore, la direzione, gli altri operatori solo col consenso al dossier; "Only me" resta dell'autore | Le linee guida del Garante sul dossier (4/6/2015): senza consenso ognuno vede solo quello che ha prodotto |
| Un solo "Given" per consenso nel registro, ed è quello attuale | La condizione della lista chiede il dossier direttamente alla tabella: un secondo sì non scrive niente, un no dopo un sì è una revoca |
| Il permesso "write" guarda lo stato salvato | Frappe controlla "write" anche mentre firma, con lo stato già a firmato in memoria: la firma in volo è ancora la bozza dell'autore |
| Nessun permesso a System Manager sulla cartella | L'agenzia legge i dati clinici solo con un accesso a tempo, che verrà |
| Ogni lettura dalla SPA passa da `get_record`, che scrive un View Log | Frappe lo scrive solo dal form del Desk |
| Il View Log almeno 730 giorni, al migrate e a ogni salvataggio di Log Settings | Il Garante chiede 24 mesi; il default di Frappe per chi lo aggiunge è 180 giorni |
| Allegati privati, o rifiutati | Il file è già scritto quando l'hook gira: meglio fermarlo che rietichettarlo |
| La visita nel composer è testo semplice | L'editor ricco carica le immagini incollate come pubbliche: per un dato sanitario no |
| La regola 1 sta nella classe base `DocumentoClinico`, e un test controlla che tutti i DocType clinici ne ereditino | Un DocType clinico nuovo è coperto senza ricordarsene |
| La cronologia si apre con l'hook `crm_timeline_gatherers` | Il CRM non importa la clinica; un hook si legge dalla cache senza gli effetti dell'import |
| Il manager apre la scheda per il solo registro degli accessi | Doc 30: vede chi e quando, non cosa; per lui non si registra nessuna lettura |
| La direzione sanitaria riceve dalla clinica le capacità del CRM della sua colonna | Il livello nasce con la clinica; senza, la pagina della persona era vuota |
| WhatsApp e SMS non compaiono a chi non può conversare | Prima le chiamate partivano e tornavano 403; chi lavora dal Desk, fuori dai livelli, resta com'era |

### File

| File | Cosa cambia |
|---|---|
| `crm/clinica/doctype/clinic_record/`, `crm/clinica/base.py` | La visita e la regola 1 |
| `crm/clinica/cartella.py` | Permessi, chiamate della scheda, registro degli accessi, nodo della cronologia, allegati privati, Log Settings |
| `crm/clinica/__init__.py` | Capacità della cartella, le capacità del CRM alla direzione |
| `crm/moduli/consensi.py` | Un solo "Given" per consenso |
| `crm/api/activities.py`, `crm/hooks.py` | `crm_timeline_gatherers`; i permessi e gli hook della cartella |
| `crm/api/whatsapp.py`, `crm/api/sms.py` | `may_converse` |
| `frontend/src/components/Clinic/ClinicArea.vue`, `Activities/*`, `utils/conversation.js`, `pages/Lead.vue`, `MobileLead.vue` | La scheda Clinic e il lucchetto |
| `crm/clinica/tests/test_cartella.py`, `test_confine.py`, `crm/tests/test_consents.py` | I test |

## Le persone collegate

> **Completato** (29/09/2026). L'ultima PR della fase 0 del gestionale medico.
> Il paziente, chi paga e chi prenota possono essere tre persone: un legame per
> coppia, la prenotazione per un altro su `/prenota`, la fattura a chi paga, il
> consenso dato da un genitore, e il contatto che resta di chi lo possiede.

### Decisioni

| Decisione | Perché |
|---|---|
| `CRM Related Person` nel CRM (`crm/persone`), non nella clinica | Una palestra ha bambini prenotati dai genitori quanto una clinica; il campo "tutore" della scheda paziente è diventato un legame, con una patch |
| Una riga per coppia, scritta dal lato di chi è seguito: `related_person` è `relation` per `person`, e paga, prenota o decide per lui | Due righe per la stessa coppia prima o poi si contraddicono; dall'altro lato la relazione si legge girata (`inversa`) |
| Pagare, prenotare e decidere sono tre bandierine, in un verso solo | Il padre separato che prenota il sabato non è quello che paga; il figlio che segue la madre anziana agisce nell'altro verso, e la riga si scrive dal lato di lei |
| Il contatto è di chi lo possiede: il figlio prenotato dalla madre non prende la sua email né il suo telefono | Restano suoi: una chiamata da quel numero è sua, e la prossima prenotazione di lei non va al figlio. I messaggi le arrivano dalla riga dell'appuntamento, che dice "Booked by" |
| Il contatto trova il titolare, il nome trova la persona: il titolare, uno dei suoi collegati (e dei loro), o una persona nuova collegata a lui | Era la decisione rimasta alla fase 0 (`find_person` riconosce da email e telefono, e in famiglia li condividono) |
| I nomi si confrontano per parole, senza somiglianze né iniziali; due candidati possibili sono nessuno | "Luca" e "Lucia" sono fratello e sorella, "M. Rossi" può essere la madre o il figlio: un doppione si unisce in un minuto, una visita sulla persona sbagliata si scopre tardi |
| Un titolare con un'email o un numero per nome è il titolare | Non dice chi è: la prenotazione con un nome vero sul suo contatto è sua |
| `/prenota` chiede "per me o per un'altra persona", con il nome e cosa si è per lei | La scelta esplicita batte l'indovinare; l'indovinare resta la rete per le pagine e le piattaforme che non la chiedono |
| L'informativa di `/prenota` si registra due volte: per chi prenota e per chi viene, "dato da" chi prenota | Chi prenota l'ha letta, per sé e per l'altro; il marketing è di chi prenota, che riceve i messaggi |
| I limiti per cliente contano chi viene; il contatto conta solo le righe che non nominano nessuno | La madre che prenota per due figli prenota tre persone, non una tre volte |
| La fattura va a chi paga quando paga uno solo, con "Prestazione resa a …" e il codice fiscale del paziente nella causale | Il documento va a chi paga; chi lo riceve, e chi detrae, deve sapere di chi era la visita |
| Una fattura che nomina già il cliente (nome o codice fiscale) resta sua | La cassa che la intesta al figlio non deve trovarci l'indirizzo del padre |
| La fattura confermata completa l'anagrafica di chi nomina, fra il cliente e chi paga | Prima non completava niente se era intestata a un altro; ora sa chi è l'altro |
| Il consenso al banco "dato da" solo chi è collegato alla persona | Un estraneo non risponde per nessuno |
| L'età viene dal codice fiscale; il minorenne senza chi decide è segnalato nella sezione Paziente | Mai scritta a mano, mai fuori passo |
| Un legame lo vede chi vede una delle due persone; lo scrive chi ha `persone.scrivi` e le vede entrambe | È delle due persone; legare chi non si vede sarebbe un modo di vederlo |
| Chi crea una persona dal legame ne è il proprietario, come nel modulo "nuova persona" | Altrimenti la segreteria creava una persona che poi non vedeva: l'ambito del doc 30 (PR 2) la allargherà |

### File

| File | Cosa cambia |
|---|---|
| `crm/persone/legami.py` | Le regole, pure: relazioni e inverse, versi, nomi, chi è di una prenotazione, età |
| `crm/persone/collegate.py` | I legami sul sito: famiglia, chi paga, chi decide, `trova_per_nome`, `persona_per_conto`, i permessi, le chiamate della pagina, `get_contact_for` |
| `crm/fcrm/doctype/crm_related_person/` | Il DocType, una riga per coppia (indice unico) |
| `crm/api/booking.py` | `find_or_create_person` col nome |
| `crm/api/service_booking.py`, `crm/www/prenota.html` | "Per me o per un'altra persona", i limiti per chi viene, i consensi, l'email a chi ha prenotato |
| `crm/fcrm/doctype/crm_appointment_participant/`, `crm/api/appointments.py` | "Booked by", che sopravvive alle modifiche della segreteria |
| `crm/invoicing/anagrafica.py`, `crm_invoice.py`, `crm/invoicing/api.py` | La fattura a chi paga, la causale, il completamento di chi è nominato |
| `crm/invoicing/engine/anagrafica.py` | `stessa_persona` usa `legami.stesso_nome`: una regola sola per i nomi |
| `crm/moduli/consensi.py`, `crm_consent.json` | "Dato da" |
| `crm/clinica/paziente.py`, `clinic_patient.json`, `crm/patches/v1_0/guardians_become_linked_people.py` | Chi decide per il paziente, il minorenne; il tutore diventa un legame |
| `frontend/src/components/RelatedPeopleSection.vue`, `PatientSection.vue`, `ConsentsSection.vue`, `Calendar/AppointmentPanel.vue`, `pages/Lead.vue`, `MobileLead.vue` | La sezione "Linked people", chi decide, chi ha risposto, chi ha prenotato |
| `crm/persone/tests/test_legami.py`, `crm/tests/test_related_people.py` | I test: 23 senza sito, 28 sul sito |

## L'ambito segue il livello, e quello che è di una persona la segue

> **Completato** (29/09/2026). La PR 2 del doc 30. La segreteria vede tutto il
> centro, il commerciale il suo team, l'operatore le persone che ha in cura;
> appuntamenti, messaggi e tracciamento seguono la persona; quello che lo schermo
> tiene al Manager, il server lo chiede alla capacità.

### Decisioni

| Decisione | Perché |
|---|---|
| L'ambito di persone e trattative lo dà la capacità (`persone.vedi`, `trattative.vedi`), non il ruolo | Ogni livello ha Sales User: il ruolo non distingue la segreteria dal commerciale. La segreteria prima non vedeva nemmeno le persone che creava |
| "Suoi" per l'operatore vuol dire assegnati e **in cura**: un appuntamento con lui, e quello che un modulo aggiunge con `crm_people_in_care` (la clinica: i pazienti per cui ha scritto in cartella) | Il doc 30 lo chiede; l'hook tiene il confine, il CRM non importa la clinica |
| Senza la capacità, niente: nemmeno le proprie | Un livello che non vede le trattative (la Direzione sanitaria) non ne vede nessuna, e non per caso |
| Chi è fuori dai livelli tiene la regola dei ruoli | Chi lavora dal Desk con i ruoli della fatturazione non deve accorgersi di niente |
| Un posto nella gerarchia restringe: chi sta nell'albero vede il suo team, qualunque sia il livello | Il doc 30: il responsabile è un posto nella gerarchia, non un livello. Sui siti con la gerarchia i Sales Manager nell'albero (i responsabili) sono diventati Manager nel passaggio: allargarli a tutto il centro avrebbe cambiato quello che vedono senza che nessuno lo chiedesse |
| L'ambito si calcola una volta per richiesta, e `dimentica_cache` lo dimentica | Una lista lo chiede per ogni sottoquery; i test cambiano livello a metà richiesta |
| Un'assegnazione chiusa apre il record per 90 giorni | Il lavoro è finito, il seguito no; per sempre sarebbe una chiave che nessuno ricorda di aver dato |
| Appuntamenti: il centro per chi ha `agenda.vedi` sul centro, per l'operatore quelli che lavora o prenota, per il commerciale quelli delle sue persone | "Vedere l'agenda": ✓, la sua, libero e occupato |
| Il resto dell'agenda arriva come **tempo occupato**: quando, chi lo lavora, quale sala; mai chi viene, perché, o il nome dell'appuntamento | Il commerciale prenota per le sue persone nella giornata di tutti; e un servizio ("visita ginecologica") è già un dato sanitario |
| L'operatore prenota solo nella sua agenda; eliminare chiede `agenda.elimina` | "Prenotare: la sua"; "Eliminare un appuntamento: Man" |
| WhatsApp e SMS: a chi conversa, sulle persone che vede; quelli di nessuno a tutti quelli che conversano | Come le chiamate; la Direzione sanitaria non conversa |
| Tracciamento: sulle persone che si vedono; il traffico anonimo a chi gestisce il tracciamento | Il percorso di una persona sta sulla sua pagina; l'anonimo è materia del marketing |
| Le scritture dei documenti del Manager passano da un hook `has_permission` con la capacità, non dai DocPerm | I DocPerm non sanno dei livelli; l'hook lascia intatti i ruoli di chi è fuori dai livelli, e un test controlla che ogni documento dell'elenco abbia l'hook |
| `create_deal` inserisce come l'utente e controlla persona e organizzazione | Con `ignore_permissions` non valevano i permessi per campo; e una trattativa si poteva attaccare a chiunque |

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/org_hierarchy.py` | `_scope` per livello e per tipo, `NIENTE`, in cura, assegnazioni chiuse, `sees_everyone`, `visible_owners` per livello |
| `crm/permissions/seguono.py` | Appuntamenti, WhatsApp, SMS, tracciamento, vecchie prenotazioni |
| `crm/permissions/documenti.py` | Le scritture per capacità |
| `crm/permissions/livelli.py` | `dimentica_cache` dimentica anche gli ambiti |
| `crm/clinica/cartella.py` | `persone_in_cura` |
| `crm/api/appointments.py` | `get_calendar` dà `busy` |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `create_deal` |
| `crm/hooks.py` | Gli hook |
| `frontend/src/pages/Calendar.vue`, `components/Calendar/ResourceScheduler.vue` | Il tempo occupato, nelle due viste |
| `crm/tests/test_ambiti.py`, `crm/tests/test_billing_profile.py` | I test; la segreteria ora vede i dati fiscali di tutto il centro |

## Lo schermo chiede la capacità, e le impostazioni si dividono

> **Completato** (29/09/2026). La PR 3 del doc 30. Menu, rotte, pulsanti e pagine
> delle impostazioni chiedono la capacità; quello che è dell'agenzia su una pagina
> (chiavi, indirizzi, segreti, lo script del sito) sta su un livello di permesso a
> parte; ERPNext e i Predefiniti passano all'agenzia.

### Decisioni

| Decisione | Perché |
|---|---|
| `isManager()`, `isAdmin()` e `isSalesUser()` escono dallo store | Il ruolo non distingue più i livelli (tutti hanno Sales User); tenerle invitava a riusarle |
| Le rotte dichiarano `meta.richiede`, e senza la capacità si torna alla prima pagina che il livello apre | Una pagina tolta dal menu si apriva ancora dall'indirizzo; la home non deve mandare su una vista predefinita che il livello non apre |
| Ogni pagina delle impostazioni ha la sua `condition`, e un gruppo compare se una sua pagina compare | Prima il gruppo intero era del Manager: la Segreteria non trovava turni e sale, che sono suoi |
| Le sale solo con `agenda.turni` su tutto il centro | L'Operatore ha i suoi turni; le sale sono di tutti e non le poteva salvare |
| La parte dell'agenzia su **permlevel 1**, solo System Manager | È il modo di Frappe: il Manager non la riceve e un suo salvataggio la lascia com'era, da qualunque strada passi. Per i singoli `get_value` guarda il documento e non il campo: i segreti restano anche Password |
| Collegare e scollegare Twilio ed Exotel è dell'agenzia; registrare le chiamate e gli ID chiamante del centro | Senza credenziali non si collega niente; se registrare è una decisione del centro, con il suo avviso |
| La trascrizione la accende il centro, il servizio lo configura l'agenzia | Come farà l'assistente (doc 30): il Manager lo accende, fornitore e regione sono dell'agenzia. Se manca il servizio, il messaggio lo dice |
| L'indirizzo del webhook delle piattaforme di prenotazione resta al Manager | È quello che si incolla nella piattaforma: senza, il Manager non finisce di collegarla. Il doc 30 lo dava all'agenzia; il test `test_a_manager_still_gets_the_urls_to_paste_into_the_platform` lo voleva già così |
| La Gerarchia la costruisce il Manager | Il doc 30 ("Man"); prima la modificava solo System Manager. I nodi mostrano i livelli, non Sales Manager e Sales User |
| La lista delle chiamate non si rompe per un utente cancellato | Una chiamata demo con un destinatario che non c'è più mandava in errore tutto il registro |

### File

| File | Cosa cambia |
|---|---|
| `frontend/src/stores/users.js` | `puoUno()`, `isAgency()`; via le funzioni dei ruoli |
| `frontend/src/router.js` | `meta.richiede` sulle rotte, la guardia, la prima pagina del livello |
| `frontend/src/components/Settings/Settings.vue`, `Layouts/AppSidebar.vue` e una ventina di componenti | Menu, impostazioni e pulsanti per capacità |
| `frontend/src/components/Settings/DashboardSettings.vue`, `Telephony/TwilioSettings.vue`, `ExotelSettings.vue`, `TranscriptionSettings.vue`, `TrackingSettings.vue`, `Invoicing/ProviderConnection.vue` | La parte dell'agenzia con `tecnico.integrazioni` |
| `frontend/src/components/Settings/Hierarchy/Hierarchy.vue` | I livelli al posto dei ruoli |
| `crm/fcrm/doctype/fcrm_settings`, `crm_twilio_settings`, `crm_exotel_settings`, `crm_transcription_settings`, `crm_tracking_settings` (JSON) | I campi dell'agenzia su permlevel 1 |
| `crm/fcrm/doctype/crm_twilio_settings/`, `crm_exotel_settings/`, `crm_transcription_settings/`, `erpnext_crm_settings/` | I metodi per capacità; collegare un provider è dell'agenzia |
| `crm/fcrm/doctype/crm_sales_hierarchy/crm_sales_hierarchy.json` | Il Sales Manager scrive la gerarchia |
| `crm/permissions/documenti.py`, `crm/hooks.py` | Gerarchia, SLA, ID chiamante ed ERPNext per capacità |
| `crm/api/tracking.py`, `crm/invoicing/api.py` | Lo script del sito e il segreto del webhook all'agenzia |
| `crm/fcrm/doctype/crm_call_log/crm_call_log.py` | Un utente cancellato non rompe la lista |
| `crm/tests/test_impostazioni_divise.py`, `test_settings_methods.py`, `test_integration_secrets.py` | I test |

## Le pagine del Manager sui documenti del core

> **Completato** (29/09/2026). La PR 3b del doc 30. Modelli email, regole di
> assegnazione, SLA, importazione e account email funzionano per il Manager, non
> solo per System Manager; le condizioni in Python restano all'agenzia.

### Decisioni

| Decisione | Perché |
|---|---|
| Un ruolo porta la regola sul documento del core, la capacità la restringe (`DEL_CORE` + `SCRITTURA`) | I DocPerm non sanno dei livelli, e un hook `has_permission` può solo togliere. Lo stesso schema di `crm.api.whatsapp.add_roles` e della PR 2 |
| Sales User per i modelli email, Sales Manager per regole e importazioni | I modelli li scriveranno anche Man e Mkt (PR 4): ogni livello ha Sales User, e la capacità decide. Regole e importazioni sono del Manager, e leggerle non serve agli altri |
| La regola si mette una volta, a ogni migrazione, e non si tocca se c'è già | Chi l'ha cambiata a mano dal Desk ha deciso lui |
| Il permesso "import" sui doctype del CRM nel loro JSON, non con i permessi personalizzati | Un permesso personalizzato copia tutte le regole del doctype e le congela: le modifiche future del JSON non arriverebbero più ai siti |
| Gli account email con API del CRM, non con i permessi | Il documento tiene password e server: l'API mostra solo quello che la pagina mostra, cambia solo quello che la pagina cambia, e mai un account con server suoi |
| Le condizioni in Python le riscrive il server dalle condizioni guidate, in `before_validate` | Prima che qualcosa le valuti: lo SLA le prova con `safe_eval` nel suo `validate`. Il convertitore è una copia di quello del browser, più severo: campi del documento, operatori dello schermo, valori sempre fra virgolette, solo `and` e `or` |
| Una condizione scritta dall'agenzia dal Desk resta, e il Manager può spegnere la regola | Il server riscrive solo quello che cambia; Python senza condizioni guidate dietro lo può cambiare solo l'agenzia |
| In Frappe 16 `has_value_changed` dice True per ogni campo di un documento nuovo | Per un documento nuovo conta se il campo è dato (`_cambiato`) |
| Il segreto del webhook della fatturazione chiede `fatture.segreti` | La fatturazione aveva già la sua capacità tecnica: ognuno chiede le sue |

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/documenti.py`, `crm/hooks.py`, `crm/install.py` | `DEL_CORE`, `concedi_documenti_del_core`, `scrivi_condizioni` e gli hook |
| `crm/permissions/condizioni.py`, `test_condizioni.py` | Le condizioni guidate in Python, senza sito |
| `crm/permissions/catalogo.py` | `tecnico.codice` |
| `crm/fcrm/doctype/crm_lead`, `crm_deal`, `crm_organization`, `crm_task`, `crm_call_log` (JSON) | Il permesso "import" |
| `crm/api/settings.py` | Gli account email per capacità |
| `frontend/src/components/Settings/EmailAccountList.vue`, `EmailEdit.vue`, `emailConfig.js`, `Profile/UserEmailSettings.vue`, `Booking/BookingPlatforms.vue` | Le pagine sulle API del CRM |
| `crm/tests/test_documenti_del_core.py` | I test, compresa un'importazione vera |

## I livelli facoltativi: Marketing, Amministrazione, Sola lettura

> **Completato** (29/09/2026). La PR 4 del doc 30. Il Marketing vede le persone con
> email e telefoni mascherati dalla maschera di Frappe; l'Amministrazione fa la
> fatturazione; la Sola lettura si aggiunge a un livello e toglie ogni scrittura.
> Scrivere persone e trattative, leggere chiamate, note ed email chiede la capacità.

### Decisioni

| Decisione | Perché |
|---|---|
| La maschera di Frappe (`mask` sul campo, permesso `mask` al ruolo) e non una del CRM | Copre scheda, liste, esportazioni e salvataggi da qualunque strada; una maschera nelle API del CRM lasciava aperte `frappe.client` e `reportview` |
| Il ruolo che vede in chiaro (`Contact Details`) lo portano tutti i livelli tranne il Marketing, dal registro | Ogni livello ha Sales User: il permesso di vedere in chiaro non poteva stare lì. Un livello nuovo lo porta da sé (`Livello.recapiti`) |
| Niente regola per Guest | Il ruolo Guest ce l'hanno tutti gli utenti collegati: toglieva la maschera anche al Marketing. `frappe.db.get_value` e `get_all` non mascherano, e gli invii leggono con `stored_value` |
| Chi è fuori dai livelli riceve `Contact Details` (patch e hook su User) | Conta come il livello che i suoi ruoli implicano, e quei livelli vedono i recapiti: nessuno perde quello che vedeva |
| La rubrica (Contact) negata a chi vede mascherato, non mascherata | La maschera su un doctype del core varrebbe per tutto il sito, anche per gli utenti delle altre app |
| Scrivere ed eliminare persone e trattative chiede la capacità | Vedere bastava, con Sales User: la Direzione sanitaria poteva modificare ed eliminare persone dall'API |
| Chiamate e note chiedono la loro capacità oltre alla persona; le email `conversazioni.usa` | Il doc 30: si vede quello che è della persona se si vede la persona *e* se il livello ha la capacità per quel dato |
| Sola lettura: un hook `has_permission` su ogni documento, con le notifiche e il profilo propri esclusi | Il registro toglie le capacità che scrivono, ma i ruoli del livello a cui si aggiunge scrivono ancora con l'API |
| Il Marketing ha un ruolo suo sui documenti del marketing | Senza Sales Manager, che gli avrebbe dato anche il resto |
| `conversazioni.vedi` e `note.vedi` accanto a `conversazioni.usa` e `note.scrivi` | La Sola lettura perde le capacità che scrivono: se leggere chiedeva quelle, non leggeva più le conversazioni e le note del suo livello |
| Rispondere chiede di conversare e di vedere, non di modificare il record | L'Operatore non modifica le trattative, e ci risponde |
| `crm.api.doc.get_doc_permissions` al posto di quello di Frappe | Frappe chiede ai controller solo la lettura: la scheda offriva campi e pulsanti che il server rifiuta |
| L'assegnazione passa da `override_whitelisted_methods` | Frappe la concede a chi legge; le regole di assegnazione chiamano le funzioni direttamente e non passano da lì |
| Un controllo al salvataggio, oltre agli hook `has_permission` | Il CRM condivide persone e trattative con il proprietario in scrittura, e Frappe concede quello che è condiviso senza chiedere ai controller |
| `dashboard.centro` per vedere, `dashboard.condivise` per condividere | Erano una capacità sola, che scrive: la Sola lettura perdeva la dashboard, e un Manager in sola lettura i numeri del centro |
| La pagina delle fatture con `fatture.vedi` e ambito centro | La Sola lettura legge il registro; l'Operatore, che vede solo le sue, le trova sulla persona come prima |

### File

| File | Cosa cambia |
|---|---|
| `crm/permissions/livelli.py`, `catalogo.py`, `crm/invoicing/capacita.py` | I livelli, le colonne Mkt e Amm, `RUOLO_RECAPITI` |
| `crm/permissions/org_hierarchy.py`, `seguono.py`, `documenti.py`, `utenti.py`, `crm/hooks.py` | Scritture per capacità (anche al salvataggio), chiamate e note, email, rubrica, Sola lettura, assegnazioni, `Contact Details` fuori dai livelli |
| `crm/api/doc.py`, `crm/integrations/api.py` | I permessi di un documento come li giudica il server; i pulsanti di chiamata a chi chiama |
| `crm/dashboard/context.py`, `store.py`, `crm/api/dashboard.py` | Vedere i numeri, condividere, fare dashboard proprie: tre capacità |
| `frontend/src/router.js`, `utils/dashboard.js`, `components/Layouts/AppSidebar.vue`, `pages/Dashboard.vue`, `pages/Invoices.vue` | Rotte con l'ambito, la dashboard a chi legge i numeri, l'onboarding e il registro delle fatture per capacità |
| `crm/fcrm/doctype/crm_lead`, `crm_deal` (JSON) | La maschera su email e telefoni, chi la toglie |
| I JSON dei doctype del marketing (automazioni, social, tracciamento, Meta, sito) | Il ruolo Marketing |
| `crm/api/activities.py`, `crm/api/whatsapp.py`, `crm/utils/__init__.py` | La cronologia per livello; il numero vero per gli invii |
| `crm/patches/v1_0/contact_details_for_users_outside_levels.py` | Il ruolo a chi è fuori dai livelli |
| `frontend/src/pages/Lead.vue`, `Deal.vue`, `MobileLead.vue`, `MobileDeal.vue`, `Notes.vue` | Schede, pulsanti e testata per capacità e per `canWrite` |
| `frontend/src/data/document.js`, `stores/users.js`, `components/SidePanelLayout.vue`, `AssignTo.vue`, `EnrichFromWebsite.vue`, `Activities/*` | `canWrite` dal server, `solaLettura()`, il pannello in sola lettura, il menu "Nuovo" per capacità; `Settings/LevelPicker.vue` mette la Sola lettura a parte |
| `crm/permissions/test_livelli.py`, `crm/tests/test_livelli_facoltativi.py` | I test |

## Fase 1, la prima cucitura: diventare paziente chiude il deal

> **Completato** (29/09/2026). Le due pipeline del centro medico, la prenotazione che
> sposta la richiesta, il paziente che la vince, l'evento "Became Patient" e i widget
> dei nuovi pazienti. `docs/gestionale-medico/README.md`, "La prima cucitura".

### Decisioni

| Decisione | Perché |
|---|---|
| Le pipeline nascono all'accensione della clinica, e `Clinic Settings` dice quali sono | Il Manager può indicare pipeline sue; il nome da solo non basta a riconoscerle |
| I nomi degli stadi nella lingua del sito, come i testi dei consensi | Sono dati che la board mostra, non stringhe dell'interfaccia |
| Vince solo chi diventa paziente adesso (`assicura_paziente(annuncia=...)`) | Il recupero dei pazienti di prima avrebbe chiuso deal vecchi e fatto partire automazioni per centinaia di persone |
| "Became Patient" registrato dalla clinica (`registra_evento`), offerto solo con la clinica accesa | Il CRM non importa la clinica; le opzioni del Select lo accettano ovunque, ma il costruttore lo offre solo dove ha senso |
| Il costo di un nuovo paziente conta chi è arrivato dagli annunci (`facebook_ad_id`) | La spesa divisa per tutti i pazienti, anche quelli arrivati dal passaparola, lo farebbe sembrare più basso |
| La prenotazione sposta solo le richieste più indietro | Una richiesta che qualcuno ha già portato avanti a mano non torna indietro |

## Fase 1, la seconda cucitura: la giornata della segreteria

> **Completato** (29/09/2026). L'accettazione con la sala d'attesa, l'appuntamento che
> si chiude da solo, il "sono venuti?" di fine giornata e la pagina Oggi.
> `docs/gestionale-medico/README.md`, "La seconda cucitura".

### Decisioni

| Decisione | Perché |
|---|---|
| "Arrived" è uno stato del partecipante, con l'ora | La sala d'attesa è di una persona, non dell'appuntamento: in un gruppo arrivano in momenti diversi |
| L'appuntamento si chiude dai suoi partecipanti (`close_from_attendance`) | La visita, l'accettazione e la fattura chiudono l'appuntamento senza che qualcuno se ne ricordi |
| Una fattura fatta prima dell'appuntamento non dice che la persona è venuta | Si fattura anche in anticipo: l'esito sarebbe falso |
| Fine giornata ogni ora, dopo l'ultimo appuntamento, una volta al giorno | Gli orari dei centri cambiano: un'ora fissa arriverebbe durante le visite o troppo tardi |
| Chi è in sala d'attesa e nessuno ha segnato conta come venuto | È arrivato: lasciarlo "in attesa" per sempre non dice il vero a nessuno |
| La giornata è quella del server | Un browser in un altro fuso mostrerebbe gli arrivi di domani |
| La notifica apre la pagina Oggi (tipo "Agenda") | Le notifiche sapevano aprire solo persone e trattative |

## Fase 1, la terza cucitura: il richiamo e la dashboard del centro

> **Completato** (29/09/2026). Ultima visita e servizio sulla persona, automazioni con
> il consenso al marketing, la ricetta del richiamo, la dashboard "Medical centre".
> Con questa la fase 1 è completa. `docs/gestionale-medico/README.md`, "La terza cucitura".

### Decisioni

| Decisione | Perché |
|---|---|
| `last_visit` e `last_service` sulla persona, tenuti dall'agenda | I richiami scelgono su dati amministrativi, mai sulla cartella; un campo si filtra, si mostra e un Date Reminder lo legge senza codice nuovo |
| Il consenso è un'opzione dell'automazione, non di ogni passo | È l'automazione che fa marketing; un passo dimenticato senza il controllo sarebbe l'invio che non doveva partire |
| L'iscrizione saltata è "Skipped", una volta, e non conta come passaggio | Si vede perché qualcuno non ha ricevuto niente; e chi dice sì più tardi entra |
| Il consenso si ricontrolla prima di ogni invio | Una revoca arriva mentre l'automazione aspetta: il messaggio dopo non deve partire |
| I modelli di dashboard si registrano, con `requires` | La clinica aggiunge il suo senza che il CRM la nomini, e nasce solo dove la clinica è accesa |
| Il piano, nel suo `on_update`, toglie dalla cache sé stesso, i livelli e le feature della dashboard | Frappe esegue `on_update` prima di `clear_cache`: la clinica appena accesa risultava spenta, e spenta risultava ancora accesa alla dashboard |
| Una patch crea pipeline e dashboard dove la clinica era già accesa | Nascono accendendo la clinica: un sito che l'aveva accesa prima non le avrebbe mai avute |
| I Link nascosti o di sola lettura non aprono liste agli ospiti | Un modulo web non li può raccogliere: `last_service` avrebbe aperto i servizi per niente |

## Fase 2, il motore dei modelli

> **Completato** (30/09/2026). Lo schema dei modelli e la sua logica, in Python e in
> JavaScript sugli stessi casi; bozza e versioni immutabili con impronta e testi dei
> consensi congelati; il builder in Impostazioni → Forms con quattro modelli di
> partenza e la prova dal vivo. `docs/gestionale-medico/README.md`, "Il motore dei modelli".

### Decisioni

| Decisione | Perché |
|---|---|
| Un renderer nostro, non `FieldLayout` | La logica è strutturata e gira uguale sul server; l'area cliente userà gli stessi componenti senza gli store del CRM |
| Una domanda guarda solo quelle prima di lei (mostra, calcola, conta) | Un passaggio in ordine decide tutto: niente cicli, niente ordine da indovinare, e i due lati restano identici |
| "Obbligatorio se" e "ferma se" guardano ovunque, anche sé stesse | Non cambiano risposte: il pacemaker si segnala sulla sua stessa domanda |
| Le condizioni con lo stesso formato e costruttore delle automazioni | Un solo modo di scrivere "se" nel CRM |
| Formule con un parser nostro (+ − * / ^, round, min, max, abs, sqrt) | Niente `eval`: una formula è dato, e dà lo stesso numero in Python e nel browser (arrotondamento half-up, non il banker's di Python) |
| `truthy()` nel JavaScript | Python e JavaScript non sono d'accordo su cosa è vuoto: un confronto differenziale lo ha trovato su 86 casi su 12.000 |
| Una condizione confronta un valore solo | Una lista come valore diventava testo in modo diverso sui due lati |
| La bozza si salva anche sbagliata; si pubblica solo giusta | Si lavora a pezzi; la gente compila solo versioni valide |
| Le parole dei consensi congelate nella versione, dentro l'impronta | Il PDF firmato porterà il testo esatto; un testo riscritto è una versione nuova |
| Una versione non si modifica né si cancella; un modello pubblicato si spegne | Quel che è stato firmato ci punta |
| Il marchio "dato clinico" lo registra la clinica | Il CRM non conosce la clinica; senza clinica il marchio prometterebbe una protezione che nessuno dà |
| La pagina Forms tiene i moduli web e i modelli, ognuno a chi lo può costruire | Il design chiede un builder solo con due destinazioni |

## Fase 2, compilare e firmare

> **Completato** (30/09/2026). Il modulo compilato (`CRM Form`) con le firme
> (`CRM Signature`), la firma semplice col dito, il PDF/A con la pagina delle prove,
> i consensi nel registro, il registro degli eventi a catena (`CRM Audit Log`), la
> scheda "Forms" della persona. `docs/gestionale-medico/README.md`, "Compilare e firmare".

### Decisioni

| Decisione | Perché |
|---|---|
| Del tratto si tiene il PNG, non i punti con pressione e tempi | Sarebbero dati biometrici (Garante, 2014); la firma avanzata passa dal codice di un fornitore |
| Firmare rifà tutti i controlli sul server | Il browser mostra le stesse regole, ma è il server che decide cosa si firma |
| Un campo con firma avanzata o qualificata non si firma col dito | Il livello lo sceglie il modello; un tratto sullo schermo spacciato per firma avanzata sarebbe peggio che non firmare |
| La firma porta l'impronta delle risposte, e il PDF quella dello schema e delle risposte | Si prova su cosa è stata messa, non solo che c'è |
| Il PDF si fa una volta, con WeasyPrint e il motore PDF/A della fatturazione | wkhtmltopdf non c'è; il motore della fatturazione converte e verifica cosa ne esce |
| Nessuna risorsa remota nel PDF: le firme dentro come immagini | Un PDF che scarica qualcosa smette di leggersi e dice a un terzo quando lo si apre |
| Il registro degli eventi è una catena di impronte | Un evento tolto o cambiato si vede, e si vede dove |
| I consensi del modulo portano la versione del testo congelata | Il registro dice su quali parole, e di quale versione, è stato dato il sì |
| `CRM Form` numerato `FRM-.YYYY.-.#####`, non `format:` | Con `format:` il contatore `{#####}` di Frappe ha chiave vuota ed è condiviso da tutti |
| La clinica dice chi legge i moduli con dati sanitari | Il CRM non conosce la clinica; senza clinica un modulo sanitario non esiste |
| In sola lettura le risposte si mostrano in parole | I controlli disabilitati, tutti grigi, non dicevano cosa era stato risposto |

## Fase 2, dove si firma: il tablet e il link

> **Completato** (30/09/2026). `CRM Form Request`: moduli dati alla persona da
> compilare da sola, con un link per email o sul tablet del banco; la pagina
> `/modulo/<link>`; "On their own" nella scheda Forms. `docs/gestionale-medico/README.md`,
> "Dove si firma".

### Decisioni

| Decisione | Perché |
|---|---|
| L'email del link non nomina i moduli, e la pagina li mostra solo dopo il codice | Il titolo di un consenso informato dice a cosa serve la visita; un link inoltrato o letto da altri non deve dirlo |
| Il codice va all'indirizzo del link ed è legato al link | Link e codice insieme sono le credenziali; lo stesso codice non apre un altro link |
| Dei segreti (link, codice, sessione) si tiene solo lo SHA-256 | Chi legge il database non apre i moduli di nessuno |
| Un link, più moduli: la prima richiesta tiene link, codice e sessione, le altre `via` | Si manda una volta, si entra una volta; ogni modulo resta una richiesta a sé con il suo stato |
| La versione del modello è quella del momento dell'invio | Si firma quello che il centro ha mandato; una versione nuova si manda con un link nuovo |
| Per chi firma un genitore o un tutore il link va a loro, e il modulo lo dice (`given_by`) | Il minore non firma; la firma "del paziente" data da chi risponde per lui è registrata come del tutore |
| Il tablet esce dall'utente dello staff e la pagina si lega al browser alla prima apertura | Sul tablet resta solo quella persona; l'indirizzo copiato altrove, o riaperto dopo, non apre niente |
| Un modulo con firma dell'operatore o avanzata si compila fuori e si firma al banco | Da soli si dà solo la propria firma semplice; il resto non si finge |
| Il modulo firmato fuori non ha autore del centro; il paziente lo registra chi ha mandato il link | "Compilato dalla persona" è la verità; la regola 1 vuole comunque un nome, non "Guest" |
| `open_request` è un POST | Frappe non salva ciò che un GET scrive: la sessione del tablet si perdeva |
| La pagina importa lo stesso motore del CRM, copiato tra gli asset | Una regola sola; un test di vitest ferma la copia che resta indietro |
| Il codice parte subito dopo il commit e, se il server di posta rifiuta, ci riprova la coda | Dura dieci minuti; un errore di posta non deve far fallire la pagina |

## Fase 2, su carta e con un fornitore di firma

> **Completato** (30/09/2026). La firma su carta con la scansione attestata
> dall'operatore; l'adattatore dei fornitori di firma avanzata e qualificata
> (`crm/moduli/firme.py`, `CRM Signature Settings`), con un fornitore finto nei
> test. `docs/gestionale-medico/README.md`, "Su carta e con un fornitore di firma".

### Decisioni

| Decisione | Perché |
|---|---|
| Una sola chiusura (`_chiudi`) per ogni modo di firmare | Stesso registro, stessa richiesta, stessi consensi: cambia solo come arriva la firma e chi fa il PDF |
| La firma su carta è "handwritten", qualunque livello chiedesse il campo | L'autografa non è un livello di firma elettronica; su carta si firma anche il consenso informato |
| La scansione entra nel PDF/A come allegato `Source`, e le sue pagine se è un PDF | Il documento conservato porta dentro l'originale da cui viene; nessun file a parte da perdere |
| L'operatore attesta la copia conforme, e senza attestazione non si firma | È la sua parola che lega la scansione all'originale di carta, come chiede il design |
| La copia da firmare ha caselle e righe per le risposte vuote | La stessa stampa serve anche come modulo di carta bianco |
| Il PDF del fornitore si tiene com'è | Convertirlo in PDF/A romperebbe la firma PAdES |
| Mandato al fornitore, il modulo non si cambia | Il fornitore ha già il PDF con quelle risposte; si riprende o aspetta il rifiuto |
| Il webhook è del fornitore attivo e lo verifica il fornitore | Ognuno firma le sue chiamate a modo suo; una busta sconosciuta, o ripresa, non firma niente |
| L'operatore di una firma data dal fornitore è chi ha compilato o mandato il modulo | Il webhook arriva senza nessuno collegato |
| Nessun fornitore reale nel codice, per ora | Il centro deve scegliere (Namirial, InfoCert, Intesi) e firmare un contratto; l'adattatore è pronto |

## Fase 2, i moduli dovuti

> **Completato** (30/09/2026). Quando un modulo si chiede e quanto vale uno
> firmato (`crm/moduli/dovuti.py`), nella scheda Forms, nella pagina Oggi e con
> la prenotazione. `docs/gestionale-medico/README.md`, "I moduli dovuti".

### Decisioni

| Decisione | Perché |
|---|---|
| `dovuto()` è pura, con i casi nei test | È la regola che decide cosa si chiede a chi: si prova senza database |
| Senza appuntamento non si chiede un modulo "per appuntamento" | Non c'è niente a cui legarlo; si chiede quando c'è la visita |
| Una versione nuova richiede solo se ha una data (`asked_from`) | Cambiare una virgola non deve far rifirmare tutti; lo decide chi pubblica |
| Si mostra cosa è già in corso invece di chiederlo di nuovo | Una bozza iniziata o un link aperto non sono moduli da chiedere due volte |
| Il link con la prenotazione parte dopo il salvataggio, in un job, fino all'ora della visita | La prenotazione non aspetta la posta; dopo la visita il link non serve |
| Non parte a meno di un'ora dalla visita, né se un link per quel modulo è aperto | Non c'è tempo di compilarlo a casa; e un secondo link confonde |
| Mandato dal centro, il paziente non lo registra "Administrator" | La regola 1 vuole un nome o nessuno, non un utente tecnico |
| La fine della giornata guarda anche ieri, e ricorda l'ultimo giorno chiesto | Un giorno che finisce dopo le 23 si chiude dopo mezzanotte; chiedere due volte lo stesso giorno sarebbe rumore |

## Fase 2, la scheda clinica, il referto e la sintesi

> **Completato** (30/09/2026). La visita scritta sulla scheda della specialità,
> firmata con il suo referto in PDF/A (`crm/clinica/referto.py`); la sintesi del
> paziente con le proposte dai moduli e dalle schede firmati
> (`crm/clinica/sintesi.py`, `Clinic Summary Value`).
> `docs/gestionale-medico/README.md`, "La scheda clinica, il referto e la sintesi".

### Decisioni

| Decisione | Perché |
|---|---|
| La scheda è un uso del modello registrato dalla clinica, non un DocType per specialità | Lo stesso motore, lo stesso builder, le stesse versioni; il CRM non sa niente di clinica (`test_confine`) |
| Solo l'uso "Form" si manda, si compila da un link e si chiede | Una scheda la scrive l'operatore nella cartella; mandarla al paziente la renderebbe un modulo |
| La visita tiene le risposte (JSON) e punta alla versione | Come un modulo compilato: il referto e la sintesi si rifanno dallo schema congelato |
| Le risposte si controllano e si fermano alla firma, con la loro impronta | Una scheda incompleta non si firma da nessuna strada; l'impronta dice che il referto è quello |
| Il referto si fa una volta sola, e se non si riesce la firma resta | Come il PDF del modulo: il documento non cambia dopo; un errore del PDF si vede nel log, non annulla la visita |
| Il referto non sta fra gli allegati della visita | È la visita stessa, non un file in più; ha il suo link |
| Le risposte vanno alla sintesi come proposte, e decide l'operatore | Un modulo compilato dal paziente non scrive da solo la sua cartella (design, "Il motore dei modelli") |
| Una riga della sintesi è l'ultimo valore confermato, e i valori restano | La sintesi ha una storia: da dove viene ogni valore, chi l'ha deciso |
| La sintesi la legge chi legge la cartella, la decide chi la scrive | Le stesse capacità della cartella (`clinica.vedi`, `clinica.scrivi`), lo stesso ambito sulle persone |
| Le righe della sintesi le registra la clinica (`registra_voce_sintesi`) | Il builder le offre solo quando c'è la clinica; il campo `summary` è una proprietà comune dello schema |

## Correzione: un documento firmato porta solo quello che c'è scritto

> **Completato** (30/09/2026). Il PDF del modulo firmato e il referto della
> visita si facevano da un HTML che stampava le risposte, il nome del browser e
> gli altri valori senza escape, e WeasyPrint caricava quello che l'HTML indicava:
> una risposta come `<a rel="attachment" href="file:///...">` avrebbe messo un file
> del server dentro il PDF firmato, che la persona poi scarica; un'immagine con un
> indirizzo avrebbe fatto chiamare quell'indirizzo al server.

### Decisioni

| Decisione | Perché |
|---|---|
| I modelli HTML dei documenti firmati stampano con l'escape (`{% autoescape true %}`) | Quello che una persona scrive, o che il suo browser dice di sé, è testo |
| Il motore dei PDF carica solo i data URI (`pdf.pdf_da_html`) | Anche se qualcosa sfuggisse all'escape, niente del disco e niente dalla rete entra in un documento firmato |
| Le note del referto scritte nel CRM restano testo; quelle del Desk passano da `sanitize_html` | L'editor del Desk scrive HTML: si tiene la formattazione, non il resto |
| Il test prova anche il contrario: senza il nostro motore il file del server entra | Un test che passa anche senza la correzione non prova niente |

## Fase 2, l'archivio clinico e il registro degli accessi

> **Completato** (30/09/2026). L'archivio (`crm/clinica/archivio.py`,
> `Clinic Document`) con i documenti caricati, il referto di ogni visita firmata e
> i file ricevuti in una conversazione. Il registro degli accessi mette insieme la
> cartella, l'archivio e i file scaricati. `docs/gestionale-medico/README.md`,
> "L'archivio clinico e il registro degli accessi".

### Decisioni

| Decisione | Perché |
|---|---|
| Un documento dell'archivio si legge con le regole della cartella (`cartella.legge_le_altre`, `condizione_condivisa`) | Una regola sola per le voci e per i documenti: autore, direzione, dossier, "solo io" |
| Ogni documento è "per" un operatore, e la segreteria lo deve dire | Senza dossier un documento di nessuno non lo leggerebbe nessun operatore |
| La segreteria archivia e poi vede solo quello che ha aggiunto (`clinica.archivia`) | Scansiona quello che porta il paziente, ma la cartella non è sua |
| Il referto in archivio è un rimando alla visita, senza un file suo | Si legge e si scarica con i permessi della visita, e non si toglie |
| Ora anche la visita libera ha il suo referto; la nota no | Il referto è quello che si consegna di una visita: serve a tutte |
| Un documento non chiude l'appuntamento (`dice_che_e_venuto`) | Un esame può arrivare prima della visita per cui è |
| Un errore si toglie in giornata da chi l'ha aggiunto, poi solo dalla direzione, con il motivo nel registro degli eventi | La persona sbagliata va corretta subito; dopo decide chi risponde della parte clinica |
| Il registro degli eventi sopravvive a ciò che registra (`ignore_links_on_delete`) | Tolto il documento, restano chi l'ha tolto e perché |
| La scheda paziente perde il rimando al documento tolto, non la regola | Un paziente resta paziente; il rimando non punterebbe a niente |
| Dalla conversazione si archivia una copia privata, e il file della chat diventa privato | frappe_whatsapp salva pubblici i file ricevuti: un documento sanitario non resta raggiungibile dal solo indirizzo |
| Il registro degli accessi raggruppa per persona, minuto e tipo, e mostra cosa è stato aperto, non il titolo | Aprire la scheda scrive una riga per voce; al manager serve chi e quando, non cosa |
| L'Access Log si tiene due anni come il View Log | Gli scaricamenti dei file sono accessi anche loro |
| La sintesi non dà permessi a System Manager | Come la cartella: i dati clinici non sono dell'agenzia |

## Fase 2, il dossier, l'oscuramento e l'apertura con motivo

> **Completato** (30/09/2026). Le regole del Garante sul dossier (4/6/2015) in
> `crm/clinica/dossier.py`: il dossier vuole il consenso e la cura, l'oscuramento
> degli episodi, la visibilità per disciplina, l'apertura fuori équipe con un
> motivo (`Clinic Access Grant`). `docs/gestionale-medico/README.md`, "Il
> dossier, l'oscuramento e l'apertura con motivo".

### Decisioni

| Decisione | Perché |
|---|---|
| Il dossier legge le voci degli altri solo per le persone in cura (`visible_leads`), anche nelle liste | Con il solo consenso, un operatore avrebbe elencato le cartelle di tutti i pazienti col dossier, via REST |
| Una regola sola per la cartella e l'archivio (`dossier.legge_le_altre`, `condizione_condivisa`) | Consenso, cura, oscuramento, disciplina e "solo io" si decidono in un posto |
| Oscura la direzione, non l'operatore, e solo un episodio firmato | Lo dice doc 30; una bozza è solo del suo autore, e la direzione non la vede |
| Una visita si oscura con le sue integrazioni e i suoi referti | L'episodio è uno: una parte lasciata fuori lo tradirebbe |
| Oscurato, gli altri non lo vedono affatto: né voce, né lucchetto, né fonte della sintesi | "Oscuramento dell'oscuramento": non si deve poter capire che qualcosa è stato oscurato |
| La sintesi, per chi non può leggere la fonte, mostra l'ultimo valore da ciò che legge | Un farmaco confermato da un episodio oscurato direbbe l'episodio |
| La disciplina è la qualifica della scheda erogatore, fissata sulla voce quando si scrive | La voce resta della disciplina di chi l'ha scritta, anche se poi cambia qualifica |
| Fuori équipe si cerca per nome e cognome interi o per codice fiscale, al massimo 5 risultati | Chi apre deve sapere chi cerca: non è un elenco del centro da sfogliare |
| L'apertura dura 24 ore e non cambia le regole del dossier | Rende la persona "in cura" per un giorno; senza consenso al dossier non apre le voci degli altri |
| L'apertura, con il motivo, è nel registro degli accessi del manager | Doc 30: "e il manager lo vede" |
| `Clinic Access Grant` non si modifica né si cancella, e non fa diventare paziente | È la traccia di un accesso, non un dato sanitario (`test_confine`) |

## Fase 2, la consegna del referto

> **Completato** (30/09/2026). Il referto al paziente, a mano o online per 45
> giorni con il consenso (`crm/clinica/consegna.py`, `Clinic Report Delivery`,
> `/referto/<link>`). Con questa la fase 2 è completa.
> `docs/gestionale-medico/README.md`, "La consegna del referto".

### Decisioni

| Decisione | Perché |
|---|---|
| Online solo con il consenso ai referti online, e mai per "Never online" | Linee guida 2009 e FAQ: adesione facoltativa; niente esiti genetici o HIV online; il paziente può escludere un esame |
| Il link per email, il codice a voce o su carta, mostrato una volta | "La password per un'altra strada": un indirizzo sbagliato da solo non apre niente (il Garante ha ammonito un centro nel 2025 per un referto mandato all'indirizzo sbagliato) |
| L'email non dice né il titolo né il contenuto | Il messaggio dice solo che c'è qualcosa, come chiedono le linee guida |
| 45 giorni al massimo, poi non si apre più | Più a lungo diventerebbe un dossier, con un consenso a parte |
| Cinque codici sbagliati chiudono la consegna; il ritiro è immediato | Accesso sospeso subito se le credenziali si perdono |
| La sessione dura dieci minuti e non è il codice | Chi ha scaricato non lascia aperto il documento a chi usa lo stesso dispositivo dopo |
| Un codice nuovo ritira quello aperto | Un solo modo valido per volta di aprire lo stesso documento |
| Senza email del centro la consegna resta, e il link si dà con il codice | La consegna non deve dipendere dalla posta |
| La consegna non si cancella | È la prova di cosa è stato dato e a chi |

## Fase 3, l'area del paziente: la porta e le prime stanze

> **Completato** (30/09/2026). `/area`, un'app a parte con le API in
> `crm/clinica/area`: l'invito del centro (`Clinic Area Access`), l'accesso con un
> codice per email, gli appuntamenti con il link della prenotazione, i documenti
> dati online, le fatture. `docs/gestionale-medico/README.md`, "L'area del
> paziente: la porta e le prime stanze".

### Decisioni

| Decisione | Perché |
|---|---|
| Un'app Vite a parte (`vite.area.config.js`, `/assets/crm/area`), non una rotta della SPA | Il paziente non scarica il codice dello staff, e la pagina d'ingresso non è quella del CRM (design, "L'area cliente") |
| Un utente del sito con il ruolo "Clinic Patient", senza Desk; mai un indirizzo dello staff | Lo staff ha le sue credenziali e il suo CRM; un paziente non deve poter aprire il Desk |
| Chi entra dove sta in `Clinic Area Access`, anche per un figlio o un genitore anziano | Una persona può seguire più aree, e ogni accesso si apre e si chiude uno per uno |
| Ogni chiamata ricava sul server le persone della sessione e rifiuta le altre | Mai un id accettato dal telefono (design) |
| Un codice per email a ogni ingresso, dieci minuti e cinque tentativi, e la stessa risposta a chiunque | Niente password da ricordare; la pagina non dice quali indirizzi hanno un'area |
| Per scaricare un documento, un codice verificato negli ultimi quindici minuti | "Per scaricare un referto si rientra" (design, linee guida sui referti online) |
| Gli appuntamenti si spostano e annullano dalla pagina di prenotazione, con il suo link | Le regole del centro (preavviso, limiti) sono già lì: una sola strada |
| L'area ha un suo dizionario italiano | Il paziente legge la sua lingua, non quella dello staff |

## Fase 3, prepara la visita e i messaggi del centro

> **Completato** (30/09/2026). "Prepara la visita" nell'Inizio dell'area, con i
> moduli compilati sulla pagina `/modulo` già aperta; la bacheca dei messaggi del
> centro (`Clinic Message`, `crm/clinica/area/messaggi.py`).
> `docs/gestionale-medico/README.md`, "Prepara la visita e i messaggi del centro".

### Decisioni

| Decisione | Perché |
|---|---|
| Dall'area si compila sulla pagina dei moduli che c'è, aperta con la sua sessione | Una sola pagina per compilare e firmare, con le sue regole e le sue prove; il codice dell'area vale come quello del link |
| Il link dell'area dura quattro ore | Basta per compilare adesso; il giorno dopo si riapre dall'area |
| Un link aperto con gli stessi moduli si riprende, anche se era arrivato per email | Le risposte date restano; un solo link vivo per gli stessi moduli |
| Firma chi firmerebbe un link per email; chi segue soltanto non firma | Il genitore firma per il figlio minorenne, un figlio segue il genitore anziano senza firmare al posto suo (design, "Familiari") |
| I messaggi sono una bacheca, non una chat | Il design lascia aperto se il paziente risponde ("Da decidere" 7): una chat è un'altra casella per i medici, e si aggiunge dopo se il centro la vuole |
| Il messaggio dell'operatore è della cura, quello della segreteria no | Un dato sanitario fa un paziente e si legge come una visita; un promemoria no |
| L'email dice solo che c'è una novità | Le notifiche non portano contenuti (design, "Notifiche") |
| Aprire la bacheca segna letti i messaggi, con chi e quando | Il centro sa che la persona l'ha visto, senza chiederle di confermare |

## Fase 3, i piani nel CRM

> **Completato** (30/09/2026). `Clinic Plan` con i suoi momenti e le sue voci, le
> librerie `Clinic Food` e `Clinic Exercise`, le regole pure in
> `crm/clinica/piani_regole.py`, l'editor nella scheda Clinica.
> `docs/gestionale-medico/README.md`, "I piani, nel CRM".

### Decisioni

| Decisione | Perché |
|---|---|
| Momenti e voci in due tabelle, la voce che punta al suo momento con una chiave | Frappe non annida le tabelle figlie (design, "I piani"); la chiave resta la stessa tra una versione e l'altra |
| Il tipo di piano lo decide la qualifica dell'erogatore, in una tabella del codice | "La dieta la firmano medico, biologo nutrizionista o dietista": è la legge, non una preferenza del centro |
| Pubblicato non si riscrive: una nuova versione lo sostituisce, o si chiude | Come la cartella: si sa sempre cosa il paziente aveva davanti in un giorno |
| Pubblicare chiude l'altro piano dello stesso tipo della persona | Una dieta alla volta: due menù aperti si contraddicono |
| Le librerie sono del centro e crescono dall'editor; i valori vengono da una tabella che si cita | "I conti dei nutrienti li fa il motore dalle tabelle, non l'IA" (design) |
| L'andamento è fatto, in parte, saltato, senza rosso | "Niente rosso fuori obiettivo, niente classifiche" (design) |
| Una bozza clinica buttata lascia la scheda paziente con la sua regola, senza il legame | Prima la prima bozza di una visita non si poteva buttare: la scheda la indicava come origine (`DocumentoClinico.on_trash`) |

## Fase 3, i piani nell'area del paziente

> **Completato** (30/09/2026). La pagina "Piani" dell'area con il giorno del piano
> e un tocco per voce (`crm/clinica/area/piani.py`, `Clinic Plan Log`).
> `docs/gestionale-medico/README.md`, "I piani nell'area del paziente".

### Decisioni

| Decisione | Perché |
|---|---|
| "Piani" nella barra solo per chi segue un piano adesso | La maggior parte dei pazienti non ne ha: una voce vuota è rumore, e la barra sta in sei posti solo con etichette corte ("Agenda") |
| Un check-in per voce e per giorno, cambiato o ritirato con un tocco | "Un tocco per pasto": niente diario da compilare, che si abbandona in pochi giorni (design) |
| Si segna fino a due giorni indietro, mai avanti | "La serie di giorni si può recuperare" (design); avanti si guarda soltanto |
| Si mostra quello che resta ("ancora 2 questa settimana"), niente rosso | "Niente rosso fuori obiettivo, niente classifiche" (design) |
| Le calorie solo se l'operatore le vuole mostrare | "Calorie solo se l'operatore le vuole mostrare" (design) |
| Gli alimenti tra cui scegliere vengono dalla libreria del centro, con la loro porzione | "Il paziente sceglie dentro i limiti" (design) |
| L'immagine di un esercizio solo se è un file pubblico o un indirizzo; il video si apre fuori | Un file privato non si mostra a un utente del sito; un player incorporato è un altro sito dentro l'area |

## Fase 4, l'assistente: le fondamenta e il modulo di carta

> **Completato** (30/09/2026). `crm/assistente`: il modulo del piano, l'adattatore
> del modello, `CRM Assistant Settings`, il registro `CRM AI Event`, "Dal modulo di
> carta". `docs/gestionale-medico/README.md`, "L'assistente: le fondamenta e il
> modulo di carta".

### Decisioni

| Decisione | Perché |
|---|---|
| L'assistente sta nel CRM, non nella clinica; la clinica registra le sue funzioni | Il lavoro d'ufficio (moduli di carta) serve a ogni cliente; le funzioni cliniche portano con sé chi legge i loro eventi |
| Un adattatore, due modi di parlare (Anthropic, compatibile OpenAI) | Dove gira il modello è un indirizzo nelle impostazioni, non un ramo del codice: API, gateway UE, server del centro |
| Senza "nessuna conservazione, nessun addestramento" non parte | Il contratto è la condizione (design, "I dati"), e l'agenzia lo dichiara dove si configura |
| http solo verso la macchina del centro | Fuori dal centro i dati viaggiano cifrati, come per la trascrizione |
| Ogni richiesta è un evento, anche fallita, e non si cancella | "Un registro dell'assistente... Ogni mese un campione si rilegge" (design) |
| Il registro tiene le parole del modello come sono arrivate; il confronto si fa a parte | L'impronta di uscita deve corrispondere al testo tenuto |
| Dal modulo di carta: solo il testo del PDF, niente immagini | Un modulo in bianco non ha dati di nessuno; leggere scansioni è un altro lavoro, e un altro rischio |
| Lo schema proposto passa le regole del motore, e diventa solo una bozza | Nessuna scorciatoia: si finisce e si pubblica nel builder come ogni modello |

## Fase 4, l'assistente nella clinica: bozze, dettatura, riassunto

> **Completato** (30/09/2026). `crm/clinica/assistente.py` (bozze dalla nota
> firmata), `dettatura.py` (la visita dettata nei campi della scheda),
> `riassunto.py` (il riassunto prima della visita con le fonti); il consenso
> `ai_assistant`. `docs/gestionale-medico/README.md`, "L'assistente nella
> clinica".

### Decisioni

| Decisione | Perché |
|---|---|
| Il consenso del paziente all'assistente, oltre al contratto del centro | È tra i consensi della clinica del design; la L. 132/2025 chiede di dire al paziente quali sistemi di IA si usano |
| Al modello non va chi è il paziente; la bozza lascia i vuoti | Il minimo che serve: il nome lo mette il professionista |
| Solo dalla propria nota firmata | "Bozze dalla nota firmata dell'operatore" (design): si parte da quello che il professionista ha già firmato |
| Tenuta, la bozza è una nota da firmare con il segno | "Niente si salva da solo: firma l'operatore"; "ogni nota porta il segno" (design) |
| La dettatura non registra l'audio: le parole sono scritte o dettate dal dispositivo | Niente audio da cancellare, niente trascrizione da tenere; il registro tiene l'impronta |
| Farmaci, allergie e dosi non si spuntano mai da soli | "Si confermano uno per uno" (design): dove gli scribe sbagliano di più |
| Il riassunto cita le fonti numerate, e non dà punteggi né avvisi | "Il riassunto prima della visita, con le fonti citate, senza classifiche né avvisi" (design) |
| Gli eventi clinici li legge la direzione, non il manager | Sono dati sanitari: la rilettura mensile è vigilanza clinica |
| "Quanto è cambiata" si misura parola per parola | Sulle lettere lunghe il confronto per lettere scambiava due nomi riempiti per una riscrittura |


## Il sigillo del centro e la marca temporale sui PDF

> **Completato** (30/09/2026). `crm/moduli/sigillo.py` (pyHanko): il sigillo PAdES
> con il certificato del centro e la marca temporale RFC 3161 sul PDF/A del modulo
> firmato (`crm/moduli/pdf.py`) e sul referto della visita (`crm/clinica/referto.py`);
> i campi in `CRM Signature Settings`; la pagina dell'agenzia
> `frontend/src/components/Settings/SealSettings.vue`.
> `docs/gestionale-medico/README.md`, "Il sigillo del centro e la marca temporale".

### Decisioni

| Decisione | Perché |
|---|---|
| Si sigilla prima di prendere l'impronta | Lo SHA-256 che il modulo tiene deve essere quello del file tenuto: un'impronta del file senza sigillo non proverebbe niente |
| Un sigillo invisibile, con il flag di stampa | Un riquadro disegnato vorrebbe i font incorporati di PDF/A; pyHanko di default resta compatibile con PDF/A-2/3 |
| La struttura PDF/A si ricontrolla dopo il sigillo | Il sigillo è un aggiornamento aggiunto al file: la conformità dichiarata riguarda i byte tenuti |
| Mai d'intralcio: senza sigillo, senza marca, mai senza documento | Una firma del paziente non si perde per un certificato o un'autorità che non rispondono; il registro dice cosa è successo |
| Un certificato non valido oggi non sigilla | Un sigillo scaduto si legge come un sigillo rotto |
| La chiave si legge in memoria (`load_pkcs12_data`) | Il file privato dell'agenzia resta l'unico posto dove la chiave sta |
| La marca con un timeout di 10 secondi | Il sigillo avviene mentre la persona firma: un'autorità lenta non deve tenerla ferma |
| Certificato, password e autorità sul permlevel 1, pagina con `tecnico.integrazioni` | Sono chiavi dell'agenzia, come quelle dei fornitori (doc 30) |

## Fase 4, il menù per il nutrizionista

> **Completato** (30/09/2026). Gli obiettivi del giorno sul piano alimentare, i
> nutrienti dalle tabelle (`crm/clinica/piani_regole.py` e
> `frontend/src/utils/piani.js`, sui casi di `crm/clinica/tests/casi_nutrienti.json`),
> le ricette dell'assistente (`crm/clinica/menu.py`), la nota del pasto nell'area.
> `docs/gestionale-medico/README.md`, "Il menù per il nutrizionista".

### Decisioni

| Decisione | Perché |
|---|---|
| Dell'IA si tengono solo gli alimenti della libreria e le proporzioni | "I conti dei nutrienti li fa il motore dalle tabelle, non l'IA" (design): un numero del modello non entra mai |
| I grammi li scala il motore all'energia del pasto | L'energia è un obiettivo del nutrizionista; la ricetta dà solo le proporzioni |
| Stessi conti in Python e in JavaScript, sugli stessi casi, con l'arrotondamento a metà in su | Il totale che il nutrizionista vede scrivendo è quello che il server conta; `round()` di Python arrotonda al pari, il browser in su |
| L'energia suggerita divide ciò che l'obiettivo lascia fra i pasti vuoti | Un punto di partenza: il nutrizionista la cambia |
| La ricetta scelta va nella nota del pasto con il segno | Il paziente legge come si prepara; il segno dice che è una bozza dell'IA controllata (AI Act art. 50) |
| Tabella dei conti senza colori | "Niente rosso fuori obiettivo" (design): i numeri li legge il professionista |
| Il dialogo delle ricette sta dentro quello del piano | Due dialoghi reka-ui fratelli: il secondo restava `aria-hidden`, invisibile a uno screen reader |

## Fase 4, la chat del paziente

> **Completato** (30/09/2026). `crm/clinica/chat_regole.py` (emergenza, salute,
> il resto: pure), `crm/clinica/area/chat.py` (la chat dell'area, il passaggio al
> centro), la domanda "Question" sulla bacheca (`Clinic Message`), l'avviso "Area"
> alla segreteria, "Answered" nel registro, le domande frequenti del centro nelle
> impostazioni dell'assistente. `docs/gestionale-medico/README.md`, "La chat del
> paziente". Con questa, la fase 4 è completa.

### Decisioni

| Decisione | Perché |
|---|---|
| L'emergenza la riconoscono le regole, prima del modello, anche a chat spenta | Il 112 non aspetta una rete o un modello; nessun dato esce |
| Niente "112" o "118" da soli fra le parole d'emergenza: "il 112", "il 118" | "Via Roma 112" è un indirizzo |
| La salute non ha risposta dalla chat: il paziente decide se passarla | "Se parla di sintomi passa a una persona" (design); la domanda con i sintomi la manda lui |
| La domanda passata va sulla bacheca, non in un compito del CRM | Un compito sulla persona lo vede anche chi vende; la bacheca ha già le regole della clinica |
| L'avviso alla segreteria non ha le parole della domanda | Le parole restano sulla bacheca, come la mail dell'area dice solo che c'è una novità |
| Si passa al centro solo dalla chat accesa | Un canale paziente→centro è la domanda 7 del design: la decide il centro |
| Al modello la domanda e gli ultimi turni, non chi chiede | Il minimo che serve per rispondere su orari e prenotazioni |
| Le risposte della chat sono "Answered" nel registro | Non sono bozze che qualcuno accetta: vanno al paziente come vengono, e la direzione le rilegge |
| La chat è spenta finché il centro non la accende | Un'IA che parla ai pazienti la sceglie il centro, con le sue domande frequenti |
