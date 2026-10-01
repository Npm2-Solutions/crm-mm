# DottorCloud — Project Context

## What this project is

DottorCloud, the management software for medical centres of NPM2 Solutions Srl,
built as the `crm` app. Vue 3 + frappe-ui frontend; the backend is Python on the
Frappe framework. Scripts in `frontend/` only; Python in `crm/`. No build step for
Form Scripts — they run as evaluated strings in the browser.

The company is **NPM2 Solutions Srl**, the brand is **DottorCloud**. Everything a
user sees says DottorCloud: never "Frappe" nor "Frappe CRM", in the CRM, the
framework's screens (login, desk, public pages, emails) or a document, and never
"the CRM" for the product ("CRM" stays for the category and in technical names).
The framework's name stays where only code sees it (imports, API paths).

A new file starts `Copyright (c) <year>, NPM2 Solutions Srl and contributors`. A
file that came from the original project keeps its authors' copyright line, as
the AGPL asks, and when NPM2 changes it for the first time it gets
`Modifications copyright (c) <year>, NPM2 Solutions Srl` right below.

---

## Where to read before working

| Task | Read first |
|---|---|
| What are we building next | [PLAN.md](./.pi/PLAN.md) |
| Stable API contracts (setFieldProperty, formDialog, helpers) | [SPEC.md](./.pi/SPEC.md) |
| Why code is the way it is (decisions, bugs fixed, history) | [ARCHIVE.md](./.pi/ARCHIVE.md) |
| Form scripting user guide | [feats/form-scripting/guide.md](./.pi/feats/form-scripting/guide.md) |
| formDialog() API reference | [feats/form-scripting/form-dialog.md](./.pi/feats/form-scripting/form-dialog.md) |
| Electronic invoicing (setup, issuing, Sistema TS) | [feats/fatturazione/guida.md](./.pi/feats/fatturazione/guida.md) |
| Any screen a phone will see (rules below) | [docs/progetto-ghl/29-telefono.md](./docs/progetto-ghl/29-telefono.md) |

---

## Key files

### Scripting engine
| File | Role |
|---|---|
| `frontend/src/data/document.js` | `useDocument` — loads doc, wires script, patches `save.submit`, exposes triggers |
| `frontend/src/data/script.js` | `getScript` — fetches Form Script records, evaluates class via `new Function`, injects helpers, `setupHelperMethods` |
| `frontend/src/utils/scriptHelpers.js` | `createDocProxy`, `getClassNames` — extracted pure helpers |

### Field rendering
| File | Role |
|---|---|
| `frontend/src/components/FieldLayout/FieldLayout.vue` | Tab/section/column layout. Accepts `context` prop for standalone mode (no useDocument) |
| `frontend/src/components/FieldLayout/Field.vue` | Renders a single field. Calls `useDocument` unless `fieldLayoutContext` is injected |
| `frontend/src/components/FieldLayout/Section.vue` | Section with CollapsibleSection |
| `frontend/src/components/FieldLayout/Column.vue` | Column wrapper |

### Form dialog system
| File | Role |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | Dialog shell + standalone FieldLayout + local reactive doc |
| `frontend/src/components/Modals/FieldLayoutDialogContainer.vue` | Renders dialog entries from reactive array |
| `frontend/src/utils/renderFieldLayoutDialog.js` | `formDialog()` — pushes to array, returns Promise |
| `frontend/src/components/Modals/GlobalModals.vue` | Mounts FieldLayoutDialogContainer + other app-wide modals |

### Field transforms & validation
| File | Role |
|---|---|
| `frontend/src/utils/fieldTransforms.js` | `processField()`, `findMissingMandatory()`, `parseLinkFilters()` — pure, tested |
| `frontend/src/utils/expressions.js` | `evaluateDependsOnValue()`, `evaluateExpression()` |

### Meta & stores
| File | Role |
|---|---|
| `frontend/src/stores/meta.js` | `getMeta(doctype)` — fetches DocType meta, exposes `getFields()`, formatters |
| `frontend/src/stores/global.js` | `$dialog`, `$socket`, `makeCall` |

### Dashboard
| File | Role |
|---|---|
| `crm/dashboard/` | Widget registry, context (period, owners), chart payloads, features, templates, store |
| `crm/dashboard/widgets/` | The widget catalogue, one file per module — `@widget(id, category, kind, requires=…)` |
| `crm/api/dashboard.py` | Dashboards list/layout/catalogue, widget data in one request, save/reset |
| `frontend/src/pages/Dashboard.vue` + `components/Dashboard/` | Switcher, period, builder (grid + widget library), the widget kinds |
| `frontend/src/utils/dashboard.js`, `dashboardCharts.js` | Pure: periods, formats, grid, catalogue search, palette, ECharts options — tested |
| `docs/progetto-ghl/28-dashboard.md` | What it does and why |

