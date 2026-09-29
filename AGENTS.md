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
| `docs/prenotazioni/` | User guide + platform API research |

---

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
| `crm/clinica/pipeline.py` | Phase 1's first seam: the two pipelines, a booking moves the new patients deal, becoming a patient wins it, "Became Patient" |
| `crm/clinica/widgets.py` | New patients, cost per new patient (registered with the "clinic" feature) |

### The desk's day
| File | Role |
|---|---|
| `crm/scheduling/esiti.py` | How an appointment went: check-in (`Arrived`, `arrived_at`), who may mark (`agenda.presenze`), visit and invoice close it, the end-of-day "did they come?" |
| `crm/api/oggi.py` + `frontend/src/pages/Today.vue` | The Today page: arrivals, waiting room, days left open, what is left to invoice |
| `frontend/src/utils/oggi.js` | Pure: waiting time, next outcomes, summary, days — tested |

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

- **578 tests · ~11s** — all must pass before committing
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
