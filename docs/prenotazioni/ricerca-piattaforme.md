# Online-booking platforms in Italy: integration research for Frappe CRM connectors

Research date: 2026-09-24. Legend:

- **[V]**: verified from official docs, an official OpenAPI/Swagger file, or an official help page fetched during this research
- **[V-2]**: verified from a secondary but concrete source, such as an archived copy of the official docs, an API-Evangelist capture of gated docs, or a partner's integration guide
- **[I]**: inferred or from memory. Treat it as a hypothesis and check it before coding.
- **not verified**: I could not confirm it. No endpoint is invented here.

Local copies of the specs I downloaded are in the same scratchpad folder: `calendly.yaml` (Calendly OpenAPI), `cal.json` (Cal.com v2 OpenAPI), `sbadmin.json` (SimplyBook REST v2 admin Swagger), `setmore.apib` (Setmore Apiary JSON), `booksyarch.html` (archived Booksy Public API docs), `mba.yml` (Mindbody appointment OpenAPI, API-Evangelist copy).

---

## 0. TL;DR: priority matrix for an Italian clinic, salon or studio CRM

| # | Platform | Sector | Italy | API access | Inbound bookings | Push availability / blocks | Recommended connector |
|---|---|---|---|---|---|---|---|
| 1 | **MioDottore (Docplanner)** | medical | #1 in IT | Partner (certified integrator), OAuth2 client-credentials | Webhook push + pull queue | Yes: `PUT slots`, `POST breaks` | **Full API connector** (apply as integrator) |
| 2 | **Treatwell (ex Uala)** | beauty | #1 beauty in IT (uala.it redirects to treatwell.it) | **Closed**. Partner deals only, no public docs | Email notifications | **iCal import per staff member** ("Calendario esterno") | ICS feed from CRM + parse notification emails |
| 3 | **Doctolib (incl. ex Dottori.it)** | medical | Yes (since 2021; dottori.it redirects to doctolib.it) | Partner-only, portal gated (developers.doctolib.com returns 401) | not verified | not verified | Partnership, or email parsing |
| 4 | **iDoctors** | medical | Yes (since 2008, ~14k specialists) | No public API. Integrates with PMS vendors (MEG, AlfaDocs) | Google Calendar sync | Google Calendar sync | Google Calendar bridge |
| 5 | **Elty** ("Elti" in the brief) | medical (marketplace + family doctor software "Elty DaVinci") | Yes (Italian) | No public API. Integrates with PMS vendors (AlfaDocs, MEG) | not verified | not verified | Partnership (bilateral like AlfaDocs), else email |
| 6 | **Top Doctors Italia** | medical | Yes | Mentions "API/integrations" in legal terms, no public docs | not verified | not verified | Partnership / email |
| 7 | **Pazienti.it** | medical | Yes | No API found | – | – | Email parsing |
| 8 | **Fresha** | beauty | Yes (fresha.com/it) | **No merchant API**, no webhooks (read-only BI "Data Connector" only) | Google 2-way sync; ICS export | **ICS import as blocked time** / Google 2-way | Google Calendar bridge or ICS |
| 9 | **Booksy** | beauty/barber | Limited (booksy.com/it-it redirects to /en-it/) | Partner-only, RSA-JWT | Webhook (CREATED/MODIFIED/CANCELLED) | Time-off API; "R" reservation-type appointments | Full API if you get partner status |
| 10 | **Planity** | beauty | **Not in Italy** (planity.it returns "unsupported-country") | none public | – | – | Skip |
| 11 | **SimplyBook.me** | general | Yes (EU server `.it`) | **Public**. REST v2 + JSON-RPC | Webhooks (REST-managed) + JSON-RPC callback | calendar-notes with `time_blocked` | **Full API connector** |
| 12 | **Calendly** | general/professionals | Yes | **Public** OAuth2/PAT | Webhooks (HMAC) | No block API (use connected calendar) | API + Google bridge for blocks |
| 13 | **Cal.com** | general | Yes | **Public** (API key/OAuth) | Webhooks (HMAC) | **ICS feed subscription** + calendar events | **Full API connector** |
| 14 | **Microsoft Bookings** | general (M365) | Yes | **Public** Graph API | No Bookings change notifications [I] | Staff Outlook calendar free/busy [I] | Graph polling of `calendarView` |
| 15 | **Acuity Scheduling** | general/wellness | Yes (EN) | **Public** Basic/OAuth2 | Webhooks (form-encoded, HMAC) | `POST /blocks` | **Full API connector** |
| 16 | **Setmore** | general | Yes | Limited beta (email api@setmore.com) | No webhooks documented | No block endpoint | Read-only poll |
| 17 | **TIMIFY** | general/enterprise | Yes (timify.com/it) | **Public** developer platform (app id/secret) | Webhooks (custom header secret) | Shifts "BLOCKER" import | **Full API connector** |
| 18 | **Mindbody** | fitness/wellness | Small | Public (paid, metered) | Webhooks (HMAC) | Availabilities/unavailabilities | Low priority |
| 19 | **Vagaro** | beauty/fitness | Negligible (US/UK/CA/AU) | Enterprise API, paid add-on | Webhooks | – | Skip |
| 20 | **Square Appointments** | general | **Not available in Italy** | Public | Webhooks | – | Skip |
| 21 | **Phorest** | salon | Minor | Partner (request by email), Basic auth, **no webhooks** | Poll `updated_at` | – | Low priority |
| 22 | **Shore / Salonized / WeGest-Prenotado / PRIMO-BeWelly / Maki App / TuoTempo / GipoNext / AlfaDocs / MEG / Appuntoo / CUP24** | various | Yes | Mostly none public (AlfaDocs has an OAuth API) | – | – | See §4 |
| 23 | **Google Reserve / Actions Center** | all | Yes | Only for **scheduling-platform partners** | Booking server (you host it) | Feeds | Only if the CRM becomes an aggregator |
| 24 | **Easy!Appointments** (self-hosted) | general | OSS | Public REST | Webhooks (X-EA-Token) | `/unavailabilities` | Easy connector |
| 25 | **TheFork / Zenchef** | restaurants | Yes | Partner B2B API / Zenchef token API | Webhooks | – | Out of scope, noted only |

