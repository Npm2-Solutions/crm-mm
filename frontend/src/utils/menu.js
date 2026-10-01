// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The main menu as data: the centre's work in groups, each entry with its page,
// its icon (a name of components/Icons/menu.js) and who sees it, on the session
// (`puo`, `puoUno`, `ambito`, `telefono`: a telephony provider is on). The day
// first, with no label - its pages, the people, the conversations, the
// invoices - then the archive, marketing, the phone.
// A group nobody sees is not drawn. The phone's bar takes the first places of
// the same menu (`barraDelTelefono`), the sidebar draws all of it.
import { DASHBOARD_CAPABILITIES } from '@/utils/dashboard'

export const MENU = [
  {
    key: 'giorno',
    entries: [
      {
        key: 'Dashboard',
        label: 'Dashboard',
        icon: 'dashboard',
        // reading the numbers is enough: Read only opens it and makes nothing
        condition: (c) => c.puoUno(DASHBOARD_CAPABILITIES),
      },
      {
        // who arrives, who is waiting, who came: the desk's day
        key: 'Today',
        label: 'Today',
        icon: 'today',
        condition: (c) => c.puo('agenda.presenze'),
      },
      {
        key: 'Calendar',
        label: 'Agenda',
        icon: 'calendar',
        condition: (c) => c.puo('agenda.vedi'),
      },
      {
        // who waits for a place that frees up
        key: 'Waiting List',
        label: 'Waiting list',
        icon: 'waiting',
        condition: (c) => c.puo('agenda.attese'),
      },
      {
        // the people the centre looks after: with the clinic, its patients.
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
        // the centre's register: whoever sees the centre's invoices, Read only too
        key: 'Invoices',
        label: 'Invoices',
        icon: 'invoices',
        condition: (c) => c.ambito('fatture.vedi') === 'centro',
      },
    ],
  },
  {
    // what stays on record beside the people: the companies, the notes
    key: 'archivio',
    label: 'Archive',
    entries: [
      {
        key: 'Organizations',
        label: 'Organizations',
        icon: 'organizations',
        condition: (c) => c.puo('persone.vedi'),
      },
      {
        key: 'Notes',
        label: 'Notes',
        icon: 'notes',
        condition: (c) => c.puo('note.vedi'),
      },
    ],
  },
  {
    // how new people arrive: the deals they open, what runs by itself, the
    // posts, the website
    key: 'marketing',
    label: 'Marketing',
    entries: [
      {
        key: 'Deals',
        label: 'Deals',
        icon: 'deals',
        condition: (c) => c.puo('trattative.vedi'),
      },
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
  {
    key: 'telefono',
    label: 'Phone',
    entries: [
      {
        key: 'Call Logs',
        label: 'Call Logs',
        icon: 'calls',
        condition: (c) => c.puo('telefono.registro'),
      },
      {
        key: 'Dialer',
        label: 'Dialer',
        icon: 'dialer',
        condition: (c) => Boolean(c.telefono) && c.puo('telefono.chiama'),
      },
    ],
  },
]

// The menu one sees: the groups with what they may open, the empty ones gone.
export function menuDi(c, menu = MENU) {
  return menu
    .map((gruppo) => ({
      ...gruppo,
      entries: gruppo.entries.filter((voce) => voce.condition(c)),
    }))
    .filter((gruppo) => gruppo.entries.length)
}

// The phone's bar: four places a phone opens all day, the rest behind "More"
// (the drawer is the sidebar). The day's pages, the people, the conversations
// and the invoices first; then whatever else the level opens, in the menu's order.
export const PREFERITI_DEL_TELEFONO = [
  'Today',
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