### Service booking & external platforms
| File | Role |
|---|---|
| `crm/scheduling/booking_rules.py` | Online booking limits — pure, tested with plain `unittest` |
| `crm/api/service_booking.py` + `crm/www/prenota.*` | Public `/prenota` page on the full scheduling engine |
| `crm/scheduling/unify.py` | One booking system: legacy Booking Calendars → services, /book redirects |
| `crm/api/booking_admin.py` | Who-does-what matrix, team rota, "why not available" explainer |
| `crm/booking_platforms/` | Connectors (MioDottore, Treatwell, Calendly, Cal.com…), sync engine |
| `crm/api/booking_platforms.py` | Webhook in, busy feed out, settings API |
| `crm/scheduling/cicli.py` + `cicli_regole.py` | Cycles of sessions (`CRM Session Cycle`, `agenda.cicli`): an appointment joins its cycle by itself (`aggancia` in its `validate`), "session 4 of 10", each session its share of the price, one invoice for a cycle paid as a whole (`invoicing.api.issue_from_cycle`); the rules pure, tested with plain `unittest` |
| `frontend/src/components/CyclesSection.vue`, `CycleDialog.vue` + `utils/cicli.js` | The person's cycles, selling and following one; the words, tested; `area/components/CycleCard.vue` in the patient area |
| `crm/scheduling/attese_regole.py` + `attese.py` | Waiting lists (`CRM Waiting List Entry`, `agenda.attese`): who waits for what (days, parts of the day, a full class), the line; what frees a place (a cancellation, a move, a deleted appointment, a seat, new hours: doc_events) runs the look in a job on `availability.get_slots`, the offer goes by email, WhatsApp or SMS with a link and the first who confirms books under /prenota's lock; every ten minutes the offers nobody answered go to the next ones; the desk's list, its free places, offering and booking by hand; `CRM Waiting List Settings`. The rules pure, tested with plain `unittest` |
| `crm/scheduling/attese_pubblico.py` + `crm/www/lista_attesa.*` | Joining from /prenota (no time suits, a full class) and the `/lista-attesa/<link>` page: the offer to confirm or let go, the list to leave. The entry keeps the email and mobile typed when joining, and the offers go there |
| `frontend/src/pages/WaitingList.vue`, `components/Waiting/` + `utils/attese.js` | The desk: the whole line, the person's section, an entry with its free places; the words, tested; `area/components/WaitingCard.vue`, `WaitingJoinDialog.vue` in the client area |
| `crm/scheduling/abbonamenti_regole.py` + `abbonamenti.py` | Subscriptions (`CRM Subscription Type`, `CRM Subscription`, `agenda.abbonamenti`): a type sold from a day, its terms copied on the subscription; an appointment of a comprised service uses an entry by itself (`aggancia` and `prezzo` in the appointment's `validate`, after its cycle) while its week or month has one left, and costs nothing; a suspension moves the end; the daily `ogni_giorno` invoices the instalments due (`invoicing.api.issue_from_subscription`, issued where the type says so), reminds of the end, renews. The rules pure, tested with plain `unittest` |
| `frontend/src/components/Subscriptions/`, `Settings/Scheduling/SubscriptionTypesSettings.vue` + `utils/abbonamenti.js` | The person's subscriptions, selling and following one, the types in Settings > Agenda > Services; the words and the instalments as the server makes them, tested; `area/components/SubscriptionCard.vue` in the client area |
| `docs/prenotazioni/` | User guide + platform API research |

---

### Forms to fill and sign (crm/moduli, docs/gestionale-medico phase 2)
| File | Role |
|---|---|
| `crm/moduli/schema.py` | Pure: what a template schema may hold, conditions, formulas, scores, `valuta()`, `pulisci()`, `valida_schema()`, SHA-256 |
| `frontend/src/utils/moduli.js` | The same rules in the browser, plus the builder's helpers — tested on the same cases |
| `crm/moduli/tests/casi_schema.json` | The cases both sides must agree on: change one side, run both suites |
| `crm/moduli/modelli.py` | Drafts (`CRM Form Template`) and immutable versions (`CRM Form Template Version`), consents' words frozen at publish; the uses: a "Form" the person fills (sent, owed at a booking, giving consents), a "Sheet" the operator writes at the desk (a treatment sheet; with the health data mark, the clinic's clinical sheet, written in the record) and a "Website" form anybody fills, built by marketing (`moduli_lead.gestisci`), a module registers its own (`registra_uso`); what a use does not allow (`problemi_dell_uso`); the summary's lines |
| `crm/moduli/sito.py` + `crm/www/crm_form.*` | A form of the website at `/crm-form/<address>`, in another site (`?embed=1`, the sites listed) or in a page of the centre's (`site_render.crm_form_html`, `templates/site/form_inline.html`): the guest `submit_site_form` finds the person by email or mobile or makes them (`find_or_create_person`), fills what the centre did not know, keeps the answers as their form (channel "Website"), records the consents, opens the deal, fires "Lead Form Submitted"; a honeypot, a rate limit; a draft only tried (`try_site_form`) |
| `crm/public/js/moduli_campi.js`, `crm/public/css/moduli_campi.css` | The questions of a public page drawn without a framework, on the engine the page hands over: `/modulo`, the website's page and block (`versione_del_motore` versions all three) |
| `frontend/src/components/Moduli/` | `FormRenderer` + `FormFieldInput`: draw and fill a schema |
| `frontend/src/components/Settings/Forms/Template*.vue` + `utils/moduliSito.js` | The one builder, in Settings > Clients > Forms: forms, sheets and the website's (its address, its Share tab, the person's field a question fills); what a use does not allow, live, the address from a title, the embed code — tested |
| `crm/moduli/compilazioni.py` | A person's forms: start, save half-way, sign (checks, strokes, submit, PDF, consents) |
| `crm/moduli/pdf.py` + `templates/modulo_firmato.html` | The signed form's PDF/A with its evidence page, made once |
| `crm/moduli/sigillo.py` | The centre's PAdES seal and RFC 3161 time stamp (pyHanko), before the fingerprint; the agency's Seal page |
| `crm/moduli/traccia.py` | `CRM Audit Log`: a document's events, each chained to the one before |
| `frontend/src/pages/FormFill.vue`, `components/Moduli/FormsArea.vue`, `SignaturePad.vue` | Filling and signing, the person's Forms tab (forms and sheets), the stroke as a PNG |
| `crm/moduli/richieste.py` | `CRM Form Request`: forms filled on their own — a link by email (code to the same address) or the desk's tablet; the guest calls |
| `crm/www/modulo.*` + `crm/public/js/moduli_engine.js` | The `/modulo/<link>` page; the engine is `frontend/src/utils/moduli.js` copied (`yarn sync-moduli-engine`, a test keeps them equal) |
| `frontend/src/components/Moduli/SendFormsDialog.vue`, `RequestRow.vue` | "On their own": send a link or hand the tablet over; what was sent and where it is |
| `crm/moduli/firme.py` + `CRM Signature Settings` | Signature providers: `FornitoreFirma` (create, page, webhook event, signed PDF, evidence), `registra_fornitore`, the webhook |
| `frontend/src/components/Moduli/PaperSignDialog.vue` | On paper: print the copy to sign, upload the scan, attest it (`compilazioni.sign_on_paper`) |
| `crm/moduli/dovuti.py` | Which forms a person owes, and when: `dovuto()` is pure (ask on, validity, a new version from a date); the Forms tab, Today and the link sent with a booking |

