// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The settings' menu: its groups, their entries, the tabs of an entry, and who
// sees each of them.
//
// A group is an area of the centre's work, the ones the app's own menu has: you,
// the centre, the agenda, the people it serves, the deals, each channel,
// marketing, invoicing, what is connected from outside. An entry is one thing to
// set up; a thing with several sides is one page with its tabs, as Meta was
// first (its connection and what it feeds). They had grown to fifty entries in
// sixteen groups, five of them with a single entry, and "Consents" sat under
// "User Management", the person's own calendar under "Booking".
//
// A page keeps the name it had, as an entry's key or a tab's (or an alias): the
// links built on the server (an OAuth callback, a dashboard's hint, the WhatsApp
// signup) and the buttons around the app ask for those names, and land on the
// page that holds them now, on its tab.
//
// What a page is drawn with (its component, its icon) is Settings.vue's; here is
// only what can be tested. A condition reads the session from `c`:
// `puo(capability)`, `ambito(capability)`, `whatsapp` (the app is installed),
// `verticale` (the vertical that is on).

const puo = (capacita) => (c) => c.puo(capacita)
const generali = puo('impostazioni.generali')
const agenda = puo('agenda.configura')
const prenotazioni = puo('prenotazione_online.configura')
const assegnazione = puo('assegnazione.regole')
const tracciamento = puo('tracciamento.gestisci')

