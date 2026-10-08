// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { MENU, menuDi, pagine, schedaDi, trova } from '@/utils/impostazioni'

// what each level may do, as crm/permissions/catalogo.py gives it with every
// module of the plan on (`calcola`)
const LIVELLI = {
  segreteria: {
    'agenda.turni': 'centro',
    'google_calendar.proprio': 'centro',
    'telefono.chiama': 'centro',
  },
  operatore: {
    'agenda.turni': 'suoi',
    'google_calendar.proprio': 'centro',
    'telefono.chiama': 'centro',
  },
  marketing: {
    'modelli_messaggio.gestisci': 'centro',
    'moduli_lead.gestisci': 'centro',
    'tracciamento.gestisci': 'centro',
    'google_calendar.proprio': 'centro',
    'social.pubblica': 'centro',
    'sito.gestisci': 'centro',
    'meta.gestisci': 'centro',
  },
  amministrazione: {
    'fatture.configura': 'centro',
    'google_calendar.proprio': 'centro',
  },
  direzione: {
    'moduli.configura': 'centro',
    'google_calendar.proprio': 'centro',
    'piani.librerie': 'centro',
    'area.invita': 'centro',
    'assistente.registro': 'centro',
    'assistente.registro_clinico': 'centro',
  },
}
const DEL_MANAGER = [
  'impostazioni.generali',
  'pipeline.configura',
  'telefono.chiama',
  'telefono.copioni_scrivi',
  'telefono.configura',
  'utenti.gestisci',
  'gerarchia.gestisci',
  'piano.vedi',
  'consensi.configura',
  'email.account_centro',
  'modelli_messaggio.gestisci',
  'canali.configura',
  'assegnazione.regole',
  'moduli_lead.gestisci',
  'moduli.configura',
  'tracciamento.gestisci',
  'fatture.configura',
  'agenda.configura',
  'agenda.turni',
  'prenotazione_online.configura',
  'piattaforme.configura',
  'google_calendar.proprio',
  'piani.librerie',
  'social.pubblica',
  'sito.gestisci',
  'meta.gestisci',
  'area.invita',
  'assistente.registro',
]
LIVELLI.manager = Object.fromEntries(DEL_MANAGER.map((c) => [c, 'centro']))
// the agency: what is technical too, and the clinical register without access
LIVELLI.agenzia = {
  ...LIVELLI.manager,
  'tecnico.predefiniti': 'centro',
  'tecnico.integrazioni': 'centro',
}

function sessione(livello, { whatsapp = true, verticale = 'clinica' } = {}) {
  const capacita = LIVELLI[livello]
  return {
    puo: (nome) => nome in capacita,
    ambito: (nome) => capacita[nome] || null,
    whatsapp,
    verticale,
  }
}

// the menu as one reads it: "Group: Entry [Tab · Tab], Entry"
function comeSiLegge(menu) {
  return menu.map(
    (gruppo) =>
      `${gruppo.label}: ` +
      gruppo.items
        .map((voce) =>
          voce.tabs?.length > 1
            ? `${voce.label} [${voce.tabs.map((s) => s.label).join(' · ')}]`
            : voce.label,
        )
        .join(', '),
  )
}

