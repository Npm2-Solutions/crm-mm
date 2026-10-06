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

DottorCloud sends nothing about its use to anybody: frappe-ui's telemetry plugin
is not installed (the `capture()` calls the original project left in components
do nothing) and the framework's is switched off at install and every migrate
(`crm/telemetria.py`). Nothing new calls `capture`.

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
| How DottorCloud looks: tokens, the brand's marks, components | [brand/design-system/espresso](./brand/design-system/espresso/README.md) (applied in `frontend/src/espresso.css`) |

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
| `crm/dashboard/widgets/` | The widget catalogue, one file per module — `@widget(id, category, kind, requires=…)`; who reads a widget is the capability of its category (`registry.READERS`: doc 30's numbers) or its own `reader`, a template's `reader` says whom it is for (`store.reads`, `store.offers`) |
| `crm/api/dashboard.py` | Dashboards list/layout/catalogue, widget data in one request, save/reset |
| `frontend/src/pages/Dashboard.vue` + `components/Dashboard/` | Switcher, period, builder (grid + widget library), the widget kinds |
| `frontend/src/utils/dashboard.js`, `dashboardCharts.js` | Pure: periods, formats, grid, catalogue search, palette, ECharts options — tested |
| `docs/progetto-ghl/28-dashboard.md` | What it does and why |

### The agenda's screen (docs/progetto-ghl/56)
| File | Role |
|---|---|
| `frontend/src/utils/agenda.js` | Pure: an hour's height (`ALTEZZE`), the whole lines a block holds (`righeDelBlocco`, `formaDelBlocco`), what it says, the person first (`testoDelBlocco`, `segniDelBlocco`, `paroleDelBlocco`), the colour by service or by state, a column's hours and where it is closed (`orarioDelGiorno`, `chiusure`), the hours a grid shows, a day's columns (who works or has something) and a week's days, the periods and their headings, what each column and each day of the month draws (`cosePerColonna`, `cosePerGiorno`) — tested |
| `frontend/src/pages/Calendar.vue` + `components/Calendar/GrigliaAgenda.vue`, `BloccoAgenda.vue`, `MeseAgenda.vue`, `ChiNellAgenda.vue`, `FiltriAgenda.vue`, `VistaAgenda.vue`, `VistaDelTelefono.vue` | One bar for every view (‹ Today › and the date, Day · Week · Month, whose, Filters, View; on a phone one row of keys of one height: the view's switch, «All», Filters and View as icons); the day one column per professional or room that works it, at least `--col-min` wide, scrolling sideways under its headers while the hours stay; a week of one of them; the month; what the reader chose kept in their browser (`crmAgenda`: the view, whose day and month, whose week, columns, height, colours), the centre's (opening view, grid step: `FCRM Settings.calendar_grid_step`) in Settings > Agenda > Agenda & reminders; who books only for themselves (`ambito('agenda.prenota') === 'suoi'`) books in their own column (`prenotabile`), who reads only their own agenda opens on it |
| `crm/api/appointments.py` `get_calendar(with_hours=1)` | For a day or a week, each professional's and room's open windows in the centre's minutes (`orari_di`, from the engine's own shifts, overrides and holidays; `null` where no hours were set) and the professionals' events as busy time (`engaged`: when, never what) |

An appointment in the agenda reads its person first, then what and where, in whole
lines (`righeDelBlocco`), never half of one; a mark is an icon with its words,
never a colour alone. A view draws its columns from `cosePerColonna`; what a column
does not work is greyed from the server's hours, never guessed in the browser.
A column offers a new appointment only where the reader may book it: a
colleague's column takes no tap and no drop from a practitioner, as the server
would refuse it.

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
| `crm/scheduling/abbonamenti_regole.py` + `abbonamenti.py` | Subscriptions (`CRM Subscription Type`, `CRM Subscription`, `agenda.abbonamenti`): a type sold from a day, its terms copied on the subscription; a person's place in a comprised service uses an entry of their own by itself (the participant's `subscription`: in a class each person uses theirs, the others pay; `aggancia` and `prezzo` in the appointment's `validate`, after its cycle) while its week or month has one left, and costs them nothing; a suspension moves the end; the daily `ogni_giorno` invoices the instalments due (`invoicing.api.issue_from_subscription`, issued where the type says so), reminds of the end, renews. The rules pure, tested with plain `unittest` |
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
| `crm/fcrm/doctype/crm_plan/` | The centre's plan: the second key of every capability; the listino's numbers (`AMBULATORI` by size, `CREDITI_SDI`, included signatures) and `crediti_sdi()`. The phone counts nothing: a year's fee, calls and SMS paid to Twilio by whoever owns the account |
| `crm/api/plan.py` + `Settings/PlanSettings.vue`, `utils/funzionalita.js` | Settings > The centre > Features (doc 36): what the product comprises (`compresi()`: the base, the vertical's module and what it comprises), the extras (invoicing, marketing, phone, assistant, advanced signature) and their trial, the size in rooms and the usage the agency bills; each module registers the settings pages it is set up from (`ModuloPiano.impostazioni`) |
| `crm/permissions/org_hierarchy.py` | Which people and deals a user sees: the scope of `persone.vedi` / `trattative.vedi` (centre, team, own + in care); calls, notes, tasks follow them |
| `crm/permissions/seguono.py` | What follows the person: appointments (`agenda.vedi`, busy time for the rest), WhatsApp, SMS, tracking, old bookings, the address book (an entry is its owner's, or comes with a deal one sees; nobody's is the centre's) |
| `crm/permissions/documenti.py` | Writing what the screens keep for the manager (services, price lists, shifts, stages, public views, WhatsApp templates, hierarchy, caller IDs) asks for the capability. `DEL_CORE`: the core documents the manager writes (email templates, assignment rules, imports) get a role's rule, narrowed by the capability |
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
A company is written like a person (`persone.scrivi`, deleted with `persone.elimina`).
A record's page that does not open says why in words (`utils/schedaChiusa.js`),
never the server's sentence nor the record's code.
People's email and phone carry Frappe's `mask`: `frappe.get_list` and the client
get masked values for Marketing; code that sends reads `crm.utils.stored_value`.
A record's page asks `useDocument(...).canWrite` (from `crm.api.doc.get_doc_permissions`,
which asks the controllers too) before offering a write; reading and writing are
separate capabilities (`conversazioni.vedi`/`.usa`, `note.vedi`/`.scrivi`).

### The main menu (docs/progetto-ghl/34)
| File | Role |
|---|---|
| `frontend/src/utils/menu.js` | The menu as data: the day's group (no label, the dashboard last where the day opens on the reception desk), then marketing; each entry its page, icon and `condition` on the session; the pages that live together (`SORELLE`: the reception desk, the agenda and the waiting list; People and the companies; Tasks and the notes); `menuDi()`, `paginaSorelle()`, `barraDelTelefono()` (the phone's four places) — tested |
| `frontend/src/components/Layouts/AppSidebar.vue`, `Mobile/MobileBottomNav.vue`, `Icons/menu.js`, `ViewBreadcrumbs.vue` | The sidebar draws the menu with the design system's group labels, the phone's bar takes its places; the same icons; a page with sisters draws their switch in its header (on a phone, three sisters are the title's menu), and lights the entry it lives in (`utils/navigation.js`) |
| `frontend/src/components/Telephony/PhoneButton.vue`, `PhonePanel.vue` + `crm/telephony/pannello.py`, `utils/telefono.js` | The phone at the top right of every page where a telephony is on: a number or a name, the keypad, the last calls, the callbacks owed, the register and the round of calls (`Dialer`) — never menu entries |

A new page that people open every day goes in the menu's data, in the group of its
work, with the capability that opens it; never straight into the sidebar. A page
that belongs with another goes in `SORELLE`, not in the menu; an action (calling)
is never a menu entry.

### The phone's own screens (docs/progetto-ghl/29, second part)
| File | Role |
|---|---|
| `crm/api/sul_telefono.py` | One call per list a phone opens every day, through `frappe.get_list`'s permissions: people by name, email or a number written any way (the last nine digits compared), with the next appointment for whoever reads the agenda; open tasks, one's own or everybody's; a pipeline's stages with their counts and a stage's deals; contacts; companies with their deals; the register of calls by a name or a number; notes by their title or words, their first words in plain text — tested in `crm/tests/test_sul_telefono.py` |
| `frontend/src/components/Mobile/` | `ElencoPersone`, `ElencoContatti`, `ElencoAziende`, `ElencoChiamate`, `ElencoNote`, `ElencoCose`, `TrattativePerFase` (in place of the desk's list and kanban), `AgendaDelGiorno` (the agenda opens on the day as a list, the hours' grid one choice away), `SchedeDelTelefono` (a record's everyday tabs in a short bar, the rest behind More), `PulsanteAggiungi` (the page's «+»), `DescrizioneRipiegata` (a tab's explaining line, two lines and «Show more») |
| `frontend/src/pages/Altro.vue` + `composables/vociAccount.js`, `visteSalvate.js` | The phone's «More» page (`/altro`): the profile, the notifications, the menu entries the bar has no room for, the saved views, the first steps, the account's entries the sidebar's dropdown draws too; the card that puts the app on the home screen (`Mobile/InstallaApp.vue`, `utils/installa.js`: the browser's offer on Android, Safari's two taps on an iPhone, nothing once installed; the client area's own on its home, `area/components/InstallCard.vue`) |
| `frontend/src/telefono.css` | What every screen shares on a phone, found by frappe-ui's markup: a dialog is a sheet from the bottom (grabber, title and actions that stay), a menu or a select's list a sheet of 48px rows, a field 16px and 40px tall (iOS zooms under 16px), small controls a touch ring, a form's full-width action 44px, a toast above the bar |
| `frontend/src/utils/sulTelefono.js` | Pure: a person's line, the tasks by when they are due, the stage a board opens on, a deal's value, the week, the day in order, where now falls — tested |

### Notifications (docs/progetto-ghl/43)
| File | Role |
|---|---|
| `crm/notifiche/avvisi.py` | `avvisa()`: the one door every notification comes in by (mentions, assignments, tasks, WhatsApp, SMS, the agenda, the client area, invoicing, automations, Twilio's answer on a new number's documents, a message on the answering service); the same one unread is not written twice, a person's messages add to the unread one ("3 WhatsApp messages from…"). A person's message (WhatsApp, SMS, email) reaches `chi_segue()`: whoever the person or deal is assigned to, else its owner, else the desk - everyone of the centre who reads conversations and may open the person, never the agency -; one's own mailbox tells only them |
| `crm/notifiche/regole.py` | The sentences (English, in the catalogue), a sentence with its names in bold, the words of the ones written before and the sentence they said (`frase_di_prima`, which the patch `the_old_notifications_name_the_person` gave them), the kind — pure, tested with plain `unittest` (every sentence in `it.po` with the same places) |
| `crm/notifiche/api.py` | The panel's page with the unread count, where each row opens (decided here: the person or deal on the message, a task with nobody behind it in the tasks `?open=`, a message left by an unknown number in the calls `?open=`, a received invoice `?ricevuta=`, a page of the settings), the message's first words where the reader may read them; read, all read, unread again in one query and one signal |
| `frontend/src/components/Notifications/`, `Notifications.vue`, `pages/MobileNotification.vue`, `stores/notifications.js`, `composables/notifiche.js` + `utils/notifiche.js` | The panel and the phone's page on one list (days, the kind's mark, the dot), listened to once per layout, the brand's toast when one arrives; the look and the days tested |
| `crm/notifiche/spinta.py` + `spinta_regole.py`, `spinta_sw.js`, `CRM Push Subscription` | On the phone and the computer (Web Push): each device turned on in Settings > Your account > Notifications (an iPhone only as the app on the home screen) keeps how to reach it, its person's own; every notification `avvisa()` writes goes to it in a job, encrypted for that browser (RFC 8291) and signed with the site's key (VAPID, in `FCRM Settings`), only to a browser maker's push service (`SERVIZI`), never about the demo; the kinds by group as the email's, all on; delivered, no email as well; a device gone is forgotten. The service worker over `/crm` only shows and opens, served from `/api/method` with `Service-Worker-Allowed`: touched, DottorCloud comes forward and is told where to go (`main.js` answers on the message's port); a page that does not answer (asleep, an old version) is loaded there, none open a new window — `spinta_regole` tested on RFC 8291's own example |
| `frontend/src/utils/spinta.js`, `composables/spinta.js`, `Settings/NotificationsSettings.vue`, `Mobile/NotificheSulTelefono.vue` | What this device can do in words (`statoDelDispositivo`), turning on and off, the test, the devices, the «Devices» column; synced once the app is idle where permission was given; a touched notification opens its page (`?notifica=` marks it read in the router) — the pure part tested |

A module tells somebody something with `avvisa()`: a sentence of `regole` (a new
one goes in its `FRASI` and in `it.po`) and its names, never words glued
together; who it is from (nobody when it is DottorCloud); the person or deal it
opens and what it is about. The panel works out where it opens: a kind about a
settings page opens it (`api.IMPOSTAZIONI`, `apriImpostazioni`; by address
`?settings=&step=`, which the router opens over the page). The panel's row, the
toast (from anywhere on it: a swipe only dismisses it), the phone's notification
and the email open the same place; only a notification with nowhere to go opens
the notifications. A page a notification opens on one thing takes it from its
query (`?open=`) and leaves the address without it (`history.replaceState`).

### Emails (docs/progetto-ghl/44)
| File | Role |
|---|---|
| `crm/templates/emails/standard.html`, `email_header.html`, `email_footer.html` | Every email's layout over the framework's (its classes kept): with a `header` or `with_container`, the brand's canvas, the white card with the cloud's tail, the centre's mark at the top (its PNG/JPEG logo, else its name; the product's only for a centre with neither), "Powered by" under the card; light theme only. A plain email somebody wrote stays plain |
| `crm/posta/aspetto.py` | `contesto_email()` (Jinja method: the centre's mark, the brand's colours, the signature), `pulsante(url, testo)` (a table every client draws, Outlook too), `codice(valore)` (a code in its box) — tested |
| `crm/notifiche/posta.py` + `Settings/NotificationsSettings.vue` | Notifications by email too: each person's choices (Settings > Your account > Notifications, only the groups they receive: `riceve()`), every five minutes what is still unread after `ATTESA` minutes, one email per person, a conversation once while unread, a button that opens DottorCloud, never the Desk; the framework's assignment, mention and share emails are skipped (`notification_skip_email_types`) |

An email of the system gets a title (`header=`) and `with_container=True`, its
message in paragraphs with the words escaped, the one thing to do in a
`pulsante()`, a code in `codice()`, and no colours of its own: the layout wears
the brand that is on. The marks are PNG (`Marchio.logo_email`, `icona_email`):
mail clients do not all show an SVG.

### The sending service and the centre's mailboxes (docs/progetto-ghl/51)
| File | Role |
|---|---|
| `crm/posta/servizio.py` | The agency's sending service (`dottorcloud_posta` in `common_site_config.json`) as each site's "DottorCloud" account, the default outgoing one: `assicura()` after migrate and hourly, saved only when it changes, a failure undoes only its own save; `intestazioni()` (`make_email_body_message`): From the centre's name on the service's address (the envelope too), "Anna Bianchi · Centro Aurora" for somebody without a mailbox, Reply-To the centre's (`FCRM Settings.reply_to_email`, else its main mailbox); the page's calls, syncing the agency's |
| `crm/posta/ingresso.py` | `alla_ricezione()` on every email received: the person who wrote (`find_person`), a new one only where the mailbox says so and never a machine, the centre or a booking platform's inbox; a reply on one of DottorCloud's documents moves to the person (the document keeps a timeline link), another app's thread stays; whoever follows the person told (`avvisa`, kind "email") |
| `crm/api/settings.py` + `Settings/EmailAccountList.vue`, `SendingService.vue`, `EmailEdit.vue`, `utils/caselle.js` | Settings > Email > Accounts: the centre's mailboxes from the providers the server knows (`FORNITORI`, servers never typed), errors in words, saved with the framework's list of document types read whole (`_dove_archivia`); where the answers go; the service never listed — tested |
| `crm/posta/personale.py` + `crm/overrides/email_account.py`, `Settings/Profile/MyEmail.vue` | Each person's own mailbox (Settings > Your account > Your email): `Email Account.crm_owner`, connected with a provider's password or signing in with Google or Microsoft through the agency's Connected App (told apart by where it signs in), back through `/oauth_connected?provider=posta`; only replies and known people's emails are read from it (`da_tenere`), nobody becomes a person from it; the composer's From and the centre's mailboxes one writes from come from the server (`get_my_senders`, `set_my_senders`: `User.user_emails` is permlevel 1) |

What DottorCloud sends by itself leaves through the service: no mailbox of the
centre is the default outgoing one while it is on, and somebody's own mailbox is
never one of the centre's (`personale.del_centro()` in every list of them). An email received is the
person's, never a new person for somebody known; a module that sends a reminder on
its own document needs nothing more: the answer reaches the person.

### The centre's archive (docs/progetto-ghl/57)
| File | Role |
|---|---|
| `crm/archivio/regole.py` | Pure: AWS Signature V4 (headers and the browser's link, tested on AWS's own examples), the bucket's address, the keys (`<prefix>/<site>/<sha[:2]>/<sha>/<name>`: the bucket is NPM2's, shared with other projects, and every site has its own folder), which files move (private only), what the plan includes (`SPAZIO_COMPRESO`: 1 TB, 2 TB from Polyclinic; `CRM Plan.storage_gb` over it), the warning at 80% — tested with plain `unittest` |
| `crm/archivio/s3.py` | The agency's bucket (`dottorcloud_archivio` in `common_site_config.json` or a site's config) through `requests`: put, head, get to a file, delete, the link, the bucket's versions and CORS (`imposta_il_bucket`) |
| `crm/archivio/archivio.py` + `CRM Archived File`, `crm/overrides/file.py` | Every hour the private files written over an hour ago go to the bucket and an empty file keeps their name on the server (`sposta`); `/private/files/…` of an archived one sends whoever the framework lets read it to the bucket for five minutes (`prima_della_richiesta`, its access log kept); `File.get_content` and the rest bring it back first (`riporta`), and it leaves again an hour later; deleted, its object goes after the commit, and at night what the database deleted (`orfani`); the space each address once (`spazio`), on Settings > The centre > Features — tested with a bucket in memory |