export const MENU = [
  {
    key: 'account',
    label: 'Your account',
    items: [
      { key: 'Profile', label: 'Profile' },
      { key: 'Preferences', label: 'Preferences' },
      {
        // each person connects their own: the hours they are busy elsewhere
        key: 'Google Calendar',
        label: 'Google Calendar',
        condition: puo('google_calendar.proprio'),
      },
    ],
  },
  {
    key: 'centre',
    label: 'The centre',
    items: [
      {
        key: 'General settings',
        label: 'General',
        tabs: [
          { key: 'Brand', label: 'Name & logo', condition: generali },
          // how a person's record answers a message, and how its story reads
          { key: 'General', label: 'Conversations', condition: generali },
          { key: 'Dashboard', label: 'Dashboard', condition: generali },
          // the items of the app's own menu, top left
          { key: 'Home Actions', label: 'Menu', condition: generali },
          // currency, numbers and dates: the agency's
          {
            key: 'Defaults',
            label: 'Formats',
            condition: puo('tecnico.predefiniti'),
          },
        ],
      },
      {
        key: 'Users',
        label: 'Users',
        tabs: [
          { key: 'Users', label: 'Users', condition: puo('utenti.gestisci') },
          {
            key: 'Invite User',
            label: 'Invite',
            condition: puo('utenti.gestisci'),
          },
          {
            // who sees whose people and deals
            key: 'Sales Hierarchy',
            label: 'Hierarchy',
            condition: puo('gerarchia.gestisci'),
          },
        ],
      },
      { key: 'Plan', label: 'Plan', condition: puo('piano.vedi') },
    ],
  },
  {
    // in the order you set it up: what you offer, when and who, where, and the
    // rules on top
    key: 'agenda',
    label: 'Agenda',
    items: [
      {
        // what the centre offers, what it costs, what the desk sells
        key: 'Services',
        label: 'Services',
        tabs: [
          { key: 'Services', label: 'Services', condition: agenda },
          { key: 'Price Lists', label: 'Price lists', condition: agenda },
          { key: 'Subscriptions', label: 'Subscriptions', condition: agenda },
        ],
      },
      {
        key: 'Hours & shifts',
        label: 'Hours & shifts',
        tabs: [
          {
            // opening hours, and what the agenda refuses to book
            key: 'Studio hours & rules',
            label: 'Hours & rules',
            condition: agenda,
          },
          // a practitioner sees only this one, with their own shifts
          {
            key: 'Team rota',
            label: 'Team rota',
            condition: puo('agenda.turni'),
          },
        ],
      },
      {
        // the rooms are the whole centre's
        key: 'Rooms & Equipment',
        label: 'Rooms & equipment',
        condition: (c) => c.ambito('agenda.turni') === 'centro',
      },
      {
        key: 'Calendar & reminders',
        label: 'Calendar & reminders',
        condition: generali,
      },
      {
        // a place that frees up goes to who waits for it
        key: 'Waiting list',
        label: 'Waiting list',
        condition: agenda,
      },
      {
        // the one place to answer "can clients book this, with this person?"
        key: 'Online booking',
        label: 'Online booking',
        tabs: [
          {
            key: 'Online booking',
            label: 'Services & people',
            condition: prenotazioni,
          },
          {
            key: 'Page & rules',
            label: 'Page & rules',
            condition: prenotazioni,
          },
          {
            key: 'Booking platforms',
            label: 'Platforms',
            condition: puo('piattaforme.configura'),
          },
        ],
      },
    ],
  },
  {
    // the people the centre serves: what they fill and sign, what they agree to,
    // their area, what their plans are written with. The vertical names them
    // ("Patients" with the clinic on)
    key: 'clients',
    label: 'Clients',
    items: [
      {
        // one builder: the forms to fill and sign, the sheets, the website's
        key: 'Forms',
        label: 'Forms',
        condition: (c) =>
          c.puo('moduli_lead.gestisci') || c.puo('moduli.configura'),
      },
      {
        key: 'Consents',
        label: 'Consents',
        condition: puo('consensi.configura'),
      },
      {
        // what the area tells outside it
        key: 'News in the client area',
        label: 'Client area',
        condition: (c) => c.puo('canali.configura') && c.puo('area.invita'),
      },
      {
        key: 'Libraries',
        label: 'Libraries',
        tabs: [
          {
            key: 'Exercises',
            label: 'Exercises',
            condition: puo('piani.librerie'),
          },
          {
            // what the clinic's diets are written with
            key: 'Foods',
            label: 'Foods',
            condition: (c) =>
              c.puo('piani.librerie') && c.verticale === 'clinica',
          },
        ],
      },
    ],
  },
  {
    key: 'deals',
    label: 'Deals',
    items: [
      {
        key: 'Pipelines',
        label: 'Pipelines',
        condition: puo('pipeline.configura'),
      },
      {
        // who takes a request, and how soon they answer it
        key: 'Assignment',
        label: 'Assignment',
        tabs: [
          { key: 'Assignment Rules', label: 'Rules', condition: assegnazione },
          {
            key: 'SLA Policies',
            label: 'Response times',
            condition: assegnazione,
          },
        ],
      },
    ],
  },
  {
    // a channel: the accounts it sends from, the templates it sends
    key: 'email',
    label: 'Email',
    items: [
      {
        key: 'Accounts',
        label: 'Accounts',
        condition: puo('email.account_centro'),
      },
      {
        // everybody uses them from the composer; writing them is the manager's
        key: 'Templates',
        label: 'Templates',
        condition: puo('modelli_messaggio.gestisci'),
      },
    ],
  },
  {
    // the same, for WhatsApp: the numbers, and the templates it may send
    // outside the 24 hours
    key: 'whatsapp',
    label: 'WhatsApp',
    condition: (c) => c.whatsapp,
    items: [
      {
        key: 'WhatsApp',
        label: 'Numbers',
        title: 'WhatsApp',
        condition: puo('canali.configura'),
      },
      {
        key: 'WhatsApp Templates',
        label: 'Templates',
        title: 'WhatsApp Templates',
        condition: puo('modelli_messaggio.gestisci'),
      },
    ],
  },
  {
    // and for the phone: the lines, and what to say on a call
    key: 'phone',
    label: 'Phone',
    items: [
      { key: 'Telephony', label: 'Telephony' },
      {
        key: 'Call Scripts',
        label: 'Call scripts',
        condition: puo('telefono.copioni_scrivi'),
      },
    ],
  },
  {
    key: 'marketing',
    label: 'Marketing',
    items: [
      {
        // only where Builder is installed: the capability needs it
        key: 'Website',
        label: 'Website',
        condition: puo('sito.gestisci'),
      },
      {
        // which profiles the planner publishes to: they come from Meta
        key: 'Social profiles',
        label: 'Social Planner',
        condition: puo('social.pubblica'),
      },
      {
        key: 'Tracking',
        label: 'Tracking',
        tabs: [
          {
            key: 'Lead Tracking',
            label: 'Lead tracking',
            condition: tracciamento,
          },
          {
            key: 'Tracked Links',
            label: 'Tracked links',
            condition: tracciamento,
          },
        ],
      },
    ],
  },
  {
    // who issues, what is sold and who performs it, how it reaches the SdI, and
    // the switches over all of it
    key: 'invoicing',
    label: 'Invoicing',
    condition: puo('fatture.configura'),
    items: [
      // the company's own record has its tabs already (company, invoicing,
      // documents, transmission, healthcare): no second row over them
      { key: 'Issuing company', label: 'Issuing company' },
      {
        key: 'Services & providers',
        label: 'Services & providers',
        tabs: [
          { key: 'Billable services', label: 'Billable services' },
          { key: 'Providers', label: 'Providers' },
          { key: 'Qualification register', label: 'Qualifications' },
        ],
      },
      { key: 'Provider connection', label: 'Provider connection' },
      { key: 'Invoicing defaults', label: 'Options' },
    ],
  },
  {
    // what is connected from outside, each with its own page
    key: 'integrations',
    label: 'Integrations',
    items: [
      {
        // one page with its own tabs, the connection and what it feeds
        key: 'Meta connection',
        label: 'Meta',
        aliases: ['Lead forms', 'Ad performance', 'Lead quality'],
        condition: puo('meta.gestisci'),
      },
      { key: 'ERPNext', label: 'ERPNext', condition: puo('tecnico.erpnext') },
      {
        // the centre's certificate and the time-stamping authority
        key: 'Seal and time stamp',
        label: 'Seal and time stamp',
        condition: puo('tecnico.integrazioni'),
      },
      {
        // the register for the manager, the model for the agency
        key: 'Assistant',
        label: 'Assistant',
        condition: (c) =>
          c.puo('assistente.registro') ||
          c.puo('assistente.registro_clinico') ||
          c.puo('tecnico.integrazioni'),
      },
    ],
  },
]

