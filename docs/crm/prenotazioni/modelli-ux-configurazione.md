# Unified booking system: admin/config UX and rule architecture research

Date: 2026-09-24. Tags: **[V]** = verified from a fetched or searched source (URL given). **[I]** = my inference or design recommendation, not taken from a source.
Caveat: WebFetch returns summaries of help pages. None of the screenshots were inspected directly, so the UI descriptions come from help text.

---

## 1. Rule inheritance / settings hierarchy

### What vendors do
- **Zoho Bookings**: two levels, workspace and then service. "Configuring preferences here will override the policies and preferences at the workspace level." This covers staff selection, slot interval, time zone, min/max notice, T&C, and cancel/reschedule policy. The help docs do not describe any visual inherited/overridden indicator. [V] https://help.zoho.com/portal/en/kb/bookings/services/features/articles/service-preferences
- **Zoho Schedules**: workspace-level reusable working-hour templates. Each event type links to exactly one schedule, or it follows the user's own hours, and there is an "Override user-specific hours" toggle. Changes to a schedule cascade to every event type that uses it. [V] https://help.zoho.com/portal/fr/community/topic/introducing-schedules-for-smarter-availability-management
- **Fresha**: service has a default price and duration. "Advanced pricing and duration" customizes them per **location** and per **team member**, with "Reset" per row and "Reset all". This is the clearest salon example of staff×service override with a way back to the default. [V] https://www.fresha.com/help-center/knowledge-base/catalog/76-set-advanced-pricing-and-durations-
- **Square Appointments**: can NOT vary duration by staff for the same service. The documented workaround is duplicate services, one per staff. Users keep asking for it on the feature-request board. This is the anti-pattern to avoid. [V] https://community.squareup.com/t5/Feature-Requests/Provider-Specific-Service-Pricing-amp-Timing-options/idi-p/849567 , https://community.squareup.com/t5/Appointments-Bookings/How-can-I-set-up-different-service-durations-for-each-team/m-p/829003
- **GoHighLevel Services**: three layers of availability. (1) "Default Availability", a baseline applied the first time a staff member is assigned to a service. (2) Weekly working hours, where each slot can carry a list of services and locations. (3) Date-specific hours override the weekly hours. Also per-staff price adjustments, per-staff booking URL, and day/week/month caps. [V] https://help.gohighlevel.com/support/solutions/articles/155000005331-configuring-staff-in-services
- **Cal.com Managed Event Types**: an admin template pushed to members. Every field is **locked by default** and shows a lock icon. The admin unlocks specific fields, typically title and description, while booking questions, reminders and availability usually stay locked. This is the best "who is allowed to override" pattern. [V] https://cal.com/help/event-types/managed-events , https://cal.com/blog/managed-events-scheduling-guide

### Canonical admin-UI patterns for inherited vs overridden (outside booking)
- **Magento/Adobe Commerce scope**: each field has a checkbox labelled for its parent scope ("Use system value", "Use Default", "Use Website"). When it is checked, the field is disabled and shows the parent value. Unchecking it creates an override. [V] https://experienceleague.adobe.com/en/docs/commerce-admin/config/scope-change
- **Google Admin console OUs**: text under each setting says "Inherited" or "Overridden". The admin clicks "Override" to pin a value, and an overridden child stops receiving parent changes. There is an explicit "Inherit" action to revert. [V] https://support.google.com/a/answer/4352075 , https://support.google.com/a/answer/2655363
- Known pitfall from Magento: when an API update is not scope-aware it silently unchecks "use default" and creates accidental overrides. [V] https://github.com/magento/magento2/issues/26484 → Store "unset" as NULL/absent, never as a copied value. [I]

### Recommended architecture [I]
Resolution chain, from most specific to least:
`staff×service → staff → service → category → location → company(defaults)`
- Store only explicit overrides: a sparse table `(scope_type, scope_id, key, value)` or nullable columns. The resolver returns `{value, source_scope, source_id}` per key.
- The UI for every overridable field has 3 states:
  - **Inherited**: grey value plus the chip "da Servizio: Pulizia denti".
  - **Overridden**: normal value with a coloured dot, "Ripristina" link, and a tooltip showing the parent value.
  - **Locked**: lock icon, cannot be changed at this level (Cal.com pattern).