A private file is read through its `File` (`get_content()`), never by opening its
path: an archived one is an empty file on the server until something asks for it.
A public file stays on the server.

### The centre's Twilio account (docs/progetto-ghl/52)
| File | Role |
|---|---|
| `crm/telephony/collegamento_regole.py` | Pure: the two codes before Twilio is asked, a SID masked, the space's name, what a number and the app need to reach DottorCloud (a SIP trunk's number left alone), Twilio's answers in words — tested with plain `unittest` |
| `crm/telephony/collegamento.py` + `Settings/Telephony/TwilioSettings.vue`, `utils/twilio.js` | The centre pastes Account SID and Auth Token once: DottorCloud makes its space in the account (a subaccount named after the site, found again on reconnecting; a subaccount's codes make it the space), its key and TwiML app, points every number of the space at itself, and keeps only the space's codes; the agency's account the same way (`dottorcloud_twilio` in `common_site_config.json`); `assicura()` every hour, only in a space; Check, Disconnect (the key goes, the space stays) — tested with a fake Twilio (`crm/telephony/tests/twilio_finto.py`) |
| `crm/telephony/numeri_regole.py` | Pure: the kinds of Italian number and what each is for, whose the number is (a company or a professional), an area's prefix, the regulation's fields and documents in DottorCloud's words, the files Twilio takes, its evaluation line by line, a month's price, approved documents good for the next number — tested with plain `unittest` |
| `crm/telephony/inbound.py`, `routing.py` + `providers/base.py` (`Ring`, `Message`), `messaggi.py` | An incoming call rings everyone who answers the number at once (browser and mobile, `find_ringing`) for the answering settings' seconds; nobody picks up: the announcement and the callback (`nobody_answered`), else the apology; when the centre wants it, a message after the tone (`take_message`), kept on the call (`left_message`) and told to whoever follows the person (notification "Call"). Twilio comes back to `ring_ended`, `message_taken`, `message_recorded` |
| `crm/telephony/numeri.py` + `CRM Phone Number Request`, `Settings/Telephony/NewNumberDialog.vue`, `utils/numeri.js` | A new number from DottorCloud: kind and price, the fields with invoicing's details in them, the documents uploaded here, Twilio's evaluation before review (a draft sent again leaves Twilio), every hour how it went with a notification ("Phone", it opens Twilio's page), the number chosen and bought pointed at DottorCloud, released from the numbers' page (only in a space); approved, the files and what was written go |
| `crm/telephony/sms_regole.py` | Pure: the sender's name Twilio takes and one made from the centre's, a message that is only STOP or START (Italian and English), promotional hours (Monday to Saturday, 8 to 22) — tested with plain `unittest` |
| `crm/telephony/sms.py` + `Settings/SmsSenderLine.vue`, `Activities/SMSBox.vue` | Every SMS of the centre from one sender (`mittente()`: its name or one of the space's numbers that send SMS, chosen on Twilio's page): written by hand, the automations', the waiting list's, the area's; STOP written to the centre stops the automatic ones (`CRM Lead.sms_opt_out`, the marketing consent withdrawn "By SMS"), START has them again, the answer kept in the conversation; the composer says who wrote STOP |
| `crm/telephony/consumi_regole.py`, `errori_regole.py` | Pure: this month's spend by kind from Twilio's usage records, the alert's amount and what to do with Twilio's usage trigger (it cannot change an amount: a new one replaces it), Twilio's error codes in DottorCloud's sentences, the problems grouped by code — tested with plain `unittest` |
| `crm/telephony/consumi.py` + `errori.py` | Twilio's page for whoever pays for the space (`get_twilio_usage`, kept ten minutes): this month by kind, the last seven days' problems from Monitor in words; the spend alert as the space's usage trigger (`allinea_l_avviso`, on save and in `assicura()`), `spend_reached` telling whoever pays ("Phone"); a failed SMS keeps Twilio's code and says why (`errori.in_parole`) |
| `crm/telephony/trasloco_regole.py`, `trasloco.py` + `Settings/Telephony/MoveNumberDialog.vue` | "I already have a number": a number of the centre's own account moves into the space with the account's codes pasted for that one request (never kept), its approved bundle cloned there first (Twilio's Clones endpoint, through `Client.request`: SDK 8.5 lacks it) and its address copied, then pointed at DottorCloud; a SIP trunk's number stays; another operator's number is forwarded or ported, explained — tested with the fake Twilio |
| `crm/telephony/uscita_regole.py` + `uscita.py` | Calls going out: only to the countries the centre chose (`CRM Twilio Settings.allowed_countries`, Italy to start with), never to a premium-rate number; the number shown is the one chosen for the call when it is the centre's (`caller_ids.usable_for_outbound`), else one's own line; an Italian mobile shown on a call to Italy is blocked since 19/11/2025 (AGCOM), so the screen says so. The same countries are Twilio's dialing permissions of the space, set on saving, on connecting and every hour (`allinea_i_paesi`, only in a space). The rules pure, tested with plain `unittest` |
| `crm/telephony/verificati_regole.py`, `verificati.py` + `Settings/Telephony/VerifyNumberDialog.vue`, `utils/verificati.js` | A number of another operator's shown on calls once Twilio verified it in the space: no document, Twilio calls from +1 415 723 4000 in English and the page shows the code; the row waits switched off and is switched on by Twilio's StatusCallback (`caller_id_verified`, signed), the page asking while it waits, or the hourly check; whoever asked is told unless the page was watching; removed from Twilio here. A verified Italian landline is shown in Italy only as far as the operators let it (AGCOM, August 2025): the dialog, the list and the call say so (`uscita_regole.incerta_in_italia`). Only the space's numbers and the verified ones are offered (`caller_ids.outbound_filters`) — tested with the fake Twilio |
| `frontend/src/components/Telephony/TwilioCallUI.vue` + `utils/chiamate.js` | The call in the browser: before it leaves, `check_number` and `get_outbound_numbers`; with more than one number the popup asks which to show (the last one used chosen already, kept in the browser), the AGCOM warning beside a mobile; during the call the keypad (`sendDigits`); the countries in Twilio's settings page — the same rules as the server's, tested |

An SMS DottorCloud sends leaves from `sms.mittente()`, never from somebody's own
line; one it sends by itself skips a person who wrote STOP (`sms.ha_fermato`), and a
promotional one (an automation asking `marketing_consent`) waits for its hours.

Twilio is the only carrier (`crm/telephony/providers`): Exotel went on
03/10/2026 (`dottorcloud_does_not_use_exotel`).

The account's own token is never stored and never in a log: the codes travel in
variables named `*_token` and `*_secret`, which a traceback hides, and an error of
Twilio's is logged with its status and code only. A connection made by hand in the
Desk (`account_owner` empty) may hold other sites' numbers: nothing is repaired in
it. Twilio Connect is not used: a Connect app cannot manage numbers, use the
regulatory API every Italian number needs, nor make the key the browser calls with.
A document goes to Twilio only from a file the person uploaded for it (private,
attached to nothing) or a request's own: never another of the site's files.
A call from the browser leaves only after the server's yes (`voice` asks
`uscita.perche_no` again, whatever the screen did), and shows a number of the
centre's or the caller's own line: never one the browser made up.

### WhatsApp's templates (docs/progetto-ghl/12)
| File | Role |
|---|---|
| `crm/integrations/whatsapp/modelli_regole.py` | Pure: a template lives on a WhatsApp Business account (WABA), never on a number: the numbers that send it (`numeri_che_possono`, `stesso_account`), its buttons by Meta's rules (10 at most, 2 links, 1 call, 25 characters, quick replies first), Meta's description read into frappe_whatsapp's fields (`da_meta`), the ones Meta no longer has (`spariti`) — tested with plain `unittest` |
| `crm/integrations/whatsapp/templates.py` + `Settings/WhatsAppTemplates.vue`, `utils/modelliWhatsApp.js` | Settings > WhatsApp > Templates, one number at a time: a new template on the number shown, with its buttons; «Sync from Meta» is ours (`porta_dentro`: every account once, every page, found by Meta's id, written without the hooks that would submit it again), frappe_whatsapp's `fetch` read one number, one page, one template per name; `modelli_inviabili()`: what the number that sends can send, the only templates the chat (`crm.api.whatsapp.get_sendable_templates`), the automations, the waiting list and the area offer |

A template is chosen where it can be sent: whatever offers one asks
`modelli_inviabili()`, never the whole list, and a check before sending compares the
account (`stesso_account`), never the number's name.

### Invoicing in words, a medical centre's preset, the invoice inside DottorCloud, test and Itala (docs/progetto-ghl/45, 46, 47, 48, 49)
| File | Role |
|---|---|
| `crm/invoicing/engine/voci.py` | Every code invoicing asks somebody to choose, in words: a family per field (regimes, VAT natures, documents, payments, funds, withholdings, 770 reasons, stamp duty, keeping, channels...), each `Voce` with its name, the line on when it applies and whether a medical centre meets it (`sanita`); `voci()` for a profile, the stored values always kept — pure, tested with plain `unittest` |
| `crm/tessera_sanitaria/engine/voci.py` | The Sistema TS's families (expense types in the specification's words, particular cases, who issues, how it is sent, the mandate, the operation), registered into invoicing's vocabulary |
| `crm/invoicing/scelte.py` | Which field speaks which family (`CAMPI`), the rules that narrow one by the document (`registra_regola`: expense types by the issuer's category), the healthcare profile (`Verticale.fatturazione`: the clinic's `sanitario`), `adatta_campi` on `crm.api.doc.get_fields` (`registra_adattatore`), `get_options` for the Desk's invoice, `get_vocabulary` for list rows |
| `frontend/src/utils/scelte.js`, `composables/vocabolarioFatturazione.js` | A choice's line, the stored value kept, a code's name in a row, a read-only choice by its name — tested |
| `crm/tessera_sanitaria/preimpostazione.py` + `Settings/Invoicing/HealthcareSetup.vue` (doc 46) | With the clinic on, a medical centre's invoicing in three questions (who issues, the facility's codes or the profession, the regime): the Sistema TS category, the regime, the fund and withholding of the profession; the agenda's services become healthcare cards, exempt, with the issuer's expense type (`cards_from_services`); a new card starts as one (`card_defaults`) |
| `crm/invoicing/emissione.py` + `components/Invoices/InvoiceDialog.vue`, `composables/fattura.js`, `utils/fattura.js` (doc 47) | The invoice made in DottorCloud's own dialog, never the Desk's form: who it is for, what was done and by whom, how it was paid, and first where it goes; `preview` classifies and adds up in memory (nothing saved half-way), `save`, `issue`, `credit_note` (to the Sistema TS the refund of the original), `delete_draft` (never a numbered one); the dialog writes only client, payment and lines, the company and the engine the rest. Opened from anywhere with `apriFattura`/`nuovaFattura` |
| `crm/invoicing/engine/messaggi.py` | `Messaggio`: an engine sentence that keeps its template and arguments, so `documento.in_parole()` translates it whole; `Nome` (a vocabulary's name, translated with it), `Rilievo` (an SdI finding, its code in a tail the same in every language: « (SdI 00422)»); a `Decimal` in a sentence is an amount in euros |
| `crm/invoicing/documento.py` `da_correggere()` + `estensioni.registra_controllo_bozza` (doc 48) | What stops a draft and what is worth saying, for issuing, the preview and the dialog: the document's rules and what a module would refuse later (the Sistema TS's `controlla_bozza`: the document's problems stop, the company's are said) |
| `crm/invoicing/engine/fatturapa.py` `valida()` | The SdI's own checks on the XML, as its "Elenco dei controlli" (v1.8) states them: `00200` for the schema, `00422` per rate with the fund, `00421` rounded half up; `bloccanti()`/`codice_di()` read the code of a finding, stored too |
| `crm/invoicing/estensioni.py` | The qualification registers in two tiers: the stored ones (what the practice edits) before every shipped one (`registra_risolutore(..., spedito=True)`), whatever order the modules load in; `QualificaRifiutata` (a switched-off qualification) stops the chain |
| `crm/invoicing/prova.py` + `Settings/Invoicing/ProviderConnection.vue` (doc 49) | A company starts in test (`provider_environment`): its invoices are test invoices (`test_document`, `segna()` at issue), numbered on their own series (`2026/PROVA-S/1`), with a band on the PDF, the Sistema TS report checked and never sent (`ts_status` `prova`), never a client nor in the area; `go_live` (the centre's manager) when nothing blocks, taking the test invoices away; `back_to_test` (the agency) only without real invoices; `mancanze()`: what is missing, what stops going live, whose it is (the agency's rows only the agency reads). Settings > Invoicing > Test and go live |
| `crm/invoicing/connessione.py` + `sdi/itala.py` (doc 49) | Itala, the one intermediary offered: its test and production doors by environment (a document's: `ambiente_del_documento`), the agency's account (`CRM Invoicing Settings`, permlevel 1, else `itala_client_id`/`itala_client_secret` in `common_site_config.json`) or a company's own; the company registered under it once per environment (`registra_azienda`, `/aziende`); Itala's file name and id kept on the invoice; the token harvested from Basic calls. The SdI's outcomes asked every ten minutes, only when something waits (`riconciliazione.da_chiedere`); every update kept before it is applied (`CRM SdI Update`: Itala gives each once) and tried again, an invoice silent for a day asked by name; each notice applied once by its own name; only the site that registered the company reads its updates (`itala_site`); the XML leaves unsigned (Itala signs a PA's) and the one transmitted is kept (`sdi_sent_file`); a send whose answer was lost asks Itala first; the webhook's `Authorization: Bearer` taken away before Frappe reads it (`webhook.prima_della_richiesta`) |
| `crm/invoicing/engine/fornitori.py` + `ricevute.py`, `components/Invoices/ReceivedInvoices.vue`, `ReceivedInvoiceDialog.vue`, `utils/ricevute.js` | The suppliers' invoices (`CRM Supplier Invoice`): filed by `riconciliazione` with the amounts read out of their own XML (taxable, VAT, due date, lines; a DOCTYPE never read), whoever manages invoicing told (`ricevute.annuncia`, «{0} sent an invoice of {1}», opens `?ricevuta=`); the Invoices page's «Received» tab: by state or to pay, by a word; seen, to the accountant, disputed with the reason, paid; Itala's PDF asked once (`itala.pdf`); the month's ZIP for the accountant, issued and received (`export_month`, `fatture.esporta`) — tested |
| `crm/invoicing/incassi.py` | Collected is `CRM Invoice.collected_on`, never `payment_date` (the issue date by default): an invoice to a person issued at the desk takes its payment date (`alla_cassa`, in `emissione.issue`), the rest wait for `fatture.incassi` to mark them; a credit note is never collected. The dashboard's «Centre economics» (`widgets/invoicing.py`: collected, to collect by age, costs with or without VAT, margin, VAT of the period) counts on it |
| `crm/invoicing/automatico.py`, `crm/tessera_sanitaria/automatico.py` | The two switches of Settings > Invoicing > Advanced > Options, off to start with: an electronic invoice leaves for the SdI in a job after its issue is committed (`api.trasmetti`, the button's send); every night (`daily_long`) the healthcare expenses not reported yet leave for the Sistema TS one by one, a test invoice or a refused one never; what stops is told (`monitoraggio.avvisa`) |

A field of invoicing that stores a code never shows it: it goes in `scelte.CAMPI`
with its family (a country kept as its two letters in `scelte.PAESI`, named by
Babel), every value its DocType admits gets a name and a line in the
vocabulary (and in `it.po`), and the ones a medical centre meets carry `sanita`.
Labels and descriptions say what a field is for in plain words, never a list of
codes nor the tracciato's names (`tipoSpesa`). What is stored stays the code.
A register a module ships goes in with `spedito=True`: what the practice wrote in
its register always answers first. A new record on a settings screen starts from
the DocType's defaults (`DocFields`), never from a copy of them in the page.
An invoice is opened with `useFattura()` (`apriFattura(name)`, `nuovaFattura()`;
something that proposes one, an appointment, passes `{ bozza }`),
never `/app/crm-invoice`; a sentence of the engine with a value in it is a
`Messaggio` (an SdI finding a `Rilievo`), never an f-string, and its English is
in `it.po` by hand: `crm/tests/test_frasi_del_motore.py` checks both.
What the centre sets up of invoicing is only what is its own: who issues, its
details, its Sistema TS credentials, and the tick that it joined the Agenzia's free
preservation. Numbering (series never empty, the format picked among examples) and
the Sistema TS's way and certificate sit on permlevel 1 (the agency's, System
Manager). What is nobody's choice - the SdI through Itala on the agency's account,
both directions, paid in the plan's credits (unless the centre invoices with Fatture
in Cloud, doc 58); the Agenzia's preservation; a paper
original for a healthcare invoice to a person - the company's controller forces
(`SEMPRE`) and the DocType hides. `crm.api.doc.get_fields` never draws a field the
user cannot read, and a settings screen (`buildTabs`) draws no hidden field nor a
section or tab left empty.
Anything with a lasting effect (a client, a patient, the area, a report to the
Sistema TS) leaves a test invoice out (`test_document`); going live takes them away.

