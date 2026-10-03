// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The main menu as data (docs/progetto-ghl/34): the centre's work in groups,
// each entry with its page, its icon (a name of components/Icons/menu.js) and
// who sees it, on the session (`puo`, `puoUno`, `ambito`, `telefono`: a
// telephony provider is on). The work of the day in one group with no label,
// in the order it is done - the agenda (with the reception desk), the people,
// answering them, what is left to do, the deals, the invoices, the numbers -
// then marketing. A group nobody sees is not drawn. The phone's bar takes the
// first places of the same menu (`barraDelTelefono`), the sidebar draws all of
// it.
//
// What is not an entry lives inside one, a switch in their header (`SORELLE`):
// the reception desk and the waiting list beside the agenda - the same day's
// appointments, for welcoming people and for booking them - the companies
// beside the people, the notes beside the tasks; the calls, the round of calls
// and the keypad in the phone at the top of every page
// (components/Telephony/PhoneButton.vue). A page with no entry lights the entry
// it lives in (utils/navigation.js).
import { DASHBOARD_CAPABILITIES } from '@/utils/dashboard'

export const MENU = [
  {
    key: 'giorno',
    entries: [
      {
        key: 'Calendar',
        label: 'Agenda',
        icon: 'calendar',
        condition: (c) => c.puo('agenda.vedi'),
      },
      {
        // everybody the centre has heard from: who asked, its patients, a
        // parent, a company's contact - "People" with the clinic on too.
        // "Lead" is what one of them is at the start, not what they are
        // forever: they stay here after a deal is opened
        key: 'Leads',
        label: 'People',
        icon: 'people',
        condition: (c) => c.puo('persone.vedi'),
      },
      {
        // the same people; this is where you answer them
        key: 'Conversations',
        label: 'Conversations',
        icon: 'conversations',
        condition: (c) => c.puo('conversazioni.usa'),
      },
      {
        key: 'Tasks',
        label: 'Tasks',
        icon: 'tasks',
        condition: (c) => c.puo('persone.vedi'),
      },
      {
        // the sale, with its quotes: work of the day for whoever sells, not
        // marketing's
        key: 'Deals',
        label: 'Deals',
        icon: 'deals',
        condition: (c) => c.puo('trattative.vedi'),
      },
      {
        // the centre's register: whoever sees the centre's invoices, Read only too
        key: 'Invoices',
        label: 'Invoices',
        icon: 'invoices',
        condition: (c) => c.ambito('fatture.vedi') === 'centro',
      },
      {
        // the numbers: last where the day opens on the reception desk, first
        // where it opens here (`menuDi`)
        key: 'Dashboard',
        label: 'Dashboard',
        icon: 'dashboard',
        // reading the numbers is enough: Read only opens it and makes nothing
        condition: (c) => c.puoUno(DASHBOARD_CAPABILITIES),
      },
    ],
  },
  {
    // how new people arrive: what runs by itself, the posts, the website
    key: 'marketing',
    label: 'Marketing',
    entries: [
      {
        key: 'Automations',
        label: 'Automations',
        icon: 'automations',
        condition: (c) => c.puo('automazioni.vedi'),
      },
      {
        key: 'Social Planner',
        label: 'Social Planner',
        icon: 'social',
        condition: (c) => c.puoUno(['social.bozze', 'social.pubblica']),
      },
      {
        // only where Builder is installed (the capability needs it): without
        // it there is no site to manage
        key: 'Website',
        label: 'Site',
        icon: 'site',
        condition: (c) => c.puo('sito.gestisci'),
      },
    ],
  },
]

