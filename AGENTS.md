# CRM — Project Context

## What this project is

Frappe CRM frontend. Vue 3 + frappe-ui. The backend is Frappe Python. Scripts in
`frontend/` only; Python in `crm/` (Frappe app). No build step for Form Scripts —
they run as evaluated strings in the browser.

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
| `docs/prenotazioni/` | User guide + platform API research |

---

### Forms to fill and sign (crm/moduli, docs/gestionale-medico phase 2)
| File | Role |
|---|---|
| `crm/moduli/schema.py` | Pure: what a template schema may hold, conditions, formulas, scores, `valuta()`, `pulisci()`, `valida_schema()`, SHA-256 |
| `frontend/src/utils/moduli.js` | The same rules in the browser, plus the builder's helpers — tested on the same cases |
| `crm/moduli/tests/casi_schema.json` | The cases both sides must agree on: change one side, run both suites |
| `crm/moduli/modelli.py` | Drafts (`CRM Form Template`) and immutable versions (`CRM Form Template Version`), consents' words frozen at publish; the uses (a module registers its own: the clinic's "Clinical sheet") and the summary's lines |
| `frontend/src/components/Moduli/` | `FormRenderer` + `FormFieldInput`: draw and fill a schema |
| `frontend/src/components/Settings/Forms/Template*.vue` | The builder, in Settings > Forms next to the web forms |
| `crm/moduli/compilazioni.py` | A person's forms: start, save half-way, sign (checks, strokes, submit, PDF, consents) |
| `crm/moduli/pdf.py` + `templates/modulo_firmato.html` | The signed form's PDF/A with its evidence page, made once |
| `crm/moduli/sigillo.py` | The centre's PAdES seal and RFC 3161 time stamp (pyHanko), before the fingerprint; the agency's Seal page |
| `crm/moduli/traccia.py` | `CRM Audit Log`: a document's events, each chained to the one before |
| `frontend/src/pages/FormFill.vue`, `components/Moduli/FormsArea.vue`, `SignaturePad.vue` | Filling and signing, the person's Forms tab, the stroke as a PNG |
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
| `frontend/src/router.js`, `components/Settings/Settings.vue` | Each route declares `meta.richiede`, each settings page its `condition`: hidden from the menu means closed at its address too |

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

