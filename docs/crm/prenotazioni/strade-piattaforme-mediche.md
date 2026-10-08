# Receiving bookings from Italian medical marketplaces: every route besides email parsing and iCal

Research date: 2026-09-24. Tags: **[V]** verified on the cited page (fetched during this research), **[V-s]** verified only through a search-engine snippet, the page itself could not be fetched, **[I]** inferred or my own judgement. No contacts are invented. Where no public contact was found, the report says so.

---

## 0. Executive summary

| Platform (owner) | Official API for a single practice? | Realistic route to our CRM | Best "chain" gestionale with its own API |
|---|---|---|---|
| **MioDottore** (Docplanner) | No. The Integrations API is "exclusively available to medical software providers" [V] | (a) Become a Docplanner integration partner as a *software vendor* (our CRM), or (b) chain through a certified gestionale | **GipoNext** (Docplanner-owned, public REST API with OAuth, clinic self-authorises) [V]; DBMedica (API + MioDottore sync) [V]; MEG (API in beta) [V] |
| **Doctolib Italia** (ex Dottori.it) | No public partner program page for IT. FR paid accounts show "Page interfaçage" with API key/secret for ApiSync/HL7 interfaces [V] | Chain through **AlfaDocs** (two-way Doctolib sync plus a public API that includes webhooks) [V], or MEG [V]; Vettore Medical is Doctolib-owned | AlfaDocs [V], MEG [V] |
| **Elty** (DaVinci Salute / Unipol) | No public API | Chain through a gestionale Elty lists as integrated | AlfaDocs, DBMedica, MEG (TimeoMeg), Medinformatica, HSG6, H2O, Onit, Isolabella, GSD, Pentasistemi [V] |
| **iDoctors** | No public API. The site says it integrates "with all gestionali" [V] | Chain | AlfaDocs [V], DBMedica [V], MEG (since 2.4.2, May 2026) [V] |
| **Cup24.it** (ex Cup Solidale, Covisian/Medicx) | "API connectors" towards gestionali. No public docs [V-s] | Chain | AlfaDocs [V], DBMedica [V], MEG [V] |
| **TuoTempo** (Docplanner) | REST API with docs behind login (apidoc.tuotempo.com returns 401) [V] | Only for large centres through a TuoTempo contract | n/a |
| **Top Doctors** | No public API. In ES they own/partner with Ofimedic [V-s] | Its UK agenda advertises Google/Outlook integration [V]. Italy is unclear | none found for IT |
| **Pazienti.it** | No booking marketplace found. It is a health-content site with a directory [I] | n/a | n/a |
| **QuiSalute** | A health news site, not a booking marketplace [V-s] | n/a | n/a |
| **"Prenotami"** | No Italian medical platform by that name found [I] | n/a | Others found: Paginemediche, CupSubito, miAgenda, PrenotaSalute (a price-comparison site) [V-s] |

**Key conclusions**
1. Only Docplanner publishes a real partner program with docs, sandbox, SDKs and webhooks. It is open to **software vendors**, not single clinics [V]. Our Frappe CRM could apply **as a software provider**, but acceptance requires implementing the full flows (mapping, full booking sync, real-time schedule updates), so our CRM would effectively have to act as the practice's master calendar [V].
2. The most practical route today is to **chain through a gestionale that has an open API**: marketplace to certified gestionale to our CRM.
   - **GipoNext** covers MioDottore natively. Its API has no webhooks, so we poll [V].
   - **AlfaDocs** covers Doctolib, Elty, iDoctors and Cup Solidale. Its API offers an API key or OAuth, and webhooks with OAuth [V].
   - **DBMedica** covers MioDottore, iDoctors, Elty and Cup24. It has "documented APIs" but no public URL [V].
   - **MEG** covers MioDottore, Doctolib, Cup Solidale, iDoctors and Elty. Its API is licensed and in beta [V].