- "**Effective settings**" panel on staff, service and staff×service pages: a read-only table of all resolved rules with their source. Add a counter "3 personalizzazioni" and let admins filter lists by "has overrides".
- When an admin edits a parent value, show an impact message: "Changing this affects 14 services; 2 have their own value and will not change". This follows Google's pinned semantics. [I]
- Split rule keys into families so each family has an obvious owner:
  - (a) **what/price/duration**: service, overridable per staff×service and per location (Fresha).
  - (b) **when**: availability. Use schedules, see §3.
  - (c) **booking policy**: notice, horizon, cancel window, max per day, deposit. Set at company, override per service/staff.
  - (d) **presentation**: online visibility, selectable staff, "any".

---

## 2. Overview UIs (matrix, rota, heatmap)

- **GHL gap**: users ask for a view of "all staff members and their open slots in one view, filter by service, one-click booking, grey-out unavailable hours". Competitor VisiBooks is cited, and clients say they are "resisting HighLevel adoption". The request has 13 votes and was merged April 2026. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/enhanced-calendar-view-staff-availability-display-for-service-based-businesses
- **GHL**: the calendar shows everything on a white background with no available/unavailable colouring. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/differentiating-between-available-unavailable-slots-on-the-calendar
- **Fresha "Scheduled shifts"**: Team → Scheduled shifts is a weekly grid, one row per team member and one column per day, showing shift chips. The pencil icon opens a repeating pattern (every 1–4 weeks, end never or on a date, day checkboxes with start/end, "Add" for a split shift or break). Time off is a separate object. [V] https://www.fresha.com/help-center/knowledge-base/calendar/102032-schedule-and-update-team-shifts , https://www.fresha.com/help-center/knowledge-base/calendar/21-add-time-off-for-team-members
- **Cal.com**: "Team availability" tab plus a Timeline view showing members' availability across the group. [V] https://cal.com/blog/enable-team-availability-calcom , https://cal.com/help/availabilities/team-availability
- **Services×staff matrix**: I found no strong public documentation of a checkbox matrix in the major vendors. They all assign from the service page (a staff checklist) or from the staff page (a services checklist). [V, absence] This is an **opportunity**. [I]

### Recommended overview screens [I]
1. **"Chi fa cosa" matrix**: rows are services grouped by category, columns are staff, filtered by location.
   - Cell states: empty (not enabled), ✓ (enabled, inherits price/duration), ✓• (enabled with an override; the tooltip shows "45 min · €60 (default 30 min · €50)"), and ⚠ (enabled but no availability windows allow this service).
   - Bulk actions: click a row or column header to toggle all; shift-select a rectangle; "copy column from staff X".
   - Clicking a cell opens a side drawer with the staff×service overrides.
2. **Weekly rota grid** (Fresha-style): staff × days, shift chips, time-off chips in a different colour, holiday columns shaded. Edit either one day or the whole pattern.
3. **Availability/occupancy heatmap**: rows are staff or resources, columns are hour buckets over a week. Colour shows the % of bookable minutes that are booked, with a hatched pattern where nobody is available. Toggle between "available capacity" and "occupancy". It answers "where do we lose demand". Use a sequential palette and the dataviz skill.
4. **Coverage per service**: for each service, how many staff-hours per week it is bookable. It flags services with zero or single-person coverage.

---

## 3. Availability modelling

- **Named reusable schedules**: Calendly schedules are independent of event types, and one schedule is "Applied to" many event types (or chosen per event type in its "Schedule:" dropdown). [V] https://calendly.com/help/availability-overview , https://assets-help-site.calendly.com/help/article/how-to-apply-your-schedule-to-multiple-event-types/
  - Cal.com: multiple schedules, one marked default. [V] https://cal.com/help/availabilities/multiple-schedules
  - Zoho: see §1. [V]
