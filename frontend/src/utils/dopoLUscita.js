// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What DottorCloud keeps in this browser's localStorage and sessionStorage,
 * and what of it goes at a logout (utils/esci.js). A computer at the desk that
 * three colleagues share, the tablet handed to a patient, a phone lent: whoever
 * comes next finds how the device is set, never what the last session wrote,
 * was writing or was looking at.
 *
 * Every key the app writes is in one of the two lists: a new one goes in the
 * first if it is a preference of the device's, else in the second
 * (tests/unit/dopoLUscita.test.js finds the files that write them). A key the
 * app does not write - the framework's desk, another app of the site - is left
 * alone.
 */

/** Kept: how this device is set, nobody's data. */
export const PREFERENZE = [
  // the agenda's view, whose columns, its height and colours (pages/Calendar.vue)
  'crmAgenda',
  // what the agenda's «+» makes, an appointment or an event (pages/Calendar.vue)
  'crmCalendarNewKind',
  // the sidebar folded (Layouts/AppSidebar.vue), as older versions said it too
  'menuPiegato',
  'isSidebarCollapsed',
  // a column's width (Resizer.vue)
  'sidebarWidth',
  // light or dark (frappe-ui's, read by App.vue)
  'theme',
  // which channels a record's history shows (Activities/Activities.vue)
  'crmActivityChannel',
  // the tab a record opens on (composables/useActiveTabManager.js)
  'lastLeadTab',
  'lastDealTab',
  // the dashboard opened last (pages/Dashboard.vue)
  'crm_dashboard_last',
  // which of the centre's numbers a call shows (Telephony/TwilioCallUI.vue)
  'dottorcloud:numero-da-mostrare',
  // the cards that offer to install the app and turn on its notifications,
  // put aside («Not now»): Mobile/InstallaApp.vue, NotificheSulTelefono.vue,
  // and the client area's (area/components/InstallCard.vue, PasskeyCard.vue)
  'dc-installa-non-ora',
  'dc-notifiche-non-ora',
  'area:installa:not-now',
  'area:passkey:not-now',
]

/** Kept by their beginning: one each person, their own choice. */
export const PREFERENZE_PER_INIZIO = [
  // the first steps hidden, by whoever hid them (composables/primiPassi.js)
  'primiPassiNascosti:',
]

/** Gone: what the app writes that is no preference. */
export const DELLA_SESSIONE = [
  // the agenda's reminders, with what they are about (data/notifications.js)
  'eventNotificationAlerts',
  // a message between two pages not delivered yet (composables/useBroadcast.js)
  'app_broadcasts',
  // whose this browser's notifications are (composables/spinta.js)
  'crm-spinta',
  // «Later» on the centre's first opening, for this tab (pages/Benvenuto.vue)
  'dc-benvenuto-dopo',
  // when the page was loaded again for a part gone from the server (utils/ricarica.js)
  'dc-ricaricata',
  // whose area is open (area/store.js)
  'area:person',
]

/** Gone by their beginning. */
export const DELLA_SESSIONE_PER_INIZIO = [
  // the same memo, one per person, as older versions kept it
  'crm-spinta:',
  // where a list was scrolled to (ListViews/ListRows.vue, MobileListRows.vue)
  'scrollPosition',
  // the tab of a record's fields, record by record (Activities/DataFields.vue)
  'fieldLayoutTab:',
  // a diet's shopping list, ticked (area/pages/PlanShopping.vue)
  'crm-area-spesa:',
  // a form's session, opened from the area (area/components/PrepareVisit.vue)
  // or on the /modulo page itself (crm/www/modulo.html)
  'modulo:',
]

function trova(chiave, esatte, inizi) {
  return esatte.includes(chiave) || inizi.some((i) => chiave.startsWith(i))
}

/**
 * A draft: `<kind>-<user>-<doctype>-<name>` (composables/drafts.js: an email,
 * a note, a WhatsApp, an SMS, their attachments), whatever the kind.
 */
export function bozzaDi(chiave, utenti) {
  const trattino = chiave.indexOf('-')
  if (trattino < 1 || !/^[A-Za-z]+$/.test(chiave.slice(0, trattino)))
    return false
  const resto = chiave.slice(trattino + 1)
  return utenti.some((utente) => resto.startsWith(`${utente}-`))
}

/**
 * The keys of a storage that go at a logout: the app's that are no
 * preference, and the drafts of whoever is signing out (`utenti`: their user
 * and the email their drafts are kept under). A colleague's drafts stay theirs.
 */
export function daTogliere(chiavi, utenti = []) {
  const chi = (utenti || []).filter(Boolean)
  return (chiavi || []).filter(
    (chiave) =>
      typeof chiave === 'string' &&
      !trova(chiave, PREFERENZE, PREFERENZE_PER_INIZIO) &&
      (trova(chiave, DELLA_SESSIONE, DELLA_SESSIONE_PER_INIZIO) ||
        bozzaDi(chiave, chi)),
  )
}