### The clinic (`crm/clinica`, switched on by the plan's "clinica" module)
| File | Role |
|---|---|
| `crm/clinica/__init__.py` | `registra()`: plan module, Medical Director level, capabilities, clinic consents |
| `crm/clinica/regole.py` | How a person becomes a patient — pure, tested |
| `crm/clinica/paziente.py` | `assicura_paziente` (the one door), the recovery over old data, the patient panel calls |
| `crm/clinica/cartella.py` | The clinical record: who reads it, the Clinic tab calls, the access log, the timeline padlock |
| `crm/clinica/base.py` | `DocumentoClinico`: every clinical DocType inherits it (rule 1) |
| `crm/clinica/referto.py` + `templates/referto.html` | A visit written on a clinical sheet, signed: its report as PDF/A, made once, private, with its SHA-256 |
| `crm/clinica/area/` (`accesso.py`, `api.py`) + `crm/www/area.py` | The patient area: invitation (`Clinic Area Access`), the door by email code, step-up before a download; every call derives the session's people on the server |
| `crm/clinica/area/api.py` (`get_forms`, `fill_forms`) | "Prepare your visit": the owed forms, opened on `/modulo` with the area's session; who signs is who a link by email would go to |
| `crm/clinica/area/messaggi.py` + `components/Clinic/AreaMessagesCard.vue` | The centre's board in the area (`Clinic Message`): the desk writes administration, a practitioner the care (read like a visit); the email says only that there is news |
| `crm/clinica/piani_regole.py` | Plans without a site: the five kinds, who writes which by qualification, what each holds, the day and the week — pure, tested with plain `unittest` |
| `crm/clinica/piani.py` | Plans on the person's page (`Clinic Plan`, `piani.scrivi`): drafts of their author, published to the area, new version or closed; the libraries (`Clinic Food`, `Clinic Exercise`) |
| `frontend/src/components/Clinic/ClinicPlans.vue`, `PlanDialog.vue`, `PlanItemEditor.vue`, `LibraryPicker.vue` + `frontend/src/utils/piani.js` | The plans card, the editor and reader, an item by its kind, the library search; the same rules as `piani_regole.py` — tested |
| `crm/clinica/area/piani.py` + `frontend/src/area/pages/Plans.vue`, `Plan.vue`, `components/PlanItem.vue` | The plans in the area: the day's moments, one tap an item (`Clinic Plan Log`), made up within two days, what is left this week |

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
| `frontend/src/area/`, `frontend/vite.area.config.js`, `frontend/area.html` | The patient area app, built apart into `/assets/crm/area` (`yarn build:area`, run by `yarn build`); its words in `it.js` |
| `crm/clinica/consegna.py` + `crm/www/referto.*` | Giving a report: by hand, or online 45 days with the consent; the link by email, the code another way; `/referto/<link>` opens it (`Clinic Report Delivery`) |
| `crm/clinica/dossier.py` | Who reads what the others wrote: the dossier (consent and care), obscured episodes, "my discipline", the opening out of the care team with a reason (`Clinic Access Grant`, `crm_people_in_care`) |
| `crm/clinica/archivio.py` | The clinical archive (`Clinic Document`): uploads, a signed visit's report, a WhatsApp file; read like the record, removed the same day or by the director, every listing and download in the access log |
| `crm/clinica/sintesi.py` | The patient's summary (`Clinic Summary Value`): answers of signed forms and sheets proposed, a practitioner confirms, discards or writes by hand |
| `frontend/src/components/Clinic/ClinicSummary.vue`, `ClinicArea.vue` | The summary card; the Clinic tab's visits, free or on a clinical sheet |
| `frontend/src/components/Clinic/ClinicArchive.vue`, `ClinicDocumentDialog.vue` | The archive card; adding or putting right a document, also from a chat message |
| `frontend/src/components/Clinic/ObscureDialog.vue`, `OutOfCareDialog.vue` | Obscuring or revealing an episode; opening a record out of one's care (People page) |
| `frontend/src/components/Clinic/DeliverDialog.vue` | Giving a document to the patient from the archive: by hand, or online with the code |
| `frontend/src/components/Clinic/AreaAccessCard.vue` | Who enters the person's area, opening and closing it |
| `crm/clinica/pipeline.py` | Phase 1's first seam: the two pipelines, a booking moves the new patients deal, becoming a patient wins it, "Became Patient" |
| `crm/clinica/menu.py` | The nutritionist's menu: targets on the plan, nutrients from the tables (`piani_regole.nutrienti`, same cases as `utils/piani.js` in `tests/casi_nutrienti.json`), recipes proposed by the assistant, kept only as library foods |
| `crm/clinica/programmi_regole.py` + `crm/clinica/programmi.py` | Programmes of stages (`Clinic Programme`): each stage with its words and maybe a plan (`Clinic Plan.programme`), opened at one's own pace (the patient in the area, `finish_stage`) or by time (`apri_del_giorno`, daily); a stage that opens publishes its plan with `piani.pubblica` |
| `frontend/src/components/Clinic/ProgrammeDialog.vue`, `frontend/src/area/components/ProgrammeCard.vue` + `frontend/src/utils/programmi.js` | Writing and reading a programme in the plans card; the programme in the area's Plans page |
| `piani_regole.spesa` + `ShoppingListDialog.vue`, `frontend/src/area/pages/PlanShopping.vue` | The shopping list of a diet: grams summed on the server over the days asked (times a week, the plan's period), rounded up in the browser; in the CRM to copy for the patient, in the area with ticks kept on the phone |
| `crm/clinica/tabelle.py` + `crm/clinica/librerie.py` | The libraries (`piani.librerie`): a food table read on the server (CIQUAL, BDA-IEO and CREA with the licence declared, any sheet in their shape), its columns and categories checked before import, energy from the EU factors when missing; exercises-dataset with its pictures from where the agency hosts them; imported again, numbers update and the centre's words stay |
| `frontend/src/components/Settings/Clinic/` + `frontend/src/utils/librerie.js` | Settings > Clinic > Libraries: the lists, correcting a food or an exercise, the import of a table and of the exercises |
| `crm/clinica/area/chat.py` + `chat_regole.py` | The patients' chat: emergency words get 112 before any model, health is passed to the desk as a "Question" on the board, the rest answered only from the centre's hours, closures and FAQ |
| `crm/clinica/area/passkey.py` + `frontend/src/area/passkey.js` | The patient area's passkeys (WebAuthn, py_webauthn): added from inside after a code, discoverable, user verification, same door as the code |
| `crm/clinica/area/avvisi.py` | News in the area by WhatsApp or SMS besides the email: same words, only to the person's number that wrote to the centre, once every two hours |
| `crm/clinica/widgets.py` | New patients, cost per new patient (registered with the "clinic" feature) |

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
and the registries (`engine.registra_evento`, dashboard features and widgets).

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

- **757 tests · ~15s** — all must pass before committing
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