- **GHL Schedules** (Labs, 2025–26): "shared availability templates that combine weekly working hours, date-specific overrides, and staff-level time-zone". Users can have multiple schedules, each calendar uses one schedule per user, admins can mark a default schedule for new calendars, and there are "Custom Schedules" per calendar. No API yet. [V] https://help.gohighlevel.com/support/solutions/articles/155000006215-schedules-centralized-availability-management
- **Date overrides vs OOO**: Cal.com separates date overrides from out-of-office.
  - Date overrides are attached to one schedule: set hours or mark unavailable on that date, and they are auto-deleted once the date passes.
  - OOO is per person across all schedules. It has a reason, optional forwarding to a teammate, and a Holidays tab for country public holidays that block automatically.
  - [V] https://cal.com/blog/mastering-cal-com-date-overrides-vs-out-of-office-settings , https://cal.com/help/availabilities/out-of-office
- **Community pain point**: Calendly users ask for one set of date-specific hours shared across event types. [V] https://community.calendly.com/how-do-i-40/can-i-use-one-set-of-date-specific-hours-for-all-event-types-3036
- **Resources**: Acuity resources are a quantity per resource (chairs, rooms), assigned to appointment types. They are an extra restriction on top of availability and are invisible to clients. When a resource count reaches 0, the slot disappears. [V] https://help.acuityscheduling.com/hc/en-us/articles/16676949567757-Use-resources-to-limit-bookings
  - GHL: resources such as rooms and equipment exist in Services. [V] https://help.gohighlevel.com/support/solutions/articles/155000003505-resources-in-services
- **Processing time**: Square splits duration into initial + processing + final. During processing the staff member can be booked by another client. Block time (cleanup) is added to the slot. [V] https://squareup.com/help/us/en/article/6756-add-gap-times-to-your-square-appointments-services

### Recommended model [I]
- `Schedule` (named: weekly rules + timezone + its own date overrides), owned by location or staff, and reusable.
- Staff default schedule = the location schedule, which is overridable.
- `TimeOff/Closure` is separate from schedules. It has a scope (company holiday calendar, location closure, staff OOO with reason, resource maintenance), which fixes the Calendly complaint.
- Optional "service windows": service X is only bookable Tue/Thu afternoons. Use the same Schedule object.
- **Slot = staff_schedule ∩ ¬staff_timeoff ∩ ¬staff_busy(bookings + external calendars) ∩ location_hours ∩ service_window ∩ resource_capacity>0 ∩ policy(notice, horizon, daily caps)**
  - Evaluate the terms in this order, so the troubleshooter (§6) can report the first failing term.
- Duration model per service: `pre_buffer + [active_1 + processing + active_2] + post_buffer`. Staff is busy only for the active segments. Resources can be held for the whole span. Buffers are overridable per staff×service.
- Slot interval ("ogni 15 min") and "start times aligned to" are policy keys in the inheritance chain.

---

## 4. Booking links architecture

- **GHL anti-pattern**: one calendar per service. Users complain: "It is difficult to create thousands of calendars for companies that have multiple services", "messy confusing never ending calendars". The request has 14 votes and was still open in April 2026. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/one-calendar-for-multiple-services
  - The Service Menu is a layer on top: calendar groups, then one service calendar per service, then the menu with a slug, checkbox selection and drag order. It is Stripe-only, with no coupons and no saved cards. [V] https://help.gohighlevel.com/support/solutions/articles/155000001161-service-menu
- **Acuity dynamic links** are one booking site with params: `appointmentType` (repeatable, restricts the list), `appointmentType=category:Name`, `calendarID` (staff), `location`, `datetime`, `quantity`, prefilled `firstName/lastName/email/phone` and form-field answers. [V] https://help.acuityscheduling.com/hc/en-us/articles/31919067234445-Parameters-for-dynamic-links , https://developers.acuityscheduling.com/docs/embedding
- **Cal.com prefill**: `name, email, notes, guests, phone`, custom fields by identifier, and `metadata[key]=value`, which is stored on the booking and sent in the webhook. It captures UTMs. [V] https://cal.com/help/embedding/prefill-booking-form-embed , https://attributer.io/blog/capture-utm-parameters-cal
- **Square**: one booking flow URL per location, and "Advanced Widgets" show only specific services, staff or a combination. [V] https://squareup.com/help/us/en/article/5355-set-up-online-booking-with-square-appointments
- **Routing forms**: Cal.com asks qualifying questions and then routes to an event type, a team member, or "no booking". Its attribute routing matches form answers to member attributes (for example a Service attribute) instead of hand-coding every route. [V] https://cal.com/help/routing/routing-with-attributes , https://cal.com/blog/why-cal-com-s-routing-forms-are-a-game-changer-for-scheduling

