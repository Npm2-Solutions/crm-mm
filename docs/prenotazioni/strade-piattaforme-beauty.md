# Integration routes for beauty/wellness booking platforms without a public API
Research date: 2026-09-24. Scope: Italian Frappe CRM for salons, spas and wellness studios. The CRM already has email-notification parsing and an iCal feed.
Tags: **[V]** means verified on the cited URL (page content or a search-engine snippet of that page). **[I]** means inferred or not confirmed. No contact address appears here unless a source published it.

---

## 0. Executive summary: the routes that actually work

| Rank | Route | Platforms | Direction | Latency | Effort | ToS risk |
|---|---|---|---|---|---|---|
| 1 | **Google Calendar as a bus.** The platform syncs with Google Calendar, and the CRM reads and writes that calendar through the Google Calendar API | Fresha (two-way), Treatwell Connect (import only, per staff) | In and out | ≤15 min (Fresha) | Low | None, because it is a built-in feature |
| 2 | **CRM-hosted iCal feed per staff, subscribed by the platform** ("Calendario esterno"). This pushes CRM appointments as busy blocks | Treatwell Connect [V], Fresha "Other calendar → import" [V], Booksy import (.ics upload, possibly one-shot) [I] | Out (availability) | Platform-dependent | Low (we already have iCal) | None |
| 3 | **Booking notification emails sent to a dedicated CRM inbox** | Fresha supports "send to specific email addresses" [V]. Treatwell and Booksy only via a staff/owner account email [I] | In | Real time | Already built | None |
| 4 | **Official partner or customer APIs** | Booksy Public API (partner-gated, webhooks) [V]; Phorest API (a single business can request it) [V]; Zenoti (customer-generated key plus webhooks) [V]; Mindbody Public API (developer account plus approval) [V]; Primo in Cloud "Rest API" [V, no docs] | In and out | Real time / polling | Medium to high | None |
| 5 | **Read-only data warehouse**: Fresha Data Connector (Snowflake, paid add-on) | Fresha | In (reconciliation) | Batch (unspecified) | Medium | None |
| 6 | **Scheduled CSV/Excel exports** (client list, appointments) | Treatwell Connect/PRO, Fresha, Booksy | In (backfill/reconcile) | Manual/daily | Low | None |
| 7 | **Become a booking channel ourselves**: Reserve with Google (Actions Center) | The CRM as a partner | Out (bookings from Google) | Real time | High (12–16 weeks for comparable E2E integrations) | None |
| 8 | **Legal lever**: EU Data Act Art. 30(2) "open interfaces" plus Art. 30(5) export, and P2B Reg. Art. 9 transparency | Treatwell/Fresha as SaaS | Negotiation lever | n/a | Letter | None |
| 9 | Unofficial scraping or private endpoints | Treatwell (Selenium), Booksy (web `x-api-key`), Fresha (Apify scrapers of public pages) | In | Varies | Medium | **High** (contract breach, account suspension) |

**Bottom line:**
- For **Fresha**, the strongest non-API route is Google two-way sync plus notification emails to a CRM address plus an optional Snowflake connector.
- For **Treatwell Connect**, the strongest route is our iCal feed per staff into "Calendario esterno" (pushes availability), plus email parsing (receives bookings). Treatwell states that bookings are **not** exported to other calendars.
- **Booksy** is the only marketplace with a real partner API and webhooks, but access is partner-gated.
- **Planity is not operating in Italy.**

---

## 1. Treatwell (Connect, PRO ex-Uala, Salonized)