// The pages that live together behind one entry, a switch between them in
// their header (components/ViewBreadcrumbs.vue): the agenda with its reception
// desk and its waiting list, the people and their companies, the tasks and the
// notes.
export const SORELLE = [
  [
    {
      // who arrives, who is waiting, who came: the day's appointments as the
      // desk welcomes them (the route keeps its name, Today)
      key: 'Today',
      label: 'Reception desk',
      condition: (c) => c.puo('agenda.presenze'),
    },
    {
      key: 'Calendar',
      label: 'Agenda',
      condition: (c) => c.puo('agenda.vedi'),
    },
    {
      key: 'Waiting List',
      label: 'Waiting list',
      condition: (c) => c.puo('agenda.attese'),
    },
  ],
  [
    {
      key: 'Leads',
      label: 'People',
      condition: (c) => c.puo('persone.vedi'),
    },
    {
      key: 'Organizations',
      label: 'Organizations',
      condition: (c) => c.puo('persone.vedi'),
    },
  ],
  [
    {
      key: 'Tasks',
      label: 'Tasks',
      condition: (c) => c.puo('persone.vedi'),
    },
    {
      key: 'Notes',
      label: 'Notes',
      condition: (c) => c.puo('note.vedi'),
    },
  ],
]

// What the pages with no entry of their own are called: a record by its list, the
// keypad's round, an import. A page with nothing to say keeps the product's name.
export const ALTRE_PAGINE = {
  Notifications: 'Notifications',
  More: 'More',
  Inbox: 'Conversations',
  Lead: 'People',
  Deal: 'Deals',
  Contacts: 'Contacts',
  Contact: 'Contacts',
  Organization: 'Organizations',
  'Call Logs': 'Calls',
  Dialer: 'Call round',
  Automation: 'Automation',
  WebsitePage: 'Site',
  FormFill: 'Form',
  DataImportList: 'Data Import',
  NewDataImport: 'Data Import',
  DataImport: 'Data Import',
  'Not Permitted': 'Not permitted',
}

/**
 * What a page is called, in the menu's words (to translate where it is shown):
 * its entry's, else its sibling's, else its own; '' for a page with no name.
 */
export function nomeDellaPagina(chiave, menu = MENU, sorelle = SORELLE) {
  for (const gruppo of menu)
    for (const voce of gruppo.entries)
      if (voce.key === chiave) return voce.label
  for (const gruppo of sorelle)
    for (const pagina of gruppo) if (pagina.key === chiave) return pagina.label
  return ALTRE_PAGINE[chiave] || ''
}

/** The pages a page lives with that the session opens, itself among them. */
export function paginaSorelle(chiave, c, sorelle = SORELLE) {
  const gruppo = sorelle.find((pagine) => pagine.some((p) => p.key === chiave))
  return (gruppo || []).filter((pagina) => pagina.condition(c))
}

// The menu one sees: the groups with what they may open, the empty ones gone.
// The numbers come first only where the day does not open on the reception
// desk (whoever marks arrivals lands there).
export function menuDi(c, menu = MENU) {
  return menu
    .map((gruppo) => {
      let entries = gruppo.entries.filter((voce) => voce.condition(c))
      const numeri = entries.find((voce) => voce.key === 'Dashboard')
      if (numeri && !c.puo('agenda.presenze'))
        entries = [numeri, ...entries.filter((voce) => voce !== numeri)]
      return { ...gruppo, entries }
    })
    .filter((gruppo) => gruppo.entries.length)
}

// The phone's bar: four places a phone opens all day, the rest behind "More"
// (pages/Altro.vue). The agenda (the reception desk is in it), the people, the
// conversations and the invoices first; then whatever else the level opens, in
// the menu's order.
export const PREFERITI_DEL_TELEFONO = [
  'Calendar',
  'Leads',
  'Conversations',
  'Invoices',
]

export function barraDelTelefono(
  menuVisibile,
  quanti = 4,
  preferiti = PREFERITI_DEL_TELEFONO,
) {
  const voci = menuVisibile.flatMap((gruppo) => gruppo.entries)
  const prima = preferiti
    .map((key) => voci.find((voce) => voce.key === key))
    .filter(Boolean)
  const poi = voci.filter((voce) => !prima.includes(voce))
  return [...prima, ...poi].slice(0, quanti)
}