### Recommended [I]
One site per company, e.g. `/prenota`, with deep links that pre-apply filters and skip steps:
- `/prenota` (menu), `/prenota/c/<categoria>`, `/prenota/s/<servizio>`, `/prenota/p/<staff>` (staff profile, shows only their services), `/prenota/l/<sede>`.
- Query params: `?servizi=a,b` (cart), `staff=`, `sede=`, `data=YYYY-MM-DD`, `ora=`, `nome/email/tel` prefill, `utm_*` + `ref=`, `lead=<id>` (signed token that links the booking to the CRM record).
- A "Link builder" in admin: pick filters, get the URL, a QR code, and embed snippets (inline, popup button, floating). UTM fields sit next to them.
- "Aiutami a scegliere": an optional questionnaire node before the menu. Answers map to a service/category (or to staff attributes, as in Cal.com) and are saved as booking metadata. Example for clinics: "prima visita o controllo?", "zona/trattamento". [I]
- Per-staff links are just filtered views of the same engine, never separate calendars. [I]

---

## 5. Booking-flow UX benchmarks

- **Staff choice**: Mangomint has an "Anyone" option, optional gender filters, random order, and assignment of "Anyone" randomly or by order, with a list of staff excluded from auto-assign. [V] https://www.mangomint.com/learn/adjusting-staff-selection-options-in-online-booking/
  - Zoho can show an "Auto-assign staff" entry first in the staff list, or disable staff choice entirely (round robin). [V] https://help.zoho.com/portal/en/kb/bookings/services/features/articles/service-preferences
  - Square can hide "Staff" completely from the client flow. [V] https://squareup.com/help/us/en/article/5351-manage-your-square-appointments-account-settings
- **Multi-service**: Mangomint supports multi-service and multi-guest, optionally restricting multi-service to one staff member. [V] https://www.mangomint.com/learn/online-booking-from-the-clients-perspective/
  - GHL multi-service puts all services in a single slot, and users ask for separate date/time per service and provider. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/enhancement-request-allow-separate-date-time-selection-for-multiple-services-in
- **Date pickers (Baymard)**: pickers that do not communicate availability cause extra verification and abandonment. Show available dates, grey out unavailable ones, and make the time zone explicit. [V] https://baymard.com/ecommerce-design-examples/date-picker
- **Form length**: fewer fields convert better, so ask only name, email/phone and time before confirming. This claim comes via Schedly citing NN/g, a secondary source whose numbers are unverified. [V-weak] https://schedly.io/whats-preventing-more-visitors-from-scheduling-appointments/
  - NN/g: appointment scheduling is the most frequent online interaction in healthcare journeys. [V] https://www.nngroup.com/articles/healthcare-customer-journeys/

### Recommended flow [I]
- **Default is service-first**: category, then service (price "da €X", duration), then staff ("Chiunque / primo disponibile" preselected), then date/time, then details, then confirm.
- Entering via `/p/<staff>` makes it **staff-first**. Offer a "Prima disponibilità" shortcut that shows the next 3–5 slots across all eligible staff above the calendar.
- **Mobile**:
  - A horizontal strip of days with a slot count per day, jumping to the next available day when the current one is empty.
  - Slots grouped into Mattina/Pomeriggio/Sera.
  - A sticky summary bar showing service, price, duration and staff.
  - Phone plus OTP or email only. Ask intake questions after the slot is held.
- **Cart**: allow sequential services with the same staff (back-to-back) in v1. Multi-staff chaining comes later.
- For clinics: show "prima visita" vs "controllo" as separate services, not as a question, because duration differs.