const vale = (cosa, c) => !cosa.condition || Boolean(cosa.condition(c))

// What a person sees: the groups with an entry for them, the entries with a
// tab for them, each with only the tabs they may open.
export function menuDi(c, menu = MENU) {
  return menu
    .filter((gruppo) => vale(gruppo, c))
    .map((gruppo) => ({
      ...gruppo,
      items: gruppo.items
        .filter((voce) => vale(voce, c))
        .map((voce) =>
          voce.tabs
            ? { ...voce, tabs: voce.tabs.filter((scheda) => vale(scheda, c)) }
            : voce,
        )
        .filter((voce) => !voce.tabs || voce.tabs.length > 0),
    }))
    .filter((gruppo) => gruppo.items.length > 0)
}

// The entry a name asks for, and its tab: an entry's key, a tab's, an alias,
// then the label it is shown with, as it is or translated (`t`) - a page
// without a key of its own was asked for by its label, in English.
export function trova(menu, nome, t = (testo) => testo) {
  if (!nome) return null
  const voci = menu.flatMap((gruppo) => gruppo.items)
  const voce =
    voci.find((v) => v.key === nome) ||
    voci.find((v) => v.tabs?.some((s) => s.key === nome)) ||
    voci.find(
      (v) =>
        v.aliases?.includes(nome) ||
        v.tabs?.some((s) => s.aliases?.includes(nome)),
    ) ||
    voci.find((v) => v.label === nome || t(v.label) === nome)
  return voce ? { voce, scheda: schedaDi(voce, nome) } : null
}

// The tab of an entry a name opens: its own, or the first one.
export function schedaDi(voce, nome) {
  if (!voce?.tabs?.length) return null
  return (
    voce.tabs.find((s) => s.key === nome || s.aliases?.includes(nome)) ||
    voce.tabs[0]
  )
}

// Every page there is, an entry without tabs or a tab: what Settings.vue has to
// draw.
export function pagine(menu = MENU) {
  return menu.flatMap((gruppo) =>
    gruppo.items.flatMap((voce) =>
      voce.tabs ? voce.tabs.map((scheda) => scheda.key) : [voce.key],
    ),
  )
}