describe('the settings menu, by who reads it', () => {
  it('gives the manager every area of the centre, in eleven groups', () => {
    expect(comeSiLegge(menuDi(sessione('manager')))).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'The centre: General [Name & logo · Language & time · Conversations · Dashboard · Menu], Users [Users · Invite · Hierarchy], Features',
      'Agenda: Services [Services · Price lists · Subscriptions], Hours & shifts [Hours & rules · Team rota], Rooms & equipment, Agenda & reminders [Agenda · Appointment reminders], Waiting list, Online booking [Services & people · Page & rules · Platforms]',
      'Clients: Forms, Consents, Client area, Libraries [Exercises · Foods]',
      'Deals: Pipelines, Assignment [Rules · Response times]',
      'Email: Accounts, Templates',
      'WhatsApp: Numbers, Templates',
      'Phone: Telephony, Call scripts',
      'Marketing: Website, Social Planner, Tracking [Lead tracking · Tracked links]',
      'Invoicing: Test and go live, Issuing company, Fatture in Cloud, Services & providers [Billable services · Providers], Payments and reminders, Advanced [Options · Qualifications]',
      'Integrations: Meta, Assistant',
    ])
  })

  it('had 48 entries in sixteen groups: now 36 for 53 pages, none alone in its group', () => {
    const menu = menuDi(sessione('manager'))
    const voci = menu.flatMap((gruppo) => gruppo.items)
    expect(voci).toHaveLength(36)
    // every page is still there, as an entry or a tab, the notifications,
    // the centre's language and Fatture in Cloud
    expect(voci.flatMap((v) => v.tabs || [v])).toHaveLength(53)
    expect(menu.filter((gruppo) => gruppo.items.length === 1)).toEqual([])
  })

  it('adds the technical pages for the agency', () => {
    const menu = comeSiLegge(menuDi(sessione('agenzia')))
    expect(menu[1]).toBe(
      'The centre: General [Name & logo · Language & time · Conversations · Dashboard · Menu · Formats], Users [Users · Invite · Hierarchy], Features',
    )
    expect(menu.at(-1)).toBe(
      'Integrations: Meta, Seal and time stamp, Assistant',
    )
  })

  it('shows the front desk its own account, the team rota and the rooms', () => {
    expect(comeSiLegge(menuDi(sessione('segreteria')))).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'Agenda: Hours & shifts, Rooms & equipment',
      'Phone: Telephony',
    ])
  })

  it('shows a practitioner their shifts and nothing of the centre', () => {
    const menu = menuDi(sessione('operatore'))
    expect(comeSiLegge(menu)).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'Agenda: Hours & shifts',
      'Phone: Telephony',
    ])
    // one tab left: the entry is that page, without a bar of tabs
    const turni = menu[1].items[0]
    expect(turni.tabs.map((s) => s.key)).toEqual(['Team rota'])
  })

  it('shows marketing what it works with', () => {
    expect(comeSiLegge(menuDi(sessione('marketing')))).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'Clients: Forms',
      'Email: Templates',
      'WhatsApp: Templates',
      'Marketing: Website, Social Planner, Tracking [Lead tracking · Tracked links]',
      'Integrations: Meta',
    ])
  })

  it('shows accounting the invoicing, and the medical director the forms and the libraries', () => {
    expect(comeSiLegge(menuDi(sessione('amministrazione')))).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'Invoicing: Test and go live, Issuing company, Fatture in Cloud, Services & providers [Billable services · Providers], Payments and reminders, Advanced [Options · Qualifications]',
    ])
    expect(comeSiLegge(menuDi(sessione('direzione')))).toEqual([
      'Your account: Profile, Preferences, Notifications, Google Calendar',
      'Clients: Forms, Libraries [Exercises · Foods]',
      'Integrations: Assistant',
    ])
  })

  it('leaves WhatsApp out where the app is not installed, the foods where the clinic is off', () => {
    const menu = menuDi(
      sessione('manager', { whatsapp: false, verticale: null }),
    )
    expect(menu.map((gruppo) => gruppo.key)).not.toContain('whatsapp')
    const librerie = menu
      .flatMap((gruppo) => gruppo.items)
      .find((voce) => voce.key === 'Libraries')
    expect(librerie.tabs.map((s) => s.key)).toEqual(['Exercises'])
  })

  it('does not change the menu it is given', () => {
    const prima = JSON.stringify(MENU)
    menuDi(sessione('operatore'))
    expect(JSON.stringify(MENU)).toBe(prima)
  })
})