---

## 6. Testing / simulation / "why not available"

- **Calendly Troubleshoot** is reached from Preview → Troubleshoot. Pick the unavailable date/time and it lists reason codes:
  - Calendar: CALENDAR, NOCAL
  - Limits and timing: DAILY/WEEKLY/MONTHLY MAX, DURATION, RANGE, TOOSOON
  - Other bookings: EVENT, GROUP, OVERLAP
  - Time off and hosts: HOLIDAY, MEETING LIMIT, HOST, ROUNDROBIN, UNFAIR
  - Other: BUFFER, PAST, RESERVED
  - Each code comes with a fix link. [V] https://calendly.com/help/how-to-troubleshoot-unavailable-times-that-should-be-available
  - There is a reverse article for times that are available but should not be. [V] https://calendly.com/help/how-to-troubleshoot-available-times-that-should-be-unavailable
- **Cal.com Troubleshooter**: a "Need Help" button on the booking page opens a calendar view with date overrides, booking limits and connected-calendar busy events (/availability/troubleshoot). [V] https://cal.com/blog/learn-all-about-cal-com-s-troubleshooting-feature
  - Criticism in a GitHub issue: it "just gives a list of busy times" and does not say which calendar or integration is blocking. [V] https://github.com/calcom/cal.diy/issues/1171
- **Acuity** has a "Fix availability issues and missing appointment times" help page, which is a checklist rather than a tool. [V] https://help.acuityscheduling.com/hc/en-us/articles/16676931784333-Fix-availability-issues-and-missing-appointment-times

### Recommended [I]
- **"Simula come cliente"**: open the real booking flow in admin with a banner, a selectable "as of" datetime, and no side effects.
- **Slot explainer**: click any greyed slot in simulation or in the admin calendar. The resolver returns the ordered list of failed terms from the §3 formula as codes, each with a human sentence and a deep link to the rule and its source scope. Example: "BUFFER – 10 min dopo appuntamento 'Igiene' (Dr. Rossi, regola ereditata da Servizio)". Support both directions: "why not available" and "why available".
- **Per-staff explanation for "Anyone"**: a table with staff as rows and the first blocking reason in each row.
- **Config linter**: services with no bookable staff, staff enabled for a service with no windows, overrides identical to the parent (propose cleanup), and resources with capacity 0.

---

## 7. GoHighLevel pain points (to position against)
- **Calendar sprawl**: one calendar per service. [V] ideas link §4.
- **Round robin**: it ignores the already-assigned owner, and users request "book with assigned user". It ignores blocked slots when choosing, and availability can't differ per appointment type for the same provider. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/add-an-option-for-round-robin-calendar-to-use-the-same-assigned-user-for-calenda , https://ideas.gohighlevel.com/scheduling-calendar/p/custom-availability-by-calendar-type-flexible-scheduling-for-round-robin-appoint , https://ideas.gohighlevel.com/scheduling-calendar/p/round-robin-calendar-block-slots
- **No all-staff availability overview**, and available/unavailable slots are not visually distinguished. [V] §2 links.
- **Multi-service**: all services share one slot. [V] §5.
- **Service Menu**: Stripe only, no coupons, no saved cards, no in-app payments. [V] §4.
- **Services V2 bugs** reported by salon and aesthetics users. [V, via search summary] https://ideas.gohighlevel.com/scheduling-calendar/p/service-calendar-booking-to-allow-for-multiple-services
- **Other**: recurring appointments requested for years; Google Calendar scopes felt excessive. [V] https://ideas.gohighlevel.com/scheduling-calendar/p/recurring-appointments-2 , https://ideas.gohighlevel.com/scheduling-calendar/p/reduce-permissions-required-to-connect-to-google-calendar
- **Workarounds seen**: Schedules (Labs) to avoid editing each calendar, and Calendar Groups plus Service Menu to fake a single site. [V] §3/§4.
- I did not find Reddit or YouTube threads through search, so the GHL evidence comes from its own ideas board (primary user voice). [I]