The browser and the server evaluate a form the same way: a question looks only at
the ones before it (to show, compute, score), a hidden answer does not count, and
the JavaScript asks Python's truth (`truthy()`: `[]` and `{}` are false).

### Levels, capabilities and the plan (doc 30)
| File | Role |
|---|---|
| `crm/permissions/livelli.py` | The registry: plan modules, levels, roles, capabilities with their scope. `puo()`, `ambito()`, `@richiede()`, pure `calcola()`. Every level carries `RUOLO_RECAPITI` (Contact Details) unless `recapiti=False` (Marketing): without it Frappe masks people's email and phone |
| `crm/permissions/catalogo.py` | The CRM's own levels and capabilities; `crm/invoicing/capacita.py` adds invoicing's |
| `crm/permissions/utenti.py` | Role Profiles from the registry, giving levels, the migration of old users |
| `crm/registrazione.py` | Every module registers here, once per process (`before_request`, `before_job`) |
| `crm/fcrm/doctype/crm_plan/` | The centre's plan: the second key of every capability |
| `crm/permissions/org_hierarchy.py` | Which people and deals a user sees: the scope of `persone.vedi` / `trattative.vedi` (centre, team, own + in care); calls, notes, tasks follow them |
| `crm/permissions/seguono.py` | What follows the person: appointments (`agenda.vedi`, busy time for the rest), WhatsApp, SMS, tracking, old bookings |
| `crm/permissions/documenti.py` | Writing what the screens keep for the manager (services, price lists, shifts, stages, public views, WhatsApp templates, hierarchy, caller IDs) asks for the capability; ERPNext is the agency's. `DEL_CORE`: the core documents the manager writes (email templates, assignment rules, imports) get a role's rule, narrowed by the capability |
| `crm/permissions/condizioni.py` | Guided conditions to Python, pure: for anybody but the agency the server writes assignment-rule and SLA conditions itself |
| `frontend/src/router.js`, `utils/impostazioni.js` | Each route declares `meta.richiede`, each page of the settings its `condition` in the menu: hidden from the menu means closed at its address too |

Code asks for a capability (`puo("fatture.emetti")`, `@richiede(...)`), never for a
role name; the frontend asks `usersStore().puo(...)`. A new module registers its
roles, levels and capabilities from its own `registra()`. A new document that
belongs to a person follows them with `org_hierarchy`'s bricks (one condition for
list and record); a new settings document gets its capability in `documenti.SCRITTURA`
and the hook in `hooks.py`. On a settings page, what is the agency's (keys, endpoints,
webhook secrets, a tag for a website) sits on permlevel 1, System Manager's only, the
screen shows it on `puo('tecnico.integrazioni')` and its methods ask for that.
People's email and phone carry Frappe's `mask`: `frappe.get_list` and the client
get masked values for Marketing; code that sends reads `crm.utils.stored_value`.
A record's page asks `useDocument(...).canWrite` (from `crm.api.doc.get_doc_permissions`,
which asks the controllers too) before offering a write; reading and writing are
separate capabilities (`conversazioni.vedi`/`.usa`, `note.vedi`/`.scrivi`).