describe('a page asked for by its name', () => {
  const menu = menuDi(sessione('agenzia'))
  const dove = (nome, t) => {
    const trovato = trova(menu, nome, t)
    return trovato && [trovato.voce.key, trovato.scheda?.key || null]
  }

  it('opens what every old name of the settings opened, now on its tab', () => {
    // [the name a link or a button asks for, the entry, the tab]
    const nomi = [
      ['Profile', 'Profile', null],
      ['Preferences', 'Preferences', null],
      ['Notifications', 'Notifications', null],
      ['General', 'General settings', 'General'],
      ['Dashboard', 'General settings', 'Dashboard'],
      ['Defaults', 'General settings', 'Defaults'],
      ['Brand', 'General settings', 'Brand'],
      ['Home Actions', 'General settings', 'Home Actions'],
      ['Pipelines', 'Pipelines', null],
      ['Call Scripts', 'Call Scripts', null],
      ['Users', 'Users', 'Users'],
      ['Invite User', 'Users', 'Invite User'],
      ['Sales Hierarchy', 'Users', 'Sales Hierarchy'],
      ['Plan', 'Plan', null],
      ['Consents', 'Consents', null],
      ['Accounts', 'Accounts', null],
      ['Templates', 'Templates', null],
      ['WhatsApp', 'WhatsApp', null],
      ['WhatsApp Templates', 'WhatsApp Templates', null],
      ['Assignment Rules', 'Assignment', 'Assignment Rules'],
      ['SLA Policies', 'Assignment', 'SLA Policies'],
      ['Forms', 'Forms', null],
      ['Tracked Links', 'Tracking', 'Tracked Links'],
      ['Lead Tracking', 'Tracking', 'Lead Tracking'],
      ['Issuing company', 'Issuing company', null],
      [
        'Qualification register',
        'Advanced invoicing',
        'Qualification register',
      ],
      ['Billable services', 'Services & providers', 'Billable services'],
      ['Providers', 'Services & providers', 'Providers'],
      ['Provider connection', 'Provider connection', null],
      ['Invoicing defaults', 'Advanced invoicing', 'Invoicing defaults'],
      ['Payment reminders', 'Payment reminders', null],
      ['Services', 'Services', 'Services'],
      ['Team rota', 'Hours & shifts', 'Team rota'],
      ['Studio hours & rules', 'Hours & shifts', 'Studio hours & rules'],
      ['Rooms & Equipment', 'Rooms & Equipment', null],
      ['Price Lists', 'Services', 'Price Lists'],
      ['Waiting list', 'Waiting list', null],
      ['Subscriptions', 'Services', 'Subscriptions'],
      ['Calendar & reminders', 'Calendar & reminders', 'Calendar & reminders'],
      [
        'Appointment reminders',
        'Calendar & reminders',
        'Appointment reminders',
      ],
      ['Online booking', 'Online booking', 'Online booking'],
      ['Page & rules', 'Online booking', 'Page & rules'],
      ['Booking platforms', 'Online booking', 'Booking platforms'],
      ['Google Calendar', 'Google Calendar', null],
      ['Exercises', 'Libraries', 'Exercises'],
      ['Foods', 'Libraries', 'Foods'],
      ['Social profiles', 'Social profiles', null],
      ['Website', 'Website', null],
      ['Meta connection', 'Meta connection', null],
      ['Lead forms', 'Meta connection', null],
      ['Ad performance', 'Meta connection', null],
      ['Lead quality', 'Meta connection', null],
      ['Telephony', 'Telephony', null],
      ['News in the client area', 'News in the client area', null],
      ['Seal and time stamp', 'Seal and time stamp', null],
      ['Assistant', 'Assistant', null],
    ]
    for (const [nome, voce, scheda] of nomi)
      expect([nome, ...dove(nome)]).toEqual([nome, voce, scheda])
  })

  it('opens an entry on its first tab, from the menu', () => {
    expect(dove('General settings')).toEqual(['General settings', 'Brand'])
    expect(dove('Hours & shifts')).toEqual([
      'Hours & shifts',
      'Studio hours & rules',
    ])
    expect(dove('Services & providers')).toEqual([
      'Services & providers',
      'Billable services',
    ])
  })

  it('finds a page by the words it is shown with', () => {
    const t = (testo) =>
      ({ 'Rooms & equipment': 'Sale e attrezzature' })[testo] || testo
    expect(dove('Sale e attrezzature', t)).toEqual(['Rooms & Equipment', null])
    expect(dove('Hours & shifts', t)).toEqual([
      'Hours & shifts',
      'Studio hours & rules',
    ])
  })

  it('finds nothing for a page that is not there, or not for this person', () => {
    expect(trova(menu, 'Nowhere')).toBeNull()
    expect(trova(menu, '')).toBeNull()
    const operatore = menuDi(sessione('operatore'))
    expect(trova(operatore, 'Price Lists')).toBeNull()
    // the entry is there, with the one tab they may open
    expect(trova(operatore, 'Hours & shifts').scheda.key).toBe('Team rota')
  })

  it('takes the first tab for a name that is not one of them', () => {
    const voce = {
      key: 'x',
      tabs: [{ key: 'a' }, { key: 'b', aliases: ['c'] }],
    }
    expect(schedaDi(voce, 'b').key).toBe('b')
    expect(schedaDi(voce, 'c').key).toBe('b')
    expect(schedaDi(voce, 'x').key).toBe('a')
    expect(schedaDi({ key: 'y' }, 'y')).toBeNull()
  })
})