3. **Legally**, the strongest new lever is the **EU Data Act, Chapter VI (applicable since 12 Sep 2025)**. Art. 30(2) + Art. 34 require SaaS providers to offer **free open interfaces** for switching and for **in-parallel use** [V text]. Whether a booking marketplace's agenda counts as a "data processing service" is untested [I].
   - **P2B Regulation art. 9** obliges the platform to describe in its T&C what data access business users have [V].
   - GDPR art. 20 is a right of *data subjects* (patients), not of the practice. The practice's lever is art. 28(3)(g) (the processor returns data) [I].
   - The DMA does not apply, because neither Docplanner nor Doctolib is a gatekeeper [V].
4. Unofficial routes (private API reverse-engineering, RPA with the practice's own login) are technically common: CalMedi, Docal.io and clicfone exist for Doctolib [V]. They conflict with the ToS clauses listed in section 6 and carry account-suspension risk.

---

## 1. MioDottore / Docplanner

### 1.1 Partner program
- **Name / URL:** "Docplanner Integrations", https://integrations.docplanner.com/ (form: select country incl. **Italy** plus privacy acceptance) [V]. Guide: https://integrations.docplanner.com/guide/ . API reference: https://integrations.docplanner.com/docs/ and https://docplanner.github.io/integrations-api-docs/ [V].
- **Who can apply:** "The Docplanner API is exclusively available to medical software providers"; "Access is limited to a specific set of resources authorized individually by each customer" [V] (https://integrations.docplanner.com/guide/).
- **Italian vendor form:** https://pro.miodottore.it/nuove-integrazioni-miodottore/form ("Se il tuo software non è ancora integrato con MioDottore, compila il form"). It targets software vendors and promises joint marketing [V].
- **Process** (https://integrations.docplanner.com/guide/integration-process.html) [V]:
  1. Sandbox credentials through the form. The sandbox includes a sample API client plus test clinic and doctor profiles.
  2. Install an SDK (PHP, .NET) or use Postman.
  3. Kick-off meeting with a Docplanner specialist.
  4. Development.
  5. **Acceptance tests.** "Only integrations with all required methods implemented will be approved". The required flows are mapping for all resources, synchronizing all bookings, and real-time schedule updates.
  6. Activation per client.
  7. After launch, regular black-box tests (manual and automatic) plus monitoring pings every 5 minutes.
- **Contact:** **integrations@docplanner.com** [V].
- **Fees / contract / timeline / minimum clients:** not published [V: absent]. The MioDottore page says integration is "Gratuita" for the clinic [V] (https://pro.miodottore.it/integrazioni).
- **Tech** [V]:
  - Auth is OAuth2 client_credentials, with a bearer token valid 24h.
  - Base URL `https://www.{domain}/api/v3/integration`, with the token at `https://www.{domain}/oauth/v2/token` (so `www.miodottore.it` for IT) [V, SDK README].
  - **Webhooks (push):** HTTPS POST from a single IP. Retries at 5 and 10 minutes (the async-flow page says 1/5/15 min). Failed pushes are deleted after 14 days.
  - **Pull:** `/notifications` and `/notifications/multiple` (100 per request), kept for 72h.
  - Events: `slot-booked`, `booking-canceled`, `booking-moved`, plus optional `booking-confirmed`, `break-*`, `presence-marked`, etc.
  - Availability is pushed with `updateSlots`, with breaks through the API. "Available slots must always be kept up to date" [V] (push-vs-pull and managing-calendars pages).
- **GitHub:** official SDK https://github.com/DocPlanner/integrations-api-sdk-php (active, updated 2026-09) [V]. Unofficial, old: umitakkaya/dp-api-sdk (C#, 2016) and umitakkaya/DpApiClient (archived) [V]. A code search for the API host found no public unofficial clients [V].

### 1.2 Can a single practice get credentials?
- Officially no ("exclusively medical software providers") [V].
- The partner logo wall includes **LuxMed**, a Polish provider group, next to software vendors [V]. So large providers with in-house software have been accepted [I].
- A single Italian clinic realistically needs a vendor. Our CRM could become that vendor [I].

### 1.3 Certified / integrated gestionali (Italy)
- **Listed on pro.miodottore.it/integrazioni:** MEG, CGM, Medico 2000, TERAPICO, TSERVE, Quaderno Elettronico, MEDIWARE, XMED, Gestionale Ambulatorio, Xilema Medical [V].
- **Docplanner-owned:** **GipoNext** and GipoDental. Docplanner acquired GIPO in Oct 2020 [V-s]. The GipoNext docs say it is "nativamente integrato con MioDottore" [V].
- **DBMedica** claims MioDottore sync [V] (https://www.dbmedica.it/funzionalita/).
- **CGM integration:** for MMG/PLS, patient registry plus prescription requests [V] (https://www.cgm.com/ita_it/lp/integrazione-cgm-miodottore.html).
- **TServe** docs: bidirectional, and since v1.4.47 MioDottore pushes appointments to the TServe server [V] (https://tserve.info/help/IntegrazioneconMiodottore.html).
- **Global partner logos** include Vettore, Timeo (the MEG vendor), GIPO and others [V].

### 1.4 Built-in sync / export
- **Google Calendar sync is discontinued.** Doctoralia ES blog, 2021-09-28: "la sincronización entre ambas plataformas ya no es posible" [V] (https://pro.doctoralia.es/blog/especialistas/agenda-doctoralia-ventajas-frente-google-calendar). The IT blog says the same ("non ha più senso") [V] (https://pro.miodottore.it/blog/centrimedici/gestione/miodottore-vs-google-calendar). No Outlook or iCal feed was documented [I].
- **Data export** (help article https://help.docplanner.com/s/article/How-to-Export-Your-Doctoralia-Online-Agenda-Data?language=it) [V]:
  - The page served the Polish text for the same Docplanner procedure.
  - Path: Settings, then "Download data". Choose patient list, medical history or appointment list.
  - You get a password-protected .zip, with the code sent by SMS.
  - This is manual only, not a feed.
- **Patient import** by CSV/Excel [V-s].

### 1.5 Widgets / notifications
- **Widget:**
  - `<a class="zl-url" ... data-zlw-doctor=... data-zlw-type="big_with_calendar">` plus `//platform.docplanner.com/js/widget.js`. Types include `big`, `big_with_calendar` and `button_calendar_floating_medium` [V-s].
  - "Prenota con Google" (Reserve with Google) integration [V-s].
  - The widget lets patients book on MioDottore. It gives us no callback [I].
- **Notifications:** preferences cover email, SMS and push (app) [V]. We found no documentation of CC-ing booking emails to a secondary address [I]. A workaround is a mail-forwarding rule on the practice mailbox [I].
- **Contacts** (Condizioni di Servizio, 14 Nov 2024 PDF: https://www.miodottore.it/public/doc/it/2024_02_condizioni_di_servizio.pdf) [V]:
  - contatto@miodottore.it
  - privacy: **privacyitalia@docplanner.com**
  - PEC (for authorities): docplanner-italy@legalmail.it
  - Docplanner Italy S.r.l., P.le delle Belle Arti 2, Roma.

---

## 2. Doctolib Italia (ex Dottori.it, acquired 2021 [V-s])

### 2.1 Partner / interop program
- **No public Italian partner or API application page was found** [V: absent].
- In France Doctolib runs vendor connectors:
  - "Zipper Web/Heavy" (Chrome-extension or desktop bridges) for software such as Weda, Calimed, Desmos, Galaxie, Oplus, Krys, Surgica and GXD5 RIS [V] (https://doctolib.zendesk.com/hc/fr/articles/38883772728212).
  - Example: Weda gets a bidirectional real-time patient sync but **one-way appointments (Doctolib to Weda)** [V] (https://doctolib.zendesk.com/hc/fr/articles/45979535321620).
- **"Page interfaçage"** (paid versions): "Interfaçage de type ApiSync", HL7-style messages (S12 = create appointment, S24 ...), in/out directions to DPI/RIS/GAM, and "Identifiants d'accès aux API Doctolib: Accéder aux clés" (client id plus secret) [V] (https://doctolib.zendesk.com/hc/fr/articles/33128282291860).
  - This shows per-customer API keys exist for interfaced establishments.
  - Availability in Italy and the conditions are unknown [I]. Ask Doctolib Italia sales or support.
- **"Doctolib Connect" is NOT an interop program.** It is the professional messaging network (ex Siilo), renamed 5 Nov 2025 [V] (https://doctolib.zendesk.com/hc/it/articles/24755141353876).
- **Vettore Medical** (Doctolib-owned since 2022, merged 1 Jul 2023 [V-s]) syncs configuration to Doctolib every 30 min, or 6h when idle [V-s] (help article 13891827706644, access-restricted).
- **Contacts:** pro.ita@doctolib.com, the support address in the IT B2B CU (Jan 2022) [V] (https://media.doctolib.com/image/upload/v1643797961/CU-B2B-ITA-Jan22-vdef_rv9tw3.pdf). Interop contact form for hospitals (FR): https://info.doctolib.fr/hopital/interoperabilite/ [V].

### 2.2 Single practice credentials?
- Only through the paid "interfaçage" setup (FR evidence) [V]/[I]. Otherwise no.

### 2.3 Integrated gestionali (IT)
- **AlfaDocs:** bidirectional. "ricevi prenotazioni ... in tempo reale. Le disponibilità ... vengono trasmesse a Doctolib automaticamente" [V] (https://www.alfadocs.com/marketplace/applicazioni/doctolib).
- **MEG:** "Sincronizzazione con MioDottore.it, CUP Solidale e Doctolib" in its Pro plan [V] (https://www.gestionalemedico.it/).
- **Vettore Medical** (in-house) [V-s].

### 2.4 Built-in sync / export
- **No real-time external calendar sync.** From the Doctolib FR help: "La synchronisation en temps réel de votre agenda Doctolib avec un calendrier externe (Google Agenda, Apple Calendrier, Outlook, etc.) n'est pas disponible". A one-off import of .ics/CSV is possible [V] (https://doctolib.zendesk.com/hc/fr/articles/202765443).
- **Export** (IT, updated 2026) [V] (https://doctolib.zendesk.com/hc/it/articles/204738165 and /360055968651):
  - Settings, then Impostazioni avanzate, then Import/export dati, then Esportazioni.
  - Exports: Dati pazienti, Cronologia appuntamenti and Orari di apertura/assenze, in **CSV or XLS**. More than 500k rows are split into several files.
  - Admin only. Rights are automatic for a verified independent sole admin, otherwise request them via support.
  - All admins get an email for each export.
  - The appointment columns are listed in the article: Id, Doctolib Patient ID, start, duration, agenda, motive, status, Appuntamento internet, created/updated/cancelled by, patient contacts, etc.
- **Third-party unofficial sync:**
  - **CalMedi:** a Chrome extension that reads Doctolib and pushes to Google, one-way, €10–35/month [V] (https://calmedi.io/en/).
  - **Docal.io:** server-side, stores the practitioner's Doctolib credentials (AES-256), polls 3–5×/day, two-way on Premium [V] (https://www.docal.io/blog/synchroniser-doctolib-google-calendar).
  - clicfone and meditrust also exist [V-s].

### 2.5 Notifications
- Push notifications (Doctolib Pro app/desktop) for online booked, moved or cancelled appointments [V].
- Email notices exist **but "Le notifiche inviate per email non contengono nessun dato personale o informazione medica relativo al paziente"**, and move/cancel emails only fire within 48h [V] (https://doctolib.zendesk.com/hc/it/articles/360062111892).
- **So email parsing of Doctolib yields no patient identity** [I, from V].

---

## 3. Elty (elty.it, "Elty DaVinci", DaVinci Salute / Unipol)
- **Clinic program:** https://elty.it/per-le-cliniche [V].
  - Steps: form, then configuration by the Elty team, then go-live.
  - **Zero fixed cost, fee only on revenue generated.**
  - Clinics without a gestionale can use the free "calendario Elty".
  - Demo form: https://elty.it/chiedo-demo-cliniche. Support: https://supporto.elty.it (patient-oriented).
  - No partner email or phone is published [V].
- **Gestionali integrated** (Elty page) [V]: Medinformatica, **DBmedica**, **Alfadocs**, **TimeoMeg**, HSG6, H2O, Onit, Isolabella, GSD, Pentasistemi.
  - AlfaDocs: slots go to Elty, bookings and cancellations come back, prices are pushed (Aug 2024) [V] (https://www.alfadocs.com/marketplace/applicazioni/elty).
  - MEG added Elty and iDoctors "tramite le API del MEG" in v2.4.2 (22 May 2026) [V].
- **Brand partnerships:** https://elty.it/partnership (corporate or brand partners, not tech) [V-s].
- **Elty DaVinci:** GP software (medico.davinci.elty.it). It imports data from common gestionali. No public API [V-s].
- **Public API / Google sync / iCal:** none found [I].
- **ToS:** Elty T&C art. 5.4 "non può decompilare ... il software". DaVinci Dottori T&C art. 5.4 is the same, and art. 5.3 limits use to "personal and non-commercial" [V] (https://elty.it/termini-e-condizioni-del-servizio, https://medico.davinci.elty.it/termini-e-condizioni-del-servizio-dottori).

## 4. iDoctors
- **Page:** https://www.idoctors.it/collabora. It advertises "integrazione con tutti i gestionali per centri medici", "agenda sempre sincronizzata con la segreteria e con Google Calendar", a website widget, and SMS reminders [V]. The direction of the Google sync is not stated [I].
- **Contact:** info@idoctors.it, Viale Parioli 160, Roma [V].
- **Integrated gestionali:**
  - AlfaDocs (iDoctors to AlfaDocs bookings, availability, new patients) [V] (https://www.alfadocs.com/marketplace/applicazioni/idoctors).
  - DBMedica [V].
  - MEG (May 2026) [V].
- **SofIA:** an AI assistant for doctors [V-s].
- **Public API docs:** none [I]. The API exists (it is used by the gestionali above), so a vendor could ask info@idoctors.it for access [I].

## 5. Cup24.it (ex CupSolidale), CUP marketplaces, TuoTempo, Top Doctors, others
- **Cup24.it** (renamed Apr 2026, Covisian/Medicx) [V-s]:
  - "integrazione diretta con il tuo software gestionale" via API connectors.
  - Join: https://cup24.it/entra-nel-network.html [V].
  - Phones: structures **+39 055 0982184**, bookings +39 02 8003532. PEC **cupsolidale@pec.it**. Viale della Giovine Italia 17, Firenze [V].
  - Integrated gestionali: AlfaDocs (bidirectional, Apr 2024) [V] (https://blog.alfadocs.com/assistenza-sanitaria-digitale-lintegrazione-di-alfadocs-e-cup-solidale), DBMedica [V], MEG [V].
- **TuoTempo** (Docplanner group):
  - https://www.tuotempo.it/api-integrazioni: web services, DB sync or file exchange. More than 60 gestionali, e.g. Dedalus, Poliwin, Zaksoft Fenice, jLab Zucchetti, SAP, Exprivia RIS, Kognitiva, Libra Sistemi, SysdatSanità [V].
  - API docs at https://apidoc.tuotempo.com (401, credentials required) [V]. The integration guide at documentation.tuotempo.net needs a password from your TuoTempo adviser [V-s].
  - Aimed at hospitals and polyclinics.
- **Top Doctors:**
  - UK agenda "Integration with Outlook and Google Calendar" [V] (https://360.topdoctors.co.uk/products/online-agenda/).
  - Spain: integration with Ofimedic (real-time availability and booking sync) [V-s] (https://www.ofimedic.com/soluciones/topdoctors.html).
  - Italy: the doctor app page mentions no integrations [V].
- **Pazienti.it:** the homepage is content plus a directory. No professional booking product was found [V/I].
- **QuiSalute:** a news site [V-s].
- **"Prenotami":** not found. Other Italian booking sites (no public APIs found) [I]: Paginemediche, CupSubito, miAgenda, PrenotaSalute (a comparator that links out).

---

## 6. Gestionali with their own public API (for the chain: marketplace to gestionale to our CRM)

| Gestionale | Marketplaces synced | API docs | Auth / access for a single clinic | Push? |
|---|---|---|---|---|
| **GipoNext** (Docplanner) | MioDottore (native) | https://integrations.giponext.it (onboarding, entities, FAQ), Swagger at https://api.giponext.it | The clinic "presents" the integrator to GipoNext, which activates a Developer role on account.gipo.it. Register an OAuth app; approval is "solitamente entro 48h" and the whole process takes "2-3 giorni lavorativi". The clinic creates a technical user in Configurazione, then Permessi, then Utenti. Trial or sandbox tenant available. OAuth **Authorization Code or Device Code only, no client_credentials**. Scopes: `giponext.patients/agenda/treatments/episodes/medicalreports/invoices`, plus `offline_access` for refresh tokens. Rate-limited (429 with Retry-After). Tech support: https://gipo.atlassian.net/servicedesk/customer/portal/140 [V] | **"Non sono disponibili webhook"**, so we must poll [V] |
| **AlfaDocs** | Doctolib (2-way), Elty, iDoctors, Cup Solidale | API reference https://app.alfadocs.com/api.html; portal https://developers.alfadocs.cloud | **API key created by the practice itself** in Impostazioni, then Studio, then Chiavi (X-Api-Key, per archive). OAuth2 for marketplace apps, with credentials from **apps@alfadocs.com**. Rate limit 10 req/s. Endpoints include Appointments (get/post/patch), Free Slots, Patients, etc. [V] | Webhooks and events exist but "require OAuth" [V] |
| **DBMedica** | MioDottore, iDoctors, Elty, Cup24 | https://www.dbmedica.it/integrazioni-api/: "API documentate"; read/write appointments, patients, services, invoices, professionals, locations, waiting lists; authenticated access controlled by the client. No public URL [V] | Contact the vendor | Webhooks not mentioned [V]. It also offers Google Calendar and iCal links for professionals [V-s] |
| **MEG** (Timeo) | MioDottore, Doctolib, Cup Solidale, iDoctors, Elty | REST API "soggetta a licenza ... in Beta"; docs in advance access through sales [V-s] (https://www.gestionalemedico.it/2025/) | Contact the vendor | Google Calendar sync on its plans [V] |
| TServe | MioDottore | none public | n/a | n/a |
| CGM (XMED etc.), Medico 2000, Terapico, Mediware... | MioDottore | none public found | n/a | n/a |
| XDENT, Dentalsoft, OsteoEasy, FisioDesk, Medinext, "Studio Medico", Infinity | none documented with these marketplaces | none found | n/a | n/a |

The chain is the fastest compliant route [I]. For a clinic on MioDottore, the path is MioDottore to GipoNext (native) to our CRM via GipoNext OAuth plus polling. For a clinic on Doctolib, Elty, iDoctors or Cup24, the path runs through AlfaDocs, using the API key the clinic creates itself or OAuth with webhooks. The downside is that the clinic must use, and pay for, that gestionale.

---

## 7. Legal routes (EU / Italy)

1. **GDPR art. 20 (portability).**
   - It belongs to data subjects (patients), not to the practice [I].
   - The practice is usually the **controller** of its patient agenda and the platform a **processor** (Doctolib: art. 28 processor for the agenda, and controller for the patient account [V-s]).
   - The practice's lever is the DPA / art. 28(3)(g): the processor returns or deletes data at the end of services. Doctolib CU 17.3 already commits to making appointment history and patient DBs available before termination, with 2 months to retrieve [V] (2022 CU).
   - This does not give a *continuous* feed [I].
2. **EU Data Act (Reg. 2023/2854)**, applicable since **12 Sep 2025** (art. 50) [V].
   - Chapter VI covers the provider of a "data processing service" (SaaS included [I]).
   - It must allow switching, with a notice period of at most 2 months and a transitional period of at most 30 days, and export all "exportable data" (art. 25) [V].
   - **Switching charges are banned from 12 Jan 2027** (art. 29) [V].
   - **Art. 30(2):** non-IaaS providers "shall make open interfaces available to an equal extent to all their customers and the concerned destination providers free of charge", with "sufficient information ... to enable the development of software to communicate with the services, for the purposes of data portability and interoperability" [V].
   - **Art. 34:** those requirements apply *mutatis mutandis* "to facilitate interoperability for the purposes of **in-parallel use**" (egress costs may be passed on at cost) [V].
   - The art. 31 custom-built exemption does not cover 30(2) [V].
   - Argument: a practice using MioDottore Agenda or Doctolib Pro in parallel with our CRM can ask for the open interface [I]. It is untested. Platforms may argue the marketplace is an intermediation service rather than a data processing service, or that the interface for parallel use is the partner API [I].
   - Enforcement: the national competent authority. For Italy, check the implementing decree [I].
3. **P2B Regulation (EU) 2019/1150, art. 9.** Online intermediation services must describe in their T&C the "technical and contractual access, or absence thereof, of business users" to data generated [V] (text via legislation.gov.uk, identical to EUR-Lex paras 1–2). This supports a formal written request for the access conditions [I].
4. **DMA.** Gatekeepers are Alphabet, Amazon, Apple, ByteDance, Meta, Microsoft and Booking. **Docplanner and Doctolib are not gatekeepers, so the DMA does not apply** [V-s] (https://digital-markets-act.ec.europa.eu/gatekeepers-portal_en).
5. **Unofficial approaches, risks.**
   - **MioDottore ToS** (14 Nov 2024) [V]:
     - §5.6: no use "per scopi diversi da quelli previsti".
     - §5.7: no "copiare, accedere, adattare ... disassemblare, decompilare, decodificare o estrarre il codice sorgente o qualsiasi codice software".
     - §9 (i)–(iii): no "scaricare, estrarre ... riadattare", and no use for purposes other than the Services, without written authorisation. Indemnity is owed.
     - §13: suspension or closure of the account.
     - Subscribers are also bound by a separate, non-public service contract that prevails.
   - **Doctolib IT CU** [V]:
     - 13.4.1: no accessing or copying source code, no use for other purposes, no "estrarre ... decompilare (salvo ... legge applicabile) o incorporare la Piattaforma Doctolib in un software diverso".
     - 13.4.2: a breach is "atto di contraffazione".
     - 8.4: the user is liable for third-party integrations not made by Doctolib.
     - 5.1: credentials must stay secret, which conflicts with storing them in an RPA service [I].
   - **Elty / DaVinci:** art. 5.4 no decompiling; 5.3 personal and non-commercial use [V].
   - **Italian criminal law [I, needs lawyer]:** art. 615-ter c.p. (accesso abusivo). The Cassazione Sezioni Unite (2011 "Casani", 2017 "Savarese") held that an authorised user can commit abusive access when acting outside the owner's conditions, which is a risk for RPA or private-API use against the ToS.
   - EU Directive 2009/24 art. 6 (decompilation for interoperability) covers installed programs, not remote SaaS APIs [I].
   - **Practical risks:** account suspension (the practice loses its booking channel), breakage on UI or API changes, 2FA / SMS-code exports, and GDPR accountability for storing credentials [I].

---

## 8. Recommended action list
1. **Email integrations@docplanner.com** (plus the IT form) as a software vendor. Ask for the sandbox, fees and acceptance criteria. Ask whether a *read-only / notification-only* scope is possible for a CRM that is not the master calendar [I]. The docs imply they are not.
2. **For MioDottore clinics:** propose GipoNext. Onboard via integrations.giponext.it (2–3 working days) and poll `/v2/tenants/{id}/...` appointments and availability.
3. **For Doctolib, Elty, iDoctors and Cup24 clinics:** propose AlfaDocs. The clinic creates the API key itself; ask apps@alfadocs.com for OAuth, which unlocks webhooks.
4. **Ask DBMedica and MEG sales** for API docs, because they cover the most marketplaces.
5. **Send a formal letter** (practice-signed, PEC to docplanner-italy@legalmail.it and Doctolib) citing Data Act art. 30(2)+34, P2B art. 9 and the DPA return clause, requesting a free open interface or continuous export [I]. Keep a scheduled CSV/XLS export (Doctolib) or zip (MioDottore) as the fallback bulk import.
6. **Avoid RPA or reverse engineering** unless the practice accepts ToS risk in writing. If used, prefer practice-run tooling (e.g. a browser extension on the practice's PC, CalMedi-style) over storing credentials server-side [I].