### The settings (docs/progetto-ghl/31)
| File | Role |
|---|---|
| `frontend/src/utils/impostazioni.js` | The menu as data: groups (your account, the centre, agenda, clients, deals, email, WhatsApp, phone, marketing, invoicing, integrations), their entries, an entry's tabs, who sees each (`condition` on `puo`, `ambito`, `whatsapp`, `verticale`); `menuDi()`, `trova()` (the entry and tab a page's name opens), `pagine()` — tested |
| `frontend/src/components/Settings/Settings.vue`, `SettingsHub.vue` | The modal draws the menu from the data (`PAGINE`, `ICONE` by key); an entry with tabs is one page with its row of tabs, the tab open being `activeSettingsPage` |
| `crm/tests/test_impostazioni.py` | Every page the server or a button names is in the menu |

A new page goes in the group of the part of the work it belongs to, as an entry
or as a tab of an entry that is there: no group of one entry. Its key never
changes (links are built on it); a page that becomes a tab keeps its key, a name
it had before stays as an alias. Its label, its tab and its page's title say the
same words, in the user's language.

### Consents, billing details, linked people (phase 0 of the medical centre project)
| File | Role |
|---|---|
| `crm/moduli/registro.py` | Kinds of consent (each module registers its own), natures, channels, the current state — pure |
| `crm/moduli/consensi.py` | The register: record, withdraw, state, who reads it, the person panel and settings calls |
| `crm/invoicing/engine/anagrafica.py` | What an invoice takes from a fiscal profile and what a confirmed one gives back — pure |
| `crm/invoicing/anagrafica.py` | `CRM Billing Profile`: whose profile an invoice uses (or whoever pays for the client), both directions, the panel calls |
| `crm/persone/legami.py` | Linked people: relations and their inverses, who acts for whom, names compared by their words, age — pure |
| `crm/persone/collegate.py` | `CRM Related Person`: who a booking is for (`trova_per_nome`), the person booked for somebody, who pays / books / represents, the panel calls |

A person's billing details, consents and links follow the person (`org_hierarchy.visible_leads`)
and are deleted with them (`on_trash`); an answer in the register is never edited. A
contact belongs to its owner: a booking finds the owner by email or phone and the
person by name (`find_or_create_person`), so a child booked by a parent gets a record
of their own, linked to the parent, never the parent's record.