### Fatture in Cloud, for a centre that already invoices there (docs/progetto-ghl/58)
| File | Role |
|---|---|
| `crm/invoicing/fic/regole.py` | Pure: a DottorCloud invoice as Fatture in Cloud's document (`documento()`: each line with its rate, the fund or INPS recharge, the withholding, the stamp duty - on an e-invoice the issuer's and a line when recharged, on paper the client's -, the payment on its method's account, a credit note's reference, the Sistema TS's fields), which of its rates and accounts stands for ours (`chiave_iva`, `scegli_tipo`, `conto_suggerito`), the totals compared (`totali_diversi`: VAT, withholding, amount due), `ei_status` in DottorCloud's states — tested with plain `unittest` |
| `crm/invoicing/fic/client.py` | The calls (`chiama`, `chiedi_token`) and Fatture in Cloud's errors in words (`ErroreFiC`, `incerto` when the answer was lost) |
| `crm/invoicing/fic/collegamento.py` + `CRM Fatture in Cloud`, `Settings/Invoicing/FattureInCloud.vue`, `utils/fattureInCloud.js` | The agency's app (`fic_client_id`/`fic_client_secret` in `common_site_config.json`, its return address on the hub, `meta_hub_url`) connected by the centre's manager: the signed state carries a nonce the site turns back into its company, for the same session only; the company there with the issuer's VAT number, its rates, accounts and numerations read (`leggi_info`) and chosen by themselves where one fits; the tokens (password fields, the System Manager's) renewed every hour near their end and once on a 401, under a row lock; the switch on only when nothing is missing (`da_fare`), a lost access a blocking row of `prova.mancanze` — the page's states tested |
| `crm/invoicing/fic/emissione.py` | With the switch on, a real invoice is born there at issue (`before_submit`, before the number): its totals asked first (`/issued_documents/totals`: to the cent, or nothing made), then created, taking Fatture in Cloud's number (`fic_document_id`); a rollback deletes it there (`after_rollback`, the access read before), a lost answer is found again by the marker in its subject; to the SdI from there (`xml_verify`, send, the XML kept), its states every ten minutes (`riconcilia`), a collection marked there too, cancelling deletes it; the Sistema TS sent by DottorCloud or by Fatture in Cloud (`ts_by`: one expense type per invoice) |

