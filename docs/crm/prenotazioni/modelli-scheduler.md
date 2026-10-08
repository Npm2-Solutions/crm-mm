# How general-purpose schedulers model bookings: research for a unified CRM booking model

Date: 2026-09-24. Audience: design of ONE unified booking system for an Italian CRM (clinics, salons, studios, consultants).
Legend: **[V]** = verified on the cited official page / review source (URL given). **[I]** = inference / prior knowledge not re-verified in this session.
Note: several vendor help centers (Acuity help.acuityscheduling.com, GHL ideas board, MS TechCommunity) returned 403/login during fetch; for those, facts come from search-result snippets of the official page (still tagged [V] with URL when the snippet quoted the page) or are marked [I].

---

## 0. Two families of models (key framing)

Across all 9 products there are two families, and most pain comes from mixing them:

| Family | "Thing you share a link to" | Rules live on | Examples |
|---|---|---|---|
| **A. Meeting / event-type centric** ("calendar" or "event type" = a bookable link) | the event type / calendar | the event type (duration, buffers, notice, limits, questions) + a user schedule | Calendly, Cal.com, GHL legacy "Meetings" calendars, MS Bookings personal |
| **B. Service-catalog centric** (services × staff × resources × locations) | a booking *page/menu* (business / location / staff), deep-linkable to a service or staff | global settings → service → staff×service override; availability from staff schedules ∩ resource ∩ location | Acuity, Zoho Bookings, MS Bookings (shared), SimplyBook.me, Setmore, Square, **GHL Services (v2)** |

GoHighLevel itself migrated from A (one calendar per appointment type, "create separate calendars" for different settings) to B (Services v2, with staff, resources, locations, variations, add-ons, global settings) — a strong signal that family A doesn't scale for salons/clinics. [V] https://ideas.gohighlevel.com/changelog/services-v2-is-now-live-for-everyone

---

## 1. GoHighLevel (HighLevel)

### 1.1 Entities
- **Legacy "Meetings" calendars** (each calendar = one bookable link with its own settings). Types: Personal/Standard (one user), Round Robin (pool, one assigned), Collective (all users must be free), Class Booking (one host, many seats), Service calendar (multi-service businesses), Event calendar (no host/user; availability at calendar level). [V] https://help.gohighlevel.com/support/solutions/articles/155000003554-creating-class-booking-calendars , https://help.gohighlevel.com/support/solutions/articles/155000007517-how-to-create-event-calendars , https://help.gohighlevel.com/support/solutions/articles/155000000578-collective-bookings-calendar-overview
- **"Unassigned" calendar**: vocabulary for a calendar that routes to a pool (round robin etc.) vs an "Assigned (User) calendar" routed to one user; has its own custom URL slug. [V] https://help.gohighlevel.com/support/solutions/articles/155000003549-custom-url-for-unassigned-calendars
- **Calendar Groups**: a container of multiple calendars under one link ("choose from multiple service providers / services"). Mandatory for a Service calendar to appear in a Service Menu. [V] https://help.gohighlevel.com/support/solutions/articles/48001161037-highlevel-group-calendar-overview-and-setup-guide
- **Service Menu** (legacy): one branded page listing multiple Service calendars; each service = its own dedicated Service Calendar; optional staff selection; can book multiple services unless "Limit to One Service". Stripe only, no coupons. [V] https://help.gohighlevel.com/support/solutions/articles/155000001161-how-to-create-service-menus-for-calendars
- **Services (v2)** (new, GA): Services, Categories, Staff, Resources (rooms/chairs/stations with capacity, per location), Add-ons, Variations, Locations, Global Settings, dedicated calendar view and reporting. Enabling it copies existing service calendars into Services; legacy "Meetings" calendars and Services can coexist. [V] https://help.gohighlevel.com/support/solutions/folders/155000000828 , https://ideas.gohighlevel.com/changelog/services-v2-is-now-live-for-everyone
- **Schedules** (centralized availability): user-owned reusable availability templates (weekly hours + date-specific overrides + timezone). A user can have many ("Consultations", "Demos", "On-site"); a calendar references one schedule per user; a calendar can instead hold a **Custom Schedule** ("customize schedule for this calendar only") managed only inside that calendar. Introduced because "managing availability calendar-by-calendar was time-consuming and error-prone". [V] https://help.gohighlevel.com/support/solutions/articles/155000006215-schedules-centralized-availability-management
- **Thing you share**: legacy = calendar link / group link / service menu slug; v2 = service booking page + per-service booking link. [V] (links above)