### The client area (`crm/area`, the plan's "area" module; the clinic comprises it)
| File | Role |
|---|---|
| `crm/area/accesso.py` + `crm/www/area.py` | The door: invitation (`CRM Area Access`, role "Client Area User"), a code by email, step-up before a download; every call derives the session's people on the server |
| `crm/area/api.py` | Appointments with the booking page's link, cycles, invoices; "Prepare your appointment": the owed forms, opened on `/modulo` with the area's session |
| `crm/area/sezioni.py` | The places other modules add to the area (`registra_sezione`): the plans, the documents given online, the quotes, shown to whom they have something |
| `crm/area/messaggi.py` | The board (`CRM Area Message`): the desk writes administration, the chat passes questions; other kinds come from other modules (`registra_tipo`, the clinic's "Care") with their own readers |
| `crm/area/chat.py` + `chat_regole.py` | The chat about hours and bookings, for any centre: emergency words get 112 before any model, health goes to a person, the rest only from what the centre wrote |
| `crm/area/passkey.py`, `crm/area/avvisi.py` | Passkeys (WebAuthn); news by WhatsApp or SMS besides the email, only to the person's own number that wrote to the centre (`CRM Area Settings`) |
| `frontend/src/area/`, `frontend/vite.area.config.js`, `frontend/area.html` | The area's app, built apart into `/assets/crm/area` (`yarn build:area`, run by `yarn build`); its words in `it.js`, the vertical's first |
| `frontend/src/components/Area/` | The person's "Client area" tab: who enters, the board, the plans |

### Plans and programmes (`crm/piani`, followed in the client area)
| File | Role |
|---|---|
| `crm/piani/regole.py` | Plans without a site: moments and items, the day and the week, one tap, the kinds of plan registered (`registra_tipo`: who writes it by qualification, what it holds, what its screens offer, the "health data" mark) and of item — tested with plain `unittest` |
| `crm/piani/api.py` | Plans on the person's page (`CRM Personal Plan`, `piani.scrivi` / `piani.vedi`): drafts of their author, published to the area, new version or closed; what a module adds (`registra_genere`, `registra_estensione`); health data read through `crm.permissions.sanitari` |
| `crm/piani/programmi_regole.py` + `programmi.py` | Programmes of stages (`CRM Programme`): each stage with its words and maybe a plan (`CRM Personal Plan.programme`), opened at one's own pace (the person in the area, `finish_stage`) or by time (`apri_del_giorno`, daily); a stage that opens publishes its plan with `api.pubblica` |
| `crm/piani/area.py` + `frontend/src/area/pages/Plans.vue`, `Plan.vue`, `components/PlanItem.vue`, `ProgrammeCard.vue` | The plans in the area: the day's moments, one tap an item (`CRM Personal Plan Log`), made up within two days, what is left this week; the programmes stage by stage |
| `crm/piani/librerie.py` + `dataset.py` | The exercises (`CRM Exercise`, `piani.librerie`, Settings > Clients > Libraries): exercises-dataset with its pictures from where the agency hosts them (`CRM Area Settings`, permlevel 1), the imports and their licences (`CRM Library Import`); imported again, numbers update and the centre's words stay |
| `frontend/src/components/Plans/` + `utils/piani.js`, `utils/programmi.js` | The plans card, the editor and reader, an item by its kind, the library search, the programme: what a kind holds and offers comes from the server — tested |

A training and habits are the CRM's own kinds; a module registers its kinds with the
qualifications that write them (the clinic: diets, exercises at home). A plan is
health data by its kind or by its author (with the clinic on, whatever a health
professional writes): the `clinical` mark, read like the clinical record by the rule
the clinic registers, every opening in the access log. Without the clinic nobody
reads a plan with the mark but its author.

### A person's documents (`crm/documenti`, given by hand or online)
| File | Role |
|---|---|
| `crm/documenti/regole.py` | The kinds of document registered (`registra_tipo`: the CRM's signed form, contract, certificate, identity document, photo, other; a module's, maybe health data, maybe made elsewhere, maybe added only with a capability), the days online — tested with plain `unittest` |
| `crm/documenti/api.py` | `CRM Document` on the person's Documents tab: read with `documenti.vedi` and the person, added with `documenti.aggiungi` (the file private, its SHA-256), put right but never given another file, taken away the same day by who added it or with `documenti.togli`; filed from a conversation; what a module adds (`registra_estensione`) |
| `crm/documenti/consegna.py` + `crm/www/documento.*` | Giving one (`CRM Document Delivery`, `documenti.consegna`): by hand to whom, or online with a link by email and a code given another way, `/documento/<link>` (and `/referto/<link>` for the links already sent); a module says when one may not go online and for how many days (`registra_regola`) |
| `crm/documenti/area.py` | The documents given online, in the client area while they are, downloaded after a code |
| `crm/permissions/sanitari.py` | Health data in what the CRM keeps for a person: who reads what carries the `clinical` mark, and what else carries it — the `Lettore` the clinic registers (the dossier; a health professional's) |
| `frontend/src/components/Documents/` | The Documents tab: `DocumentsCard`, `DocumentDialog` (also from a chat message), `DeliverDialog` |

The kinds decide the fields: a module registers its own (the clinic: report, test
result, image, prescription) with the mark of health data and the capability that
adds them (`clinica.archivia`), its fields as customisations (`crm/clinica/custom`),
and its rule on going online. A document with the mark is read like the clinical
record, every listing in the access log; without the clinic only whom it is for and
who added it read it.

### Quotes (`crm/preventivi`, followed to the end by the agenda)
| File | Role |
|---|---|
| `crm/preventivi/regole.py` | A quote without a site: its states, the rows' amounts and sums, the phases, which row an appointment takes, what is checked before it is proposed — tested with plain `unittest` |
| `crm/preventivi/api.py` | `CRM Quote` on the person's Quotes tab: a draft of its author (`preventivi.scrivi`); proposed, read with `preventivi.vedi` and the person, recorded accepted or declined by the author or `preventivi.gestisci` (the desk); a new version, closed half-way; what a module adds to the rows (`registra_estensione`) |
| `crm/preventivi/documento.py` + `templates/preventivo.html` | The quote's PDF, made once when it is proposed, private |
| `crm/preventivi/appuntamenti.py` | `CRM Appointment` doc_events: an appointment of a service still to do takes its row at the price agreed, done when the person came, given back when cancelled |
| `crm/preventivi/pipeline.py` + `CRM Quote Settings` | The "Quotes" pipeline: delivered, won, lost with the reason; which one and how long a quote holds, in Settings > Deals > Pipelines |
| `crm/preventivi/area.py` | The quotes proposed and going on, in the person's area (the Plans page) |
| `frontend/src/components/Quotes/` + `utils/preventivi.js` | The Quotes tab (`QuotesCard`), the editor and reader (`QuoteDialog`: a module's row fields where the server offers them); the same sums as `regole.py` — tested; `area/components/QuoteCard.vue` in the area |

With the clinic on, what a health professional writes carries the mark: a dentist's
care plan is a quote read like the clinical record (and by the desk once proposed),
every opening in the access log.

### New clients (`crm/clienti`)
| File | Role |
|---|---|
| `crm/clienti/regole.py` | Who came, without a site: checked in, an appointment attended, an invoice that sold something (not a credit note), the first fact in time — tested with plain `unittest`; the clinic's rules are built on it |
| `crm/clienti/cliente.py` | The one door, `diventa_cliente`: `CRM Lead.client_since` written once, never in the future; the new clients deal won and "Became Client" (`client_created`) heard by the automations; `recupera()` finds last year's clients and announces nothing; `registra_regole`: a module with rules of its own (the clinic) takes the CRM's place where it is on |
| `crm/clienti/eventi.py` | `CRM Appointment` and `CRM Invoice` doc_events: a booking moves the deal, a check-in, an attended appointment or an invoice makes a client |
| `crm/clienti/pipeline.py` + `CRM Client Settings` | The "New clients" pipeline: which one and the stage after a booking, in Settings > Deals > Pipelines (`NewClientsPipeline.vue`); a vertical names it in its words (`registra_nomi`: the clinic's "New patients") |
| `crm/dashboard/widgets/people.py`, `marketing.py` | "New clients" counts `client_since`, "Cost per new client" divides the ads' spend by the clients they brought; the dashboard's titles in the vertical's words (`verticali.traduttore()`) |

With the clinic on, a client is a patient: its rules decide, `assicura_paziente`
calls `diventa_cliente` from the same moment, and the CRM's words read "New
patients", "Became Patient", "Patient since".

### Verticals (`crm/verticali.py`)
A module of the plan that makes the CRM the software of a trade registers a
`Verticale`: its words over the CRM's (pairs of English strings: the SPA gets them
translated in its boot, the area in its own, the server asks `parola()`), and the
places of the base it hides because it shows its own. The CRM underneath speaks
neutral words (clients, appointments, the client area); with the clinic on it says
patients, visits, the patient area, everywhere. A new place of the base that names
the people adds its pair to the vertical's words (`crm/clinica/parole.py`).

### The clinic (`crm/clinica`, switched on by the plan's "clinica" module)
| File | Role |
|---|---|
| `crm/clinica/__init__.py` | `registra()`: plan module, Medical Director level, capabilities, clinic consents |
| `crm/clinica/regole.py` | How a person becomes a patient — pure, tested |
| `crm/clinica/paziente.py` | `assicura_paziente` (the one door), the recovery over old data, the patient panel calls |
| `crm/clinica/cartella.py` | The clinical record: who reads it, the Clinic tab calls, the access log, the timeline padlock |
| `crm/clinica/base.py` | `DocumentoClinico`: every clinical DocType inherits it (rule 1) |
| `crm/clinica/referto.py` + `templates/referto.html` | A visit written on a clinical sheet, signed: its report as PDF/A, made once, private, with its SHA-256 |
| `crm/clinica/piani_regole.py` | The clinic's kinds on the CRM's plans (`crm.piani.regole`): a menu, an exchange diet, exercises at home, who writes which by qualification; a food and a food group; the nutrients and the shopping list — pure, tested with plain `unittest` |
| `crm/clinica/piani.py` + `crm/clinica/custom/` | The clinic's plans on `crm.piani`: its kinds of item, what a diet keeps (the calories shown, a menu's targets: custom fields on `CRM Personal Plan`), who reads health data (the dossier) and what is health data by its author (a health professional's plan), the foods (`Clinic Food`), the shopping list |
| `crm/clinica/area/piani.py`, `crm/clinica/parole.py` | The clinic's places in the client area (a diet's shopping list; registered with `crm.area.sezioni`) and its words over the CRM's: patients, the patient area, the visit to prepare (`crm.verticali`) |
| `crm/clinica/documenti.py` + `crm/clinica/custom/crm_document.json` | The clinic's documents on `crm.documenti`: its kinds (health data, added with `clinica.archivia`, a practitioner's), who reads one ("only me", a discipline), obscured, never online, a signed visit's report (`dal_referto`); online only with the `online_reports` consent, 45 days |

### The assistant (`crm/assistente`, its own plan module)
| File | Role |
|---|---|
| `crm/assistente/__init__.py` | `registra()`: plan module, capabilities, `registra_funzione()` — each function says who uses it and who reads its events |
| `crm/assistente/regole.py` | Pure: the purpose sentence, the draft's mark, JSON out of a model's answer, the difference, `pronto()` — tested with plain `unittest` |
| `crm/assistente/modello.py` | The adapter (Anthropic Messages, OpenAI compatible), `chiedi()` writes a `CRM AI Event` whatever happens, `accetta`/`scarta`, the register's calls |
| `crm/assistente/modulo_di_carta.py` + `Settings/Forms/PaperFormDialog.vue` | A paper PDF into a draft template: the engine's components in the prompt, its rules on the proposal |
| `frontend/src/components/Settings/AssistantSettings.vue` | Where the model runs (agency, permlevel 1), which functions (manager), the register |
| `crm/clinica/assistente.py`, `dettatura.py`, `riassunto.py` + `components/Clinic/AssistantDraftDialog.vue`, `DictationDialog.vue`, `SummaryDialog.vue` | The assistant in the clinic, with the patient's `ai_assistant` consent and nothing about who they are: a letter or instructions from one's signed note, a visit from dictation (medicines, allergies, doses ticked one by one), a summary citing its sources; the clinical events are the medical director's |

The assistant writes only what was written or said, saves nothing by itself, and
every request stays in the register: a new function registers with
`registra_funzione`, asks with `modello.chiedi`, and records what a person made of
the draft with `modello.accetta`.
| `crm/clinica/dossier.py` | Who reads what the others wrote: the dossier (consent and care), obscured episodes, "my discipline", the opening out of the care team with a reason (`Clinic Access Grant`, `crm_people_in_care`) |
| `crm/clinica/sintesi.py` | The patient's summary (`Clinic Summary Value`): answers of signed forms and sheets proposed, a practitioner confirms, discards or writes by hand |
| `frontend/src/components/Clinic/ClinicSummary.vue`, `ClinicArea.vue` | The summary card; the Clinic tab's visits, free or on a clinical sheet |
| `frontend/src/components/Clinic/ObscureDialog.vue`, `OutOfCareDialog.vue` | Obscuring or revealing an episode; opening a record out of one's care (People page) |
| `crm/clinica/pipeline.py` | Phase 1's first seam: the CRM's two pipelines where the clinic is switched on, the new clients one named "New patients" (`NUOVI_PAZIENTI`) |
| `crm/clinica/menu.py` | The nutritionist's menu: targets on the plan, nutrients from the tables (`piani_regole.nutrienti`, same cases as `utils/piani.js` in `tests/casi_nutrienti.json`), recipes proposed by the assistant, kept only as library foods |
| `piani_regole.spesa` + `ShoppingListDialog.vue`, `frontend/src/area/pages/PlanShopping.vue` | The shopping list of a diet: grams summed on the server over the days asked (times a week, the plan's period), rounded up in the browser; in the CRM to copy for the patient, in the area with ticks kept on the phone |
| `crm/clinica/tabelle.py` + `crm/clinica/librerie.py` | The foods (`piani.librerie`): a food table read on the server (CIQUAL, BDA-IEO and CREA with the licence declared, any sheet in their shape), its columns and categories checked before import, energy from the EU factors when missing; imported again, numbers update and the centre's words stay |
| `frontend/src/components/Settings/Clinic/` + `frontend/src/utils/librerie.js` | Settings > Clients > Libraries, the Foods tab: the list, correcting a food, the import of a table; the exercises' page is the CRM's (`Settings/Plans/`) |
| `crm/clinica/cure_regole.py` | The teeth without a site: FDI teeth and arches, surfaces, the chart's conditions, the teeth on a quote's rows (`valida_denti`) — tested with plain `unittest` |
| `crm/clinica/cure.py` + `crm/clinica/custom/crm_quote*.json` | The odontogram (`Clinic Dental Chart`, `cure.scrivi` and a dentist's qualification); a care plan is a quote of the CRM's: the tooth and its surfaces on its rows, only by a dentist, read as "Tooth 36 · OM" (`preventivi.registra_estensione`) |
| `frontend/src/components/Clinic/DentalCard.vue`, `DentalChart.vue` + `utils/cure.js` | The Clinic tab's teeth and the chart; the same rules as `cure_regole.py` — tested |

### The brand
| File | Role |
|---|---|
| `brand/` | The logo, the design system (`tokens.css`), video, presentation, ads — `brand/README.md` |
| `crm/marchio.py` | The brand of the vertical that is on (`Marchio`, `registra_marchio`, `attivo()`; `BASE` without one): `nome()`, `con_nome()`, `colori()`, `accento()`, `per_il_boot()`, `per_le_pagine()` (with the centre's mark: `centre_logo`, `centre_logo_shape`, `centre_name`), `contesto()` (every web page), `manifest()` (the phone's). `forma_di()` measures a logo of the site's ("wide" on its own, "square" beside the name). `applica()` writes it into Website/System/Navbar Settings, the desk's workspace and icons (install, patch, `piano_aggiornato` when the plan changes), `boot()` names the apps in the desk, `nome_scelto()` keeps the software's name from passing for a centre's |
| `crm/verticali.py` | A vertical names its brand (`Verticale.marchio`): the clinic wears DottorCloud |
| `crm/hooks.py` (top) | `app_title`, `app_logo_url` (fallbacks), `update_website_context` (`marchio.contesto`), `extend_bootinfo`, the apps screen |
| `frontend/src/utils/marchio.js`, `marchio.css` | The brand in the SPA and the area: `marchio()` from the boot, `conMarchio()` in `__()`, `indossa()` (colours as `--brand*`, favicon, icons, title); the centre's mark: `formaDelLogo()`, `misureSvg()`, `iniziali()`, `nomeDelCentro()`; primary buttons, switches and ticks in its colour — tested |
| `frontend/src/components/CentreTile.vue`, `composables/formaDelLogo.js` | The centre's tile (a square logo, the initials, the product's icon) in the client area and the previews; a logo's shape, from the server or measured |
| `frontend/src/components/UserDropdown.vue`, `Icons/CRMLogo.vue`, `Modals/AboutModal.vue`, `Layouts/GettingStartedPanel.vue` | The product's logo heading the sidebar (its icon when collapsed), the About with the licence's notices, getting started without a help centre |
| `crm/templates/includes/marchio_*.html` | The public pages' head (favicon, phone icon), accent, the centre's mark at the top (`marchio_segni`) and the product's signature at the foot (`marchio_piede`) |
| `crm/public/images/` (`dottorcloud-*.svg`, `favicon.png`, `amministrazione.svg`), `crm/public/manifest/` | The icon, the logos, the favicon, the desk's tools; the phone's icons and splash screens, made from `brand/logo` |
| `crm/locale/en.po` | The framework's own words that name it, in English with the product's name (`marchio.PAROLE_DEL_FRAMEWORK`) |

One mark per place, never two side by side. The product's brand - the
vertical's - heads the sidebar (its horizontal logo, as the design system wants,
`brand/design-system/espresso`) and is the tab's (title, favicon), the framework's
screens', the emails', the PDFs' producer's, the phone's manifest's; its colours
are everywhere. Where a person deals with the centre - the client area, the public
pages - the centre's mark leads (Settings > The centre > General > Name & logo, the
booking page's own logo): its logo as it is drawn (wide on its own, square beside
its name), else its name; the product signs at the foot ("Powered by {brand}"), and
stands in at the top only for a centre with neither a logo nor a name. A sentence that names the product says `{brand}`: `__()`
fills it in the browser, `con_nome(_("…"))` on the server (before any `.format()`).
A public page's title names the centre (`FCRM Settings.brand_name`) beside the
product's name: `nome_scelto()` treats every brand's name as no name of the centre's.