describe('the pages there are', () => {
  it('names each page once', () => {
    const tutte = pagine()
    expect(new Set(tutte).size).toBe(tutte.length)
    // the 51 pages there were, none lost, the notifications and one's email;
    // ERPNext gone (02/10/2026); the demo data (doc 53); the centre's language;
    // Fatture in Cloud (06/10/2026); the centre's data in and out (07/10/2026)
    expect(tutte).toHaveLength(58)
  })

  it('gives every group, entry and tab a label', () => {
    for (const gruppo of MENU) {
      expect(gruppo.label).toBeTruthy()
      for (const voce of gruppo.items) {
        expect(voce.label).toBeTruthy()
        for (const scheda of voce.tabs || []) expect(scheda.label).toBeTruthy()
      }
    }
  })
})

describe('what Settings.vue draws them with', () => {
  // the modal names each page's component and each category's icon by its key:
  // one forgotten, and the page is blank, or the category has no icon
  const vue = fs.readFileSync(
    path.resolve(
      import.meta.dirname,
      '../../src/components/Settings/Settings.vue',
    ),
    'utf8',
  )
  const blocco = (nome) => vue.split(`const ${nome} = {`)[1].split('\n}\n')[0]
  // `Users,` as well as `'Price Lists': PriceListsSettings,`
  const ha = (testo, chiave) => {
    const nome = chiave.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return new RegExp(`^\\s*(${nome}|'${nome}')\\s*[:,]`, 'm').test(testo)
  }

  it('has a component for every page', () => {
    const pagineVue = blocco('PAGINE')
    for (const chiave of pagine())
      expect([chiave, ha(pagineVue, chiave)]).toEqual([chiave, true])
  })

  it('has an icon for every category: the categories carry them, not the entries', () => {
    const icone = blocco('ICONE')
    for (const gruppo of MENU)
      expect([gruppo.key, ha(icone, gruppo.key)]).toEqual([gruppo.key, true])
  })
})

describe('what the settings explain', () => {
  // a category's page lists its entries, each with a line on what one sets up
  // there: none goes without
  it('says what each category and each entry is for', () => {
    for (const gruppo of MENU) {
      expect([gruppo.key, Boolean(gruppo.description)]).toEqual([
        gruppo.key,
        true,
      ])
      for (const voce of gruppo.items)
        expect([voce.key, Boolean(voce.description)]).toEqual([voce.key, true])
    }
  })

  it('keeps it to one line a person reads at a glance', () => {
    for (const cosa of MENU.flatMap((gruppo) => [gruppo, ...gruppo.items]))
      expect([cosa.key, cosa.description.length <= 100]).toEqual([
        cosa.key,
        true,
      ])
  })
})