### 1.2 Where rules live
Legacy calendars — essentially everything at **calendar** level: slot duration, slot interval, pre/post buffer, appointments per slot, appointments per day (per calendar only, *does not limit across calendars*), minimum scheduling notice, date range (with "count available days only"), office hours. "To implement different settings for various appointment types, create separate calendars." [V] https://help.gohighlevel.com/support/solutions/articles/48001155718-adjusting-availability-settings-for-individual-calendars , https://ideas.gohighlevel.com/changelog/date-range-setting-can-now-count-only-the-days-you-actually-work
- Availability: calendar-level (event calendars) or per user via Schedules / per-calendar custom schedule. Date-specific hours override weekly hours. [V] https://help.gohighlevel.com/support/solutions/articles/155000001716-calendar-availability-weekly-working-hours-date-specific-hours
Services v2:
- **Global settings** (all services): slot interval, min notice, booking window (+count available days only), browse by category vs all, staff selection & auto-assign rules, payment mode (online/in person/card on file), coupons, auto-confirm, cancel/reschedule expiry windows, notifications (email/SMS/WhatsApp). [V] https://help.gohighlevel.com/support/solutions/articles/155000003546-global-settings-in-services
- **Service**: duration, price, variations (own duration & price), processing time (initial/processing/final phases where staff is free during processing), buffers, add-ons, resources, deposit (fixed/%), private flag, category, own booking link. [V] https://help.gohighlevel.com/support/solutions/articles/155000005330-how-to-create-services-
- **Staff**: default availability, weekly hours (multiple ranges/day), date-specific hours (bulk), location per time block, assigned services, **service-specific price per staff**, appointment limits per day/week/month per staff. [V] https://help.gohighlevel.com/support/solutions/articles/155000005331-configuring-staff-in-services
- **Resource**: quantity = separate records (Room 1, Room 2), capacity per unit, per location; service can list several resources and the system picks any free one; slot hidden if no resource. [V] https://help.gohighlevel.com/support/solutions/articles/155000003505-resources-in-services
- Intake questions: legacy calendars attach a custom form [V snippet] https://www.ghlscaleup.com/blog/gohighlevel-calendar-booking

### 1.3 Staff assignment
- Round robin: "optimize for availability" or "optimize for equal distribution" (monthly count, nobody more than 3 ahead). Help center: "Round Robin currently only supports availability-based or equal distribution settings" — no manual weights/priority for specific clients (older priority setting existed per member [I]). Booker can optionally pick staff. [V] https://help.gohighlevel.com/support/solutions/articles/155000001485-round-robin-calendars-setup-distribution-availability-explained , https://help.gohighlevel.com/support/solutions/articles/155000001484-appointment-distribution-logic-for-round-robin-calendars
- Collective: all members must be free. [V] (above)
- Services v2: booker chooses staff or auto-assign (global setting). [V]

### 1.4 Links
Calendar link, custom slug, group link, service menu slug, per-service link (v2), widget styles Classic vs Neo, embeds. [V] https://help.gohighlevel.com/support/solutions/articles/155000003552-calendar-widget-styles . No routing forms native to calendars (done via forms + workflows) [I].

