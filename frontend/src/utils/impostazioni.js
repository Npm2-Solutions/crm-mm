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
    description:
      'Your profile, how {brand} looks, your notifications, your mailbox, the calendar you bring.',
    items: [
      {
        key: 'Profile',
        label: 'Profile',
        description: 'Your name, your photo, your password.',
      },
      {
        key: 'Preferences',
        label: 'Preferences',
        description: 'The theme and the language you read {brand} in.',
      },
      {
        // what reaches you outside the panel: this phone or computer, and by
        // email when the panel has not been read
        key: 'Notifications',
        label: 'Notifications',
        description:
          'What reaches you on your phone, your computer and by email.',
      },
      {
        // the mailbox one writes to people from, and the signature (doc 51)
        key: 'Your email',
        label: 'Your email',
        description:
          'The mailbox you write to people from, and your signature.',
        condition: puo('conversazioni.usa'),
      },
      {
        // each person connects their own: the hours they are busy elsewhere
        key: 'Google Calendar',
        label: 'Google Calendar',
        description:
          'Your hours busy elsewhere, so that nobody books you then.',
        condition: puo('google_calendar.proprio'),
      },
    ],
  },
  {
    key: 'centre',
    label: 'The centre',
    description:
      'Who the centre is, who works in it, how {brand} behaves, what it includes.',
    items: [
      {
        key: 'General settings',
        label: 'General',
        description:
          "The centre's name, logo, language and clock, how conversations behave, the dashboard, the menu.",
        tabs: [
          { key: 'Brand', label: 'Name & logo', condition: generali },
          // Italian or English, and Europe's time zone of the agenda
          { key: 'Language', label: 'Language & time', condition: generali },
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
        description:
          'Who works in the centre and at what level, invitations, who sees whom.',
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
      {
        // the plan as the centre reads it: what the product comprises, the
        // extras; "Features", not "Plan", which are the patients' (doc 36)
        key: 'Plan',
        label: 'Features',
        description:
          'What {brand} includes for the centre, and what can be added.',
        condition: puo('piano.vedi'),
      },
      {
        // the centre's data are the centre's: brought over from the previous
        // software (crm/importazione), taken away in one archive (crm/esportazione)
        key: 'Your data',
        label: 'Your data',
        description:
          'Bring your people over from the previous software, take all your data away.',
        condition: (c) => c.puo('dati.esporta') || c.puo('persone.importa'),
      },
      {
        // a centre full of life to look around in, taken away in one tap
        // (doc 53)
        key: 'Demo data',
        label: 'Demo data',
        description:
          'A centre full of people and appointments to try {brand} on, taken away in one tap.',
        condition: puo('dati_prova.gestisci'),
      },
    ],
  },
  {
    // in the order you set it up: what you offer, when and who, where, and the
    // rules on top
    key: 'agenda',
    label: 'Agenda',
    description:
      'What the centre offers, when and where: services, hours, rooms, reminders, online booking.',
    items: [
      {
        // what the centre offers, what it costs, what the desk sells
        key: 'Services',
        label: 'Services',
        description:
          'What the centre offers, its price lists and its subscriptions.',
        tabs: [
          { key: 'Services', label: 'Services', condition: agenda },
          { key: 'Price Lists', label: 'Price lists', condition: agenda },
          { key: 'Subscriptions', label: 'Subscriptions', condition: agenda },
        ],
      },
      {
        key: 'Hours & shifts',
        label: 'Hours & shifts',
        description: 'When the centre is open, and who works when.',
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
        description: 'Where appointments take place and what they need.',
        condition: (c) => c.ambito('agenda.turni') === 'centro',
      },
      {
        // its key stays: the links are built on it
        key: 'Calendar & reminders',
        label: 'Agenda & reminders',
        description:
          'Where the agenda opens, the minutes its grid moves by, the reminders people receive.',
        tabs: [
          { key: 'Calendar & reminders', label: 'Agenda', condition: generali },
          // the day before, by WhatsApp with its buttons, SMS or email (doc 59)
          {
            key: 'Appointment reminders',
            label: 'Appointment reminders',
            condition: agenda,
          },
        ],
      },
      {
        // a place that frees up goes to who waits for it
        key: 'Waiting list',
        label: 'Waiting list',
        description: 'Who gets a place that frees up, and how they are told.',
        condition: agenda,
      },
      {
        // the one place to answer "can clients book this, with this person?"
        key: 'Online booking',
        label: 'Online booking',
        description:
          'What can be booked online and with whom, the booking page, the platforms.',
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
    description:
      'What the people you look after fill in, sign and see, and what their plans are written with.',
    items: [
      {
        // one builder: the forms to fill and sign, the sheets, the website's
        key: 'Forms',
        label: 'Forms',
        description:
          "The forms people fill and sign, the sheets you write, the website's forms.",
        condition: (c) =>
          c.puo('moduli_lead.gestisci') || c.puo('moduli.configura'),
      },
      {
        key: 'Consents',
        label: 'Consents',
        description: 'What people agree to, and the words they read.',
        condition: puo('consensi.configura'),
      },
      {
        // what the area tells outside it
        key: 'News in the client area',
        label: 'Client area',
        description:
          'The news their area sends: the email with its link, WhatsApp or SMS.',
        condition: (c) => c.puo('canali.configura') && c.puo('area.invita'),
      },
      {
        key: 'Libraries',
        label: 'Libraries',
        description: 'What plans are written with: exercises, foods.',
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
    description:
      'How a new request is followed: its stages, who takes it, how soon they answer.',
    items: [
      {
        key: 'Pipelines',
        label: 'Pipelines',
        description:
          'The stages a request goes through, until it is won or lost.',
        condition: puo('pipeline.configura'),
      },
      {
        // who takes a request, and how soon they answer it
        key: 'Assignment',
        label: 'Assignment',
        description: 'Who takes a new request, and how soon they answer.',
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
    description: "The centre's mailboxes and the emails you send often.",
    items: [
      {
        key: 'Accounts',
        label: 'Accounts',
        description:
          "The centre's mailboxes, and where the answers to {brand}'s emails go.",
        condition: puo('email.account_centro'),
      },
      {
        // everybody uses them from the composer; writing them is the manager's
        key: 'Templates',
        label: 'Templates',
        description: 'The emails you send often, ready to use.',
        condition: puo('modelli_messaggio.gestisci'),
      },
    ],
  },
  {
    // the same, for WhatsApp: the numbers, and the templates it may send
    // outside the 24 hours
    key: 'whatsapp',
    label: 'WhatsApp',
    description: "The centre's numbers and the messages WhatsApp has approved.",
    condition: (c) => c.whatsapp,
    items: [
      {
        key: 'WhatsApp',
        label: 'Numbers',
        description: "The centre's WhatsApp numbers.",
        title: 'WhatsApp',
        condition: puo('canali.configura'),
      },
      {
        key: 'WhatsApp Templates',
        label: 'Templates',
        description: 'The messages WhatsApp approved, to write after 24 hours.',
        title: 'WhatsApp Templates',
        condition: puo('modelli_messaggio.gestisci'),
      },
    ],
  },
  {
    // and for the phone: the lines, and what to say on a call
    key: 'phone',
    label: 'Phone',
    description: 'Calls from {brand} and what to say on them.',
    items: [
      {
        key: 'Telephony',
        label: 'Telephony',
        description: 'The lines {brand} calls and answers on.',
        // one's own line is for whoever calls, the centre's lines for whoever
        // sets them up: the others found a title over an empty page
        condition: (c) =>
          c.puo('telefono.chiama') || c.puo('telefono.configura'),
      },
      {
        key: 'Call Scripts',
        label: 'Call scripts',
        description: 'What to say on a call, step by step.',
        condition: puo('telefono.copioni_scrivi'),
      },
    ],
  },
  {
    key: 'marketing',
    label: 'Marketing',
    description: 'The website, the social posts and where people come from.',
    items: [
      {
        // only where Builder is installed: the capability needs it
        key: 'Website',
        label: 'Website',
        description: "The pages of the centre's website.",
        condition: puo('sito.gestisci'),
      },
      {
        // which profiles the planner publishes to: they come from Meta
        key: 'Social profiles',
        label: 'Social Planner',
        description: 'The pages and profiles the planner publishes to.',
        condition: puo('social.pubblica'),
      },
      {
        key: 'Tracking',
        label: 'Tracking',
        description:
          'Where people come from: visits, campaigns, tracked links.',
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
    description:
      'Who issues the invoices, what is billed, how they reach the tax system.',
    condition: puo('fatture.configura'),
    items: [
      // where to start: what is still missing, each row a click from the page
      // that fills it, then going live. The key stays: links are built on it
      {
        key: 'Provider connection',
        label: 'Test and go live',
        description:
          'Start here: what is still missing, a test invoice, then go live.',
      },
      // the company's own record has its tabs already (company, invoicing,
      // documents, transmission, healthcare): no second row over them
      {
        key: 'Issuing company',
        label: 'Issuing company',
        // the clinic says its Sistema TS credentials too (crm/clinica/parole.py)
        description: 'Who issues the invoices: details, tax regime, numbering.',
      },
      // a centre that invoices with Fatture in Cloud: its invoices are born there
      {
        key: 'Fatture in Cloud',
        label: 'Fatture in Cloud',
        description:
          'If the centre invoices with Fatture in Cloud: the invoices are born there.',
      },
      {
        key: 'Services & providers',
        label: 'Services & providers',
        description: 'What is billed, and who performs it.',
        tabs: [
          { key: 'Billable services', label: 'Billable services' },
          { key: 'Providers', label: 'Providers' },
        ],
      },
      // what a centre opens once a year, if ever: the switches over everything,
      // and the register the accountant confirms
      {
        key: 'Advanced invoicing',
        label: 'Advanced',
        description:
          'The switches over all invoicing, and what each qualification means for VAT.',
        tabs: [
          { key: 'Invoicing defaults', label: 'Options' },
          { key: 'Qualification register', label: 'Qualifications' },
        ],
      },
    ],
  },
  {
    // what is connected from outside, each with its own page
    key: 'integrations',
    label: 'Integrations',
    description:
      "What is connected from outside: Meta, the assistant, the agency's tools.",
    items: [
      {
        // one page with its own tabs, the connection and what it feeds
        key: 'Meta connection',
        label: 'Meta',
        description:
          'Facebook and Instagram: lead forms, ads, the quality of the leads.',
        aliases: ['Lead forms', 'Ad performance', 'Lead quality'],
        condition: puo('meta.gestisci'),
      },
      {
        // the centre's certificate and the time-stamping authority
        key: 'Seal and time stamp',
        label: 'Seal and time stamp',
        description:
          "The centre's certificate and the time stamps on signed PDFs.",
        condition: puo('tecnico.integrazioni'),
      },
      {
        // the register for the manager, the model for the agency
        key: 'Assistant',
        label: 'Assistant',
        description: 'Where the assistant runs, what it may do, what it did.',
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