With Fatture in Cloud on, the number, the SdI and its keeping are Fatture in Cloud's,
paid in the centre's own subscription: Itala is not used for that company and the
plan's SdI credits leave its invoices out. A test invoice and the demo's never reach
it (`tocca_a_fic`, `guardie.mai_fuori`), and an invoice reaches it only whole, with
Fatture in Cloud's totals equal to ours. Its ids are numbers, the ordinary rate's
is 0: never read one as «nothing chosen». The tokens travel in variables named
`*_token` and are never logged.

### The settings (docs/progetto-ghl/31, 35)
| File | Role |
|---|---|
| `frontend/src/utils/impostazioni.js` | The menu as data: groups (your account, the centre, agenda, clients, deals, email, WhatsApp, phone, marketing, invoicing, integrations), their entries, an entry's tabs, who sees each (`condition` on `puo`, `ambito`, `whatsapp`, `verticale`), the line on what each group and entry is for (`description`); `menuDi()`, `trova()` (the entry and tab a page's name opens), `pagine()` — tested |
| `frontend/src/components/Settings/Settings.vue`, `SettingsHub.vue` | The modal draws the menu from the data in two levels: the groups on the left with their icons (`ICONE` by group), on the right the group open with its entries and their lines, or the entry open (`PAGINE`) with the way back to its group; an entry with tabs is one page with its row of tabs, the tab open being `activeSettingsPage` |
| `crm/tests/test_impostazioni.py` | Every page the server or a button names is in the menu |

A new page goes in the group of the part of the work it belongs to, as an entry
or as a tab of an entry that is there: no group of one entry. Its key never
changes (links are built on it); a page that becomes a tab keeps its key, a name
it had before stays as an alias. Its label, its tab and its page's title say the
same words, in the user's language, and its `description` says in one line what
one sets up there.