### 1.5 UX strengths / complaints
- Strength: calendars live inside CRM + workflows (reminders, pipelines). [V] https://www.capterra.com/p/177156/HighLevel/reviews/
- "Large learning curve… clunky and hard to navigate at first"; getting any of buffers/min notice/sync/plan limits wrong loses availability or double-books. [V] https://www.capterra.com/p/177156/HighLevel/reviews/ , https://schedulingkit.com/pros-and-cons/gohighlevel-pros-and-cons
- Calendar sprawl: one calendar per appointment type because settings can't vary; duplicate calendars "quietly split bookings", round-robin needs each member's calendar connected separately. [V] https://www.newmotionit.com/blog/automation/gohighlevel-calendar-not-working , https://help.gohighlevel.com/support/solutions/articles/48001155718-adjusting-availability-settings-for-individual-calendars
- "GoHighLevel does not allow different availability settings per appointment type for the same provider" (before Schedules/custom schedules). [V snippet] https://hlgrowthpartner.com/post/gohighlevel-calendars-booking-setup-2026
- Feature board: "View all calendars at once", side-by-side staff view (salons from Vagaro call it "a nightmare"), multi-service booking creates N separate appointments (duplicate reminders), cannot pick separate date/time per service in one booking, only one linked Google calendar per GHL calendar, recurring appointments, packages (88 votes), multiple appointment booking (97), glance-view of availability ("without simulating a booking"). [V] https://ideas.gohighlevel.com/scheduling-calendar , https://ideas.gohighlevel.com/scheduling-calendar/p/view-all-calendars-at-once , https://ideas.gohighlevel.com/scheduling-calendar/p/service-calendar-multiple-service-should-be-one-appointment-for-same-customer , https://ideas.gohighlevel.com/scheduling-calendar/p/add-multiple-linked-calendars
- Setup time: 30–45 min per single-user calendar, 60–90 for a round-robin team calendar (third-party guide). [V] https://www.newmotionit.com/blog/automation/gohighlevel-calendar-not-working

### 1.6 Admin overview
- **Troubleshoot Calendar** tool: hover a slot to see why unavailable (USER / CONFLICT / BOOKED / BUFFER), works on group/team calendars and names the user causing failure. [V] https://help.gohighlevel.com/support/solutions/articles/155000003358-troubleshooting-tool-for-calendar
- Calendar view with filters by user/calendar; Services v2 calendar view (staff columns). [V] https://help.gohighlevel.com/support/solutions/articles/155000006757-calendar-view-enhancements , https://help.gohighlevel.com/support/solutions/articles/155000006096-calendar-view-services
- No staff×service matrix screen; staff edit is tabbed: Basic / Assign services / Weekly hours / Date-specific. [V] https://help.gohighlevel.com/support/solutions/articles/155000005331-configuring-staff-in-services

---

## 2. Calendly

### 2.1 Entities
User → Availability **schedules** (many per user) → **Event types** (one-on-one, group, collective, round robin; plus meeting polls, one-off meetings). Event types can be personal, **shared** (ad-hoc, no landing page) or **team** event types (on team landing page). **Managed events**: admin templates assigned to users with per-section lock. **Routing forms** in front. The link = event type URL (or user/team landing page). [V] https://calendly.com/help/multi-person-scheduling-options-for-your-organization , https://help.calendly.com/hc/en-us/articles/4914418007831-Event-types-overview , https://calendly.com/help/managed-events-overview

### 2.2 Where rules live
- **Event type**: duration (multiple durations option), date range (rolling days / fixed range / indefinite), minimum notice, start-time increments, buffers before/after, meeting limits per day/week/month, secret/visibility, questions, location. [V] https://calendly.com/help/how-to-fine-tune-your-availability-settings , https://calendly.com/help/how-to-set-up-multiple-durations-for-an-event-type
- **Schedule** (user-owned): weekly hours + date-specific hours; assigned to event types via "Active on"; or event can use custom hours. Limitation: date overrides don't propagate across schedules → edit each. [V] https://calendly.com/help/how-to-set-your-availability , https://community.calendly.com/how-do-i-40/date-override-for-multiple-schedules-341
- **Account**: connected calendars (max 6 per user), timezone. [V] https://calendly.com/help/availability-overview , https://www.g2.com/products/calendly/reviews?qs=pros-and-cons
- Price: via Stripe/PayPal per event type [I]. No per-host price. No per-host limits in round robin ("Maximum number of bookings per host" is a community request). [V] https://community.calendly.com/how-do-i-40/maximum-number-of-bookings-per-host-round-robin-760

### 2.3 Staff assignment
Round robin: "Maximize for availability" (priority stars, then least-recent, then random) or "Optimize for equal distribution" (hide someone >3 ahead). No % weights. Rescheduled meeting can keep host or re-distribute. Collective = all free. Group = 1 host N invitees. [V] https://calendly.com/help/round-robin-distribution-overview

### 2.4 Links
User page, team landing page, event link, secret events, single-use links, URL pre-fill, embeds (inline/popup) [I for single-use/pre-fill details]. Routing forms: questions + logic → event type / user / external URL; Salesforce/HubSpot owner lookup; fallback; prefill via URL; CSV of responses. [V] https://calendly.com/help/routing-forms , https://calendly.com/help/how-to-manage-routing-forms