### The desk's day
| File | Role |
|---|---|
| `crm/scheduling/esiti.py` | How an appointment went: check-in (`Arrived`, `arrived_at`), who may mark (`agenda.presenze`), visit and invoice close it, the end-of-day "did they come?" |
| `crm/api/oggi.py` + `frontend/src/pages/Today.vue` | The Today page: arrivals, waiting room, days left open, what is left to invoice |
| `frontend/src/utils/oggi.js` | Pure: waiting time, next outcomes, summary, days — tested |

An automation for marketing asks `marketing_consent`: `engine.enroll` skips whoever
did not agree (an enrollment `Skipped`, once, never counted as having been through
it) and a message step re-checks before sending. Recalls pick people by
`CRM Lead.last_visit`/`last_service`, which the agenda keeps. A module adds its own
dashboard template with `crm.dashboard.templates.registra` (`requires` features).

Nothing outside `crm/clinica` imports it except `crm/registrazione.py`
(`tests/test_confine.py`); it hooks on through doc_events, `crm_timeline_gatherers`
and the registries (`clienti.registra_regole`, dashboard features and templates).

`crm/clinica` keeps only what exists for health data or medical practice: the
patient, the record and reports, dossier and obscuring, the summary, the dental
chart, diets and rehabilitation. What a beauty centre or a gym would use the same
way belongs in the CRM, and the clinic registers its rules on it, with the "health
data" mark deciding who reads (docs/gestionale-medico/design.md, "Tre strati",
30/09/2026). The client area moved there first (`crm/area`), then plans,
programmes and exercises (`crm/piani`), a person's documents (`crm/documenti`),
quotes (`crm/preventivi`), the new clients pipeline (`crm/clienti`) and one forms
builder, with the operator's sheet and the website's forms (`crm/moduli/sito.py`).