### A person: one page, two doors (docs/progetto-ghl/54)
| File | Role |
|---|---|
| `crm/persone/riepilogo.py` | A person's summary in one call (`get_summary`): each module adds its lines (`registra_voce`, from its `registra()`), each deciding what the session reads, left out (never refused) where it may not; a line that breaks is logged and the rest opens. The base's: what they have going (cycles, subscriptions, a place in a waiting list), the tasks still to do, the open deals; invoicing's what is left to collect (`incassi.della_persona`), the forms' what is owed (`dovuti.nel_riepilogo`), the quotes' the ones waiting or going on (`api.nel_riepilogo`) — tested |
| `frontend/src/components/Activities/SummaryArea.vue` + `utils/riepilogo.js` | The Summary tab (first on the desk and the phone) and the column beside a conversation (`compatto`): the last message the person carries, the appointments the page's head asked for (the same resource), the server's lines, each a tap from its tab; three lines of a list, the rest on its tab — the pure part tested |
| `frontend/src/router.js`, `notifiche/api.py` `percorso`, `Conversations/ConversationAside.vue` | The doors: a person opens on `#summary` wherever one comes without naming a tab (not the tab left last time); a message opens the Chat (its notification names it, the conversations' «Open the record» says `#activity`) |
| `components/ViewControls.vue`, `Mobile/ElencoPersone.vue`, `api/sul_telefono.get_people(relationship=)` | The People list: one list, its step as views (the quick filter drawn as buttons), at `/crm/persone` - the old `/crm/leads` addresses redirect |

A person opens on their summary, from anywhere that names no tab; a message, a
conversation or its notification, opens their chat; the same summary sits beside
the chat in Conversations. A module with something to say about a person
registers a line of the summary, its own key, from its `registra()`; the page
draws the keys it knows. The people live at `/crm/persone/<name>`: a link the
server writes (an email, a push, the Desk) says so.

### What a list offers to choose (docs/progetto-ghl/55)
| File | Role |
|---|---|
| `crm/liste/regole.py` | Pure: for each use (`filtro`, `ordine`, `gruppo`, `colonna`, and `scheda` for a record's layout editors: any kind of field, never the layout's structure) the kinds of value it takes, the framework's own columns it offers and their words («Created By», «Last Modified By», «Favourite»), what no list offers (a code, a series, comments, tags); each field once, two of the same name told apart by their section («Sorgente (Primo contatto)»), the document's own field over the framework's of that name; a saved column under the framework's old name read by the new (`nome_della_colonna`) — tested with plain `unittest` |
| `crm/liste/campi.py` + `crm/api/doc.py` | `della_lista(doctype, uso)`: the fields off the meta that the session reads, with their section and tab, less what a document keeps only for the machine (`SOLO_PER_LA_MACCHINA`); `sort_options`, `get_filterable_fields`, `get_group_by_fields` and `get_list_fields` (columns, a board's card, quick filters) answer from it |
| `frontend/src/composables/campiDellaLista.js`, `utils/gruppi.js`, `Kanban/KanbanSettings.vue`, `SidePanelLayoutEditor.vue`, `FieldLayoutEditor.vue` | The list's fields asked the first time a picker opens, never while the list loads; the layout editors' from the same rule (`useCampiDellaLista(doctype, 'scheda')`, a placed field named by `nomeDelCampo`); a group's heading as a row reads the value (`intestazioneDelGruppo`: the reader's words, a step in its context, yes or no, a colleague by name, a day as a date) — tested |

A list's pickers offer what `crm/liste/regole.py` says, never the meta whole: a
field a document keeps only for the machine goes in `campi.SOLO_PER_LA_MACCHINA`,
a field's name in a picker is the reader's, never its fieldname or its type.

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
of their own, linked to the parent, never the parent's record. Somebody the desk types
into an appointment with a contact is found or made the same way
(`appointments._persona_scritta`); a name alone stays a name.

### The client area (`crm/area`, the plan's "area" module; the base comprises it, every centre has it)
| File | Role |
|---|---|
| `crm/area/accesso.py` + `crm/www/area.py` | The door: invitation (`CRM Area Access`, role "Client Area User"), a code by email, step-up before a download; every call derives the session's people on the server |
| `crm/area/api.py` | Appointments with the booking page's link, cycles, invoices; "Prepare your appointment": the owed forms, opened on `/modulo` with the area's session |
| `crm/area/sezioni.py` | The places other modules add to the area (`registra_sezione`): the plans, the documents given online, the quotes, shown to whom they have something |
| `crm/area/messaggi.py` | The board (`CRM Area Message`): the desk writes administration, the chat passes questions; other kinds come from other modules (`registra_tipo`, the clinic's "Care") with their own readers |
| `crm/area/chat.py` + `chat_regole.py` | The chat about hours and bookings, for any centre: emergency words get 112 before any model, health goes to a person, the rest only from what the centre wrote |
| `crm/area/collegamento.py` + `CRM Area Link` | The link every email of the area's carries: it enters once, within seven days, only its fingerprint kept; the door's «Enter» spends it (a POST: a mail scanner opening links never does), it counts as a code just read, an old one leads to the code. A new document told by email where the centre wants it (`CRM Area Settings.email_new_documents`, off to start with): an invoice to a person, never a test one, the area opened if there was none (the parent's for a minor), never for the demo |
| `crm/area/passkey.py`, `crm/area/avvisi.py` | Passkeys (WebAuthn); news by WhatsApp or SMS besides the email, only to the person's own number that wrote to the centre (`CRM Area Settings`) |
| `frontend/src/area/`, `frontend/vite.area.config.js`, `frontend/area.html` | The area's app, built apart into `/assets/crm/area` (`yarn build:area`, run by `yarn build`); its words in `it.js`, the vertical's first |
| `frontend/src/area/area.css` + `aspetto.js`, `components/AreaChip.vue`, `NextAppointment.vue` | The area as the brand draws the patient's phone (doc 42, `brand/presentazione/sorgenti/img/telefono-*.png`): `area-*` classes on Espresso's tokens - titles, small-capital labels, cards with the tail, a kind in its category's cloud (a plan kind's `colore` and `icona`), the next appointment the one deep block, the days, the one-tap tick, the code's boxes; five places at the bottom, the open one in the brand's colour; light or dark as the phone is set, and following it (`utils/temaDelTelefono.js`), the centre's wide logo on a white card in the dark; the dates and a day's progress pure, tested |
| `frontend/src/components/Area/` | The person's "Client area" tab: who enters, the board, the plans, the preview |
| `crm/area/anteprima.py` + `frontend/src/area/anteprima.js` | The centre's preview of a person's area (doc 41): `start` from the person's page ties it to the session for half an hour, before the invitation too, nothing sent; the area shows only what whoever previews reads in DottorCloud (`vede`, `filtra`: the rest keeps its place empty, `HiddenCard`), health data read go in the access log |

A call of the area that only reads passes `anche_in_anteprima=True` to `_mia` (or `_utente`), and in a list keeps what the previewer does not read in its place (`anteprima.filtra`); one that writes, sends, books or downloads passes nothing: the preview refuses it.

### Plans and programmes (`crm/piani`, followed in the client area)
| File | Role |
|---|---|
| `crm/piani/regole.py` | Plans without a site: moments and items, the day and the week, one tap, the kinds of plan registered (`registra_tipo`: who writes it by qualification, what it holds, what its screens offer, the "health data" mark) and of item — tested with plain `unittest` |
| `crm/piani/api.py` | Plans on the person's Plans tab (`CRM Personal Plan`, `piani.scrivi` / `piani.vedi`), each kind with its line (`TipoPiano.descrizione`) and whether the person's area is open: drafts of their author, published to the area, new version or closed; what a module adds (`registra_genere`, `registra_estensione`); health data read through `crm.permissions.sanitari` |
| `crm/piani/programmi_regole.py` + `programmi.py` | Programmes of stages (`CRM Programme`): each stage with its words and maybe a plan (`CRM Personal Plan.programme`), opened at one's own pace (the person in the area, `finish_stage`) or by time (`apri_del_giorno`, daily); a stage that opens publishes its plan with `api.pubblica` |
| `crm/piani/area.py` + `frontend/src/area/pages/Plans.vue`, `Plan.vue`, `components/PlanItem.vue`, `ProgrammeCard.vue` | The plans in the area: the day's moments, one tap an item (`CRM Personal Plan Log`), made up within two days, what is left this week; the programmes stage by stage |
| `crm/piani/librerie.py` + `dataset.py` + `dati/esercizi.json` | The exercises (`CRM Exercise`, `piani.librerie`, Settings > Clients > Libraries): the library DottorCloud ships, its names in Italian (NPM2's, `names.it` in the file; the dataset's English kept as `name_in_source` and searched too), in the code with its licence, loaded at install and at every migrate that brings a new file (`carica_libreria`); the centre never imports nor changes the library's: it switches off what it does not use (`switch_exercise`, a switch on each row) and adds its own (`save_exercise`, which refuses the library's), NPM2 adds to the library in that file. Its pictures always with "© Gym visual", the server's own copy (`crm/piani/immagini.py`: every hour the missing ones from the dataset at the library's commit into `sites/assets/crm-esercizi`, one site's job at a time, nobody pressing anything) or a CDN the agency names in the Desk (`CRM Area Settings`, permlevel 1); the screens never name the dataset; loaded again, pictures and muscles update and what a centre wrote before stays, while words NPM2 put right in the file (its steps in the imperative, not «Ripetere…») reach a site's copy by the fingerprints a record keeps of what it said before (`before`, `dataset.nella_lingua`) |
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
who added it read it. Whoever may know of health data they do not read (the
clinic's `si_sa`: who knows a visit happened, never of what is "only me" or
obscured) finds their padlock in a person's documents and plans
(`sanitari.nascosti`, `hidden`), never «Nothing yet» over a list that is not empty.

### Quotes (`crm/preventivi`, followed to the end by the agenda; deals and quotes, doc 50)
| File | Role |
|---|---|
| `crm/preventivi/regole.py` | A quote without a site: its states, the rows' amounts and sums, the phases, which row an appointment takes, what is checked before it is proposed — tested with plain `unittest` |
| `crm/preventivi/api.py` | `CRM Quote` on the person's Quotes tab, and on the deal's: a draft of its author (`preventivi.scrivi`); proposed, read with `preventivi.vedi` and the person, recorded accepted or declined by the author or `preventivi.gestisci` (the desk); a new version, closed half-way; what a module adds to the rows (`registra_estensione`); who reads one as a condition (`condizione`), which the dashboard counts on |
| `crm/preventivi/documento.py` + `templates/preventivo.html` | The quote's PDF, made once when it is proposed, private |
| `crm/preventivi/appuntamenti.py` | `CRM Appointment` doc_events: an appointment of a service still to do takes its row at the price agreed, done when the person came, given back when cancelled |
| `crm/preventivi/pipeline.py` + `CRM Quote Settings` | The "Quotes" pipeline: delivered, won (worth the quote) or lost with the reason; which one and how long a quote holds, in Settings > Deals > Pipelines. A quote is a deal's only in that pipeline (`prende_preventivi`): it moves no other pipeline's deal and opens no closed one (`si_puo_spostare`) |
| `crm/preventivi/area.py` | The quotes proposed and going on, in the person's area (the Plans page) |
| `frontend/src/components/Quotes/` + `utils/preventivi.js` | The Quotes tab of the person and of the deal (`QuotesCard`, the deal the server confirms), the editor and reader (`QuoteDialog`: a module's row fields where the server offers them, the deal a click away, the states with the "Quote" context); the same sums as `regole.py` — tested; `area/components/QuoteCard.vue` in the area |
| `crm/dashboard/widgets/quotes.py` | Quotes proposed, the share accepted (a "no" followed by a new version is not one), what the waiting ones are worth, the ones to call back after three days; only what the viewer reads, in the quotes' currency; the Sales dashboard's "Quotes" section |

With the clinic on, what a health professional writes carries the mark: a dentist's
care plan is a quote read like the clinical record (and by the desk once proposed),
every opening in the access log.

A deal is the sale, a quote what the person is asked to accept: two levels, as in
every CRM ("Deals" reads "Trattative"). A deal's value comes from its quotes: the
deal has no products grid of its own (the fields stay, `CRM Product` stays for the
website). Marketing's "offers", if they come, are catalogue packages, neutral where
the clinic is on. DottorCloud connects to no ERP: the ERPNext integration went on
02/10/2026 (`dottorcloud_does_not_connect_erpnext`).

### New clients (`crm/clienti`)
| File | Role |
|---|---|
| `crm/clienti/regole.py` | Who came, without a site: checked in, an appointment attended, an invoice that sold something (not a credit note), the first fact in time — tested with plain `unittest`; the clinic's rules are built on it |
| `crm/clienti/cliente.py` | The one door, `diventa_cliente`: `CRM Lead.client_since` written once, never in the future, and `relationship` from "Contact" to "Client" (never down from a step above it); the new clients deal won and "Became Client" (`client_created`) heard by the automations; `recupera()` finds last year's clients and announces nothing. Its rules decide in every centre, the clinic's too |
| `crm/clienti/eventi.py` | `CRM Appointment` and `CRM Invoice` doc_events: a booking moves the deal, a check-in, an attended appointment or an invoice makes a client |
| `crm/clienti/pipeline.py` + `CRM Client Settings` | The "New clients" pipeline: which one and the stage after a booking, in Settings > Deals > Pipelines (`NewClientsPipeline.vue`); a vertical names it in its words (`registra_nomi`: the clinic's "New patients") |
| `crm/dashboard/widgets/people.py`, `marketing.py` | "New clients" counts `client_since`, "Cost per new client" divides the ads' spend by the clients they brought; the dashboard's titles in the vertical's words (`verticali.traduttore()`) |
| `frontend/src/utils/rapporto.js` | Who a person is to the centre, on their page's head (`PersonHeader.vue`: «Cliente dal…», «Paziente dal…», «Lead»), in the People list's «Rapporto» column and on the phone's line: the step, its tag's tone, the fact with its date; the list's quick views, everybody then each step plural (`vistePerRapporto`: Tutti · Lead · Clienti · Pazienti, the steps' words in the "Relationship" context) — tested |

Three steps, never one renamed as another: a lead (`CRM Lead.relationship`
"Contact", read «Lead» in its "Relationship" context, English too: `en.po`), a client (whoever came or bought, by the CRM's rules, in every centre:
a Pilates class too) and, with the clinic, a patient (`assicura_paziente`: a health
service, or health data the centre keeps), the step above, which a later client
fact never takes down. The clinic writes `CRM Lead.patient_since` and "Patient"
(its custom field and the option it adds, `crm/clinica/custom/crm_lead.json`),
announces "Became Patient" (`patient_created`, offered where the clinic is on)
and counts "New patients" and "Cost per new patient" (`crm/clinica/cruscotto.py`);
the new clients deal is won the first time the person comes, whatever for. Only a
health service makes a patient (`regole.servizio_sanitario`): its card does not say
otherwise and, where the professionals' qualifications are known, one of them is a
health profession - a Pilates class with the kinesiologist makes clients, not
patients. The kinesiologist is no health profession (Ris. AdE 9/2026): invoicing's
ordinary register has it, and what one writes is no health data by its author.

### Verticals (`crm/verticali.py`)
A module of the plan that makes the CRM the software of a trade registers a
`Verticale`: its words over the CRM's (pairs of English strings: the SPA gets them
translated in its boot, the area in its own, the server asks `parola()`), and the
places of the base it hides because it shows its own. The CRM underneath speaks
neutral words (clients, appointments, the client area); with the clinic on it says
patients, visits, the patient area, everywhere - but the list of people stays
"People": it holds everybody the centre has heard from, not only its patients. A new place of the base that names
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
| `crm/clinica/tabelle.py` + `crm/clinica/librerie.py` + `dati/alimenti.json` | The foods (`piani.librerie`): the library DottorCloud ships, CIQUAL 2025 under the Licence Ouverte with the names in Italian (NPM2's, kept by code from one version to the next; `alimenti.LICENSE.txt`), made by `tabelle.libreria_ciqual` from ANSES's sheet and loaded at install and at every migrate that brings a new file (`carica_libreria`). The centre never imports nor changes the library's: it switches off the foods it does not use (`switch_food`) and adds its own (`save_food`); an Italian table (BDA-IEO, CREA) NPM2 adds the same way once licensed. Loaded again, numbers update, a name a centre changed before stays (`library_name` keeps the library's own); a food without its energy is left out |
| `frontend/src/components/Settings/Clinic/` + `frontend/src/utils/librerie.js` | Settings > Clients > Libraries, the Foods tab: the list with a switch on each row, a food of the library to read, a new one of the centre's; the exercises' page is the CRM's (`Settings/Plans/LibraryPage.vue`) |
| `crm/clinica/cure_regole.py` | The teeth without a site: FDI teeth and arches, surfaces, the chart's conditions, the teeth on a quote's rows (`valida_denti`) — tested with plain `unittest` |
| `crm/clinica/cure.py` + `crm/clinica/custom/crm_quote*.json` | The odontogram (`Clinic Dental Chart`, `cure.scrivi` and a dentist's qualification); a care plan is a quote of the CRM's: the tooth and its surfaces on its rows, only by a dentist, read as "Tooth 36 · OM" (`preventivi.registra_estensione`) |
| `frontend/src/components/Clinic/DentalCard.vue`, `DentalChart.vue` + `utils/cure.js` | The Clinic tab's teeth and the chart; the same rules as `cure_regole.py` — tested |

### The language (docs/progetto-ghl/40)
| File | Role |
|---|---|
| `crm/locale/it.po` | DottorCloud's Italian, over the framework's: every word a user reads, the server's sentences, the DocTypes' labels and names (`CRM Lead` is "Persona"); the voice and the product's words (persona, trattativa, cosa da fare, ambulatorio…) are in doc 40 |
| `frontend/vite/frappeUi.js` | frappe-ui's own English words through `__()` at build ("Load More", "Search", the select's empty texts, the data import pages, the editor's toolbar), the agenda's calendar named by Intl in the boot's language, the date picker's months and the letters over its columns, the agenda's and the picker's weeks from Monday, «4 more» under a full day; each rewrite must match frappe-ui's source — tested |
| `frontend/src/area/it.js` | The client area's dictionary: a test reads every `__()` of `src/area` and wants it there |
| `frontend/src/utils/emoji.js` + `src/assets/emoji/it.json` | The emoji found and named by their Italian words too, in the picker (`IconPicker.vue`) and after ":" in the editor (rewritten in `vite/frappeUi.js`), the closest first: Unicode's CLDR annotations for the emoji gemoji has, made by `scripts/emoji-italiane.mjs` (`it.LICENSE.txt` carries Unicode's notice, the About credits it), fetched with the picker and only for a reader in Italian — tested |
| `crm/lingue.py` | The language DottorCloud writes its own words in on a site (`del_centro()`): the one the centre chose, else the site's, Italian where it was left on the framework's English in Italy or nowhere said; the consents' texts, the pipelines' stages, the libraries' words. What DottorCloud wrote in another language follows it at a migrate and after the setup wizard (a consent's text by `registro.testo_da_tradurre`, a new version of the forms frozen on it, the libraries loaded again); the centre's words stay. The currency the centre counts in (`valuta()`): the one chosen in Settings, else its country's, the euro where nobody said; the dashboard and a deal's exchange rate ask it, never a fallback of their own. Italian and English, nothing else (`LINGUE`): at install and every migrate the two are on, the framework's other languages off and System Settings' language the centre's (`solo_italiano_e_inglese`): the framework ships Italian off, and a visitor reads only a language the site has on, so /prenota and the sign-in came in English to a phone set in Italian, and in the framework's German around DottorCloud's English to one set in German. The centre picks Italian or English and a zone of Europe in Settings > The centre > General > Language & time (`get_centre_language`, `save_centre_language`, `CentreLanguageSettings.vue`): its own whatever its country (`SCELTA`), whoever kept the centre's clock following it, DottorCloud's words following it in a job (the `crm_lingua_del_centro` hooks); each user reads the centre's («As the centre», which follows it) or their own (Preferences), whoever had another the centre's (`everybody_reads_italian_or_english`). A site the setup wizard never ran on (no country) reads as a centre in Italy at every migrate (`italia_dove_nessuno_ha_scelto`): Rome's clock, not the framework's Kolkata, Italy's date and number formats, the euro, the week from Monday, Italian where no language was written, and the users made meanwhile, who took Kolkata as their own zone (`utenti_sul_fuso_del_centro`); what somebody chose stays — tested |