### 2.5 UX
Strength: simplest booker UX, polish. Complaints: per-seat cost, rigid automations for large teams, 6-calendar cap, poor admin visibility across members (each user must be a paid seat). [V] https://www.g2.com/products/calendly/reviews?qs=pros-and-cons , https://community.calendly.com/how-do-i-40/managing-multi-user-availability-1400 . Not built for service catalogs (no staff×service price, no resources) [I].

### 2.6 Admin overview
Admin can see calendar-connection status per user; event-type permissions to edit others' availability; managed events with locks. No team availability grid [I]. [V] https://calendly.com/help/availability-overview

---

## 3. Cal.com

### 3.1 Entities
User → availability **schedules** (with date overrides; default schedule) → **Event types** (personal) / **Team event types**: Collective, Round Robin, **Managed** (template → child event type per member, locked fields). Seats on event types (group). Organizations → teams → **attributes** on members. **Routing forms**. Link = event-type URL (user or team slug), private links, embeds. [V] https://cal.com/help/event-types/managed-events , https://cal.com/blog/cal-com-s-team-appointment-types-exploring-collective-round-robin-and-managed-eve

### 3.2 Where rules live
- **Event type** tabs: Setup (duration, *booker-selectable durations*, multiple locations), Availability (choose schedule), Limits (before/after buffers, min notice, slot interval, **booking frequency** per day/week/month/year, **total booking duration** limit, **limit future bookings** (rolling calendar/business days or date range), **offset start times**), Advanced (booking questions, requires confirmation, hide notes, private URL, seats, lock timezone), Recurring, Apps (Stripe, no-show fee), Workflows, Webhooks. [V] https://cal.com/blog/a-guide-to-cal-com-s-event-settings-and-features , https://cal.com/docs/core-features/event-types/limit-future-bookings
- **Restriction schedule** on event type: a filter layer that only *hides* slots outside a window (never adds availability); option "use booker timezone". [V] https://cal.com/blog/restriction-schedules-scheduling-app
- **User-level booking limits**: cap across all personal+team events; most restrictive wins (event 10/day, user 5/day → 5). Orgs only. [V] https://cal.com/help/event-types/user-booking-limits
- Team: **team availability** tab, admins can edit team schedules. [V] https://cal.com/help/availabilities/team-availability
- Per-host price/duration: not supported (price is per event type) [I].

### 3.3 Staff assignment
Round robin with **priority** (High/Med/Low…), **weights** (default 100%, ratio maintained on confirmed bookings, new hosts get adjusted weights), fallback least-recently-booked then random; **fixed hosts + RR hosts** in one event; **round-robin groups** (one host from each pool per booking = "one per role"); common team schedule or individual host calendars; reassignment without cancellation; attendee can pick different host on reschedule. Collective = all hosts. [V] https://cal.com/help/event-types/round-robin , https://cal.com/blog/round-robin-groups-scheduling , https://cal.com/blog/calcom-v6-8

### 3.4 Links & routing
Event URL, team URL, private (hashed) links, embed (inline/popup/floating), URL prefill of booking fields [I]. Routing forms: questions → event type / member / external URL / block; **attribute-based routing** (answer "service=X" matches member attribute, then RR among matches with attribute weights). [V] https://cal.com/help/routing/routing-with-attributes

### 3.5 UX
Strengths: most flexible model, open source, API. Complaints [I]: settings sprawl across many tabs; team setup harder than Calendly; per-seat pricing for teams. Managed events v2 no webhooks/apps. [V] https://cal.com/help/event-types/managed-events

### 3.6 Admin overview
**Availability troubleshooter** (v6.8): per-slot reasons (calendar events, OOO, limits, notice, buffers), ranks blockers by impact ("which setting change opens most availability"), month view with day drill-in. Daily digest to admins listing members with no availability on managed events. Insights (incl. OOO analytics). [V] https://cal.com/blog/calcom-v6-8 , https://cal.com/help/event-types/managed-events

---

## 4. Acuity Scheduling (Squarespace)