**What "Elti" is: [V]** Almost certainly **Elty** (https://elty.it). It is an Italian medical booking marketplace ("Cerca, confronta e prenota online visite mediche", with more than 2,000 facilities) and also sells *Elty DaVinci*, practice software for family doctors (https://medico.davinci.elty.it/). It is not Treatwell or Uala.

---

## 1. Medical platforms

### 1.1 MioDottore / Docplanner (Italian domain `www.miodottore.it`)

- Website: https://www.miodottore.it (docplanner.it redirects there) [V]. Pro site: https://pro.miodottore.it
- Sector: medical (doctors, clinics, psychologists, physiotherapists). Largest Italian marketplace. Group sister brands: Doctoralia (ES/BR/MX…), ZnanyLekarz (PL), jameda (DE), and TuoTempo (enterprise patient engagement, Italy).
- API: **Docplanner Integrations API**. It is partner-only: you are onboarded as a PMS/software vendor. There is a sandbox, and **acceptance testing before production is mandatory**. "Only integrations with all the flows implemented will be accepted" (resource mapping, bi-directional booking sync, real-time schedule updates). [V] https://integrations.docplanner.com/guide/integration-process.html
- Docs [V]:
  - Reference: https://integrations.docplanner.com/docs/
  - Guide: https://integrations.docplanner.com/guide/
  - Auth: https://integrations.docplanner.com/guide/fundamentals/authorization.html
  - Push vs pull: https://integrations.docplanner.com/guide/callbacks/push-vs-pull.html
  - SDKs: PHP https://github.com/DocPlanner/integrations-api-sdk-php and .NET
  - Integrations Hub guide: https://docplanner.github.io/integrations-hub-front-app/guide/

**Auth [V]:** OAuth2 client-credentials.
```
POST https://www.miodottore.it/oauth/v2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded
grant_type=client_credentials&scope=integration
```
The response contains `access_token`, which is valid for **24 h**. Send it as `Authorization: Bearer <token>`. An unauthenticated call to `https://www.miodottore.it/api/v3/integration/facilities` returns 401 (checked live).

**Base URL [V]:** `https://www.miodottore.it/api/v3/integration/`

**Endpoints [V]** (all relative to the base; `{f}`=facility_id, `{d}`=doctor_id, `{a}`=address_id):

| Purpose | Method + path |
|---|---|
| Facilities | `GET /facilities`, `GET /facilities/{f}` (`?with=facility.doctors`) |
| Doctors (staff) | `GET /facilities/{f}/doctors`, `GET /facilities/{f}/doctors/{d}` (`with=doctor.profile_url,doctor.specializations,doctor.addresses…`) |
| Addresses (= a doctor's calendar at a location) | `GET /facilities/{f}/doctors/{d}/addresses`, `GET …/addresses/{a}`, `PATCH …/addresses/{a}`, `DELETE …/addresses/{a}/integration` |
| Service dictionary | `GET /services` |
| Address services | `GET/POST …/addresses/{a}/services`, `GET/PATCH/DELETE …/services/{address_service_id}` |
| Insurance | `GET /insurance-providers`, `GET /insurance-providers/{id}/plans`, `GET/POST/PUT …/addresses/{a}/insurance-providers`, `DELETE …/insurance-providers/{id}` |
| Calendar on/off | `GET …/addresses/{a}/calendar`, `POST …/calendar/enable`, `POST …/calendar/disable` |
| **Breaks (blocks)** | `GET …/addresses/{a}/breaks?since=&till=`, `POST …/breaks`, `GET/PATCH/DELETE …/breaks/{break_id}` |
| **Slots (availability)** | `GET …/addresses/{a}/slots?start=&end=` (max 180 days), **`PUT …/addresses/{a}/slots`** (replace slots), `DELETE …/slots/{date}` (delete a day's slots), `POST …/slots/{start}/book` (book) |
| **Bookings** | `GET …/addresses/{a}/bookings?start=&end=&page=&limit=`, `GET …/bookings/{booking_id}`, `DELETE …/bookings/{booking_id}` (cancel), `POST …/bookings/{booking_id}/move`, `PUT …/bookings/{booking_id}/confirm` |
| Presence | `POST/DELETE …/bookings/{id}/presence/patient` |
| Reviews | `PUT /facilities/{f}/doctors/{d}/opinion-request` |
| **Notifications (pull)** | `GET /notifications` (one, FIFO), `GET /notifications/multiple?limit=1..100` |
| Release notifications | "Release Notifications" endpoint, at most once per 60 min (exact path not verified) |

**Booking object [V]** (fields from the reference examples):
```json
{ "id":"string", "status":"booked", "start_at":"2021-05-16T14:00:00+01:00", "end_at":"2021-05-16T14:30:00+01:00",
  "duration":30, "booked_by":"user|doctor", "booked_at":"…", "canceled_by":"…", "canceled_at":null,
  "patient":{"name":"","surname":"","email":"","phone":"+39…","birth_date":"1985-01-01","nin":"<codice fiscale>","gender":"m|f","is_returning":false,"insurance_number":null},
  "address_service":{"id":"","name":"","price":50,"is_price_from":false,"is_default":false,"service_id":"","description":"","is_visible":true},
  "comment":"", "insurance":{"id":"","name":"","plan":null,"plan_id":null} }
```
- Dates are ISO 8601 with offset (`2020-12-01T00:00:00+01:00`). URL-encode `:` as `%3A` and `+` as `%2B` in query strings. Times are converted to the locale's timezone (Europe/Rome for IT).
- Lists are HAL-style: `_items`, `_links` (self, first, last, next, previous), `_embedded`. Pagination uses `page`, `limit` (default 100) and returns `page`, `limit`, `pages`, `total`.

**Request bodies [V]:**
- `PUT …/slots` (declare availability):
  ```json
  {"slots":[{"address_services":[{"address_service_id":"111","duration":30}],"start":"2021-05-16T14:00:00+01:00","end":"2021-05-16T15:00:00+01:00","insurance_accepted":"with-insurance-only","insurance_providers":[52,67]}]}
  ```
- `POST …/breaks`: `{"since":"…+01:00","till":"…+01:00","description":"…","apply_on_coupled_addresses":true}`
- `POST …/slots/{start}/book`: `{"address_service_id":"113","is_returning":false,"duration":30,"comment":"…","patient":{"name","surname","email","phone","birth_date","nin","gender","marketing_consent","data_privacy_consent"}}` (optional: `label`, `insurance_provider_id`, `insurance_plan_id`, `is_recurring`)
- `POST …/bookings/{id}/move`: `{"address_service_id":"112","start":"…","duration":30,"address_id":"optional"}`

**Webhooks / notifications [V]:**
- Two modes:
  - **Push:** Docplanner POSTs to your HTTPS endpoint from a single fixed IP. Whitelist that IP. Optional "API Key authorization in the request header", arranged with the integration specialist (header name not published). There is **no HMAC signature**.
  - **Pull:** you read the FIFO queue. Messages expire after 72 h.
- Push retries: return 2xx. A failed delivery is retried twice, after 5 and 10 min, and then archived.
- Event names: `slot-booking`, `slot-booked`, `booking-canceled`, `booking-moved`, `booking-moving`, `booking-confirmed`, `booking-payment-status-changed`, `break-created`, `break-removed`, `break-moved`, `presence-marked`, `address-service-created|deleted|changed`, `address-commercial-type-changed`, `address-assigned`, `address-unassigned`.
- Payload shape:
  ```json
  {"name":"slot-booking","data":{"facility":{"id","name"},"doctor":{"id","name","surname"},"address":{"id","name","street","post_code"},
   "visit_booking_request":{"booking_at","booking_by","duration","start_at","end_at","address_service":{…},"patient":{…},"comment"}},
   "created_at":"2021-05-12T10:18:34+01:00"}
  ```
  For `slot-booked` and similar events, the key under `data` is the booking object (for example `visit_booking`). The exact key per event is **not verified**: dispatch on `name` and check the sandbox.

**Rate limits [V]:** GET 8,000/h. Write calls 40/min. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Used`, `X-RateLimit-Reset` (ISO 8601). Over the limit returns 429.

**Fallbacks:**
- MioDottore's agenda used to offer Google Calendar sync. Their blog now says it "no longer makes sense" [V-2] https://pro.miodottore.it/blog/centrimedici/gestione/miodottore-vs-google-calendar
- No Zapier app (zapier.com/apps/docplanner returns 404).
- Booking confirmation emails from MioDottore can be parsed.

---

### 1.2 Elty (the "Elti" in the brief)
- Websites: https://elty.it (marketplace) and https://medico.davinci.elty.it (Elty DaVinci practice software for family doctors) [V]
- Italy: Italian company with more than 2,000 facilities; Milan and major cities.
- API: **no public API found**. Bookings are integrated **bilaterally with PMS vendors**:
  - AlfaDocs: open slots go to Elty, bookings and cancellations come back in real time, price changes propagate [V-2] https://blog.alfadocs.com/agenda-senza-buchi-e-pi%C3%B9-visibilit%C3%A0-online-con-lintegrazione-di-alfadocs-ed-elty
  - MEG ("Tramite le API del MEG è ora possibile integrare iDoctors ed ELTY") [V-2] https://www.gestionalemedico.it/
- Auth, endpoints, webhooks: not verified (non-public).
- Fallback: contact Elty partnerships for a PMS integration, or parse booking emails.

### 1.3 Doctolib Italia (absorbed Dottori.it)
- https://www.doctolib.it. `www.dottori.it` redirects to `www.doctolib.it` (checked live) [V]. In Italy since 2021; it also acquired Vettore Medical and Appocrate [V-2].
- API: partner and integration API behind the **authentication-gated** portal https://developers.doctolib.com (returns 401 to anonymous users) [V]. There is no public OpenAPI spec. Italian integrations run through PMS partners, for example Vettore Medical https://www.vettoremedical.it/integrazione/.
- Endpoints and webhooks: not verified.
- Fallback: partnership request, or parse email notifications.

### 1.4 iDoctors
- https://www.idoctors.it. Private specialist visits since 2008, about 14,000 specialists [V-2].
- Integration statements [V] (https://www.idoctors.it/collabora):
  - "possibilità di integrazione con tutti i gestionali per centri medici"
  - "agenda sempre sincronizzata con la segreteria e con **Google Calendar**"
  - Doctor app "AgendaMedici"
- API: none public. PMS integrations exist with MEG and AlfaDocs (https://www.alfadocs.com/marketplace/applicazioni/idoctors).
- **Recommended:** a Google Calendar bridge. The CRM reads and writes the Google calendar that iDoctors syncs with. The direction and conflict semantics are not verified.

### 1.5 Top Doctors Italia
- https://www.topdoctors.it, plus the Top Doctors 360 agenda (https://360.topdoctors.it). Its legal terms mention "widgets, integrations, API", but there are no public docs. Not verified. Contact the company for a partnership, or parse emails.

### 1.6 Pazienti.it
- https://www.pazienti.it. Health portal with doctor directory and booking. No API or integration documentation found. Fallback: email parsing.

### 1.7 Other Italian medical channels (for completeness)
- **CUP Solidale / CUP24**: https://cup24.it (cupsolidale.it redirects there). Private-CUP marketplace. It integrates with PMS vendors such as MEG. No public API found.
- **TuoTempo** (https://www.tuotempo.it): Docplanner group, enterprise patient engagement for hospitals. Partner only.
- **MiAgenda** (https://specialisti.miagenda.it): free agenda app for specialists. The site returned 503 during research, so not verified.
- **AlfaDocs** (dental/medical PMS): it has an **OAuth2 API** [V-2] https://developers.alfadocs.cloud/docs/quickstart
  - Base `https://app.alfadocs.com`; token at `POST /oauth2/token`
  - `GET /api/v1/me`
  - `GET /api/v1/practices/{practiceId}/archives/{archiveId}/free-slots/{startDate}`
  - `GET …/operators`
  - Credentials from apps@alfadocs.com. Relevant only if a clinic already uses AlfaDocs.
- **MEG, GipoNext, OpenStudio, Appuntoo, FisioDesk, PsicoGest, OsteoEasy, DBMedica, CGM XMedical**: Italian PMS vendors, not marketplaces. MEG explicitly offers APIs that bridge iDoctors, Elty and CUP24 [V-2].
- **QuiSalute, GuidaMedica, Prenoto Visite**: domains did not resolve (curl `000`). Treat them as defunct or irrelevant.
- **"Doctorlink", "Dottori online"**: no Italian booking platform of note found.
- **"YouMed"** (youmed.it): a medical video/education site, not a booking platform [V].
- **"Prenotami"**: prenotami.it is a parked domain [V]. `prenotami.esteri.it` is the Foreign Ministry consular booking system (irrelevant). "Prenota Online" is a generic term; `prenotaonline.it` redirects to a municipal site.

---

## 2. Beauty / wellness platforms

### 2.1 Treatwell (includes ex-Uala)
- https://www.treatwell.it. `www.uala.it` redirects to `treatwell.it` (checked live) [V]. Treatwell and Uala merged into one group: https://www.treatwell.it/partners/risorse/blog/treatwell-uala-si-uniscono-unico-gruppo/. Salon software: *Treatwell Connect* / *Treatwell PRO*. Salonized is owned by Treatwell.
- API: **no public API**. Treatwell says it opened "nuove forme di collaborazione con altri software gestionali" [V-2]. These are bilateral partner deals; Salonized is the flagship integration. The API Tracker entry and the "Treatwell API" references in the partner T&Cs point to non-public APIs.
- **iCal import (block availability) [V]:**
  - Treatwell Connect → Team → staff member → **"Calendario esterno"** → paste iCal URL → "Link calendario".
  - "Connect aggiorna automaticamente la tua disponibilità e blocca gli orari in base all'altro calendario."
  - It is **one-way**: Connect appointments are not written to the other calendar.
  - Tip: use `https://` instead of `webcal://`.
  - Sources: https://partners.treatwell.com/hc/it/articles/115005413069 and https://partnercare.treatwell.com/s/article/Come-impostare-la-sincronizzazione-di-iCal?language=it
- **Inbound bookings:** use email. Proven pattern [V-2] (Booking Connect for Phorest, https://www.booking-connect.com/guide): add a dedicated inbound address as a *secondary notification email* in Treatwell. Parse the booking, cancel and change emails, and create or update events in the CRM. Publish a per-staff iCal from the CRM and paste it into "Calendario esterno".
- Treatwell iCal **export**: not verified.
- Webhooks: none public. Zapier: no app (404).
- Reserve with Google: Treatwell is a partner [V-2].

**Recommended CRM design for Treatwell:**
- `GET /api/method/crm.ics.staff_feed?token=…`: a per-staff busy feed (VEVENT with `TRANSP:OPAQUE`, `SUMMARY:Occupato`, stable `UID`s).
- An inbound email handler (Frappe Email Account plus parser) keyed on Treatwell's sender domain.

### 2.2 Fresha
- https://www.fresha.com/it (Italy locale live) [V].
- API: **none** for merchants: no REST/GraphQL, no webhooks. There is only a read-only "Data Connector" for BI tools [V-2] (supergood.ai, usecarly.com, apitracker). No Zapier app.
- **Calendar sync [V]** (https://www.fresha.com/help-center/knowledge-base/calendar/101373-sync-your-fresha-calendar):
  - "Export events to calendar"; "Import events to calendar: pull events from your calendar into Fresha as **blocked time**"; "**Two-way sync** with your calendar (Google calendar only)".
  - Other calendars use an **ICS link** that you paste.
  - Scope is per workspace and **per team member**. Choose whether to sync appointments and/or blocked time, and the detail level ("All details" or "Time and duration only").
  - Sync takes up to 15 min.
- **Recommended:**
  - Option A: Google Calendar bridge. The CRM syncs with a Google calendar per staff member via the Google Calendar API and watch channels; Fresha two-way-syncs to the same calendar.
  - Option B: the CRM publishes an ICS busy feed that Fresha imports as blocked time, and reads bookings from email notifications. Whether Fresha exposes an ICS export URL for non-Google calendars is unclear (not verified).

### 2.3 Booksy
- https://booksy.com (booksy.com/it-it redirects to /en-it/, so Italian presence is limited) [V]. Sector: barbers, hair, beauty. Reserve with Google partner.
- API: **Booksy Public API**, partner-only. Docs at https://docs.booksy.com/v01.html are HTTP-Basic gated (401). The archived identical docs are at https://web.archive.org/web/20220706184310/https://alpha.docs.booksy.net/ [V-2 via archive].
- **Base URL:** `https://<cc>.booksy.com/public-api/<cc>/`, for example `https://us.booksy.com/public-api/us/`. The host answers 401 `{"detail":"Authentication credentials were not provided."}`.
- **Versioning:** `Accept: application/json; version=0.3`
- **Auth [V-2]:**
  - Build an RS256 JWT with the partner RSA private key (separate keys for sandbox and prod). Claims: `{"iss":"https://public-api.booksy.com","iat":now,"exp":now+3min,"aud":"<partner_uuid>"}`.
  - `POST {base}/token/` (form: `partner_name`, `token`) returns `{"access","refresh"}`.
  - Access token lives 5 min; refresh token lives 3 days. Refresh with `POST {base}/refresh/` (form `refresh`).
  - Send `Authorization: Bearer <access>`.
- **Endpoints [V-2]** (prefix `{base}/business/{business_id}`):
  - Appointments:
    - `GET appointment/` (query `booked_from`, `booked_till` as `YYYY-MM-DDTHH:MM`), `GET appointment/{id}/`
    - `POST appointment/`, `PUT appointment/{id}/`, `POST appointment/mapping/` (`import_uid`)
    - `PATCH appointment/{id}/status/{cancel|confirm|decline|finish|no_show}/`
  - Resources (staff/appliances): `GET/POST resource/`, `GET/PATCH/DELETE resource/{id}/`
  - Services: `GET/POST service/`, `…/service/{id}/variant/`, `service_category/`
  - Customers: `GET/POST customer/`, `GET/PATCH/DELETE customer/{id}/`
  - Schedules: `GET/PUT schedule/default/`, `GET schedule/custom/`, `PUT schedule/custom/{date}/`, `GET/PUT schedule/resource/{rid}/default/`, `…/custom/{date}/`
  - **Time off (blocks):** `GET/POST schedule/resource/{rid}/time_off/`, `GET/PATCH/PUT/DELETE …/time_off/{id}/`. Body: `{"date_from":"2021-12-01","date_till":"2021-12-02","hour_from":"09:00","hour_till":"13:00","reason_code":"other","reason":"…","approved":true}`. Reason codes: `personal_day, sick_day, vacation, training, no_show, late, early, other` for staff; `day_off, holiday, maintenance, break, other` for appliances.
- **Appointment object [V-2]:**
  ```json
  {"id":1,"business_id":123,"booked_for_id":321,"booked_from":"2021-07-02T18:15","booked_till":"2021-07-02T19:30",
   "status":"A","type":"C","customer_name":"","customer_phone":"","customer_email":"","customer_note":null,"business_note":null,
   "business_timezone":"Europe/Warsaw","import_uid":"some-uid",
   "subbookings":[{"id":11,"booked_from":"…","booked_till":"…","staffer_id":456,"appliance_id":null,"service_variant_id":789,"service_name":"…"}],
   "traveling":null}
  ```
  - Datetimes are **naive local** times; interpret them in `business_timezone`.
  - Status codes: `A` accepted, `C` cancelled, `D` declined, `F` finished, `M` modified by customer, `N` no-show, `P` proposed by staff, `W` waiting for business confirmation.
  - Type codes: `B` by business, `C` by customer, `R` **resource time reservation** (usable to block a slot).
  - Create body: `booked_for_id`, `subbookings[{booked_from, booked_till?, service_variant_id|service_name, staffer_id|appliance_id (-1 = auto)}]`, `customer_name`, `customer_phone`, `customer_email`, `business_note`, `force`.
- **Pagination:** DRF-style `{"count","next","previous","results"}`.
- **Webhook [V-2]:** an HTTP POST to a partner endpoint configured at onboarding. Body `{"action":"CREATED|MODIFIED|CANCELLED","appointment":{…}}`. Respond 200. Retries after 5, 10, 20 and 40 min, then stop. **Signing is not documented.**
- **Rate limits [V-2]:** 10/min unauthenticated (token), 200/min authenticated. Over the limit returns 429.
- **Fallback:** Booksy supports .ics import for one-off imports. Its Google Calendar sync for staff is not verified. Apply for partner status, or use email.

### 2.4 Planity
- https://www.planity.com. **Not in Italy**: planity.it redirects to `/unsupported-country` (checked live) [V]. Present in France, Belgium and Germany; Italy was "planned" in the 2024 Series C [V-2]. No public API. Skip for now.

### 2.5 Italian salon software with built-in booking portals (no public APIs found)
- **WeGest** (https://www.wegest.it) with the consumer portal **Prenotado** and custom booking apps. No public API found.
- **PRIMO Software** with the **BeWelly** app (https://primosoftware.it/agenda-appuntamenti/). No API found.
- **Maki App** (https://www.makiapp.it). No API found.
- **EZsalonware**, **Bookio**, **BarberOS**, **Colibryx**: no public APIs found.
- **Shore** (shore.com): public docs repo archived in 2019; no current public API found; shore.com/it returns 404.
- **Salonized**: Treatwell-owned; salonized.com/it returns 404. It has an integration with Treatwell; no public API found.
- **Phorest**: Irish; API on request (api-requests@phorest.com), HTTP Basic `global/{email}` + password, scoped `business/{businessId}/branch/{branchId}`, **no webhooks** (poll with `updated_at`) [V-2] https://developer.phorest.com/docs/getting-started. Little Italian presence.
- **"Sunday"/"Flowbook"/"GoBooking"/"Appuntamenti.it"/"Agendo"/"MyAgenda"/"Mia Agenda"/"Bookly.it"**: their `.it` domains did not resolve [V]. "Bookly" is a WordPress plugin (booking-wp-plugin.com) with Google Calendar two-way sync as a paid add-on. "Qaplà" is a shipping-tracking SaaS, not booking.
- Fallback for all of these: the salon's own Google Calendar sync if offered, or email parsing.

### 2.6 Mindbody (fitness/wellness; small Italian presence)
- Docs: https://developers.mindbodyonline.com (Public API v6, Webhooks API https://developers.mindbodyonline.com/WebhooksDocumentation).
- **Auth [V-2]:** headers `Api-Key: …` and `SiteId: …`, plus an optional staff bearer token.
- **Base [V-2]:** `https://api.mindbodyonline.com/public/v6/`
- **Appointment endpoints [V-2]:**
  - `GET appointment/staffappointments`, `GET appointment/bookableitems`, `GET appointment/availabledates`, `GET appointment/scheduleitems`, `GET appointment/unavailabilities`
  - `POST appointment/addappointment`, `POST appointment/updateappointment`
  - `POST/PUT appointment/availabilities`, `DELETE appointment/availability`
- **Webhook events [V]:** `appointmentBooking.created`, `appointmentBooking.updated`, `appointmentBooking.cancelled`, `appointmentAddOn.created`, `appointmentAddOn.deleted`.
- **Signature [V-2]:** header `X-Mindbody-Signature: sha256=<base64(HMAC-SHA256(body, messageSignatureKey))>`.
- API calls are metered (paid).

### 2.7 Vagaro
- Enterprise Business API V2 at https://docs.vagaro.com (OAuth client id/secret). Webhooks for appointments and customers. Paid add-on ($10/month) [V-2]. Not active in Italy. Skip.

---

## 3. General-purpose schedulers (public APIs)

### 3.1 SimplyBook.me (strongest general option with a full public API)
- https://simplybook.me. Has an EU server (`.it`).
- Docs:
  - https://simplybook.me/en/api/developer-api
  - Swagger: **https://simplybook.me/api/swagger-admin** and https://simplybook.me/api/swagger-public [V]
  - JSON-RPC: https://help.simplybook.me/index.php/Company_administration_service_methods

**REST v2 [V from swagger]**
- Servers: `https://user-api-v2.simplybook.me`, **`https://user-api-v2.simplybook.it`** (Europe), plus `.asia`, `.vip`, `.cc`, `.us`, `.pro`.
- Auth:
  - `POST /admin/auth` with `{"company","login","password"}` returns `TokenEntity {token, company, login, refresh_token, domain, require2fa, allowed2faproviders, auth_session_id}`.
  - Handle 2FA with `POST /admin/auth/2fa`. Refresh with `POST /admin/auth/refresh-token` (`{company, refresh_token}`). Log out with `POST /admin/auth/logout`.
  - Headers: `X-Company-Login: <company>`, `X-Token: <token>`.
- Endpoints:
  - Bookings:
    - `GET /admin/bookings` (`page`, `on_page`, `filter[upcoming_only]`, `filter[status]` = confirmed|confirmed_pending|pending|canceled, `filter[services][]`, `filter[providers][]`, `filter[client_id]`, `filter[date]`, `filter[date_from]`, `filter[date_to]`, `filter[search]`)
    - `GET /admin/bookings/{id}`, `POST /admin/bookings`, `PUT /admin/bookings/{id}` (edit/reschedule), `DELETE /admin/bookings/{id}` (cancel)
    - `PUT /admin/bookings/{id}/approve|decline|status|comment`, `GET /admin/bookings/{id}/links`
  - Calendar view: `GET /admin/calendar` (same filters, `mode`). It returns `Calendar_BookingEntity {id, service_name, service_id, provider_name, provider_id, client_name, client_email, client_phone, client_id, from, to, status, duration, …}`, which is handy for sync.
  - Availability:
    - `GET /admin/schedule?service_id&provider_id&date_from&date_to`
    - `GET /admin/schedule/slots?service_id&provider_id&date`
    - `GET /admin/schedule/available-slots?service_id&provider_id&date&count`
    - `GET /admin/schedule/first-available-slot`
    - `GET /admin/timeline/slots?service_id&date_from&date_to&provider_id&with_available_slots`
  - **Blocks:** `GET/POST /admin/calendar-notes`, `GET/PUT/DELETE /admin/calendar-notes/{id}`. Body `CalendarNoteRequestEntity {provider_id, service_id, start_date_time, end_date_time, note_type_id, note, mode, time_blocked:true}`. Note types: `GET /admin/calendar-notes/types`.
  - Services: `GET/POST /admin/services`, `GET/PUT/DELETE /admin/services/{id}`
  - Staff: `GET/POST /admin/providers` (`filter[service_id]`), `GET/PUT/DELETE /admin/providers/{id}`
  - Clients: `GET/POST /admin/clients` (`filter[search]`), `GET/PUT/DELETE /admin/clients/{id}`, `…/block|unblock`
  - **Webhooks:** `GET /admin/webhooks`, `POST /admin/webhooks` `{"url","event"}` where event is one of `new_booking | change_booking | cancel_booking | new_client | change_client | delete_client | new_invoice | new_offer`; `DELETE /admin/webhooks/{id}`.
- Objects:
  - Booking: `AdminBookingDetailsEntity {id, code, is_confirmed, start_datetime, end_datetime, duration, status, service_id, provider_id, client_id, location_id, category_id, service{…}, provider{id,name,email,phone,…}, client{id,name,email,phone,…}, can_be_edited, can_be_canceled, invoice_*}`
  - Create body: `AdminBookingBuildEntity {start_datetime, end_datetime, service_id, provider_id, client_id, location_id, category_id, count, additional_fields[], recurring_settings, accept_payment, …}`
  - Datetimes are `"YYYY-MM-DD HH:MM:SS"` in company-local time [I: verify offset handling].
- Pagination: lists return `{data:[…], metadata:{items_count, pages_count, page, on_page}}`.
- **Webhook/callback payload [V-2]** (official example repo https://github.com/vetalsimplybook/simplybook_callback_example_php): raw JSON `{"booking_id","booking_hash","company","notification_type":"create|cancel|change|notify"}`. The **payload is only an ID**; fetch details via the API.
- **No HMAC is documented.** Verify authenticity by calling `GET /admin/bookings/{booking_id}`, or with JSON-RPC `getBookingDetails(id, sign)` where `sign = md5(booking_id + booking_hash + secret_api_key)`.
- **JSON-RPC (legacy):** `https://user-api.simplybook.me/login` → `getToken(company, apiKey)` / `getUserToken(company, login, password)`. Services: `https://user-api.simplybook.me` (public, headers `X-Company-Login` + `X-Token`) and `/admin` (header `X-User-Token`). Methods: `getBookings`, `getBookingDetails`, `book`, `cancelBooking`, `getStartTimeMatrix`, `getEventList`, `getUnitList`, `getClientList`.
- Rate limits: not formally documented. Tokens are valid about 1 h [V-2].
- Zapier: yes (zapier.com/apps/simplybook).

### 3.2 Calendly (API v2)
- https://calendly.com. Docs: https://developer.calendly.com. OpenAPI: **https://developer.calendly.com/openapi/calendly-api.yaml** [V]
- Base: `https://api.calendly.com`. Auth: `Authorization: Bearer <PAT or OAuth2 token>`. OAuth metadata: https://calendly.com/.well-known/oauth-authorization-server
- **Endpoints [V]:**
  - `GET /users/me`, which returns `resource.uri` and `current_organization`
  - `GET /scheduled_events?user|organization=<uri>&status=active|canceled&min_start_time&max_start_time&sort=start_time:asc&count&page_token&invitee_email`
  - `GET /scheduled_events/{uuid}`
  - `GET /scheduled_events/{uuid}/invitees?status&email&count&page_token`; `GET /scheduled_events/{event_uuid}/invitees/{invitee_uuid}`
  - `POST /scheduled_events/{uuid}/cancellation` `{"reason"}`
  - `POST /invitees` (Scheduling API, create booking): `{"event_type":"<uri>","start_time":"<UTC ISO>","invitee":{"name","first_name","last_name","email","timezone","text_reminder_number"},"location":{…},"questions_and_answers":[…],"event_guests":[…]}`
  - `GET /event_types?user|organization&active&count&page_token` (services); `POST /event_types`
  - `GET /event_type_available_times?event_type&start_time&end_time` (slots): `[{status, invitees_remaining, start_time, scheduling_url}]`
  - `GET /user_busy_times?user&start_time&end_time`, `GET /user_availability_schedules`, `GET /event_type_availability_schedules`
  - `GET /organization_memberships` (staff)
  - `POST /scheduling_links` (single-use link)
  - `POST /webhook_subscriptions` `{"url","events":[…],"organization","user","group","scope":"organization|user|group","signing_key"}`; `GET /webhook_subscriptions`; `DELETE /webhook_subscriptions/{uuid}`
  - `GET /sample_webhook_data`
- **Objects [V]:**
  - Event: `{uri, name, status:"active|canceled", start_time, end_time, event_type, location, invitees_counter, created_at, updated_at, event_memberships[], event_guests[], cancellation, calendar_event}`
  - Invitee: `{uri, email, first_name, last_name, name, status, timezone, event, text_reminder_number, rescheduled, old_invitee, new_invitee, cancel_url, reschedule_url, questions_and_answers, cancellation, payment, no_show, scheduling_method, invitee_scheduled_by}`
  - Times are UTC ISO 8601. IDs are URIs; the UUID is the last path segment.
- **Pagination:** `pagination {count, next_page, previous_page, next_page_token, previous_page_token}`.
- **Webhooks [V]:**
  - Events: `invitee.created`, `invitee.canceled`, `invitee_no_show.created|deleted`, `routing_form_submission.created`, `event_type.created|updated|deleted`, `contact.*`, `meeting_recap.*`.
  - Payload: `{"event":"invitee.created","created_at","created_by","payload":{<Invitee> + "scheduled_event":{…}}}`.
  - **Reschedule** = `invitee.canceled` (with `rescheduled:true`) followed by `invitee.created` (with `old_invitee`).
  - **Signature [V]:** header `Calendly-Webhook-Signature: t=<unix>,v1=<hex>`, where `v1 = hex(HMAC_SHA256(signing_key, f"{t}.{raw_body}"))`. Reject if `|now-t| > ~180 s`. https://developer.calendly.com/api-docs/overview/webhooks/webhook-signatures
  - Webhooks require a paid plan (Standard or higher) [I].
- **Push availability:** there is **no API to create busy blocks**. Calendly reads the connected calendars (Google/Outlook/iCloud). The CRM writes busy events into a Google calendar that Calendly checks for conflicts.
- Rate limits: not in the spec [I: returns 429 with Retry-After]. Zapier: yes.

### 3.3 Cal.com (API v2)
- https://cal.com. Docs: https://cal.com/docs/api-reference/v2/introduction. OpenAPI: **https://raw.githubusercontent.com/calcom/cal.com/main/docs/api-reference/v2/openapi.json** [V]
- Base: `https://api.cal.com`. Self-hosted instances use their own host.
- Auth:
  - `Authorization: Bearer cal_live_…` (API key)
  - OAuth / platform: `x-cal-client-id` + `x-cal-secret-key`, managed users
  - Rate limits [V-2]: API key 120/min; OAuth client credentials or managed-user token 500/min.
- **Required header:** `cal-api-version`. Use `2024-08-13` for bookings and `2024-09-04` for slots [V].
- **Endpoints [V]:**
  - Bookings:
    - `GET /v2/bookings?status=upcoming,recurring,past,cancelled,unconfirmed&attendeeEmail&eventTypeId(s)&afterStart&beforeEnd&afterUpdatedAt&sortStart&take&skip`
    - `GET /v2/bookings/{bookingUid}`, `POST /v2/bookings`
    - `POST /v2/bookings/{uid}/reschedule` `{start, rescheduledBy, reschedulingReason}`
    - `POST /v2/bookings/{uid}/cancel` `{cancellationReason, cancelSubsequentBookings}`
    - `POST …/confirm|decline|mark-absent|reassign`, `GET …/attendees`
  - Create body: `{start (UTC ISO), eventTypeId | eventTypeSlug+username, attendee:{name,email,timeZone,phoneNumber,language}, bookingFieldsResponses, guests[], location, metadata, lengthInMinutes}`
  - Booking output: `{id, uid, title, description, hosts[], status:"accepted|pending|cancelled|rejected", cancellationReason, cancelledByEmail, reschedulingReason, rescheduledFromUid, rescheduledToUid, start, end, duration, eventTypeId, eventType, meetingUrl, location, createdAt, updatedAt, metadata, icsUid, attendees[{name,email,timeZone,phoneNumber,language,absent}], guests, bookingFieldsResponses}`
  - Slots: `GET /v2/slots?eventTypeId&start&end&timeZone=Europe/Rome&duration&format`; `POST /v2/slots/reservations` (hold a slot); `GET/PATCH/DELETE /v2/slots/reservations/{uid}`
  - Services: `GET/POST /v2/event-types`, `GET/PATCH/DELETE /v2/event-types/{id}`
  - Schedules: `GET/POST /v2/schedules`, `GET /v2/schedules/default`, `PATCH /v2/schedules/{id}`
  - **Push busy time:**
    - **`POST /v2/calendars/ics-feed/save` `{"urls":["https://crm…/busy.ics"],"readOnly":true}`**: Cal.com then treats the CRM's ICS feed as a busy calendar. This is an ideal fit for the CRM.
    - Also `GET /v2/calendars/busy-times`, `/v2/calendars/{calendar}/events`, and connection-level events and freebusy.
  - Webhooks: `POST/GET /v2/webhooks`, `PATCH/GET/DELETE /v2/webhooks/{id}`, per event type `/v2/event-types/{id}/webhooks`, per OAuth client `/v2/oauth-clients/{clientId}/webhooks`. Body `{subscriberUrl, triggers[], active, secret, payloadTemplate, version}`.
- **Webhook triggers [V]:** `BOOKING_CREATED, BOOKING_RESCHEDULED, BOOKING_CANCELLED, BOOKING_REQUESTED, BOOKING_REJECTED, BOOKING_PAID, BOOKING_PAYMENT_INITIATED, BOOKING_NO_SHOW_UPDATED, MEETING_STARTED, MEETING_ENDED, OOO_CREATED, FORM_SUBMITTED, …`
- **Webhook payload [V]:** `{"triggerEvent":"BOOKING_CREATED","createdAt":"…Z","payload":{…booking: uid, bookingId, title, startTime, endTime, organizer{…}, attendees[{name,email,timeZone}], status, rescheduleUid, …}}`. `MEETING_STARTED` and `MEETING_ENDED` are flat. The exact payload field list is not fully verified.
- **Signature [V]:** header `x-cal-signature-256` = hex(HMAC-SHA256(secret, raw_body)).
- Pagination: `take` / `skip`. Zapier: yes (calcom).

### 3.4 Microsoft Bookings (Microsoft Graph)
- Docs: https://learn.microsoft.com/en-us/graph/api/resources/booking-api-overview and https://learn.microsoft.com/en-us/graph/api/resources/bookingappointment?view=graph-rest-1.0 [V]
- Base: `https://graph.microsoft.com/v1.0`
- Auth: Entra ID OAuth2. Use the client-credentials flow for app permissions:
  - Application permissions: `BookingsAppointment.ReadWrite.All` (list appointments), `Bookings.Read.All` (getStaffAvailability), `Bookings.ReadWrite.All`, `Bookings.Manage.All`
  - Delegated: `Bookings.Read.All` and above [V]
- **Endpoints [V]:**
  - Businesses: `GET /solutions/bookingBusinesses`, `GET /solutions/bookingBusinesses/{id}` (id is the business SMTP address)
  - Appointments: `GET /solutions/bookingBusinesses/{id}/appointments`; **`GET /solutions/bookingBusinesses/{id}/calendarView?start=…&end=…`** (use this for date ranges; `$filter` is not supported); `POST …/appointments`; `GET/PATCH/DELETE …/appointments/{apptId}`; `POST …/appointments/{apptId}/cancel` `{"cancellationMessage":"…"}`
  - Staff availability: `POST /solutions/bookingBusinesses/{id}/getStaffAvailability` `{"staffIds":[…],"startDateTime":{"dateTime","timeZone"},"endDateTime":{…}}` returns `staffAvailabilityItem[{staffId, availabilityItems[{status:"Available|Busy|…",startDateTime,endDateTime,serviceId}]}]`
  - Services: `…/services`. Staff: `…/staffMembers`. Customers: `…/customers`.
- **bookingAppointment fields [V]:** `id, selfServiceAppointmentId, start{dateTime,timeZone}, end{…}, duration (ISO8601 "PT30M"), preBuffer, postBuffer, serviceId, serviceName, staffMemberIds[], customers[{customerId,name,emailAddress,phone,timeZone,notes,customQuestionAnswers}], customerName/customerEmailAddress/customerPhone/customerNotes (legacy single-customer), customerTimeZone, price, priceType, isLocationOnline, joinWebUrl, serviceLocation, serviceNotes, optOutOfCustomerEmail, smsNotificationsEnabled, createdDateTime, lastUpdatedDateTime, filledAttendeesCount, maximumAttendeesCount, appointmentLabel`.
- Webhooks: Graph change notifications are **not** available for bookingAppointment [I]. Alternatives: poll `calendarView` and use `lastUpdatedDateTime`, or subscribe to `/users/{bookingMailbox}/events` change notifications, because Bookings appointments land in the business mailbox calendar [I].
- **Push blocks [I]:** create events in the staff member's Outlook calendar. Bookings respects staff free/busy when "use Outlook calendar availability" is enabled.
- Pagination: `@odata.nextLink`. Throttling: standard Graph 429 with `Retry-After`.

### 3.5 Acuity Scheduling (Squarespace)
- Docs: https://developers.acuityscheduling.com (llms index: https://developers.acuityscheduling.com/llms.txt) [V]
- Base: `https://acuityscheduling.com/api/v1`. Auth: HTTP Basic (`userId:apiKey`) or OAuth2 for multi-account apps [V].
- **Endpoints:**
  - [V] `GET /appointments` with params `max`(100), `minDate`, `maxDate`, `calendarID`, `appointmentTypeID`, `canceled`, `firstName`, `lastName`, `email`, `phone`, `field:<id>`, `excludeForms`, `direction`
  - [V] `GET /appointments/:id`, `POST /appointments`, `PUT /appointments/:id`
  - [V, from the quick-start list] `PUT /appointments/:id/cancel`, `PUT /appointments/:id/reschedule`
  - [V] `/availability/dates`, `/availability/times`, `/availability/check-times`; `/appointment-types`, `/calendars`, `/clients`
  - [V] **`POST /blocks`** `{"start","end","calendarID","notes"}` returns `{id, notes, description}`
  - [I] params: `availability/times?appointmentTypeID&date&calendarID&timezone`; `availability/dates?month=YYYY-MM&appointmentTypeID`; `reschedule` body `{"datetime"}`; `DELETE /blocks/:id`
- **Appointment fields [V]:** `id, firstName, lastName, phone, email, date, time, endTime, datetime (ISO with offset), datetimeCreated/dateCreated, duration, price, paid, amountPaid, type, appointmentTypeID, calendar, calendarID, timezone (IANA), canClientCancel, canClientReschedule, location, notes, forms[], labels[], addonIDs, classID, confirmationPage`. `canceled` is included when `canceled=true`.
- **Webhooks [V]:**
  - Static (account settings) or dynamic: `POST /webhooks {"event","target"}`, `GET /webhooks`, `DELETE /webhooks/:id`; at most 25 per account.
  - Events: `appointment.scheduled`, `appointment.rescheduled`, `appointment.canceled`, `appointment.changed`, `order.completed`.
  - Payload is **form-encoded**: `action`, `id`, `calendarID`, `appointmentTypeID`. Fetch details with `GET /appointments/:id`.
  - **Signature [V]:** header `X-Acuity-Signature` = base64(HMAC-SHA256(api_key, raw_body)).
  - Retries on 5xx or network errors only, for 24 h with exponential backoff; disabled after 5 days of failures.
- Rate limits [V-2]: 10 req/s, 20 concurrent connections. Over the limit returns 429.
- Zapier: yes.

### 3.6 Setmore
- Docs (Apiary): https://setmore.docs.apiary.io [V]. **Limited beta**: requires a Pro account and an email to api@setmore.com. Setmore sends you a refresh token.
- Base: `https://developer.setmore.com/api/v1`
- Auth: `GET /o/oauth2/token?refreshToken=<rt>` returns `{"data":{"token":{"access_token","token_type":"BEARER","expires_in":604799}}}`. Send `Authorization: Bearer`.
- **Endpoints [V]:**
  - Services: `GET /bookingapi/services`, `GET /bookingapi/services/categories`, `GET /bookingapi/services/categories/{categoryKey}`. Service: `{key, service_name, staff_keys[], duration, buffer_duration, cost, currency}`
  - Staff: `GET /bookingapi/staffs` (at most 50, `?cursor=`)
  - Slots: `POST /bookingapi/slots` `{"staff_key","service_key","selected_date":"DD/MM/YYYY","off_hours","double_booking","slot_limit","timezone"}` returns strings like `["05.00","05.30",…]`
  - Customers: `POST /bookingapi/customer/create` `{first_name, last_name, email_id, country_code, cell_phone, …, additional_fields}`; `GET /bookingapi/customer?firstname=&email=&phone=`
  - Appointments:
    - `POST /bookingapi/appointment/create` `{staff_key, service_key, customer_key, start_time:"2021-02-19T19:00Z", end_time, comment, label}`
    - `GET /bookingapi/appointments?startDate=dd-mm-yyyy&endDate=dd-mm-yyyy&staff_key=&customerDetails=true&cursor=` (at most 150 per page)
    - `PUT /bookingapi/appointments/{key}/label?label=`
  - Appointment: `{key, start_time, end_time, duration, staff_key, service_key, customer_key, customer{…}, cost, currency, comment, label}`
- **No cancel/update and no webhook endpoints are documented.** Poll for changes. Rate limits are unspecified.

### 3.7 TIMIFY
- https://www.timify.com/it (Italian site live). Docs: https://docs.timify.dev (index https://docs.timify.dev/llms.txt) [V]
- Base: `https://api.timify.com/` (QA: `https://api-qa.timify.com/`).
- Auth: `POST /v1/auth/token {"appid","appsecret"}` returns token + refresh token (`expires` in seconds); refresh with `POST /v1/auth/refresh-token`. Header `authorization: <token>` (apiKey scheme). Most calls also need a `company-id` header.
- **Endpoints [V]:**
  - Appointments: `GET /v1/appointments` (`from_date`, `to_date`, `from_time`, `to_time`, `timezone`; **max 31 days**); `POST /v1/appointments`; `GET/PATCH/DELETE /v1/appointments/{id}`; bulk import `postbulkappointments` (`importEventId`)
  - Create body: `{resource_ids[] | external_resource_ids[], datetime:"YYYY-MM-DD HH:MM" (UTC), duration (5-min steps), service_id | title, notes, color, …}`
  - Appointment object: `{id, title, resourceId, customers, date, duration, externalId, from, until, isOnlineBooking, notes, price, currency, resources, serviceId, createdAt, updatedAt, …}`
  - Availability: "getavailability", and the booker endpoints `GET booker-services/availabilities`, `POST booker-services/reservations`, confirm, delete. Exact paths are in the per-page `.md`.
  - Services, resources, customers: full CRUD, with `?external=` to address items by external ID.
  - **Blocks:** "Import or update timeshift" bulk shifts, including non-workable `VACATION`, `SICK`, `BLOCKER`.
- **Webhooks [V]:**
  - Configured in the Developer Platform UI (no API).
  - Events include Event/Events created, updated and deleted (appointments), Customers, Services, Resource, Company, Shift, Notification, Before Confirmations/Reminders (Sync), Service Groups.
  - Security: an optional **custom header name + secret value** that you choose. **No HMAC.**
- Zapier: yes.

### 3.8 Square Appointments
- **Not available in Italy** [V-2]. Square operates in US, CA, UK, IE, FR, ES, AU and JP. For reference:
  - Bookings API: `POST /v2/bookings`, `GET /v2/bookings`, `GET/PUT /v2/bookings/{id}`, `POST /v2/bookings/{id}/cancel`, `POST /v2/bookings/availability/search`
  - Webhooks: `booking.created`, `booking.updated`
  - Signature: `x-square-hmacsha256-signature` = base64(HMAC-SHA256(key, notification_url + raw_body)) [V]
  - Skip.

### 3.9 Easy!Appointments (open source, self-hosted)
- Docs: https://easyappointments.org/docs/rest-api/ [V]
- Base `https://<host>/index.php/api/v1/`. Auth: Basic (admin) or `Authorization: Bearer <api token>`.
- Resources (all CRUD): `/appointments`, `/unavailabilities` (blocks), `/services`, `/providers`, `/customers`, `/service_categories`. `GET /availabilities?providerId&serviceId&date=Y-m-d`.
- Query params: `page`, `length`, `sort`, `q`, `fields`, `with`.
- Appointment: `{id, book, start, end, hash, location, notes, customerId, providerId, serviceId, googleCalendarId}`
- Webhooks (v1.5+): JSON POST on appointment save/delete and similar events, with secret header `X-EA-Token` (configurable) [V-2].

### 3.10 Google Reserve / Actions Center (Appointments)
- Only **scheduling platforms** become partners, not individual merchants. Merchants enable it inside their provider (Treatwell, Booksy, Fresha, Setmore, SimplyBook, Acuity, Calendly and others are partners [V-2]).
- For the CRM to appear on Google, it would have to become an Actions Center partner:
  - It hosts a **Booking Server** called by Google: `GET /v3/HealthCheck`, `POST /v3/BatchAvailabilityLookup`, `POST /v3/CreateBooking`, `POST /v3/UpdateBooking`, `POST /v3/GetBookingStatus`, `POST /v3/ListBookings`, with HTTP Basic auth that you configure [V-2].
  - It uploads merchant, service and availability feeds.
  - It calls the Booking Notification API.
  - Docs: https://developers.google.com/actions-center/verticals/appointments/e2e/overview
- In the EU, the DMA changes of 2024 moved some flows to "redirect" integrations [V-2].
- This is not a source of bookings for you to pull. **Low priority.**

### 3.11 Restaurants (noted only)
- **TheFork (TheFork Manager B2B API):** https://docs.thefork.io/B2B-API/introduction. Partner API at `api.thefork.io/manager`, with webhooks for reservation and customer events [V-2].
- **Zenchef:** token + restaurant id; `https://api.zenchef.com/api/v1`; Postman docs https://documenter.getpostman.com/view/874040/Uz5AseV7 [V-2].

---

## 4. Fallback integration toolkit (what the Frappe connector framework should support)

1. **ICS busy-feed publisher (outbound, "block slots")**: needed for Treatwell (Calendario esterno), Fresha (import) and Cal.com (`ics-feed/save`); Booksy supports one-off .ics import.
   - One URL per staff member or resource with a secret token, for example `/api/method/crm.integrations.ics.feed?key=…`.
   - Emit VEVENTs for CRM appointments and blocks: `UID` stable, `DTSTART`/`DTEND` in UTC with `Z`, `TRANSP:OPAQUE`, and a generic `SUMMARY` for privacy (GDPR, especially for medical data).
   - Consumers poll every 15–60 min, so blocks are not instant.
2. **Google Calendar bridge (bidirectional)**: covers Fresha (2-way Google), iDoctors (Google sync) and Calendly (conflict calendars). Microsoft Bookings is the Outlook equivalent. Use the Google Calendar API with incremental `syncToken` and `events.watch` push channels. Frappe already has a Google Calendar integration you can reuse.
3. **Inbound email parser**: covers Treatwell, Fresha, Booksy, MioDottore (without partner status), Doctolib, Elty, iDoctors, Pazienti.it and Top Doctors. Use a Frappe Email Account on a dedicated mailbox and add it as a secondary notification address on each platform. Use per-sender regex/HTML parsers. Deduplicate on the platform booking reference in the subject or body.
4. **Webhook receiver with pluggable signature verifiers**:
   - Calendly: `t.body` HMAC-SHA256 hex, header `Calendly-Webhook-Signature`
   - Cal.com: HMAC-SHA256 hex of the body, header `x-cal-signature-256`
   - Acuity: HMAC-SHA256 base64 of the body with the API key, header `X-Acuity-Signature`; form-encoded body
   - Mindbody: `sha256=` + base64 HMAC, header `X-Mindbody-Signature`
   - Square: HMAC of URL + body, base64
   - TIMIFY and Easy!Appointments: static secret header
   - Docplanner: IP allow-list plus optional API-key header
   - SimplyBook and Booksy: no signature. Re-fetch the booking via the API to confirm.
5. **Pollers** for platforms without webhooks (Setmore, Phorest, MS Bookings) and as a safety net for all of them: Docplanner `/notifications/multiple` pull mode, and SimplyBook `filter[date_from]`.
6. **Zapier/Make:** apps exist for Calendly, Acuity, Cal.com, SimplyBook, TIMIFY, Mindbody and Square. There is none for Docplanner/MioDottore, Treatwell, Fresha, Booksy, Planity, Doctolib, iDoctors or Elty (zapier.com/apps/<slug> returned 404). Make has community apps for Setmore and AlfaDocs by Maxmel Tech.

---

## 5. Suggested normalized model (for the CRM connector layer)

```
ExternalBooking {
  platform, external_id, external_parent_id (e.g. Calendly event uuid, Booksy appointment id for subbookings),
  status: booked|pending|confirmed|cancelled|no_show|completed,
  start_utc, end_utc, source_tz,
  service_external_id, service_name, staff_external_ids[], location_external_id,
  customer {first_name, last_name, full_name, email, phone, tax_code (MioDottore `nin`), birth_date, gender},
  notes, price, currency, raw_payload(json), last_synced_at, etag/version
}
```
Status mapping hints:
- Docplanner: `booked`, `canceled_at`, and the `booking-confirmed` event
- Booksy: A/W/P/C/D/F/N/M
- Cal.com: accepted/pending/cancelled/rejected
- Calendly: active/canceled
- SimplyBook: confirmed/confirmed_pending/pending/canceled
- Square: PENDING, ACCEPTED, CANCELLED_BY_CUSTOMER, CANCELLED_BY_SELLER, DECLINED, NO_SHOW [I]

Timezone handling:
- Docplanner, Acuity and Calendly/Cal.com carry offsets or UTC.
- Booksy is naive local time plus `business_timezone`.
- SimplyBook is company-local time [I].
- Setmore uses a `Z` suffix; its slots are in company tz.
- MS Graph uses `dateTimeTimeZone`.
- TIMIFY takes UTC `YYYY-MM-DD HH:MM` input.

---

## 6. Sources (main)
- Docplanner: https://integrations.docplanner.com/docs/ · https://integrations.docplanner.com/guide/fundamentals/authorization.html · https://integrations.docplanner.com/guide/callbacks/push-vs-pull.html · https://integrations.docplanner.com/guide/integration-process.html
- Elty: https://elty.it · https://blog.alfadocs.com/agenda-senza-buchi-e-pi%C3%B9-visibilit%C3%A0-online-con-lintegrazione-di-alfadocs-ed-elty · https://www.gestionalemedico.it/
- Treatwell iCal: https://partners.treatwell.com/hc/it/articles/115005413069 · https://www.booking-connect.com/guide
- Fresha: https://www.fresha.com/help-center/knowledge-base/calendar/101373-sync-your-fresha-calendar
- Booksy: https://web.archive.org/web/20220706184310/https://alpha.docs.booksy.net/ · https://github.com/api-evangelist/booksy
- SimplyBook: https://simplybook.me/api/swagger-admin · https://github.com/vetalsimplybook/simplybook_callback_example_php
- Calendly: https://developer.calendly.com/openapi/calendly-api.yaml · https://developer.calendly.com/api-docs/overview/webhooks/webhook-signatures
- Cal.com: https://raw.githubusercontent.com/calcom/cal.com/main/docs/api-reference/v2/openapi.json · https://cal.com/docs/developing/guides/automation/webhooks
- MS Graph Bookings: https://learn.microsoft.com/en-us/graph/api/bookingbusiness-list-appointments?view=graph-rest-1.0 · https://learn.microsoft.com/en-us/graph/api/bookingbusiness-getstaffavailability?view=graph-rest-1.0
- Acuity: https://developers.acuityscheduling.com/reference/quick-start · https://developers.acuityscheduling.com/docs/webhooks · https://developers.acuityscheduling.com/page/webhooks-webhooks-webhooks
- Setmore: https://setmore.docs.apiary.io
- TIMIFY: https://docs.timify.dev/llms.txt · https://docs.timify.dev/docs/webhooks.md
- Mindbody: https://developers.mindbodyonline.com/WebhooksDocumentation
- Square: https://developer.squareup.com/reference/square/bookings-api · https://developer.squareup.com/docs/webhooks/step3validate
- Easy!Appointments: https://easyappointments.org/docs/rest-api/
- AlfaDocs: https://developers.alfadocs.cloud/docs/quickstart
- Google Actions Center: https://developers.google.com/actions-center/