### 1.1 Partner/API program
- **No public API or developer program found.** A Zapier community thread says "treatwell doesn't have an API", and Zapier staff added it to the wishlist. [V] https://community.zapier.com/how-do-i-3/calendar-sync-between-squarespace-and-treatwell-calendar-22432
- `zapier.com/apps/treatwell/integrations` returns 404 (checked 2026-09-24). [V]
- The Italian partner contract (treatwell.it/info/termini-legali-del-fornitore, version dated Sept 2026) **defines "API"** (§2.3.1) and forbids sublicensing an API to third parties (§7.1.11.i) and reverse-engineering "qualsiasi API o software" (§7.1.11.vi). This implies that API access can exist contractually, but no application page was found. [V] https://www.treatwell.it/info/termini-legali-del-fornitore/
- **Only official software integration: Salonized** (acquired by Treatwell). Treatwell bookings flow into the Salonized calendar, and treatments and availability sync to the marketplace. Commission is 35% + VAT on a new client's first booking, and 0% on repeat clients within 365 days. The integration is available only in **NL, BE, DE, CH, UK**, so **not Italy**. [V] https://help.salonized.com/en/articles/6287754-what-is-the-treatwell-integration and https://www.salonized.com/en/features/treatwell
- Salonized public API/webhooks/Zapier: none found; the Zapier page is 404. [V for Zapier 404, I otherwise]
- **Uala** merged into Treatwell (IT/ES/FR), and the process completed in 2022. Its software is now "Treatwell PRO", with a separate help center at propartnercare.treatwell.com. [V] https://www.treatwell.it/partners/risorse/blog/treatwell-uala-si-uniscono-unico-gruppo/
- Treatwell claims it "non si sincronizza con altri gestionali" (it acts as the salon's exclusive partner). This is a search snippet from its Italian partner pages. [V-snippet] https://www.treatwell.it/partners/soluzioni/gestionale/
- Contacts: only press@treatwell.com was found, via a third-party aggregator [I]. There is no public integrations/partnerships email. Recommended path: go through the salon's Treatwell account manager or partner support (help center chat) and ask about "integrazione software partner". [I]

### 1.2 Built-in sync
- **iCal import per staff member ("Calendario esterno")**. Path: Team → Team → [member] → External Calendar → paste the iCal URL → "Link Calendar". Busy times from the external calendar block availability in Connect. **One-directional: Connect appointments are NOT reflected in the other calendar.** [V-snippet] https://partnercare.treatwell.com/s/article/Come-impostare-la-sincronizzazione-di-iCal?language=it (old URL partners.treatwell.com/hc/it/articles/115005413069, now 301-redirected)
  - **Implication:** the CRM can push availability to Treatwell by exposing one secret iCal URL per operator. This is a real "push availability" route. Refresh interval is not documented. [I] Test the interval empirically.
- A separate article, "Come sincronizzare Connect con altri software per la gestione del calendario", mentions software allowing two-way sync. Content is behind a Salesforce JS-rendered page and could not be read. [V exists; content I] https://partnercare.treatwell.com/s/article/How-to-sync-Connect-with-other-calendar-softwares?language=it
- A Treatwell PRO (ex-Uala) Google Calendar sync article exists (snippet: make sure "My calendars" and "Other calendars" are checked in Google Calendar). [V-snippet] https://propartnercare.treatwell.com/s/?language=it&path=The-Treatwell-Pro-Calendar&view=article

### 1.3 Exports
- Connect client list export as CSV. [V-snippet] https://partnercare.treatwell.com/s/article/How-do-I-export-my-client-list?language=en_GB
- PRO client list export as Excel. Only the owner/account holder can export, and the file is **sent by email to the account holder**. That email is parseable, so a scheduled manual export could be ingested automatically. [V-snippet] https://propartnercare.treatwell.com/s/?language=it&path=How-to-download-the-Client-List&view=article
- PRO appointments summary download or email: [V-snippet] https://propartnercare.treatwell.com/s/?language=en_US&view=article&path=How-do-I-download-an-appointments-summary-or-get-it-by-email
- POS reports: https://partnercare.treatwell.com/s/?language=en_GB&view=article&path=POS-reports [V exists]
- Contract §10.8: before termination the partner may download its data (reviews excluded). [V] termini-legali-del-fornitore

### 1.4 Notifications
- Client-side notifications: confirmation email 15 minutes after booking, a 24h reminder, and reschedule/cancel emails. Salons configure these under Marketing → Automated messaging. [V-snippet] https://partnercare.treatwell.com/s/?language=en_GB&path=appointments%2FClient-notifications-about-appointments&view=article
- Staff: the Connect app notifies staff in real time. [V-snippet] https://www.treatwell.it/partners/ (blog/features)
- No documented option was found for "send salon booking alerts to an additional email". **Workaround [I]:** create a team member whose login email is the CRM inbox, or set up a forwarding rule on the owner mailbox.
- Treatwell Connect release notes for March and June 2026 mention nothing about API, export or sync. [V] https://www.treatwell.it/partners/risorse/blog/the-salon-pulse-le-novita-di-treatwell-connect-marzo-2026/ and https://www.treatwell.it/partners/risorse/blog/the-salon-pulse-le-novita-di-treatwell-connect-giugno-2026/

### 1.5 Payments
- **Treatwell Pay** (POS, card machine, Tap to Pay) is **powered by Stripe**. Payouts can be daily, weekly or bi-weekly (default bi-weekly). [V] https://www.treatwell.co.uk/partners/solutions/payments/ and the March 2026 Italian release notes
- There is no evidence that the salon gets its own Stripe dashboard or webhooks. The setup is likely Stripe Connect under Treatwell as the platform, so the webhooks belong to Treatwell. [I]
- The only event stream the salon owns is **bank payouts**, which could be read via PSD2/open-banking aggregation (aggregated, not per booking). [I]

### 1.6 Unofficial / GitHub
- `supawichza40/TreatwellDailySummary`: Selenium browser automation that scrapes daily appointments from the Treatwell partner web app (2022). [V] https://github.com/supawichza40/TreatwellDailySummary
- No maintained unofficial API client was found. The Connect mobile app package is `com.wahanda.connect`. [V]
- **ToS risk:** §7.1.11 prohibits reverse engineering and interfering with APIs or servers. Scraping the partner web app is therefore a contract risk. [V]

---

## 2. Fresha

### 2.1 Partner/API program
- **No merchant REST/GraphQL API, no developer program, no webhooks.** [V] https://supergood.ai/api-report-card/fresha (third-party assessment, Aug 2026) and https://www.usecarly.com/blog/fresha-ai/
- `github.com/fresha/api-tools` is internal OpenAPI tooling, not a customer API. [V]
- `zapier.com/apps/fresha` returns 404, and there is no Pipedream app. [V checked]
- `partners.fresha.com` is the merchant back-office ("Partner Account"), not a developer or integrator program. It has an add-ons page at partners.fresha.com/add-ons. [V]
- Partner Terms: "Fresha Widget or other application program interfaces (APIs)" is mentioned for embedding booking. Partners may not reverse engineer or access the platform to build a competing product. [V] https://terms.fresha.com/partner-terms
- The consumer Terms of Use prohibit scraping. [V] https://terms.fresha.com/terms-use

### 2.2 Official integrations
- Reserve with Google: [V] https://www.fresha.com/help-center/knowledge-base/online-profile/179-get-booked-on-reserve-with-google
- Facebook/Instagram "Book now": [V] https://www.fresha.com/help-center/knowledge-base/online-profile/180-set-up-facebook-and-instagram-bookings
- Data Connector (Snowflake to 40+ BI tools): [V] see §2.4
- No intermediary with a public API/webhooks that chains Fresha data was found. [I]

### 2.3 Calendar sync (key route)
Source for everything in this list [V]: https://www.fresha.com/help-center/knowledge-base/calendar/101373-sync-your-fresha-calendar
- **Google Calendar supports three modes: export only, import only, or two-way.**
- For "Other calendars" (Outlook, Apple, generic ICS): export only or import only. You can link twice, once for export and once for import.
- The link is per team member (Team → Team members → profile → Settings). Managers can link calendars for team members.
- **Imported events become "blocked time"**, with either all details or "time and duration only".
- Sync takes **up to 15 min**.
- **Privacy caveat [V-snippet]:** exported events contain only start/end time and a link to the appointment in Fresha. **Client and service details are not included.** https://www.fresha.com/help-center/knowledge-base/calendar/208-sync-your-fresha-calendar
- **Recipe:**
  - One Google calendar per operator, owned by the salon, is linked in Fresha as two-way (or export plus import).
  - The CRM uses the Google Calendar API with push notifications (watch channels) on that calendar.
  - A new or moved event gives the slot occupation within ≤15 min. The CRM enriches it with the details from the notification email (§2.5), matching on staff, start time and the link/appointment id in the event description.
  - CRM appointments written into the same calendar become blocked time in Fresha, which pushes availability.

### 2.4 Data Connector (read-only warehouse)
- Paid add-on priced per number of locations, with a 7-day trial.
- Gives raw Fresha data via **Snowflake** credentials (account URL, user, warehouse, db, schema).
- One-way (Fresha to tool). Requires the "Manage Data connections" permission.
- [V] https://www.fresha.com/help-center/knowledge-base/reports/432-data-connector-overview and https://www.fresha.com/help-center/knowledge-base/reports/479-available-data-connector-tools
- The tables page exists (https://www.fresha.com/help-center/knowledge-base/reports/279-data-connector-tables), and a snippet mentions a bookings table with the services per appointment. Refresh latency is undocumented and the price is not public. [V-snippet / I]
- **Use:** a Frappe scheduled job queries Snowflake (Python `snowflake-connector-python`) for reconciliation of appointments, clients and sales. Legitimate and ToS-safe. [I]

### 2.5 Notifications
- Settings → Scheduling → Online bookings → Notifications → Edit. Options are **"send to team member booked"** or **"send to specific email addresses" (comma-separated)**, for Booked, Rescheduled and Cancelled events. Email only. [V] https://www.fresha.com/help-center/knowledge-base/calendar/101218-manage-online-bookings-settings
  - **This makes a dedicated CRM ingestion address officially supported.**
- Personal notifications: [V] https://www.fresha.com/help-center/knowledge-base/personal-account/36-manage-your-personal-notifications

### 2.6 Exports
- Client list export: [V] https://www.fresha.com/help-center/knowledge-base/clients/58-export-your-client-list
- Service menu export: [V] https://www.fresha.com/help-center/knowledge-base/catalog/100646-export-your-service-menu
- Card data is non-exportable. [V] supergood report card

### 2.7 Payments
- Fresha payments are **Adyen for Platforms**, not Stripe. [V] https://www.adyen.com/knowledge-hub/case-study-fresha-american-express and https://terms.fresha.com/adyen-for-platforms-terms-conditions
- The salon has no documented webhook access. [I]

### 2.8 Unofficial
- Only Apify scrapers of **public marketplace listings** exist (leads, services, prices), e.g. apify.com/scrapesage/fresha-scraper and apify.com/figue/fresha-salon-scraper. [V]
- Nothing for the partner back-office. There is no official Fresha MCP server. [V] supergood
- Supergood markets an "unofficial API" that automates the authenticated web app. That is a ToS risk. [V exists]

---

## 3. Booksy

### 3.1 Partner API (the only real marketplace API)
- **Booksy Public API**: a partner-facing REST API.
  - Docs at https://docs.booksy.com/v01.html (plus an alpha copy at alpha.docs.booksy.net) **return HTTP 401**. Checked 2026-09-24. [V]
  - Base URL `https://us.booksy.com/public-api/us/`.
  - Auth: RSA key pair (sandbox and prod), an RS256 JWT assertion exchanged at `/token/` for a 5-minute access token and a 3-day refresh token. Versioned via `Accept: application/json; version=0.3`.
  - About 96 endpoints: business, schedules, resources (staff/appliances), time off, services and variants, customers, appointments, reviews.
  - [V] https://apis.io/apis/booksy/booksy-public-api/ and https://github.com/api-evangelist/booksy
- **Appointment webhook**:
  - Actions CREATED, MODIFIED, CANCELLED.
  - Payload includes customer name, phone and email, `booked_from/till`, `subbookings[staffer_id, service_variant_id, service_name]`, and `import_uid`.
  - Retries at 5, 10, 20 and 40 minutes, then stop. Configured during partner onboarding.
  - `import_uid` suggests Booksy supports **importing appointments from an external system of record**, i.e. two-way sync for software partners. [I]
  - [V] https://raw.githubusercontent.com/api-evangelist/booksy/main/asyncapi/booksy-appointment-webhooks.yml
- **Access:** there is no self-serve portal; you must contact Booksy. No public application form or email was found. [V-snippet] supergood / apis.io
- Who can apply: software partners, since the API is built around partner-level keys. Evidence of single salons getting keys: none. [I]
- Other partners: Google (agentic booking launch partner, Aug 2025) [V-snippet] https://www.usecarly.com/blog/booksy-ai/ ; Groupon [V-snippet] businesswire 2021.
- Zapier: no Booksy app; the Zapier community says there is no integration. [V] https://community.zapier.com/how-do-i-3/how-to-use-booksy-app-for-appointments-46721

### 3.2 Italy presence
- `booksy.com/it-it/` redirects to `booksy.com/en-it/`, a generic landing page with no visible Italian listings. There are Italian App Store listings. Actual Italian salon density is likely low. [V redirect; I density]

### 3.3 Built-in sync / exports
- External calendar import is available, with a maximum of 5,000 events and 12 MB. It looks like a one-shot .ics import, not a subscription. [V-snippet] https://support.booksy.com/hc/en-us/articles/17499276381458 (403 to bots) [I on subscription]
- There is a Data Export section in the help center (client list copy). [V-snippet] https://support.booksy.com/hc/en-us/sections/20664663544594-Data-Export
- Google two-way sync: conflicting evidence. Third-party guides use Make. [I]

### 3.4 Unofficial
- The web consumer API is `https://us.booksy.com/api/us/2/customer_api/...` with a baked-in web `x-api-key`. It is documented by:
  - `klappy/TataOroWhatsAppGPT/docs/BOOKSY_API_DISCOVERY.md`, citing `RT-Tap/booksyCORSproxy`
  - `mvanhorn/printing-press-library` (Booksy CLI brief, 2026-08). Public reads (business, services, reviews, availability) work anonymously, and booking requires a user token.
  - [V] GitHub
- **Useful read-only for availability** of any public Booksy business, but it is a ToS and privacy risk. There are also Apify scrapers. [V]

---

## 4. Planity
- **Not available in Italy.** `planity.it` redirects to `planity.com/unsupported-country`, which lists France, Belgium and Germany. [V] Checked 2026-09-24.
- Expansion plans for IT/ES/PT/CH/AT/NL have been reported, with no date. [V-snippet]
- Planity uses Stripe for payments. [V] https://stripe.com/customers/planity
- No public API. [I]

---

## 5. Italian salon software and portals

| Product | API / integration evidence | Notes |
|---|---|---|
| **WeGest + Prenotado** | Prenotado is WeGest's own marketplace. Bookings land automatically in the WeGest agenda. It is included in the subscription with zero commission [V] https://www.wegest.it/marketplace-prenotado/. No public API or docs were found [I]. | Ask WeGest for a web service. Contacts are on wegest.it. |
| **PRIMO / Primo in Cloud / BeWelly** | "Primo in Cloud, grazie allo sviluppo di apposite **Rest API** si presta all'integrazione con qualsiasi piattaforma esterna". It already integrates with WhatsApp, Wati, HubSpot ("HunSpot" in the snippet), WooCommerce, SendApp and Blueticks [V-snippet from Primo site]. BeWelly is Primo's consumer booking app [V] https://primosoftware.it/bewelly/ | **Best Italian candidate for an official API partnership.** The toll-free number 800 911 947 is for sales, not support. PEC primosoftware@pec.it [V]. |
| **Maki App** | Custom salon app plus agenda. No API mention [V] https://www.makiapp.it/ | Contacts published: info@makiapp.it, +39 0776 310902 [V-snippet] |
| **Shore** | An old API existed (HTTP Basic with API key). The docs repo `shore-gmbh/docs.shore.com` was **archived in May 2019** [V]. Google Calendar sync exists [V] https://help.shore.com/en/frequently-asked-questions-about-the-google-calendar-sync. No Zapier app (404) [V]. | Use the Google Calendar route. |
| **Phorest** | **API available to a single business on request.** Contact Phorest support or api-requests@phorest.com, quoting the Phorest Account Number and CC'ing the owner. Third-party vendors may pay integration charges. **No webhooks**, so you must poll. Basic auth with a `global/` username [V] https://support.phorest.com/hc/en-us/articles/360018509300-Getting-Started-with-Phorest-API, https://developer.phorest.com/docs/getting-started | Low Italian presence [I] |
| **Zenoti** | Customers generate an API key in the admin console, and webhooks are available (Configuration > Integration > Webhooks). Rate limit 60 calls/min per org [V] https://docs.zenoti.com/docs, https://help.zenoti.com/en/articles/6133162 | Enterprise spa chains. Zapier app exists (200) [V]. |
| **Mindbody** | Public API v6. Build on a developer sandbox, request Live access (manual review, metered), then an activation code per Site ID. Webhooks cover appointments, clients, sales and more [V] https://developers.mindbodyonline.com/ | Zapier and Pipedream apps exist [V] |
| **Booker** (Mindbody-owned) | Separate Booker API [V] https://developers.mindbodyonline.com/ui/documentation/booker-api | Mostly US |
| **Salon Iris** | US product. No public API or Zapier found [I] | Not relevant for Italy |
| **Wellyou** | **Not found.** Possible confusion with Wellify, Welly or WellBy (Zucchetti) [V negative search] | WellBy (Zucchetti) targets spa/gym [V] |
| Others seen in Italy | Beautycheck, Magnolia PRO, BeautyOnWeb (Dylog), Biuday, Panema, Vanity (GAB Tamagnini), Bookizon, Wellenys, Bookiapp [V listings]. No public API docs found [I]. | Candidates for bilateral agreements |

---

## 6. Automation platforms
- **Zapier** (HTTP check 2026-09-24):
  - 404 for fresha, treatwell, booksy, salonized, phorest, shore, planity and wegest.
  - 200 for zenoti, mindbody, acuity-scheduling and timely.
  - [V]
- **Pipedream:** only mindbody (200). The others return 404. [V]
- **Make.com:** returned 403 to automated checks, so could not verify. Make community posts mention Booksy↔Google via Make, with no official module. [I]
- **n8n community nodes:** no npm packages for fresha, treatwell, booksy or phorest. [V negative search]

---

## 7. Reserve with Google (becoming a channel)
- Partners fill in the Actions Center partner interest form.
- Requirements:
  - a direct contract with merchants
  - a merchant list that matches Google Maps locations
  - data quality obligations
- Comparable E2E integrations take about 12–16 weeks with two technical staff.
- [V] https://developers.google.com/actions-center/verticals/reservations/e2e/overview and https://developers.google.com/actions-center/verticals/local-services/e2e/integration-steps/overview
- The lighter alternative is **Appointments Redirect** (a link-out to our booking page). [V] https://developers.google.com/actions-center/verticals/appointments/redirect/overview
- Treatwell PRO, Fresha and WeGest-type tools are already RwG providers. Whether a merchant can have multiple providers depends on Google's matching. [I]

---

## 8. Legal levers

### GDPR
- **Art. 20 portability** belongs to *data subjects* (natural persons), not to the salon as a business. It does not give a salon a right to continuous export. [I, legal reading]
- If the platform acts as the salon's **processor** for the salon's own client database, Art. 28(3)(g) (return or deletion of data) applies, and the controller directs processing. That covers export on request, not an API. [I]
- Treatwell's contract §12.14 splits data access: Treatwell sees everything, and partners see their own data plus customer data needed for the order. [V]

### EU Data Act (Reg. 2023/2854), Chapter VI, applicable from **12 Sept 2025** to data processing services, including SaaS [V]
Sources: https://data-act-law.eu/article/30/, https://www.eu-data-act.com/Data_Act_Article_34.html, and DLA Piper/W. Fry summaries.
- **Art. 30(2):** non-IaaS providers "shall make **open interfaces** available to an equal extent to all their customers and the concerned destination providers **free of charge** to facilitate the switching process". [V]
- **Art. 30(5):** absent common specifications, the provider "shall, at the request of the customer, export all exportable data in a structured, commonly used and machine-readable format". [V]
- **Art. 34:** interoperability for **in-parallel use** of multiple services. Only egress costs may be charged. [V]
- **Art. 29:** switching charges are fully banned from **12 Jan 2027**. [V]
- "Exportable data" covers input and output data generated by the customer's use, excluding the provider's IP or trade secrets. [V]
- **Assessment [I]:**
  - Treatwell Connect/PRO and Fresha as salon *software* are plausibly "data processing services". The marketplace part is intermediation and arguably out of scope.
  - Art. 30(2) and Art. 34 give a credible basis to ask for an interface for in-parallel use with our CRM.
  - A "continuous export" duty is not explicit. The text frames it around switching and parallel use, so it is a negotiation lever, not a guaranteed right.
  - No SME exemption was found for providers in Art. 31, which only exempts custom-built and non-production services. [V]
  - Enforcement is by national authorities. For Italy the likely authority is AGCOM/AgID; this was not verified. [I]

### P2B Regulation (EU) 2019/1150, Art. 9
- Online intermediation services (the Treatwell, Fresha and Booksy marketplaces) must describe in their T&C the business user's technical and contractual access, or absence of access, to personal and other data. [V] https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A32019R1150
- Use it to ask formally what data access exists. [I]

### ToS on automation

| Platform | Clause | Tag |
|---|---|---|
| Treatwell | §7.1.11(i) no API sublicensing; (vi) no reverse engineering of any API/software; no interfering with servers | [V] |
| Fresha | Partner Terms: no reverse engineering or access to build a competing product, no framing/mirroring. Terms of Use: no scraping | [V] |
| Booksy | ToS text not retrieved (help center 403) | [I] |

- In all cases, credential-sharing automation of partner back-offices carries a suspension risk. [I]

---

## 9. Recommended roadmap for the CRM
1. **Per-operator secret iCal feed (already built), plus onboarding docs** for Treatwell "Calendario esterno" and Fresha "Other calendar → Import". This delivers availability push immediately.
2. **Google Calendar connector in Frappe:**
   - OAuth per salon, one calendar per operator.
   - Watch channels for change notifications.
   - Read Fresha-exported slots and write CRM appointments.
   - Match Fresha slots with notification emails.
3. **Dedicated inbound mailbox per salon**, e.g. `bookings+<salon>@crm-domain`.
   - Fresha: configure via "send to specific email addresses".
   - Treatwell/Booksy: owner-mailbox forwarding rule or an extra team member.
   - Extend the parsers to export emails (Treatwell PRO client list is emailed as Excel).
4. **Outreach (partnership requests):**
   - Booksy (Public API partner status; `import_uid` suggests two-way support)
   - Primo in Cloud (REST API)
   - WeGest (web service)
   - Phorest, via api-requests@phorest.com with the salon's account number
   - Treatwell, via account manager, citing Data Act Art. 30(2)/34
5. **Optional Fresha Snowflake reconciliation job** for salons willing to pay the add-on.
6. **Avoid scraping** partner back-offices. The Booksy public-read endpoint for availability is at best a last resort, given its ToS risk.