### 4.1 Entities
**Calendars** (a calendar = a staff member *or* a location/room; "each calendar represents a separate set of hours"; counted against plan limit, e.g. 6 on Standard) × **Appointment types** (each type picks which calendars offer it; categories) + **Classes** (group, fixed dates) + **Resources** (quantity, required by types) + **Appointment type groups** (per-calendar sub-schedules). Packages, subscriptions, gift certificates, add-ons, coupons. [V] https://acuityscheduling.com/learn/managing-availability-and-calendars , https://help.acuityscheduling.com/hc/en-us/articles/16676949567757-Use-resources-to-limit-bookings , https://pabau.com/blog/acuity-scheduling-review/
Thing you share: the scheduling page (full menu), filtered by URL params.

### 4.2 Where rules live
- **Global limits** → **calendar limits override global** → **appointment-type-group limits** (own availability + limits on the same calendar): min hours notice, max days ahead, max appointments per day/week (optionally per type), cancel/reschedule window, start time intervals. [V snippets] https://help.acuityscheduling.com/hc/en-us/articles/27141282369037-Using-global-and-calendar-scheduling-limits , https://help.acuityscheduling.com/hc/en-us/articles/16676870764813-Availability-and-scheduling-limits-by-appointment-type
- **Appointment type**: duration, price, padding before/after, intake form assignment, calendars offering it, category, private flag [I for padding detail].
- **Calendar**: regular weekly hours or custom daily hours, per calendar. [V] https://acuityscheduling.com/learn/managing-availability-and-calendars
- Per-staff price: not supported → duplicate appointment types per staff or use negative add-ons. [V snippet] https://help.acuityscheduling.com/hc/en-us/articles/16676886445837-Using-Acuity-Scheduling-add-ons

### 4.3 Assignment
Client picks a calendar or **"Any available"** (pooling is default when ≥2 calendars offer a type); can hide calendar selection. No weights. [V snippet] https://help.acuityscheduling.com/hc/en-us/articles/16676903042829-Pooling-calendar-availability-in-Acuity-Scheduling

### 4.4 Links
Direct scheduling links with params: `calendarID`, `appointmentType` (id, `category:Name`, or `appointmentType[]` multiple), prefill `firstName,lastName,email,phone`, `datetime`, `location`, `quantity`, `certificate`, `field:{id}=value` for intake fields; embed. [V] https://help.acuityscheduling.com/hc/en-us/articles/31919067234445-Parameters-for-dynamic-links , https://developers.acuityscheduling.com/docs/embedding

### 4.5 UX
Strength: clean client flow, intake forms, packages. Complaints: back-end settings "confusing once you move past basic booking… options buried"; calendar limits per plan; weaker for multi-practitioner clinics; weak staff permission groups. [V] https://pabau.com/blog/acuity-scheduling-review/ , https://www.capterra.com/p/191978/Acuity-Scheduling/reviews/

### 4.6 Admin
Availability troubleshooting article ("Fix availability issues and missing appointment times"); no matrix. [V snippet] https://help.acuityscheduling.com/hc/en-us/articles/16676931784333-Appointment-availability-troubleshooting

---

## 5. Zoho Bookings

### 5.1 Entities
Organization → **Workspaces** (group event types by team/department/location/category; own users, availability, booking page) → **Services/event types**: one-on-one, group, collective (via staff group), resource (rooms/equipment) → **Staff** assigned to services → **Schedules** (2.0: named, many per workspace, assigned to multiple event types; overrides: additional availability / unavailability). [V] https://help.zoho.com/portal/en/kb/bookings-2-0/admin-center/modules/articles/workspaces-in-bookings , https://help.zoho.com/portal/en/kb/bookings-2-0/availability/schedules/articles/schedules-bookings , https://www.zoho.com/bookings/features/meeting-types.html

### 5.2 Where rules live
- **Workspace** policies: min & max booking notice, cancel/reschedule window, scheduling interval (multiples of 5, default 15), staff selection, booking ID format, T&C, timezone preset, confirmation page. [V] https://help.zoho.com/portal/en/kb/bookings/workspace/articles/bookings-policies-and-preferences
- **Service preferences** override workspace policies — one-on-one services only (not group/resource). [V] same + https://help.zoho.com/portal/en/kb/bookings/services/features/articles/service-preferences
- **Service**: duration, buffer, price, staff list; availability = assigned staff availability (default) or custom service hours (which then makes assigned staff available in those windows); date range forever/custom. [V] https://help.zoho.com/portal/en/kb/bookings/services/features/articles/service-availability
- **Staff × service**: custom price per staff ("+Customize service price" under Staff → Assigned Services); no documented per-staff duration; staff-level policy overrides not supported. [V] https://help.zoho.com/portal/en/community/topic/tip-15-customize-service-prices-for-each-staff-member
- **Limits**: per event type per day/week/month, per customer email/domain, one active booking at a time per customer, resource hour caps, group caps, date-specific. [V] https://www.zoho.com/bookings/features/appointment-limits.html