A module moved to the CRM keeps its data through two patches: before the sync its
DocTypes are renamed (`*_are_the_crms`), after it what they held is put back
(`*_keep_their_health_data`, which reloads its DocTypes first and never skips in
silence). Before a migrate syncs anything, `crm/migrazione.py` rebuilds the map of
the modules from `modules.txt`: the cache may hold the previous release's, and a
new module would not sync.

## Mobile

`isMobileView` (< 768px) picks the phone components, so what changes on a phone
uses `max-md:` — not `sm:`, which leaves 640–768px half desktop.

- Nothing only on hover: add `[@media(hover:none)]:opacity-100`, or reveal on focus.
- Small controls get `.touch-target` (an invisible ring on touch screens); frappe-ui
  switches already have it. Long dialogs put `.dialog-footer` on their actions
  (frappe-ui's own `#actions` row gets the same treatment in `index.css`).
- Titles have no fixed height; a header stacks title, description, then actions.
- In a row the words get `min-w-0`, the control `shrink-0`; descriptions wrap.
- Three or four fields per row become one (or two); tables keep a minimum column
  width and scroll sideways.

---

## Tests

```bash
cd frontend
yarn test:run      # single run
yarn test          # watch mode
```

- **785 tests · ~15s** — all must pass before committing
- Location: `frontend/tests/unit/`
- Only pure utility functions are unit-tested (no Vue component tests yet)
- Add tests in `tests/unit/` when adding pure logic to `src/utils/`

---

## Commit style

```
feat: short description
fix: short description
refactor: short description
test: short description
docs: short description
```

Multiple logical commits per PR — one commit per coherent change, not one giant commit.
Pre-commit hooks run prettier + eslint + oxlint automatically. If they modify a file,
`git add` the file again and re-commit.

---

## Docs structure

```
PLAN.md          — future only (phases 3B, 4, 5, 6)
SPEC.md          — stable contracts
ARCHIVE.md       — completed phases + decision rationale
feats/           — user-facing feature docs
archives/        — old docs preserved verbatim
```

When a phase completes: move its spec from PLAN.md to ARCHIVE.md, update SPEC.md if
the API surface changed.