A value a list shows from a choice (status, priority) or from a translated
DocType (stages, sources, reasons) goes through `__()`: the default ones read in
the user's language, a name the centre wrote stays as written. What DottorCloud
writes into a site once (a consent's text, a pipeline's stages, a library's words,
the qualifications' notes) is in `lingue.del_centro()`, never the System Settings
language read on its own: a site installed before anybody chose is in the
framework's English. Times are the
system's 24-hour clock (`HH:mm`, the only one Frappe has), never `hh:mm a`.
DottorCloud is European: English is written the way Europe writes it
(`appLocale()` gives «en-GB»: the day before the month, the 24-hour clock), an
`Intl` clock carries `hourCycle: 'h23'`, a format takes the user's language
(`appLocale()`), never the browser's (`navigator.language`), the week starts on
Monday in System Settings too (`per_l_italia`, whatever country), and a
measure is metric.
A currency is chosen and read by its name, the code stored («Euro», never «EUR»:
`components/Controls/CampoValuta.vue`, `utils/valute.js`), a price as the reader
writes it («65,00 €», `prezzo()`), never «65 EUR»; a time zone by its city in the
reader's language («Roma · Ora dell'Europa centrale», `utils/fusiOrari.js`),
never «Europe/Rome». A sentence names the agency for what is the agency's (System
Manager, `tecnico.*`) and the centre's manager for what is theirs, never «an
administrator».
In Italian an article before a date's day 1, 8 or 11 drops its vowel («dall'11
set», «l'1 ott»): both translators (the SPA's and the area's) put it right once
the sentence is filled (`conLApostrofo`, `utils/locale.js`), so a sentence keeps
«dal {0}» in the catalog; a sentence the server fills with a date (an email, a
public page) goes through `lingue.con_l_apostrofo` once filled.
A week starts on Monday, everywhere: the phone's strip, the dashboard's periods, the
agenda and the date pickers (`frappeUi.js` gives frappe-ui's own the same Monday).
An appointment's day and hours are the centre's clock (`window.timezone.system`), never
the phone's own zone: a free slot (UTC) is read with `sulCentro()`, a moment is sent as
the agenda keeps it with `oraDelCentro()`, and where the agenda, the reception desk or a
sale asks for now or today it takes `adessoDelCentro()` / `oggiDelCentro()`
(`utils/scheduler.js`) - so does every «now» or «today» the browser sends (a call logged
by hand, a table row's «Now», the chat's «later», a form version's first day), never
`dayjs()` or `new Date().toISOString()`.
When one English sentence needs two Italian ones, the rarer place passes a
context (`__('Hours', null, 'Service editor tab')`) and the catalog gives it a
`msgctxt` entry. A short word the framework already translates («Read», «Start»,
«Parent») is read in Italian where it is used: its translation is the
framework's place's («Leggere» a permission), and ours passes a context.

A sentence is whole in every language: never a DocType's name or an English word
glued into it ("mentioned you in {0}" with "lead"), one sentence per case instead
(a person named by their name, "the deal {1}": `crm_notification.in_grassetto`,
`nome_di`). What the code reads back is never a translated sentence: a marker
written in one language is looked for in English and in the site's
(`booking_platforms.sync._dalla_piattaforma`), a state is asked of the data. Words
handed as props are translated where they are drawn (`EmptyState`'s title and
description), and a standard record created in English (the kinds of consent, a
library's licence) is shown through `__()`: the shipped words read in the user's
language, what the centre wrote stays as written. A DocType's description or label
never calls the product "the CRM", and a changed one moves the JSON's `modified`, or
migrate keeps the old words.

What a rule without a site says is wrong - a `Problema` (plans, programmes,
quotes, teeth, foods) or an `Errore` (the forms' schema) - is English translated
when it is said (`testo(_)`); the catalog's extraction never sees it, so its
Italian goes in `it.po` by hand: `crm/tests/test_frasi_delle_regole.py` checks.
The same for a word a pure helper hands to the translator it is given
(`t('1 month')` in `src/utils`): `tests/unit/paroleDaTradurre.test.js` checks.

### The brand
| File | Role |
|---|---|
| `brand/` | The logo, the design system (`tokens.css`; Espresso and its 28 components in `design-system/espresso`), the font, icons, shapes, compositions, the website's layer, video, presentation, ads, and the generators that remake them (`brand/generatori`, paths in `percorsi.py`) — `brand/README.md` |
| `crm/marchio.py` | The brand of the vertical that is on (`Marchio`, `registra_marchio`, `attivo()`; `BASE` without one): `nome()`, `con_nome()`, `colori()`, `accento()`, `per_il_boot()`, `per_le_pagine()` (with the centre's mark: `centre_logo`, `centre_logo_shape`, `centre_name`), `contesto()` (every web page), `manifest()` (the phone's). `forma_di()` measures a logo of the site's ("wide" on its own, "square" beside the name). `applica()` writes it into Website/System/Navbar Settings, the desk's workspace and icons (install, patch, `piano_aggiornato` when the plan changes), `boot()` names the apps in the desk, `nome_scelto()` keeps the software's name from passing for a centre's |
| `crm/verticali.py` | A vertical names its brand (`Verticale.marchio`): the clinic wears DottorCloud |
| `crm/hooks.py` (top) | `app_title`, `app_logo_url` (fallbacks), `update_website_context` (`marchio.contesto`), `extend_bootinfo`, the apps screen |
| `frontend/src/espresso.css` | The design system on frappe-ui (`brand/design-system/espresso`): its variables with the brand's values, the cloud's tail and the cross through rules on frappe-ui's markup (avatars, menus, lists and their bar, the date's calendar, dialogs, toast, spinner), under `[data-marchio]` (set by `indossa()`); our own required marks carry `segno-obbligatorio`, our chosen items `dc-scelto` |
| `frontend/src/espresso-componenti.css` + `components/Espresso/` | The components frappe-ui has not (doc 39): `StatTile` (Today; the dashboard's numbers, the first of each row a deep block, `highlightedNumbers`), `EmptyState`/`EmptyArt` (every empty list), `CategoryTag`, `InProgressBadge`, `LoaderMark`; the agenda's `dc-evento` (first visit: `first_visit` in `crm.api.appointments.get_calendar`), the cycles' `dc-steps`; their tokens on the brand that is on |
| `frontend/src/utils/marchio.js`, `marchio.css` | The brand in the SPA and the area: `marchio()` from the boot, `conMarchio()` in `__()`, `indossa()` (colours as `--brand*`, favicon, icons, title); the centre's mark: `formaDelLogo()`, `misureSvg()`, `iniziali()`, `nomeDelCentro()`; primary buttons, switches and ticks in its colour — tested |
| `frontend/src/components/CentreTile.vue`, `composables/formaDelLogo.js` | The centre's tile (a square logo, the initials, the product's icon) in the client area and the previews; a logo's shape, from the server or measured |
| `frontend/src/components/UserDropdown.vue`, `Icons/CRMLogo.vue`, `Modals/AboutModal.vue` | The product's logo heading the sidebar (its icon when collapsed), the About with the licence's notices |
| `crm/templates/includes/marchio_*.html` | The public pages' head (favicon, phone icon), accent, the centre's mark at the top (`marchio_segni`) and the product's signature at the foot (`marchio_piede`); the framework's sign-in, new password and message in the brand's action colour and a phone's sizes (`marchio_framework`, added to their head by `contesto()` for `PAGINE_DEL_FRAMEWORK`) |
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

A screen looks the way the design system says (`brand/design-system/espresso`):
frappe-ui's components with its variables, the brand's action colour for what one
acts with (`--brand-action`, never the darkest gray), `--brand-segno` for a mark
that is not under words (progress), a required field's mark `segno-obbligatorio`.
A new mark of the brand goes in `espresso.css`, for every screen at once, never as
one screen's colours. A token it sets for the light theme gets its value in the
dark block too: `:root[data-marchio]` weighs more than frappe-ui's
`[data-theme=dark]`, so without one the light colour stays on the dark. A frame
drawn inside a page (an email's iframe) says `color-scheme: dark` in the dark
theme as the page does (`index.css`): one that says nothing gets an opaque white
canvas behind it, under the dark theme's light words.
An element whose tag is chosen while drawing is `ElementoNativo`
(`components/ElementoNativo.js`), never `<component :is="'button'">`: Vue resolves
the name to frappe-ui's Button, registered for the whole app, and the card becomes
a 28px-high button with its words cut to one line.

### The first steps (docs/progetto-ghl/37)
| File | Role |
|---|---|
| `crm/benvenuto.py` + `pages/Benvenuto.vue` | The centre's first opening, before anything else for whoever sets it up (`impostazioni.generali`, the boot's `benvenuto`): its language, Italian or English, each said in its own words, then its name, its clock and maybe the demo data; offered while the centre has no name and nobody finished it (`FATTO`), «Later» for that tab; it marks the framework's setup wizard done |
| `crm/primi_passi.py` | The registry: a `Passo` says who takes it (capabilities), its module, where it is taken (a settings page or a route) and whether the centre's data say it is done; `get_first_steps()`; the base's steps |
| `frontend/src/components/FirstSteps/`, `composables/primiPassi.js`, `utils/primiPassi.js` | The sidebar's card and the panel (in `GlobalModals.vue`); the pure part tested |

A module with steps of its own registers them from its `registra()`; a step is
done by the data, never by a click, so a centre that already works sees nothing.
The data are the centre's own: `c_e` leaves out what the demo made.

### The website (`sito/`)
| File | Role |
|---|---|
| `sito/pagine/`, `sito/parti/` | DottorCloud's own site (`dottorcloud.com`): one file per page with its title, description and path in a comment on top; layout, header, footer, closing band |
| `sito/approfondimenti/`, `sito/seo.mjs` | The articles (guides, rules with their sources, organisation) and the glossary; `seo.mjs` writes each page's schema.org graph (company, breadcrumbs, FAQ from `<details>`, product, article, glossary), the sitemap with dates, the RSS feed — pure, tested |
| `sito/build.mjs` | Builds into `sito/dist` with no dependencies: parts, Lucide icons inlined, image sizes, brand tokens in front of the CSS and `brand/sito/sito-marchio.css` after it, logo, font, compositions and video from `brand/`, sitemap |
| `sito/api/richiesta-demo.php` | The demo form: checks, trap and hourly limit, emails NPM2; settings in `private/sito.ini` outside the web root |
| `sito/deploy.sh`, `sito/server/` | Publishes on the HestiaCP server (never over a folder holding something else), nginx's 404 and headers |
| `.github/workflows/sito-pubblica.yml`, `sito/domini.txt` | Publishing from GitHub on every push that changes `sito/` or `brand/`: tests, then `deploy.sh --crea --nginx` for each domain listed; needs the `HOSTING_SSH_KEY` secret |
| `sito/test/sito.test.mjs` | `node --test sito/test/sito.test.mjs`: pages, links, images, no prices, the form under `php -S` |

The site promises the finished product as the marketing material does, and shows no
plan and no price. It sets no cookie and loads nothing from other sites. It is not
the Frappe site's public pages: those belong to each centre.

### The demo data (docs/progetto-ghl/53)
| File | Role |
|---|---|
| `crm/demo/registro.py` | The parts (`Parte`, `registra_parte`: a module's share, its plan module, the parts it needs, the ones that take what it makes, `prima`) and the register (`CRM Demo Record`): every record made while a part runs, written down by the `"*"` `after_insert` (`annota`), with a key a later part finds it by (`ricorda`, `trova`); `fuori_dal_registro` for what is the product's (the new clients pipeline) |
| `crm/demo/modo.py` | `in_prova(parte)`: the part through the screens' own code, with nothing leaving - no email (kept in the part, where the demo person reads a link or a code: `registro.posta_per`), job, realtime, automation, calendar mirror, platform push, global search, time stamp (`sigillo.marcatore`); committed whole, written down as it goes |
| `crm/demo/base.py`, `simulazione.py`, `dati.py`, `contesto.py` | The base's parts: the team (levels, qualifications, shifts; `collega`, which a module's own colleague joins by too), rooms and services, three months of the centre day by day through the CRM's own rules - with the cycle sold or the quote proposed at a first visit, the sessions after it joining the cycle and taking the quote's rows by themselves - companies and agreements, tasks, notes, calls; the Italian words; today in the centre's clock, the same chances every time (one seed per part) |
| `crm/demo/abbonati.py`, `in_attesa.py`, `conversazioni.py` | The regulars' subscriptions (sold, renewed and suspended by `crm.scheduling.abbonamenti`; in a class each regular uses their own), the waiting list through its engine (`Sguardo`, `offri`, `conferma`; a full class with people waiting), the emails and - where they are on - SMS and WhatsApp, each at its moment, the conversations dealt with, waiting or parked |
| `crm/demo/meta.py`, `marketing.py` | The "marketing" module's two parts: where the centre has no Meta page nor ad account of its own, Meta's page, lead forms, ad account, campaigns and their daily spend, stored as the connection stores what Meta sends and never asked of Meta, made before the people so that whoever comes "from Instagram" while an ad ran arrives through its form (`leads.store_lead`); four automations written in the builder and left switched off, who went through them by the engine at their moment (`enroll`, `advance_enrollment`), the tasks they left; where the centre has no social profile of its own, the profiles with their posts published, scheduled and a draft; two tracked links clicked. Made again after a half-way stop, a part takes what it made back (`ctx.trova`) |
| `crm/moduli/demo.py`, `crm/documenti/demo.py`, `crm/invoicing/demo.py`, `crm/area/demo.py`, `crm/piani/demo.py` | The forms', the documents', invoicing's, the client area's and the plans' shares, from their modules' `registra()`: the forms published this morning and signed today through the person's own pages (the link, the code read in their email, the desk's tablet), half-way or not opened yet, the physiotherapist's sheets, the website's requests; every subscription's contract handed over, the regulars' certificates, a few online, one downloaded; where the centre has no issuing company, the demo's own in test: its cards as the services page makes them, the visits invoiced on their days as they were paid, the cycles, a credit note, test invoices only, the codice fiscale born at a «Y» nobody has; the area opened this morning to the regulars (a mother with her child's), who came in (`get_me` as them), the desk's board, read by some; the trainings and habits given at the last session (dated there), a programme of each written today, ticked in the area as far back as it lets one make up (`log_item` as the area's user) |
| `crm/clinica/demo/` | The clinic's parts, registered from its `registra()`: the medical director and the clinical sheets; the last weeks' first visits written on them this morning and signed, each with its report filed; the summary decided, the dossier's consents, an episode obscured, a record opened out of the care team with its reason; results and images filed, a report given online; the dentist, with shifts, chart and care plans on the teeth, the treatments booked (`prima` invoicing); the dietitian's menus from the library and an exchange diet, the physiotherapist's exercises at home, ticked in the area. Tested with the clinic on by the CRM's own demo tests (`crm/clinica/tests/test_dati_di_prova.py`) |
| `crm/demo/togli.py` | Taking it away by the database: what is about the demo goes with it whoever wrote it, then what the centre took over stays, whole (`PARTI`: a form with its versions, a price list with the prices of the services that stay), then the framework's traces (never one older than the demo: the framework gives a deleted record's name again, and the centre's row in the bin stays), the users, the files, the counters - every table counted before and after in `crm/tests/test_demo_data.py`, what the centre kept in `test_demo_moduli_tenuti.py` |
| `crm/demo/guardie.py` + `whatsapp.py` | While the demo is in, nobody is written to: email (`Email Queue` before_insert), WhatsApp and SMS (`trattenuto`: any while a part is made, a demo number's after; `api/sms.deliver_via_twilio`), calls (`uscita.perche_no`), notifications by email (`avvisa`), the public booking page (`service_booking`), no outside service (`mai_fuori`: Meta's conversions, an ad's preview, a post handed to a network); the demo's forms are owed by its people only (`solo_per_la_demo`, in `dovuti`); and nothing real lands on a demo person: a message or call from a number one of them has too goes to the real person (`persona_vera`, in `integrations/api.py` and Twilio's `link`) |
| `crm/demo/api.py` + `Settings/DemoDataSettings.vue`, `composables/demoData.js` | Settings > The centre > Demo data: the parts, loading in a job with its progress by the socket, the parts a module switched on later adds, removal in one request |

A module adds its share of the demo from its `registra()` with `registra_parte`,
and makes it through its own code paths, never rows written beside them; what
carries evidence (a signature, a delivery, a download) is dated when the part
runs, never back. A module that extends another adds to that one's part the way it
extends it, never by an import the other may not make (the Sistema TS's healthcare
setup: `crm.invoicing.demo.registra_preparazione`). A part leaves the centre's own
records as they were (its company never takes the centre's default flag). A module
that sends something on its own, or asks something of people by itself, adds its
guard to `crm/demo/guardie.py`; one that
keeps something by a person outside its records (a file, a cache) makes sure
`togli` finds it. A demo person has an address at example.com and a number the
guards know: never a real domain, never a real person's number.

### The desk's day
| File | Role |
|---|---|
| `crm/scheduling/esiti.py` | How an appointment went: check-in (`Arrived`, `arrived_at`), who may mark (`agenda.presenze`), visit and invoice close it, the end-of-day "did they come?" |
| `crm/api/oggi.py` + `frontend/src/pages/Today.vue` | The reception desk («Accoglienza», `/accoglienza`, once Today at `/oggi`): arrivals, waiting room, days left open, what is left to invoice; a view of the agenda, beside it and the waiting list in the header's switch |
| `frontend/src/utils/oggi.js` | Pure: waiting time, next outcomes, summary, days — tested |

An automation for marketing asks `marketing_consent`: `engine.enroll` skips whoever
did not agree (an enrollment `Skipped`, once, never counted as having been through
it) and a message step re-checks before sending. Recalls pick people by
`CRM Lead.last_visit`/`last_service`, which the agenda keeps. A module adds its own
dashboard template with `crm.dashboard.templates.registra` (`requires` features).

Nothing outside `crm/clinica` imports it except `crm/registrazione.py`
(`tests/test_confine.py`); it hooks on through doc_events, `crm_timeline_gatherers`
and the registries (`engine.registra_evento`, dashboard features, widgets and templates).

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
new module would not sync. It compiles DottorCloud's catalogue too, where its `.po`
is newer (`il_catalogo_del_rilascio`): `bench update` migrates before it builds, and
the words a migrate writes in the centre's language (a qualification's points to
check, a consent's text) came out in English until the migrate after.

## Mobile

`isMobileView` (< 768px, or a phone held sideways: under 500px tall and
touched, `isPhoneSize`) picks the phone components, so what changes on a phone
uses `max-md:` — not `sm:`, which leaves 640–768px half desktop. A phone's rule in
CSS asks `(max-width: 767px), (max-height: 499px) and (pointer: coarse)`, as
`telefono.css` does; sideways, what stays put is compact (a record's card in one
row, the bar's words beside their icons).

- A tablet keeps the desk's layout, touched by a finger: a tap's size asks
  `(pointer: coarse)` (`[@media(pointer:coarse)]:`), never `max-md:` alone;
  held upright the menu folds to its icons until its button chooses
  (`AppSidebar.vue`, `menuPiegato`), the dashboard stacks below
  `GRIGLIA_MINIMA` as on a phone (`data-impilata`), and a row's chips wrap
  under a name rather than squeezing it (doc 29, eighth part). Upright, a
  record's column beside its panel is a phone's width (368px) at `md:`: what
  sits side by side there wraps by its own width, never by the screen's - a
  tab's words keep `min-w-[15rem]` in a `flex-wrap` row with their buttons, a
  section's columns wrap at 11rem (`FieldLayout/Column.vue`), cards are a grid
  of `repeat(auto-fit,minmax(12rem,1fr))`, a card that lays out by its own
  width asks a container query (`ClinicSummary.vue`).
- A settings page follows its pane, not the screen: `impostazioni-strette:`
  (`tailwind.config.js`) is the pane under 40rem, a phone's or a tablet's
  held upright beside the menu (500px). What goes in a column on a phone - a
  page's header and its actions, side-by-side columns, a preview beside its
  fields, a status beside a name - does so with it; `max-md:` stays for what
  touches the screen's edges (paddings) and the phone's own rules.
- A phone's page may be zoomed: large text on Android zooms the page (277
  points on a 360 phone at 130%), Safari's «aA» too (312 on a 390 at 125%).
  The daily pages, the records and the area hold at 280: a name is read
  whole and its chips wrap under it (`flex-wrap`, the name `max-w-full
  truncate`), a row of equal keys gives a word the width it needs
  (`minmax(min-content, 1fr)`), the record's tabs are as many as fit beside
  «More» (`quanteNellaBarra`), a sentence wraps rather than stopping
  half-way, and a key that is a word on a desk may be its icon on a phone
  (with its `aria-label`).
- What a finger drags never takes the page's scroll: a list that reorders has
  a handle, or waits on a finger (`:delay="200" :delay-on-touch-only="true"`:
  the mouse of a touch screen's PC drags at once);
  a widget of the dashboard moves from its grip, the only place that does not
  pan (`touch-action: none`, `Dashboard/DashboardGrid.vue`: grid-layout-plus
  says so only on Android). An appointment is not dragged by a finger: its
  hours change in its panel.
- Nothing only on hover: add `[@media(hover:none)]:opacity-100`, or reveal on focus.
  What the pointer shows beside a thing (a message's actions) is, where nothing
  hovers, a bar a tap shows, inside the screen, taking no tap while hidden, its
  focus on a parent the bar is in (`azioni-della-bolla` in `index.css`).
- Small controls get `.touch-target` (an invisible ring on touch screens); frappe-ui
  switches already have it. A ring a scrolling strip would cut gets room inside
  the strip (the channels above a conversation); icon buttons side by side, with
  no room for a ring, are 40px on a phone (`strumenti-compositore`, a composer's
  tools; `icone-a-dito` elsewhere, a conversation's decisions). A row a link
  opens is opened from the whole row (the link's `after:absolute after:inset-0`,
  the row's other controls above it). Long dialogs put `.dialog-footer` on their actions
  (frappe-ui's own `#actions` row gets the same treatment in `index.css`).
- Titles have no fixed height; a header stacks title, description, then actions.
- In a row the words get `min-w-0`, the control `shrink-0`; descriptions wrap.
- Three or four fields per row become one (or two); tables keep a minimum column
  width and scroll sideways.
- A list people open every day gets its own phone screen in `components/Mobile/`
  (one line per thing, found by typing, the next action a tap away, its data
  from `crm/api/sul_telefono.py`), never the desk's table in rows; the page's
  main action is `PulsanteAggiungi`; more than five tabs go through
  `SchedeDelTelefono`; pulled down from its top it reloads
  (`useTiraPerAggiornare` and `TiraPerAggiornare`: the browser's own pull is
  off, it reloaded the whole app), on the box that scrolls, there even when the
  list is empty; a back finds it as it was left, its search, rows and scroll,
  then brought up to date (`useRitorno`; a list found by typing is
  `useElencoDelTelefono`), while the menu opens it from the top; the crumb or
  the tab a record came from goes back to it (`tornaConLeBriciole`: an
  iPhone's installed app has no swipe back). The tab one is on, tapped again,
  takes the page to the top; a page with something open in it (a chat) says
  what it does first with `alToccoDellaScheda` (`utils/schedaAttiva.js`).
- A box drawn as a field (what was chosen, with the × that puts the search
  back) carries `data-campo`: `telefono.css` gives it the fields' 40px and
  16px.
- A record's card above its tabs folds away while the tab below is scrolled
  and comes back at its top (`useTestataRaccolta`): the tabs scroll in boxes
  of their own, so the page never takes it off by itself. Only somebody's
  scrolling folds it (a finger, a wheel, a key, or the keyboard up): a tab that
  scrolls by itself (the history opening at its newest day) leaves it open.
  Something that opens inside a tab (a visit to write) comes into view by
  itself.
- A conversation with its box to write in is the screen, as in a phone's own
  messengers (`useChatAperta`, `telefono.css` «11»): the bar at the bottom
  steps aside and the box (`data-compositore`) is the screen's bottom; with
  the keyboard up only the bottom rises: what is above the messages stays
  where it is, the box's row of channels (`data-via-scrivendo`) steps aside.
  On a person's
  conversation the card waits folded and the name in the header opens it; a
  thread of the Chat draws its own header in the page's (`inTestata`).
- A record's tabs on a phone are two panels, each mounted the first time it
  opens and then kept (`v-show`): the record's data (a person's Data, a deal's
  Details) and one conversation that draws every other tab (`MobileLead.vue`,
  `MobileDeal.vue`), a person's Summary first and their Chat after it. A
  person's data are one tab: the fields of the panel a
  computer shows beside the conversation, with their billing details, linked
  people and consents; what they have going (subscriptions, cycles, the waiting
  list) is the Subscriptions tab, where they came from the History, last of
  all, on a phone and on a computer alike. A panel per tab
  unmounted the one left and mounted the next, the conversation and its editor
  with it: half a second a tap on a slow phone. The router view is keyed on the
  page without its hash (`App.vue`): the hash names a tab, or the message a
  notification opens, never another page. A hash that names no tab is a
  message: it opens the conversation (`useActiveTabManager`), which lands on it
  (`target`), an email too (its name is its `id`). A page that follows its
  query itself (`?d=`, `?person=`) says so in its route (`meta.segueLaQuery`)
  and is keyed on its path; the others are rebuilt when their query changes,
  which the lists need (`ViewControls` reads `?view=` once).
- A dialog, a menu and a select are sheets from the bottom by themselves
  (`telefono.css`): never a size, a margin or a position of one's own on a
  phone. A select's list is a popper there (`vite/frappeUi.js`): set over its
  trigger, reka-ui gave a finger's scroll back while the list grew, and it
  never moved. A dialog's sheet scrolls itself, as tall as the screen at most,
  never the box behind it (`.dialog-scroll-container`): while a dialog is
  open that box takes `pointer-events: none` from the page reka-ui locks, and
  an iPhone need not scroll it under a finger; the client area's dialogs the
  same (`area/area.css`), its buttons at its foot. A sheet is tried with a finger
  (touch events), never only with the wheel, which scrolls what a finger does
  not. A popover that holds a list of choices (the agenda's filters) marks
  the list `data-foglio`, and is a sheet of 48px rows as well. A sheet's or a page's row of actions is one row on a phone: what
  does not fit goes under a «⋯» (an icon button, which stays a 44px square),
  as the form's «Discard» and «Other ways to sign» do. A sheet taken by its grabber, or anywhere while it is at its top,
  follows the finger down and closes as Escape does (`utils/trascinaFoglio.js`;
  the field one writes in, a drawing, a list's grip or a box scrolled down
  keep the finger);
  a dialog that is a screen of its own
  draws no grabber and is not dragged. A page that opens over another (a panel) hides what it covers there
  (`v-show`), or the covered page's positioned controls are drawn over it, and
  registers with `chiudeConIndietro(chiudi)` (`utils/indietro.js`): Android's
  back closes it before leaving the page, as it does a sheet or a menu.
- An icon given by name to frappe-ui is Feather's (`crm/fcrm/feather_icons.json`)
  or `lucide-…`: any other name draws an empty circle.
- A button that is only an icon says what it does (`:aria-label="__('Close')"`,
  «Opzioni», «Il mese prima»): without it VoiceOver and TalkBack read «pulsante».
  A tooltip is not its name. A switch outside a `SettingsRow` (whose words are its
  `<label>`) takes `:aria-label`: the words beside it, or in a list the name of
  what its row turns on. frappe-ui's Switch is mended at build
  (`vite/frappeUi.js`): the name goes to its button, and a check field's 1 from
  the server is drawn on. A field's words name its control: a form's `Field` and a
  record's side panel tie them (`useEtichettaDelCampo`, `useEtichetteDeiCampi`
  in `composables/nomeAlControllo.js`), a button or a select read with what it
  shows; a new list of fields does the same. What a tooltip tells on a mouse
  (a message's ticks) a screen reader reads too: `role="img"` and the same
  words as `aria-label`. A page's name is its heading for a screen reader:
  `App.vue` draws it, unseen, from the menu's words (`titoloDellaPagina`); a
  page headed by a heading of its own (a record's name) is in `CON_UN_TITOLO`.
- While somebody writes, the frame follows the keyboard (`utils/tastieraAperta.js`:
  `:root[data-tastiera='aperta']`, `--altezza-con-tastiera`, `--tastiera`): what
  must stay in sight sits at the bottom of the frame or of a sheet, never
  `position: fixed` at the bottom of the screen, which the keyboard covers.
  Android makes the page shorter by itself (`interactive-widget=resizes-content`
  in `index.html` and `area.html`, which `--tastiera` 0 says); on an iPhone the
  page never slides: a focus never scrolls it (`HTMLElement.prototype.focus`
  takes `preventScroll`, a tap's focus is handed over), a field is shown inside
  its own boxes (`inVista`, never `scrollIntoView`, which slides the page;
  a sheet's `scroll-padding` keeps it off its title and actions), and while the
  keyboard is up a finger moves only a box with something to scroll. Nothing
  follows a gesture frame by frame: the root's variables change when the
  keyboard comes, goes or changes height.
- A field asks for its keyboard (`utils/tastiera.js`): `tastieraDi(field)` for
  a DocType's field, `tastiera('telefono')`, `'email'`, `'url'`, `'codice'`,
  `'cifre'`, `'nome'` (a person's name: a capital to each word, never
  corrected; `tastieraDi` gives it to first, last and full names, and the
  public pages write the same three attributes), `'cerca'` (a list's search:
  the key closes the keyboard, a surname is never corrected) elsewhere; a whole
  number on `type="number"` has
  `inputmode="numeric"`. An amount on `type="number"` keeps the browser's
  keyboard: iPhone's decimal pad has only the comma. A DocType's amount reads
  the keyboard's separator whatever the site's format (`flt()` in
  `utils/numberFormat.js`): «12,5» is 12.5 where the site writes 1,234.56.
- A settings page scrolls as one on a phone (`data-pagina-impostazioni`): a
  setting's words above, its field under them as wide as the screen, a switch
  beside its words; a page's save bar is the screen's bar, its button as wide
  as it: a page's own action («Update», «Save») is `AzioneImpostazioni`, beside
  the title on a desk, in the bar at the bottom of the settings on a phone. A
  page's fields wait for the settings they read (`v-if="settings.doc"`).
- Text never wears the palest inks (`ink-*-4`): warnings take the 7th step.
- A table one writes in (a quote's rows) is a card per row on a phone; a table
  one only reads keeps its columns and scrolls sideways.
- What a page's first download carries, a phone pays for: a heavy control
  (the text editor) is imported with `defineAsyncComponent` where a field may
  draw it, never at the top of a component the layout loads. What is always
  mounted but opened now and then - a settings page, a global dialog, a
  record's tab - comes with `aRichiesta()` (`utils/aRichiesta.js`), a dialog
  mounted the first time it opens with `apertoUnaVolta()`; a big library used
  on a gesture (Twilio's voice SDK, the emoji) is `import()`ed where it is
  used. A package published only as CommonJS that requires `vue` brings Vue's
  template compiler along: alias it to its ES sources (`vuedraggable` in
  `vite.config.js`). A part that does not arrive loads the page again once,
  only when the version it runs is gone from the server (`utils/ricarica.js`).
  The PWA plugin's service worker removes itself (`selfDestroying`): on
  `/assets/crm/frontend/` it served no page and downloaded the whole app. The
  page's words are a script the browser keeps (`crm.www.crm.traduzioni`, its
  address carrying `impronta_delle_traduzioni()`), never inside the page, which
  no browser keeps: they were 380 KB compressed at every opening. The typeface
  is Inter cut to the Latin alphabets and the signs the words use
  (`src/carattere.css`, `src/assets/fonts/README.md`), declared after
  frappe-ui's whole files, which still draw a Greek or Cyrillic letter.
  What frappe-ui weighs for nobody is cut at the build in `vite/frappeUi.js`,
  each rewrite tested on the pinned frappe-ui: the code block without
  highlight.js, the emoji list fetched at the first ":", no Markdown format.
  A dynamic import preloads only what is not loaded (`vite/precarica.js`).
  A Lucide icon drawn by name (`Icon.vue`) goes into the page by itself
  (`utils/icone.js`), the sprite's text fetched when the app is idle; all of
  them only for the picker (`ScegliIcona.vue`), never frappe-ui's
  `spritePlugin`: 82 KB of the first download and 8,673 hidden elements.
- The first page waits on no call in a row: what the router needs comes with
  the page's boot (`crm_user`, `benvenuto`, the capabilities), and a page asks
  its calls together - what the server would answer from a capability, the
  browser asks `puo()` for before the first answer arrives.
- A tap is drawn before anything else is asked of the page. A CSS rule finds an
  element down a path (`body:has(> … > …)`), never through the whole page:
  `body:has(.x)` was looked for in 9,000 elements at every `data-state` that
  changed. Tailwind builds no typography size nobody draws (`blocklist` in
  `tailwind.config.js`): a typography rule is tried on every element. A link
  field asks for its options when its list opens, never when it is drawn
  (`Link.vue`: a person's details asked fourteen times before anybody opened
  one). The address follows a record's tab once the tab is drawn
  (`useActiveTabManager`): a push reads the scroll, and the page was laid out
  again for it in the middle of the tap. What a record's tab draws a screen
  below the first comes once the tab is drawn (`DopoIlDisegno`: a person's
  sections under the fields, seven calls, a fifth of the first tap on Details).
- A tooltip opens only where a pointer rests over things, never on a touch: where
  none does, frappe-ui's Tooltip and a Button's `tooltip` are their trigger alone
  (`utils/puntatore.js`, rewritten in `vite/frappeUi.js`; a dozen components
  each, two thirds of a person's page on a phone). What a tooltip says is never
  the only place it is said. A dialog and a menu's content mount at their first
  opening (`Dialog.vue`, `Dropdown.vue` there), and stay.

---

## Tests

```bash
cd frontend
yarn test:run      # single run
yarn test          # watch mode
```

- **1198 tests · ~15s** — all must pass before committing
- Location: `frontend/tests/unit/`
- Only pure utility functions are unit-tested (no Vue component tests yet)
- Add tests in `tests/unit/` when adding pure logic to `src/utils/`

No check runs on a pull request (NPM2, 05/10/2026): the server's tests, the
frontend's, the linters and Semgrep run every night on develop, and every
workflow - the migration from develop and the E2E tests too - by hand from
Actions > Run workflow, on develop or on a branch, when a change needs it. So
before a pull request is merged, what CI would have said is run on the machine:
prettier 3.2.5, eslint and oxlint on the files changed, `yarn test:run`, the
build; ruff 0.8.1 and Semgrep on the Python changed, and the server's tests of
the modules it touches (`bench --site … run-tests --module …`). A change to
patches or DocTypes is migrated on a site first, or run through the Migration
workflow on its branch. Out of a pull request Semgrep reads the whole
repository, with the rules as they are that night: a finding is put right, or,
where the shape is meant (an OAuth redirect is a GET, a template is the app's
own), carries `# nosemgrep: <rule> — why` on its line or the line before.

The server's tests run on a CI bench with only frappe and crm. What needs
frappe_whatsapp asks `crm.tests.serve_whatsapp(self)` (skipped there, run where
the app is) or `con_whatsapp()` to leave WhatsApp's part out; what needs Builder
stands in for it with `livelli.registro_isolato` and the "builder" requirement.
Without the repository's `CODECOV_TOKEN` the coverage stays in the run's artifacts.

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
