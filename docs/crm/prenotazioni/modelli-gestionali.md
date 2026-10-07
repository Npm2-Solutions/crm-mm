# Vertical booking software: how services, staff and online booking are modelled

Research date: 2026-09-24. Scope: Fresha, Treatwell Connect/PRO (ex Uala), Booksy Biz, Phorest, Timely, Mindbody, Zenoti, Vagaro, Jane App, Cliniko, Doctolib Pro, MioDottore/GipoNext, AlfaDocs, TIMIFY, Planity, Shore, WeGest.

Tags: **[V]** = verified against the URL next to it (an official help centre unless noted). **[I]** = inferred, or from my prior knowledge without a source fetched in this session. Treat [I] as a hypothesis.

Caveat on sources: many help centres render client-side or block bots (Fresha KB article bodies, Zendesk 403s at Vagaro/Booksy/Doctolib/Timely, Mindbody's Salesforce site). In those cases the fact comes from the search engine's snippet of that official page. It is still tagged [V] with the page URL, but a human should re-check it before relying on the detail.

---

## 0. Cross-vendor synthesis (read this first)

### 0.1 Converged entity model
Nearly every product has the same core: **Location → Staff (per-location schedule) ↔ Service (catalog, per-location enablement) ↔ Resource (room/chair/equipment)**. The two things that differ are where the *staff×service* overrides live and what an "availability" window is attached to:

| Pattern | Who | Availability is attached to… |
|---|---|---|
| **Staff shift + service eligibility** (a slot is valid if staff is on shift ∧ can do service ∧ resource free) | Fresha, Phorest, Booksy, Vagaro, Timely, Shore, Planity, Treatwell, TIMIFY, Zenoti | staff shift / rota |
| **Shift + tag filter** (a treatment is only offered on shifts carrying a matching tag) | Jane | shift with tags |
| **Opening slots carry allowed visit reasons** ("plages d'ouverture" + "motifs") | Doctolib, MioDottore (per address), GipoNext (doctor+room+machine) | agenda block per address |
| **Class = scheduled instance with capacity**, separate from appointments | Mindbody, Cliniko (group appt type), Jane (Class/Group), Fresha (group appts) | class schedule |

**Takeaway [I]:** support *both* "any service the staff can do during the shift" (beauty default) and "this block is only for services X,Y" (clinic default, Doctolib/MioDottore/Jane tags) through one mechanism: an optional service filter on a working-hours block.

### 0.2 Staff×service override fields seen in the wild
- Price per staff: Fresha, Booksy, Vagaro, Zenoti ("price scaling"/provider pricing) [V]
- Duration per staff: Fresha, Booksy, Vagaro [V]
- Processing/gap time per staff: Vagaro [V]
- Price/duration per location: Fresha [V], Zenoti (center override) [V]
- Online bookable per staff×service: Phorest (set a service to "No" in the staff profile, so the staff member stays bookable in-house but not online) [V]
- Commission per staff/service: Zenoti adjusts commission per segment [V]. Common in Fresha/Phorest payroll [I]
- Staff levels / tiers (junior/senior/director price) [I]: Phorest and Timely have them; Booksy uses variants instead

### 0.3 Service anatomy (the richest version: Vagaro, Zenoti, Fresha)
`initial duration → processing/gap (staff freed) → finishing duration → cleanup/blocked time`. Vagaro names them *Initial Duration, Gap, Finish Duration, Cleanup Time* [V]. Zenoti names them *servicing / processing / finishing* segments and can drag segments to different providers [V]. Fresha has *Processing, Blocked, Extra servicing time* [V].

### 0.4 Online rules: where they live
- **Global (business/location)**: slot step, lead time, horizon, cancellation window, gap optimisation, multi-service splitting (Phorest, Fresha, Shore, Jane) [V]
- **Per service override**: lead time (Cliniko overrides the default per appointment type [V], Doctolib min/max per motif [V], Planity per service [V]), online visible, deposit (Booksy "only specific services" [V]), patch test (Phorest [V])
- **Per staff**: Jane has individual staff preferences (online booking start time, etc.) [V]. Otherwise mostly just "bookable online yes/no"
- **Per shift**: Jane shifts can be "Contact to Book" [V]

---

## 1. Fresha

**Entities**
- Service catalog with categories. Each service has price, duration, extra time, locations, team, resources and an online toggle [V https://www.fresha.com/help-center/knowledge-base/catalog/102404-manage-service-availability]
- **Variants** ("Create service variants") [V https://www.fresha.com/help-center/knowledge-base/catalog/create-service-variants]. Page body not readable
- **Bundles** booked *in sequence* (one after another) or *in parallel* (same time, several team members). Resource policy is "use same resources" (couples massage in one room) or "separate". Price is the sum of services, a custom fixed price, or a % discount. Bundles have their own online toggle [V https://www.fresha.com/help-center/knowledge-base/catalog/101256-create-service-bundles]
- **Resources**: rooms, equipment, tools, linked per service as "any resource of this type" or specific ones, auto-reserved. Online booking is blocked when no resource is free [V 102404 above; https://www.fresha.com/help-center/knowledge-base/calendar/19-create-and-manage-resources]. "Bookable Resources" can be booked without a team member [V https://www.fresha.com/blog/fresha-bookable-resources-feature]
- Group appointments: several clients, one checkout [V https://www.fresha.com/help-center/knowledge-base/calendar/27-create-and-manage-group-appointments]

**Staff×service**
- Tick services per team member, with an "All services" shortcut. New members default to all services and to shifts equal to location opening hours [V search snippet of 102404 / team KB]
- **Advanced pricing & duration**: per location and per team member, set duration and price type (Fixed / From / Free) [V https://www.fresha.com/help-center/knowledge-base/catalog/76-set-advanced-pricing-and-durations-]
- Extra time: Processing (others can be booked meanwhile), Blocked (cleanup/prep), Extra servicing [V https://www.fresha.com/help-center/knowledge-base/catalog/578-add-extra-time-to-services-and-appointments-1]

**Availability**
- Location opening hours, plus scheduled shifts per team member, plus time off and blocked time [V https://www.fresha.com/help-center/knowledge-base/calendar/252-schedule-and-update-team-shifts]
- A service is bookable only if it is "delivered at the location ∧ assigned team member available ∧ required resources available" [V 102404]
- Service time windows ("specific times, such as special promotions") [V 102404]

**Online rules** (Settings → Scheduling → Online bookings / Schedule optimization)
- *Time slot interval* (e.g. 30 min) **or** *Eliminate calendar gaps* mode, which offers only slots adjacent to shift start/end, other appointments, breaks and blocked time [V https://www.fresha.com/help-center/knowledge-base/calendar/496-optimize-online-schedule-availability]
- *New appointment lead time*: none, immediately … 2 weeks [V same]
- Appointment reassignment lead time ("dynamic reassignment") [V https://www.fresha.com/help-center/knowledge-base/calendar/101735-set-up-dynamic-reassignment-for-appointments]
- **"Any professional"** assigns to an eligible member (bookable online ∧ assigned to the service ∧ free ∧ working at the location). Ties go to the member with *the most free time that day* [V https://www.fresha.com/help-center/knowledge-base/calendar/101218-manage-online-bookings-settings]
- Payment policies: deposits, card on file with no-show/late-cancel fees, per-appointment customisation [V https://www.fresha.com/help-center/knowledge-base/payments/615-set-up-payment-policies ; …/617-charge-no-show-and-cancellation-fees]
- Multiple services in one booking [V https://www.fresha.com/help-center/knowledge-base/online-profile/101646-learn-how-clients-book-appointments-online]

**Public UX**
- Marketplace profile plus a **Link builder** for links to a specific service, location or team member. Direct links carry no marketplace new-client fee [V https://support.fresha.com/hc/en-us/articles/360017064359]
- Reserve with Google [V https://www.fresha.com/help-center/knowledge-base/online-profile/179-get-booked-on-reserve-with-google]

**Admin/complaints**
- Bulk edit of availability across services [V 102404]
- Complaints: marketplace new-client commission and unexpected fees ("need a fixed price without surprises") [V Capterra https://www.capterra.com/p/142138/Shedul-com/reviews/?page=7 snippet]

## 2. Treatwell Connect / PRO (ex Uala, strong in Italy)
- Price list ("listino") with services that can require a **mandatory patch test** [V https://www.treatwell.it/partners/risorse/blog/funzionalita-treatwell-connect-che-non-conosci/]
- Per service: execution time, assigned to collaborators [V search snippet of Treatwell partner pages]
- Public staff profiles (photo, specialisations, portfolio). Clients pick the professional on the marketplace [V same]
- Waitlist with automatic notifications, customisable deposits (all services, some services, specific clients), customisable cancellation conditions [V same]
- "Prenota con Google", a "Prenota subito" button for site and social, multi-location agenda [V same]
- Since the DMA change (April 2024), Google sends users to the Treatwell page instead of completing in-SERP [V https://help.treatwell.pro/en/articles/6076097-how-does-reserve-with-google-work ; https://partnercare.treatwell.com/s/article/Reserve-with-Google?language=en_GB]
- [I] Uala-heritage PRO has cabins/"postazioni" and per-operator service lists. Not verified this session

## 3. Booksy Biz
- **Service Variants**: one service with several duration/price options, each variant assignable to qualified staff (Business Settings → Services Setup → Duration/Pricing → Add Service Variant) [V https://support.booksy.com/hc/en-us/articles/16538342476946 ; https://biz.booksy.com/en-us/blog/service-variants-take-control-of-your-service-list-and-price-menu]
- Per-staff price/duration [V https://support.booksy.com/hc/en-us/articles/16535124505362]
- Processing time frees the calendar mid-service. Buffer time between appointments [V Salon Today https://www.salontoday.com/1084464/…]
- **No-Show Protection**: Deposits (partial/full, deducted at checkout) *or* Cancellation Fees (card captured and charged on late cancel/no-show). Can apply to specific services only. The cancellation window lives in Booking Rules [V https://support.booksy.com/hc/en-us/articles/16487371034130 ; …/16487431553810]
- Reserve with Google [V https://support.booksy.com/hc/en-us/articles/19034280045458]

## 4. Phorest
- Service field **"Available Online: Yes/No"** [V https://support.phorest.com/hc/en-us/articles/360016262040]
- **Per staff×service online flag**: set the service to "No" in the staff profile, so the member stays bookable in-house but not online [V https://support.phorest.com/hc/en-us/articles/360017899999]. A whole staff member can be hidden from online booking
- **Add-ons**: services linked to a primary service ("Linked Addons" tab), shown online after the primary is picked, can be 0 minutes (shown as a banner). They can't be combined with packages, courses, memberships or group bookings. Guidance: about 5 add-ons from at most 2 categories [V https://support.phorest.com/hc/en-us/articles/34677418988050]
- Packages, multi-person packages for groups, Series/Courses [V https://support.phorest.com/hc/en-us/articles/360017402460 ; …/360017458039]
- **Online booking settings** (Manager → Settings → Online → Booking Rules) [V https://support.phorest.com/hc/en-us/articles/360016262000]:
  - Booking Slots (display interval)
  - Smart Booking (limits the slots shown, to reduce gaps)
  - Minimum Gap Time (no bookings that leave gaps smaller than X)
  - Cancellation Period (no online cancel/reschedule within X)
  - Patch Test Period
  - Short Notice Period (lead time)
  - Limit Availability in the Future (horizon)
  - **Multi-Service Rules**: split across staff or one provider. "Will only split for max utilisation" [V search snippet]
  - Online discount (first appointment or all), double loyalty points, notes box, **abandoned cart emails**
- Rota: rostered hours, breaks. **Online bookings cannot land on a break, in-house bookings can** [V https://support.phorest.com/hc/en-us/articles/7516615190290 snippet ; https://support.phorest.com/hc/en-us/articles/360016298819]
- Recovery time between online bookings per staff [V https://support.phorest.com/hc/en-us/articles/360016261980]

## 5. Timely
- Resources: rooms/equipment assigned to services, auto-assigned online. A slot with no resource free is not shown [V https://help.gettimely.com/hc/en-gb/articles/360062550413 ; https://help.gettimely.com/article/438-booking-a-resource]
- Services assigned to locations. A service's availability follows the hours and locations of the staff who can perform it [V https://help.gettimely.com/hc/en-gb/articles/360062549093]
- Fixed/specific booking times [V https://help.gettimely.com/hc/en-gb/articles/360062497673-How-to-set-fixed-or-specific-booking-times] (body 403)
- Booking time policies: min notice and max horizon (e.g. 1 h / 3 weeks) [V https://help.gettimely.com/hc/en-gb/articles/33525113423639]
- Deposits as a % of the total (TimelyPay). Custom questions asked during booking [V https://help.gettimely.com/hc/en-gb/articles/27481285992087]
- **Multi-staff appointments**: a multi-service booking can spread across staff when no single person has room, with a configurable *max wait between services*. Requires turning off "Minimise gaps" [V https://help.gettimely.com/hc/en-gb/articles/360062491693]
- **Waitlist**: clients add themselves online (higher tiers) [V https://help.gettimely.com/hc/en-gb/articles/360060665974]

## 6. Mindbody (fitness/wellness)
- Two worlds: **Classes/Courses (enrollments)** vs **Appointments**. Service categories feed *pricing options* (class pricing options pay for any class in a category, course options only for specific events) [V https://support.mindbodyonline.com/s/article/Classes-vs-Enrollments-What-s-the-Difference?language=en_US ; https://support.mindbodyonline.com/s/article/219555867-Classes-Adding-pricing?language=en_US]
- Capacity: total vs **online (web) capacity**, auto-promoting waitlist [V https://www.mindbodyonline.com/business/scheduling]
- Appointment availability per staff ("edit appointment availability") [V https://support.mindbodyonline.com/s/article/203259013]
- **Bold Times**: restrict client-booked appointments to marked start times (e.g. :00/:30) [V https://support.mindbodyonline.com/s/article/205735258]. Scheduling increments / active business hours per service [V https://support.mindbodyonline.com/s/article/203253593]
- Restrict appointment types to members, suspend a client's online booking privileges [V https://support.mindbodyonline.com/s/article/203758926]
- "View client sign-up restrictions" diagnostic tool explains why a class isn't bookable (membership, prerequisites, capacity, client view) [V https://support.mindbodyonline.com/s/article/Why-is-the-sign-up-button-not-available-for-my-class?language=en_US]. **Worth stealing.**
- Complaints: expensive, complex pricing, frequent price increases [V https://koalendar.com/blog/mindbody-pricing-costs (3rd party)]

## 7. Zenoti (enterprise spa/salon/medspa)
- Organisation-level catalog with **center-level overrides** ("Allow Center Override") [V https://help.zenoti.com/en/configuration/services-configurations/manage-services.html]
- **Service segments**: servicing/processing/finishing. Segments can be dragged to different providers, with commission and utilisation adjusted per segment [V https://help.zenoti.com/en/articles/917660-what-are-service-segments]
- Rooms (with a room-based **price factor %**) and equipment (with quantity = concurrent use) [V https://help.zenoti.com/en/configuration/business-details-configurations/create-rooms.html ; …/configure-equipment.html]
- Add-ons, prerequisites, parallel services, guest-specific durations [V https://help.zenoti.com/en/master-data/services/edit-services.html ; https://help.zenoti.com/en/configuration/guests-configurations/enable-guest-specific-service-duration-for-your-business.html]
- Webstore therapist settings: *Mandate Therapist Selection* (otherwise auto-assign), *gender-specific therapist*, therapist photo/description, online booking start/end hours [V https://help.zenoti.com/en/configuration/webstore-configurations/configure-therapist-settings.html]
- "Enforce Room Selection for Every Service" [V https://help.zenoti.com/en/configuration/webstore-configurations/configure-appointment-booking.html]

## 8. Vagaro
- Service → per-employee toggle plus **price per provider**, **duration and gap per provider** [V https://support.vagaro.com/hc/en-us/articles/360008884054 ; …/360034831093]
- Service anatomy: Initial Duration / Gap (processing) / Finish Duration / Cleanup Time [V https://support.vagaro.com/hc/en-us/articles/360010299394]
- "Show Online" and "Show Service Price Online" flags [V Edit a Service]
- Online Appointment Rules: lead time (min/h/days), waitlist, prepayment refund policy, cancellation/no-show/reschedule policies, **accept/deny online requests (approval mode)** [V https://support.vagaro.com/hc/en-us/articles/204347060]
- Customers can book **up to 6 services, same day, back-to-back** [V https://support.vagaro.com/hc/en-us/articles/360007887174]
- Service bundles [V https://support.vagaro.com/hc/en-us/articles/360038357414]
- Complaints: some tasks take many steps, and users want payment plans for bundles [V Capterra snippet]

## 9. Jane App (physio, chiro, psych: the closest analogue for Italian allied health)
- **Disciplines** (e.g. Physio) group **Treatments**. A treatment is *shared* (any staff of the discipline, listed under the discipline online) or *staff-specific* (only visible after choosing that practitioner) [V https://jane.app/guide/setting-up-treatments ; https://jane.app/guide/turning-on-online-booking-and-setting-up-different-permissions]
- Treatment fields: type (One-on-One / Class / Group + capacity), In-person/Online, length, **Scheduled Length** (can differ for staggering or post-treatment break), locations, price, income category, colour, **Description (before booking)**, **Booking Information (after booking)**, call-to-book, show price [V setting-up-treatments]
- **Shifts** drive availability both internally and online. **Tags** on shifts and treatments: a treatment is offered only on shifts with a matching tag, and tags are also used to model rooms/equipment [V https://jane.app/guide/online-booking-choosing-what-is-offered-online-locations-staff-shifts-treatments-etc-and-individual-staff-preferences ; https://jane.app/guide/setting-up-shifts]
- "Contact to Book" at shift or treatment level (shown, not self-bookable) [V same]
- Clinic-wide online settings (explicitly **not per practitioner**): same-day toggle, "do not allow booking within X", "show openings within the unallowed period as *Contact to Book*", late-cancellation period, allow self-cancel, **upcoming appointments limit**, related (family) profiles, post-booking info prompt, time zone, browse by treatment/staff/month, practitioner order (alphabetical / random / **most available**), Google sign-in [V https://jane.app/guide/turning-on-online-booking-and-setting-up-different-permissions]
- Individual staff preferences: online booking start time (sequential vs on the hour/half hour) and **max appointments shown per day** ("show 3 spots to look busier") [V https://jane.app/guide/online-booking-individual-staff-preference ; snippet]
- Praise: best patient self-booking UX. Cons: per-practitioner pricing on higher tiers [V https://schedulingkit.com/compare/jane-app-vs-cliniko (3rd party)]

## 10. Cliniko
- **Appointment type** fields: name, description, category, individual/group (**max patients**), colour, telehealth, **practitioners who offer it**, **businesses (locations)**, reminders/confirmations, **online lead time override**, show in online bookings, preload billable items/products, default treatment note template, online ordering [V https://help.cliniko.com/en/articles/1023911-set-up-appointment-types]
- Practitioner "display in online bookings" flag [V https://help.cliniko.com/en/articles/1023919]
- **Default appointment type sets the slot step**: e.g. 60-minute default means start times 1 h apart [V https://help.cliniko.com/en/articles/8529147]. Separate "time between appointments in online bookings" setting [V https://help.cliniko.com/en/articles/2701586]
- Availability per practitioner **per business**: regular weekly, recurring breaks, one-off block/open [V https://help.cliniko.com/en/articles/4681646]
- Online: slots grouped morning/afternoon/evening, default lead time overridable per type, **max appointments per day** and **per-patient daily limit**, min cancel notice, show/hide prices and durations, Stripe prepayment, automatic pre-appointment forms, embeddable [V https://help.cliniko.com/en/articles/1150377 ; https://help.cliniko.com/en/articles/1023955]
- **Custom booking URLs filtered to specific appointment types** [V https://help.cliniko.com/en/articles/3360316]
- Group appointments: recurring classes, bookable online while spots remain [V https://help.cliniko.com/en/articles/9668605]

## 11. Doctolib Pro
- **Motifs de consultation** (visit reasons: duration, online bookable) are attached to **plages d'ouverture** (opening blocks). Patients can book, move and cancel online only within blocks carrying that motif [V https://doctolib.zendesk.com/hc/fr/articles/23521218336276 ; https://doctolib.zendesk.com/hc/fr/sections/360012490791]
- **Min and max online delay per motif** (e.g. bookable from 1 day before until 1 h before) [V https://doctolib.zendesk.com/hc/fr/articles/360054003732]
- **Block new patients** per motif and agenda through a "blocking question" (are you already a patient?) [V https://doctolib.zendesk.com/hc/fr/articles/360053912052]
- Configurable online booking journey (specialty → motif categories → questions), video motifs [V https://doctolib.zendesk.com/hc/fr/articles/23531240284308]
- "Réservable sur demande" (request-based) for health establishments [V https://doctolib.zendesk.com/hc/fr/articles/11091243449876]
- [I] Motifs carry patient instructions shown after booking. Motif categories drive the patient-facing menu

## 12. MioDottore (Docplanner) / GipoNext / TuoTempo
- Agendas organised **per address (indirizzo)**: Settings → Agende → choose address → weekday working hours (several intervals), **exceptions**, **"Attiva agenda"** in the online booking tab, and **booking margins** visible to patients (next available visit, last slots) [V https://help.docplanner.com/12/doc/come-gestire-le-agende-nel-proprio-account-miodottore]
- Different hours for online (video) vs in-person visits [V snippet of same help centre]
- [I] Each address has its own list of *servizi* (prestazioni) with price ("a partire da") and duration. A working-hours block can be limited to selected services. Slot step follows the service duration. Not verified this session
- GipoNext: one agenda over **doctors, rooms (ambulatori) and machines (macchinari)**. The algorithm suggests combinations for cyclic bookings (e.g. physio cycles). Online booking comes via MioDottore Premium / TuoTempo [V https://gipo.it/prodotto/funzionalita-piu-amate/agenda-e-prenotazioni]
- Complaints (patient-side Trustpilot): slots shown as available but not really, price mismatches. Professionals report hard contract exits [V https://it.trustpilot.com/review/www.miodottore.it (snippet)]. **Lesson: availability must be computed live from the real agenda, not a copy.**

## 13. AlfaDocs (Italian dental/medical)
- Multi-operator, multi-chair ("poltrone") agenda in parallel views [V https://www.alfadocs.com/organizzazione/agenda-avanzata]
- **Chairs linked to visit reasons**: e.g. a hygiene chair shows up online only for hygiene requests. Also used for physio/psych rooms [V snippet of https://www.alfadocs.com/nuove-funzionalit%C3%A0]
- Patient flow: doctor → service → slot [V https://www.alfadocs.com/organizzazione/prenotazione-online]
- Google Calendar/iCal sync [V agenda-avanzata]

## 14. TIMIFY
- Services with categories, durations and required resources (auto-reserved). Resources (staff, rooms, equipment) have **working hours distinct from online-bookable hours** [V https://www.timify.com/en-us/features/resource-service-management/]
- **Service allocation groups**: % of capacity reserved for given services [V https://www.timify.com/en/support/5562430]
- **Daily booking limit per service** [V https://www.timify.com/en/support/8795705]
- Availability slot display mode [V https://www.timify.com/en/support/12689190]

## 15. Planity (FR beauty)
- Per-service online conditions: slot frequency and lead time per service [V snippet https://info.planity.com/solution/agenda-en-ligne]
- **Services needing several collaborators or resources at once** ("Plusieurs collaborateurs en même temps", number required plus resources) [V https://support.planity.com/hc/fr/articles/28225488590226]
- **Per-collaborator service limit** [V https://support.planity.com/hc/fr/articles/33884833656978]
- Pauses and technical breaks inside services [V snippet]

## 16. Shore (DE/AT)
- Booking hours at three levels: **general (business/branch)**, **individual per employee**, or a **shift plan**. If the shift plan is on, it overrides the rest [V https://help.shore.com/en/managing-booking-hours-and-absences]
- Absences: company closed days and per-employee absences [V same]
- Booking limits: "as few as … in advance" and "at most … in advance" [V https://help.shore.com/en/einstellungen-deines-kalenders]
- **Employee+room combination**: rooms are not visible to customers. Each room lists the services that need it. Online slots require both to be free [V https://help.shore.com/en/how-do-i-set-the-employee-room-combination-correctly]
- Services are ticked in the employee profile [V https://help.shore.com/en/my-online-booking-doesnt-work.-whats-wrong]. There is also a troubleshooting article, "My online booking doesn't work", which confirms that misconfiguration is common

## 17. WeGest (IT hair/beauty)
- Agenda showing service durations, **operator shifts and cabin availability** [V https://www.wegest.it/agenda-software-digitale/]
- Online booking via a **branded custom app** and the Prenotado portal [V https://www.wegest.it/app-di-prenotazione-personalizzata/]
- [I] Tempi di posa handled as service phases. Not verified

---

## 2. Staff×service matrix: summary table

| Product | Assign | Price/staff | Dur/staff | Processing | Online flag per staff×svc | Variants |
|---|---|---|---|---|---|---|
| Fresha | tick / All | ✔ (+loc) | ✔ (+loc) | svc-level extra time | via "bookable online" staff flag [I] | ✔ |
| Booksy | ✔ | ✔ | ✔ | ✔ | [I] | ✔ (variants→staff) |
| Phorest | staff profile | tiers [I] | [I] | ✔ | **✔ explicit** | [I] |
| Vagaro | toggle per employee | ✔ | ✔ + gap | initial/gap/finish/cleanup | [I] | bundles |
| Zenoti | job category/provider | ✔ scaling | guest-specific | segments | ✔ [I] | ✔ |
| Jane | shared vs staff-specific | per-staff treatment | per-staff treatment | scheduled length | shift/treatment call-to-book | treatments |
| Cliniko | appt type → practitioners | billable items | – | – | practitioner-level | – |
| Doctolib/MioDottore | motif per agenda | per address | per motif | – | motif online flag | – |

(Jane's "per-staff treatment" = a separate staff-specific treatment rather than an override. That duplicates records.)

## 3. Availability layering (most complete synthesis)
1. Location opening hours / closed days (Shore, Fresha)
2. Staff shifts/rota per location (Fresha, Phorest, Shore shift plan, Cliniko per business)
3. Breaks and time off (in-house can override breaks, online cannot: Phorest)
4. Block filters: shift tags (Jane), motifs on plages (Doctolib), online vs in-person hours (MioDottore), separate online-bookable hours (TIMIFY), online start/end hours (Zenoti)
5. Service time windows (Fresha), daily limits per service (TIMIFY), capacity allocation groups (TIMIFY)
6. Resources free (Fresha, Timely, Shore, Zenoti, AlfaDocs chairs, GipoNext rooms/machines)
7. Online rules: lead/horizon/step/gap optimisation/max per day/per client

## 4. Public UX patterns
- Service-first menu with an "any professional" option (Fresha: most-free-time assignment. Zenoti: optional mandate. Jane: order by *most available*)
- Staff-first browsing option (Jane, Cliniko, AlfaDocs doctor → service → slot)
- **One page per business, deep links carry filters** (Fresha Link builder: service/location/member. Cliniko custom URL filtered to appointment types). This is how they avoid "one link per calendar"
- Embeddable widget (Cliniko, Fresha, Treatwell) plus Reserve with Google (Fresha, Booksy, Treatwell). In the EU the post-DMA flow goes through a landing page
- Slots grouped morning/afternoon/evening (Cliniko). Artificial scarcity: show only N per day (Jane)

## 5. Admin UX
- Fresha: bulk edit of service availability, "All services" checkbox in the staff profile [V]
- Phorest: dedicated Online Booking Settings page grouping every rule [V]. Services tab inside the staff profile with a per-row online Yes/No [V]
- Mindbody: **sign-up restriction diagnostic** [V]. Shore/Phorest/Cliniko all have "why is nothing showing online?" help articles [V], which shows that explainability of empty availability is a universal pain
- [I] No vendor verified here offers a true services × staff grid editor. Assignment happens from one side (service or staff) with bulk ticks. A matrix would be a differentiator