### 5.3 Assignment
Customer selects staff, or disabled → auto-assign by availability with equal distribution (load balancing). Collective via staff groups. [V] https://www.zoho.com/bookings/features/team-scheduling.html

### 5.4 Links
Org booking page, **workspace booking page**, **service booking URL**, **staff booking URL** (lists all staff's services). [V] https://help.zoho.com/portal/en/kb/bookings/workspace/articles/bookings-workspace-booking-page-url

### 5.5 / 5.6
Strength: Zoho CRM integration, per-staff price. Weakness: overrides only for 1:1, confusing 1.0→2.0 migration [I]. Admin sees all workspaces' appointments; no matrix [I].

---

## 6. Microsoft Bookings

### 6.1 Entities
**Shared booking page** (a "business" calendar/mailbox) → **Services** (limit ~50) → **Staff** (M365 users) ; also personal booking pages. Link = booking page, deep link per service [I]. [V] https://learn.microsoft.com/en-us/microsoft-365/bookings/define-service-offerings?view=o365-worldwide

### 6.2 Where rules live
- **Booking page scheduling policy** (top level): time increments (5 min–4 h), lead time (hours, for booking and cancel), max days in advance, notify on change. "Automatically applied to all services unless modified per service." [V] https://learn.microsoft.com/en-us/microsoft-365/bookings/set-scheduling-policies?view=o365-worldwide
- **Service**: name, description, location, online meeting, duration, buffer before/after (counted in free/busy), price (or "not set"), notes, **max attendees** (1:N class), language, custom fields (per service), reminders/confirmations/follow-ups, "Default scheduling policy" toggle (off → custom per service), publish on/off. [V] https://learn.microsoft.com/en-us/microsoft-365/bookings/define-service-offerings?view=o365-worldwide
- **Service availability**: "Bookable when staff are free" / "Not bookable" / "Custom hours", plus date-range overrides. [V] https://learn.microsoft.com/en-us/microsoft-365/bookings/configure-service-availability?view=o365-worldwide
- **Staff**: business hours or custom hours, Outlook free/busy respected. **No per-staff-per-service availability** — workaround: duplicate services or separate booking pages. [V] https://learn.microsoft.com/en-us/answers/questions/5583823/bookings-setting-staff-availability-by-service-typ
- No per-staff price/duration [I].

### 6.3 Assignment
"Assign any of your selected staff" (single staff), "Multiple staff" (N:1, all must be free), "Allow customers to choose a particular staff". [V] define-service-offerings (above)

### 6.4–6.6
Links: booking page, per-service/staff deep links [I]. Complaints: availability-by-service impossible, slots missing (Q&A threads), SMS needs Teams Premium. [V] https://learn.microsoft.com/en-us/answers/questions/5843594/microsoft-bookings-not-showing-all-available-time . Admin: calendar tab with staff filter [I].

---

## 7. SimplyBook.me

### 7.1 Entities
Company → (optional) **Locations** (custom feature; group providers) → **Service providers** (staff or resource; "number of clients they can serve at a time") ↔ **Services** (checkbox mapping on provider "Services" tab) → **Categories** (custom feature). **Classes** (custom feature: service+provider on special dates). Everything optional is a toggleable **Custom Feature** (Limit bookings, Any employee selector, Multiple locations, Classes, Related resources, Packages, Memberships, Approve bookings, Cancellation policy, Waiting list, Appointment at fixed time, Provider color coding…). [V] https://help.simplybook.me/index.php/Service/Provider_relations , https://help.simplybook.me/index.php/Custom_Features , https://help.simplybook.me/index.php/Multiple_Locations_custom_feature

### 7.2 Where rules live
- Strict schedule hierarchy: **provider/service special days > company special days > provider/service regular schedule > company opening hours**; provider & service schedules must sit inside company hours ("open the time for the company first"); if both provider and service schedules exist → **intersection**. [V] https://help.simplybook.me/index.php/Opening_hours_of_the_company_vs_Working_hours_of_provider/service , https://help.simplybook.me/index.php/How_to_set_my_availability
- Provider schedule per location ("working hours of a provider related to location automatically apply"). [V snippet] https://help.simplybook.me/index.php/Categories_and_Locations
- Limit Bookings feature: global concurrent limit and per-service limit (chair/room). [V] https://help.simplybook.me/index.php/Limit_Bookings_custom_feature
- Service: duration, price, buffer, etc. Per-provider price/duration: via "Service duration per provider"/special pricing features [I — not verified].

### 7.3 Assignment
Client picks provider, or "Any provider" (shows union of times) or hide step and auto-allocate randomly. [V] https://help.simplybook.me/index.php/Any_Employee_Selector_custom_feature

### 7.4 Links
Booking site with deep links per service/provider/category/location [I]; widgets.

### 7.5 UX
"The interface is very… complicated, not intuitive"; "so many features… daunting to find what you need"; "settings divided into several interconnected tabs, so it's sometimes necessary to double-check that one change hasn't affected another area". [V] https://capterra.com/p/140086/Simplybook-me/reviews/ , https://www.capterra.com/p/140086/Simplybook-me/reviews/?page=2
### 7.6 Admin
Timeline/calendar by provider, provider colour coding. [I]/[V custom features]

---

## 8. Setmore

- Entities: Business hours → Team members (working hours within business hours, breaks, time off) → Services & Classes (assigned to team members). [V] https://support.setmore.com/en/articles/490976-your-team-availability , https://support.setmore.com/en/articles/5335526-services-classes
- Rules: booking policies (lead time, slot size, scheduling window, cancellation notice) at Settings > Booking Page — account-level [V] https://support.setmore.com/en/articles/491024-booking-lead-slot-size-advance-or-cancellation-time ; custom service availability (Pro) *inside* business hours, can't open closed days [V] https://support.setmore.com/en/articles/14724724-how-to-set-different-availability-for-each-service
- Links: business Booking Page; **per-staff booking page** `yourbusiness.setmore.com/teammember` with staff preselected; per-service/class links. [V] https://support.setmore.com/en/articles/490965-staff-booking-page-url
- Assignment: client chooses staff or "any" [I].
- Strength: very simple, free tier. Weakness: few granular rules (policies global) [I].

## 9. Square Appointments

- Entities: Business → **Locations** → Services (catalog items) with **Variations** (own price, duration, team members who can perform, online bookable, location) + modifiers (add-ons) + resources; Team members. [V] https://squareup.com/help/us/en/article/6487-create-a-service-from-the-square-appointments-app
- Rules: business/location-level settings: lead time (1 h–4 w), max advance (7–365 d), time slot increments (by duration or 10/15/20/30), auto-accept vs request, "Any available" option, multi-staff per appointment (Plus), **daily online booking cap**, multiple services per appointment, "Fake-it filter" (hide 25–50% of availability), cancellation policy/prepayment; service: processing time (gap time), block extra time after. [V] https://squareup.com/help/us/en/article/5351-manage-your-square-appointments-account-settings , https://squareup.com/help/us/en/article/6756-add-gap-times-to-your-square-appointments-services
- **No per-team-member price/duration** for the same service — workaround separate services/variations; open feature request. [V] https://community.squareup.com/t5/Feature-Requests/Provider-Specific-Service-Pricing-amp-Timing-options/idi-p/849567 , https://community.squareup.com/t5/Appointments-Bookings/How-can-I-set-up-different-service-durations-for-each-team/m-p/829003
- Links: booking site per location, staff selection, embeds/"Book now" buttons [I]. Strength: POS integration. Admin: calendar with staff columns [I].

---

## 10. Cross-product matrix: where each rule lives

| Rule | GHL legacy | GHL Services v2 | Calendly | Cal.com | Acuity | Zoho | MS Bookings | SimplyBook | Square |
|---|---|---|---|---|---|---|---|---|---|
| Availability window | user Schedule / per-calendar custom | staff hours (+location per block) | user schedule per event | user schedule per event + restriction sched. | calendar (+type group) | staff or service custom | staff (+service custom) | company ⊇ provider ∩ service | team member / location |
| Duration | calendar | service/variation | event (multi) | event (booker-select) | appt type | service | service | service | variation |
| Buffers | calendar | service | event | event | appt type [I] | service | service | service | service |
| Min notice / horizon | calendar | global | event | event | global→calendar→group | workspace→service | page→service | company [I] | business |
| Daily/weekly limits | calendar/day | staff day/wk/mo | event | event + user | global/calendar/type | event/customer/resource | — | Limit Bookings feature | daily cap (business) |
| Slot interval | calendar | global | event | event | global/calendar [I] | workspace→service | page | company [I] | business |
| Price | payment on calendar | service/variation + **staff×service** | event | event | appt type | service + **staff×service** | service | service | variation |
| Staff-specific duration | — | via variations [I] | — | — | — | — | — | [I] | — |
| Confirmation | calendar | global | — | event | [I] | service | — | Approve feature | business |
| Cancel/reschedule | calendar [I] | global | event [I] | event [I] | global/calendar | workspace→service | page→service | feature | business |
| Intake questions | calendar form | [I] | event | event | appt type forms | service [I] | service | company/service [I] | [I] |

## 11. Admin overview features inventory
- Slot-level "why not available" troubleshooter: GHL (reason codes, names blocking user), Cal.com (reasons ranked by impact + month view). [V]
- Daily "members with zero availability" digest: Cal.com managed events. [V]
- Team availability tab: Cal.com. [V]
- Staff column calendar views: GHL Services v2, Square, SimplyBook [V/I].
- Staff×service assignment matrix screen: **none found** in any product — mapping is edited from either the service (staff checklist) or the staff (services checklist) side. [I, based on all sources above]
- Preview/test link: GHL recommends incognito test [V snippet https://growthable.io/gohighlevel-tutorials/calendar/how-to-create-and-edit-an-unassigned-calendar/]; Calendly/Cal.com "preview" buttons [I].

## 12. Synthesis for our design

Best ideas to steal
1. Service-catalog model (family B) with a single public booking page, deep-linkable by location/category/service/staff and pre-fillable (Acuity params, Zoho workspace/service/staff URLs, Setmore staff pages).
2. Clear 3-level rule inheritance: company defaults → service override → staff×service override (only price, duration, maybe buffers). MS Bookings' "Use default scheduling policy" toggle is the right UX idiom. Show inherited values greyed with "override" button.
3. Reusable named availability Schedules owned by staff (GHL Schedules, Calendly, Zoho 2.0) with date overrides that propagate; optional per-service "restriction window" that only filters (Cal.com restriction schedule, Setmore custom service hours inside business hours, MS "custom hours").
4. Resources as first-class constraints (rooms/chairs/devices with quantity & location; GHL v2, Acuity, SimplyBook Limit Bookings).
5. Assignment modes per service: client chooses / any available (pooled) / auto: availability-first with priority, equal distribution, or weights (Cal.com); "one from each group" (Cal.com RR groups) for clinic roles (doctor + assistant); collective.
6. Limits at multiple scopes, most restrictive wins (Cal.com user limits + event limits; GHL staff day/week/month).
7. Processing time (GHL v2, Square) — essential for salons (colour processing).
8. Slot troubleshooter with reason codes + "what change would open most slots" (Cal.com v6.8, GHL).
9. Routing via attributes (Cal.com) → for us: intake question → filter services/staff by tags.
10. Variations & add-ons instead of duplicating services (Square, GHL v2).

Pitfalls to avoid
1. "One calendar per appointment type" (GHL legacy, MS workaround, Acuity per-staff-price workaround) → calendar sprawl, split bookings, hard overview.
2. Settings that exist only at one level (GHL legacy calendar-wide everything; Zoho overrides only for 1:1; MS no per-staff-per-service availability; Square/Acuity no per-staff price).
3. Hidden precedence / scattered interconnected tabs (SimplyBook complaints) — surface the effective value and its source.
4. Multi-service booking creating N independent appointments with N reminders (GHL).
5. Per-calendar daily caps that don't aggregate across calendars (GHL).
6. Date overrides that must be duplicated in every schedule (Calendly limitation).
7. Plan-gated seat/calendar counts that make modelling rooms as "calendars" expensive (Acuity).
8. No glance view of availability — owners must simulate a booking to see if a date is free (GHL feature board).
