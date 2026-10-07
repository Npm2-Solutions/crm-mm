# Cross-cutting routes for getting bookings out of closed platforms into the CRM

Research date: 2026-09-24. Scope: MioDottore/Docplanner, Treatwell/Uala, Fresha, Elty, iDoctors, Doctolib, Booksy.
Baseline already in place: parsing notification emails, reading iCal feeds, publishing an iCal busy feed.

Tags: **[V]** means verified on the linked page during this research. **[I]** means inferred, from memory, or from a secondary source I could not confirm on a primary page. Anything tagged [I] should be checked before you build on it.

---

## 0. Executive summary (ranked)

| Rank | Route | Coverage | Latency | Cost | Legal/ToS risk | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Official Docplanner/MioDottore Integrations API** (become a "medical software provider" partner) | MioDottore (the largest medical platform in Italy) | Real time (push webhooks) | Dev effort + partner process; no public fee | None (contractual) | **Do it.** A real, documented API with push notifications, already open to software vendors in Italy. |
| 2 | **Harden the email pipeline** (inbound email service + deterministic parser + LLM fallback + iCal reconciliation) | All 7 platforms | Seconds to about 1 minute | About €0–20/month infrastructure + about $0.004–0.01 per email for the LLM | Low | **Do it now.** This is the only route that covers every platform. |
| 3 | **Partner integrations with iDoctors and Elty** (Italian; both already integrate with Italian practice software such as AlfaDocs and MEG) | iDoctors, Elty | Real time | Business development effort | None | **Start conversations.** Smaller companies, local, and proven to integrate. |
| 4 | **Google Calendar push bridge** (events.watch + syncToken; replace Frappe's polling) | Fresha (two-way Google sync over OAuth), iDoctors (claims Google sync), staff personal calendars | 15 min Fresha-side delay + seconds for Google push | Free | None | **Useful for Fresha and for busy-time**, but the events carry no client or service details. |
| 5 | **Fresha Data Connector** (Snowflake credentials, paid add-on) | Fresha | Unknown, likely hours [I] | Paid per location | None (official) | Good for **reconciliation and backfill**, not for real time. |
| 6 | **Google Business Profile booking link → the CRM's own booking page** | Bookings that come from Google | n/a | Free | None | This **diverts** future bookings away from the marketplaces rather than capturing them. Recommended. |
| 7 | Reserve with Google / Actions Center partner (Appointments Redirect) | Same as rank 6, plus an automatic "Prenota" button | n/a | High engineering + Google approval | None | Only worth it at scale. The booking link in rank 6 gives about 80% of the value for free. |
| 8 | Android SMS/push-notification forwarder on a salon or clinic phone | Any platform that sends SMS or app pushes | Seconds | About €0 plus a spare phone | Low to medium (GDPR security) | Niche fallback. |
| 9 | Unified calendar APIs (Nylas, Cronofy) | Google, Outlook and iCloud only, not the marketplaces | Seconds to minutes | Nylas about $1.50 per account per month; Cronofy from $99/month | None | Only if you want to stop maintaining three calendar adapters yourself. |
| 10 | RPA / unofficial APIs (Playwright, Supergood-type services, CalMedi-type browser extensions) | Any | Minutes | Medium | **High**, including Italian criminal-law exposure (art. 615-ter c.p.) | Last resort. Needs an explicit customer mandate and a legal opinion. |
| 11 | Legal leverage (Data Act, GDPR art. 20, P2B) | Any | n/a | Letters | n/a | Does **not** force a continuous machine-readable feed. Use it as negotiating pressure and for one-off exports. |

---

## 1. Calendars as a bridge (Google / Microsoft 365 / iCloud)

### 1.1 Which platforms push to Google Calendar in 2026

| Platform | What it offers | Direction and mechanism | Useful for the CRM? |
|---|---|---|---|
| **Fresha** | Calendar sync with Google, Outlook and Apple. **Two-way only with Google**, via OAuth. Other providers use ICS URLs. "It may take up to 15 minutes for your calendar to sync." "For privacy and security reasons, client and service details are not included in your personal calendar." [V] https://www.fresha.com/help-center/knowledge-base/calendar/101373-sync-your-fresha-calendar and https://support.fresha.com/hc/en-us/articles/4410097464338-How-do-I-sync-my-calendar-with-Fresha | Export to Google through the Google API (OAuth) | Yes for **busy time and near-real-time "something changed"** signals, but with no client or service details. Pair it with email parsing to fill in the details. |
| **Treatwell Connect / Uala** | Per-employee "secret iCal address" that can be subscribed to from Google. One-way. [V] https://partnercare.treatwell.com/s/article/Come-impostare-la-sincronizzazione-di-iCal?language=it. Imports external calendars as blocks, refreshed about every 5 minutes, with a Sync button. [V, snippet] https://partners.treatwell.com/hc/en-gb/articles/360003392840-How-to-sync-Connect-with-other-calendar-softwares | ICS pull only | No added value over reading the ICS directly. A Google subscription to an ICS URL refreshes **more slowly** (typically hours) [I]. |
| **MioDottore (Docplanner)** | The old Google Calendar sync was **withdrawn**. Docplanner says its own agenda makes it unnecessary. [V] https://pro.miodottore.it/blog/centrimedici/gestione/miodottore-vs-google-calendar. Agenda data export exists. [V, snippet] https://help.docplanner.com/s/article/How-to-Export-Your-Doctoralia-Online-Agenda-Data?language=it | None to Google | Use the partner API (§8) and email instead. |
| **Doctolib** | "Real-time synchronization with an external calendar is not available." Only a one-way iCal URL that is not instant. Third-party tools fill the gap: **Docal.io** (5 syncs/day on Premium, both directions, time slots only) and **CalMedi** (a Chrome extension that reads Doctolib from the logged-in browser "several times per hour"; €10–35/month depending on sync frequency). [V] https://www.docal.io/ and https://calmedi.io/en/ | iCal pull, or third-party scraping into Google | CalMedi/Docal show that the market accepts "browser session → Google" bridges. Their risk profile is the same as RPA (§6). |
| **iDoctors** | Markets "an agenda always synchronised with your staff and with Google Calendar". [V, snippet] https://www.idoctors.it/collabora. It also has a real-time integration with the AlfaDocs practice software. [V] https://www.alfadocs.com/marketplace/applicazioni/idoctors | Google sync (mechanism not documented) | Worth testing with a pilot account. If it writes to Google through the API, the watch bridge in §1.2 gives near-real-time data. |
| **Elty** | A shared agenda synced "in real time". Integrates with MEG and AlfaDocs (two-way, instant availability, bookings and cancellations). [V] https://www.alfadocs.com/marketplace/applicazioni/elty | A partner API exists (not public) | Go the partner route (§8). |
| **Booksy** | Help-centre pages refer to calendar sync with Google/Apple and to importing a .ics file. Two-way sync is claimed in Booksy marketing, but I could not verify it (help centre returned 403). [I] https://support.booksy.com/hc/en-us/articles/17499276381458-Can-I-import-my-external-calendar-to-Booksy | Unclear | Test with a pilot account. |

**Conclusion:** Google Calendar is only a *better* bridge than iCal when the platform writes to Google through the API. Among these platforms that means Fresha, possibly iDoctors, and possibly Booksy. For ICS-only platforms, Google's refresh of subscribed calendars makes things slower, not faster.

### 1.2 Consuming Google Calendar changes in near real time

- `events.watch` sends a POST to your HTTPS webhook. The certificate must be valid (no self-signed certificates). The **notification has no body**: only headers `X-Goog-Channel-ID`, `X-Goog-Resource-ID`, `X-Goog-Resource-State` (`sync`, `exists`, `not_exists`), `X-Goog-Message-Number` and an optional `X-Goog-Channel-Token`. You must then call `events.list` with the stored `syncToken` to get the changes. There is "no automatic way to renew a notification channel", so you create a new one before it expires. [V] https://developers.google.com/workspace/calendar/api/guides/push
- Channel lifetime is typically at most about 7 days (default TTL 604800 s), so renew daily. [I, secondary] https://developers.google.com/workspace/calendar/api/v3/reference/events/watch
- `syncToken` gives incremental sync. A `410 Gone` means you must do a full resync. [V, visible in Frappe code below]
- OAuth: Calendar scopes are *sensitive* (brand plus sensitive-scope verification). Gmail read scopes are *restricted* and need a **CASA security assessment every year**. So read notification emails through forwarding to an inbound address, **not** through the Gmail API. [V] https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification and https://deepstrike.io/blog/google-casa-security-assessment-2025

### 1.3 Frappe's built-in Google Calendar integration: what it does and where it stops

Checked against `frappe/integrations/doctype/google_calendar/google_calendar.py` on the develop branch [V] https://raw.githubusercontent.com/frappe/frappe/develop/frappe/integrations/doctype/google_calendar/google_calendar.py and `frappe/hooks.py`. This repo already uses it in `crm/api/booking.py`.

- **Pull is polling only.** `google_calendar.sync` sits in the `"all"` scheduler bucket (by default every scheduler tick, about 4 minutes [I]). It calls `events.list(syncToken=…, showDeleted=True, singleEvents=False, maxResults=2000)` and stores `next_sync_token` encrypted. On a 410 it clears the token.
- **No `events.watch` / push channel support.**
- One Google calendar per "Google Calendar" doc, which is per user. Events land in Frappe's generic **`Event`** doctype, not in CRM bookings. Cancelled events become `status=Closed`.
- Recurring-instance changes are skipped (`if event.get("recurringEventId"): ...`). Docs confirm: "If an instance of a recurring event is cancelled in Google Calendar, this change will not be reflected." [V] https://docs.frappe.io/framework/user/en/guides/integration/google_calendar
- Known bugs: a `DoesNotExistError` on cancelled events (issue #37010) and wrong owner on pulled events (issue #30918). [V] https://github.com/frappe/frappe/issues/37010 and https://github.com/frappe/frappe/issues/30918
- Push to Google happens through `Event` doc_events (after_insert, on_update, on_trash).

**Recommendation:** add a whitelisted `allow_guest` webhook endpoint in `crm/` that validates `X-Goog-Channel-Token` and `frappe.enqueue`s `sync_events_from_google_calendar(g)` (with debounce and deduplication). Add a daily job that (re)creates watch channels. Keep the 4-minute poll as a safety net. Then map `Event` records whose source is a "Fresha"/"Treatwell" calendar into CRM bookings. Match on time slot and staff, and fill in details from the parsed emails.

### 1.4 Microsoft 365 / Outlook (Graph)

- Subscriptions on `/users/{id}/events`. Maximum lifetime **10,080 min (under 7 days)**, or **1,440 min** with rich notifications that include resource data. Latency for `event` is "Unknown" (`calendar` is under 1 min average, 3 min max). Limit of 1,000 subscriptions per mailbox. Lifecycle notifications warn about missed events. [V] https://learn.microsoft.com/en-us/graph/change-notifications-overview
- Use `calendarView/delta` for the incremental read after each notification [I]. No platform in the list pushes to Outlook through the API. Fresha exports to Outlook via ICS [V], so Graph only helps for staff personal calendars.

### 1.5 Apple iCloud (CalDAV)

- There is **no third-party push**. You poll with `sync-collection` (RFC 6578) or ctag/ETag, using the Apple ID plus a **16-character app-specific password** over Basic Auth. [V, secondary] https://cli.nylas.com/guides/caldav-explained and https://www.onecal.io/blog/how-to-integrate-icloud-calendar-api-into-your-app
- Low value as a bridge. None of these platforms writes to iCloud except by ICS subscription.

### 1.6 Managed calendar APIs (if you do not want to maintain three adapters)

- **Nylas v3**: covers Google, Microsoft, Exchange and iCloud, is webhook-first with polling fallback. About **$10/month for 5 connected accounts, then $1.50 per account per month**. [V, secondary] https://zeeg.me/en/blog/post/nylas-api-pricing and https://www.nylas.com/products/calendar-api/
- **Cronofy**: covers Google, Microsoft and Apple with push notifications. Usage-based from a **$99/month minimum** [V, secondary] https://www.cronofy.com/api-pricing
- Neither one connects to the marketplaces themselves.

---

## 2. Reserve with Google / Actions Center, and Google Business Profile booking links

- **Appointments Redirect** is the current appointments integration. The partner sends entity, action and service feeds; Google shows the button and redirects the user to the partner's booking page; the partner implements Conversion Tracking v2. To join, you fill in the partner interest form. [V] https://developers.google.com/actions-center/verticals/appointments/redirect/overview
- Merchant policy: the business must match Google Maps (name, address, phone, website). Beauty and Healthcare are supported. 60+ countries including most of Europe. **No minimum merchant count is published.** [V] https://developers.google.com/actions-center/verticals/appointments/redirect/policies/platform-policies
- **End-to-end (booking inside Google)**: the migration guide covers moving *existing* E2E appointments partners to Redirect. From that I infer **E2E is not open to new appointments partners**. [V migration page, I conclusion] https://developers.google.com/actions-center/verticals/appointments/redirect/migration/overview
- An independent software vendor *can* apply for Redirect. In practice Google prioritises partners with meaningful merchant inventory and a working availability feed; approval takes months [I].
- **DMA**: Google's EEA changes (2024–2026) mainly reshaped hotels, flights and comparison-site units. I found nothing specific that changes the local appointments "Prenota" button in Italy [I]. https://blog.google/company-news/inside-google/around-the-globe/google-europe/complying-with-the-digital-markets-act/
- **Does it help receive bookings?** It *diverts* bookings rather than capturing them. MioDottore turns on the GBP "Prenota ora" button automatically when the profile matches [V] https://www.tecnomedicina.it/miodottore-si-integra-con-google/. Booksy, Treatwell and Fresha are also RwG partners [V] https://biz.booksy.com/en-us/blog/reserve-with-google-x-booksy-get-more-bookings-online. Without being a partner, the business can **add its own booking URL** (up to 10 links per category) and mark one as **"Business preferred"**. Provider links "may appear automatically" and are removed by asking the provider. These links are **not** manageable through the Business Profile API. [V] https://support.google.com/business/answer/6218037?hl=en
- **Action:** in CRM onboarding, have the business add the CRM's public booking page as the preferred booking link. That costs nothing and moves Google-origin demand away from commission-charging marketplaces. Apply to Redirect later if the customer base grows to hundreds of locations.

---

## 3. Aggregators, unified APIs and channel managers

| Vendor | Covers these platforms? | Notes |
|---|---|---|
| Unified.to | **No**. Its calendar category lists Acuity, Cal.com, Calendly, Google Calendar and similar; no Fresha, Treatwell, Booksy, Doctolib, Docplanner or Mindbody. [V] https://unified.to/integrations?c=calendar | |
| Merge, Kombo | No. They cover HR, ATS and accounting [I]. | |
| Nylas, Cronofy | Calendars only (§1.6). | |
| **Supergood.ai** | **Unofficial, managed APIs** built by "automating the authenticated web app directly" with the customer's credentials, one customer at a time. Beauty/salon list: Booksy, Boulevard, DaySmart, Envision, **Fresha**, GlossGenius, Insight. **Treatwell, MioDottore and Doctolib are not listed.** It "recommend[s]" official APIs where they exist. [V] https://supergood.ai/docs/booksy-api and https://supergood.ai/api-report-card/fresha | Same legal profile as §6, just outsourced. US-based, so there are GDPR transfer questions for health data [I]. |
| CalMedi, Docal.io | Doctolib → Google only (§1.1). [V] | |
| Parse.bot, Apify actors | **Public marketplace** data only (salon listings, prices, reviews), not the business agenda. [V] https://apify.com/unfenced-group/treatwell-scraper/api and https://apify.com/gio21/doctoralia-scraper/api | Not useful for bookings. |
| Salonized | Real-time Treatwell marketplace integration, but **Salonized is owned by Treatwell** ("Salonized by Treatwell") and the integration is limited to NL, BE, DE, CH and UK. [V] https://help.salonized.com/en/articles/6287754-what-is-the-treatwell-integration | Shows that Treatwell has a partner-side API. |
| AlfaDocs (IT) | Integrates **iDoctors** (instant, iDoctors → AlfaDocs) and **Elty** (two-way, real time). [V] (links in §1.1) | Shows that Italian partner APIs exist for iDoctors and Elty. |
| OnSched, Trafft, Hapio, Zenoti, SimplyBook, Setmore | Booking engines or practice software. I found no evidence that any of them resells Treatwell, Fresha or MioDottore connectivity to third parties [I]. | |
| Salon "channel managers" (hotel-style) | **No product found** that offers Treatwell, Fresha or Booksy channel management to third-party software in Italy [I, based on a negative search result]. | |

**Conclusion:** no aggregator solves this. The only "connectivity products" are unofficial automation services, and they carry the same risk as building RPA yourself.

---

## 4. Production-grade email pipeline

### 4.1 Inbound email services

| Service | How it delivers | Cost (2026) | Notes |
|---|---|---|---|
| **Cloudflare Email Routing + Email Workers** | A Worker receives the raw MIME message, parses it, and can `fetch()` a POST to Frappe or store it in R2 | Routing is free with no volume limit; 200 rules per domain plus a catch-all; 25 MiB maximum; the Worker bills at Workers pricing (free tier available). [V, secondary] https://mecanik.dev/en/posts/cloudflare-email-routing-free-custom-domain-email/ and https://developers.cloudflare.com/email-service/platform/limits/ | Cheapest. A catch-all on `in.<crm-domain>` gives per-tenant addresses. |
| **Amazon SES receiving** | Receipt rule → S3, SNS or Lambda → webhook | **$0.10 per 1,000 emails**, plus chunk fees above 256 KB; same price in all regions, including EU. [V, secondary] https://aws.amazon.com/ses/pricing/ | EU region available, which helps for health data. |
| **Postmark Inbound** | JSON webhook with parsed body, headers and attachments, plus spam score | Needs the Pro tier (about $16.50/month) or higher. [V, secondary] https://postmarkapp.com/developer/user-guide/inbound and https://klymentiev.com/blog/postmark-pricing | Nicest JSON format and retries. |
| **Mailgun Routes** | Regex matching on recipient or headers → forward to URL as parsed JSON | Paid plans from about $15/month; log retention depends on plan. [V, secondary] https://www.mailgun.com/features/inbound-email-routing/ | |
| **SendGrid Inbound Parse** | Multipart POST; 30 MB maximum | No free tier; Essentials from $19.95/month. [V, secondary] https://mails.ai/blog/best-inbound-email-parsing-api-for-developers | |

**Recommended design:**
1. Give each tenant an address such as `t-<hash>@in.<crm>`. Where the platform allows it, set that address directly as a notification recipient. MioDottore lets you add an assistant as a recipient [V, snippet] https://pro.miodottore.it/prodotto/funzionalita/messaggi-automatizzati-di-conferma-e-promemoria. Otherwise use a Gmail/Outlook forwarding rule, and have the pipeline detect and surface the forwarding-confirmation code.
2. Verify DKIM/SPF alignment to the platform's sending domain, so spoofed "bookings" are rejected.
3. Store the raw MIME in the Frappe File store for replay and auditing.
4. Parse: deterministic per-template parser first, then LLM fallback, then schema validation.
5. Reconcile against the iCal feed (does the time slot exist?) before auto-confirming. Otherwise send it to a review queue.
6. Make it idempotent with a key made of platform, platform booking reference (or hash of start time, staff and client), and event type.

### 4.2 LLM extraction (Claude API, structured outputs)

- Use `output_config.format` with a JSON schema for platform, event type (new, modify, cancel), booking reference, start/end, staff, service, client name, phone, email and price [V, from the Claude API skill docs]. Keep a frozen system prompt and cache it.
- Prices (Anthropic first party, per million tokens): **Claude Haiku 4.5 $1 in / $5 out**; **Claude Sonnet 5 $2 / $10**; Opus 5 $5 / $25. Batch API is 50% off. Cached input costs about 0.1×. [V, from the Claude API skill model table, cached 2026-06-24]
- **Cost estimate** for a typical notification email of about 1.5–3k input tokens after stripping HTML, plus about 300 output tokens:
  - Haiku 4.5: about **$0.003–0.0045 per email**, so about **$3–5 per 1,000 emails**.
  - Sonnet 5: about **$0.006–0.009 per email**.
  - Only emails that fail the deterministic parser need the LLM, which typically cuts spend by 90% or more [I].
- **Latency**: about 1–4 s per call [I], negligible next to email delivery (seconds to a minute).
- **Privacy**: clinic emails contain health data (GDPR art. 9). You need a DPA with the LLM provider, data minimisation (strip signatures and footers, redact what is not needed), and a choice of region or deployment. An EU region through a cloud provider (Bedrock or Vertex EU) may be needed [I].

---

## 5. SMS and WhatsApp capture

- MioDottore notifies the doctor of each new or changed visit **by SMS and/or email** (configurable), and you can add an assistant as a recipient [V, snippet above]. Treatwell, Fresha and Booksy mostly send app pushes and emails to the business [I].
- **Twilio inbound** needs an Italian number with SMS capability. Italian numbers are subject to AGCOM numbering rules and a ban on sub-assignment. Availability of SMS-capable Italian mobile numbers is limited [V for the rules, I for availability] https://www.twilio.com/en-us/guidelines/it/regulatory and https://www.twilio.com/en-us/legal/numbering-requirements. Changing the doctor's notification phone to a virtual number is also a usability regression.
- **Practical alternative:** an Android phone at the clinic or salon (or a cheap dedicated device logged into the platform's business app) running an open-source forwarder. Options: SmsForwarder (SMS, calls and **app notifications** → webhook), SMSGate/android-sms-gateway, httpSMS, android_income_sms_gateway_webhook. [V] https://github.com/capcom6/android-sms-gateway, https://github.com/bogkonstantin/android_income_sms_gateway_webhook and https://www.opensource-hub.com/en/project/sms-forwarder
  - Reading push notifications from the Treatwell Connect, Fresha or Booksy Biz apps gives latency of seconds with no server-side scraping.
  - Downsides: it is fragile (battery optimisation, OS updates), push text is truncated, and it needs a device-security policy for GDPR.
  - I rate it a legitimate fallback: the business reads its own notifications on its own device.
- **WhatsApp**: the Business Platform cannot read messages sent to someone else's personal number, and these platforms do not send booking notifications to the business over WhatsApp [I]. Not viable.

---

## 6. RPA / browser automation / reverse-engineered private APIs (existence and risks only)

### What exists
- Apify actors for Treatwell, Doctoralia/MioDottore, Fresha and Booksy all scrape **public listings, prices and reviews**. I found **no public actor that reads a business agenda**. [V] (links in §3)
- GitHub: many Doctolib *patient-side* availability checkers using the undocumented `availabilities.json` endpoint [V] https://github.com/topics/doctolib. `sallar/booksy-api` is patient/consumer side [V, listing] https://github.com/sallar/booksy-api. I found **no public repo** for Treatwell Connect, Fresha Partners, MioDottore PRO or Doctolib Pro agenda APIs.
- Commercial: Supergood (web-app automation with the customer's credentials, §3). CalMedi (a Chrome extension using the practitioner's logged-in Doctolib session) [V].
- Hosted headless browsers: Browserless and Apify are technically usable with the customer's credentials. Expect MFA, bot detection and frequent UI changes [I].

### Risks under Italian and EU law
1. **Criminal law, art. 615-ter c.p. (unauthorised access / remaining in a system).** Cass. SU *Casani* n. 4694/2012 held that a person holding valid credentials still commits the offence if they access or remain "in violation of the conditions and limits set by the owner of the system". The motive does not matter. [V] https://canestrinilex.com/risorse/accesso-abusivo-al-sistema-informatico-cass-pen-469412
   - If the platform's ToS forbid automated access or credential sharing, a vendor running bots with a customer's login is exposed.
   - This is a real Italian-specific risk, higher than under most EU laws [I, assessment].
2. **ToS / contract**: breach can lead to account suspension for the *customer*, which hurts their marketplace revenue. That is the most likely practical consequence [I].
3. **Database sui generis right** (Dir. 96/9, arts. 102-bis/ter of L. 633/1941): repeated, systematic extraction of substantial parts may infringe [I]. Reading one's own bookings is a weak basis for an infringement claim, but it cannot be excluded.
4. **TDM exception** (Dir. 2019/790 art. 4 → art. 70-quater of L. 633/1941, introduced by D.Lgs. 177/2021): allowed only with lawful access and **no machine-readable opt-out**. [V] https://www.agendadigitale.eu/mercati-digitali/text-e-data-mining-come-tutelare-il-database-dopo-la-direttiva-copyright/ and https://www.advant-nctm.com/en/news/il-diritto-di-opt-out
   - It covers "text and data mining" (analysis). Operational syncing of agenda records is arguably *not* TDM, so it is unlikely to be a defence [I].
5. **GDPR**: patient data is special-category (art. 9). The CRM would be a processor (art. 28 DPA with the clinic). Storing customers' platform passwords raises art. 32 security duties and breach exposure. The platform, as controller or processor, may claim the automated access is itself a security incident [I].
6. **Mitigations if you go ahead anyway:**
   - written instruction from the customer;
   - read-only access, low frequency, own session only;
   - no evasion of anti-bot measures;
   - encrypted credential vault;
   - kill switch;
   - legal opinion first.

**Verdict:** use only as a temporary bridge for a specific customer who explicitly asks for it. Never make it the default product path.

---

## 7. Legal leverage

### EU Data Act (Reg. 2023/2854), applicable from 12 Sept 2025
- **Chapter II** (arts. 3–5, access to data from *connected products*) does **not** apply to SaaS booking platforms [I, based on the scope of the regulation].
- **Chapter VI (arts. 23–31)** applies to data processing services **including SaaS** provided to EU customers. [V] https://www.dlapiper.com/en/insights/publications/2025/07/understanding-switching-termination-rights-under-the-data-act and https://www.osborneclarke.com/insights/data-act-part-4-data-act-regulates-cloud-switching-and-influences-contractual-relationship
- The rights are about **switching**: notice period of at most 2 months, a 30-day transitional period, porting of "exportable data" (input and output data, excluding the provider's proprietary data), and switching charges phasing out. [V, secondary] https://www.pinsentmasons.com/out-law/guides/switching-porting-rules-eu-data-act
- **It does not require continuous export during the contract.** Recurring egress for "in-parallel use" (multi-cloud) may be charged at cost (art. 34) [V, secondary, same source].
- Arguable leverage: MioDottore PRO, Treatwell Connect and Fresha are SaaS agendas, so a business customer can demand a **structured, machine-readable export** at switching, and good-faith cooperation (art. 27) [I].
- Platforms may argue that marketplace bookings are *intermediation* data, not SaaS customer data [I].
- Micro and SME providers get some exemptions (art. 31) [I]. These platforms are not SMEs.

### GDPR arts. 15 and 20
- Rights of **natural persons**. A sole-practitioner doctor or beautician may request *their own* personal data. Art. 20 portability covers data "provided by" the data subject and processed on the basis of consent or contract, in a "structured, commonly used and machine-readable format", with direct transmission "where technically feasible" [I, from the GDPR text].
- Patient and client booking data is the *patients'* personal data, so a clinic cannot use art. 20 to obtain it. The clinic's own controller relationship with the platform (processor DPA) decides whether it can instruct the platform to return data [I].
- Nothing here creates a continuous feed.

### P2B Regulation (EU) 2019/1150, art. 9
- Marketplaces (Treatwell, MioDottore, Fresha marketplace) must **disclose** in their ToS what data business users can access.
- This is a transparency duty, **not** an access right. [V, secondary] https://www.osborneclarke.com/insights/regulation-eu-20191150-new-rules-protect-business-users-online-intermediation-platforms

### DMA
- None of these platforms is a gatekeeper. Not applicable [I].

### Template letter
I found none published. A draft for customers to send, in Italian:

> Oggetto: Richiesta di esportazione dati strutturata ai sensi del Reg. (UE) 2023/2854 (Data Act), artt. 23–30, e del Reg. (UE) 2016/679 art. 28 / art. 20
>
> Spett.le [Piattaforma], in qualità di cliente business del servizio [agenda/gestionale] (account [ID]), chiediamo: (1) l'elenco dei dati esportabili e dei formati/interfacce disponibili (art. 26 Data Act); (2) l'esportazione, in formato strutturato, di uso comune e leggibile da dispositivo automatico (CSV/JSON/ICS), di tutti gli appuntamenti, clienti/pazienti, servizi e operatori associati al nostro account; (3) indicazione se esista un'interfaccia (API/webhook) per l'uso in parallelo con altro software (art. 34) e relative condizioni; (4) in qualità di titolare del trattamento per i dati dei nostri pazienti/clienti, conferma delle istruzioni ex art. 28 GDPR per la restituzione dei dati. Restiamo in attesa di riscontro entro 30 giorni. [Firma, P.IVA]

The letter is useful mainly for negotiation and for one-off migration exports.

---

## 8. Commercial route: becoming an official integration partner

| Platform | Programme and API | What they require | Notes |
|---|---|---|---|
| **Docplanner / MioDottore** | **Integrations REST API** "exclusively available to medical software providers". Each clinic authorises access individually. Countries include **Italy**. PHP and .NET SDKs. [V] https://integrations.docplanner.com/guide/ and https://integrations.docplanner.com/ (Italian portal: https://integrations.miodottore.it/) | Contact form → specialist → **sandbox** (test clinic and doctors) → **acceptance test** requiring complete resource mapping, **full two-way booking sync** and real-time schedule updates → clinic activation (credentials through Customer Success, or with written clinic approval to integrations@docplanner.com) → endpoint monitoring (ping every 5 minutes, alert after 3 failures). [V] https://integrations.docplanner.com/guide/integration-process.html. **Notifications**: push (HTTPS POST from one IP, API-key header) or pull (`/api/v3/integration/notifications`, FIFO, up to 100 per call, expire after **72 h**). Events: `slot-booked`, `booking-canceled`, `booking-moved`, optional synchronous `slot-booking` / `booking-moving`, and `break-*`. Push retries after 5 and 10 minutes, then the event is "buried" (release endpoint available once every 60 minutes). [V] https://integrations.docplanner.com/guide/callbacks/push-vs-pull.html | **Best route found.** The CRM must act as the doctor's calendar master (push availability and slots). That fits the CRM's scheduling module. Fees are not published [I]. |
| **Doctolib** | Official API for **accredited partners only** (medical software vendors, hospital information systems); docs are gated. Examples: Optimum (audiology), DrSanté. [V, secondary] https://www.ouiemagazine.net/2023/05/02/les-logiciels-optimum-s-interfacent-avec-doctolib-pour-la-gestion-des-rendez-vous/ and https://www.octoparse.fr/blog/extraction-de-donnees-medicales-sur-doctolib | Expect a security review, HDS-style hosting in France, a partnership contract, and a meaningful installed base [I]. | Doctolib's footprint in Italy is small [I]. Lower priority. |
| **Treatwell (incl. Uala)** | A partner API exists (used by Salonized; ClinicSoftware advertises a "Treatwell partner" integration [V, listing] https://clinicsoftware.com/treatwell-partner/). The Italian partner site mentions opening to "altri gestionali" [V, snippet] https://www.treatwell.it/partners/soluzioni/gestionale/ | Business-development contact. They likely want salon volume in the market and a commission-compatible flow [I]. | Worth a direct approach for the Italian market. |
| **Fresha** | **No merchant or partner API.** The only official programmatic surface is the **Data Connector** (Snowflake credentials, a paid add-on priced per location, one-way, 7-day trial, "fair use up to 8 h/day"). [V] https://www.fresha.com/help-center/knowledge-base/reports/432-data-connector-overview and https://supergood.ai/api-report-card/fresha. `developers.fresha.com` did not resolve in my test [V, via curl]. | n/a | Use the Data Connector (with the customer's consent) for backfill and reconciliation. Freshness is unknown [I]. |
| **Booksy** | A public REST API exists at `alpha.docs.booksy.net` (OAuth2 with JWT), **alpha and partner-gated** (returns 401) [V, curl 401; secondary] https://supergood.ai/api-report-card/booksy | Partner outreach | Low presence in Italy [I]. |
| **iDoctors** | Integrates with AlfaDocs (real time) and asks integrators to contact gestione@idoctors.it. [V] https://www.alfadocs.com/marketplace/applicazioni/idoctors | Business-development contact | Italian, approachable. **High priority.** |
| **Elty** | Integrates with AlfaDocs (two-way, real time) and MEG (API). [V] https://www.alfadocs.com/marketplace/applicazioni/elty | Business-development contact | Italian, **high priority.** |

**What vendors typically need** [I, industry norm]:
- an Italian or EU legal entity, and a signed partner agreement or NDA;
- a GDPR art. 28 DPA, with health-data (art. 9) security measures, an EU hosting statement and a sub-processor list;
- a security questionnaire, with ISO 27001 or SOC 2 as a plus (not always required for small partners);
- a recent **penetration test** report, logging and incident response;
- a named technical contact and a support SLA;
- proof of demand (number of clinics or salons that will activate) or pilot customers;
- passing a certification test (Docplanner does this explicitly);
- sometimes revenue sharing or co-marketing.

---

## 9. Suggested roadmap

1. **Now (weeks):**
   - Put Cloudflare Email Workers or SES in front of the existing parser, with LLM fallback (Haiku 4.5) and iCal reconciliation.
   - Add a Google `events.watch` webhook to Frappe's Google Calendar sync; onboard Fresha customers with Google two-way sync.
   - In onboarding, set the CRM booking page as the **preferred** GBP booking link.
2. **Next (1–3 months):**
   - Apply to the **Docplanner Integrations API**; build the two-way sync on its sandbox.
   - Approach **iDoctors** and **Elty**; contact the Treatwell IT partnerships team.
   - Offer an optional Fresha Data Connector import.
3. **Optional fallback:** an Android notification/SMS forwarder for salons that insist on it.
4. **Avoid by default:** RPA and unofficial APIs. Use them only case by case, with a written customer mandate and a legal opinion (art. 615-ter c.p. exposure).
5. **Legal:** give customers the Data Act / GDPR letter template for one-off exports and as negotiating leverage. Do not count on it for a live feed.
