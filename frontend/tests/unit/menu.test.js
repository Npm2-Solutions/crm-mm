// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  ALTRE_PAGINE,
  MENU,
  PREFERITI_DEL_TELEFONO,
  barraDelTelefono,
  menuDi,
  nomeDellaPagina,
  paginaSorelle,
  SORELLE,
} from '@/utils/menu'

// what each level may open of the menu, as crm/permissions/catalogo.py gives it
// with every module of the plan on (`calcola`)
const LIVELLI = {
  segreteria: {
    'persone.vedi': 'centro',
    'trattative.vedi': 'centro',
    'conversazioni.usa': 'centro',
    'note.vedi': 'centro',
    'agenda.vedi': 'centro',
    'agenda.presenze': 'centro',
    'agenda.attese': 'centro',
    'dashboard.personali': 'centro',
    'telefono.chiama': 'centro',
    'telefono.registro': 'centro',
    'fatture.vedi': 'centro',
  },
  operatore: {
    'persone.vedi': 'suoi',
    'trattative.vedi': 'suoi',
    'conversazioni.usa': 'suoi',
    'note.vedi': 'suoi',
    'agenda.vedi': 'suoi',
    'agenda.presenze': 'suoi',
    'agenda.attese': 'suoi',
    'dashboard.personali': 'centro',
    'telefono.chiama': 'centro',
    'telefono.registro': 'suoi',
    'fatture.vedi': 'suoi',
  },
  manager: {
    'persone.vedi': 'centro',
    'trattative.vedi': 'centro',
    'conversazioni.usa': 'centro',
    'note.vedi': 'centro',
    'agenda.vedi': 'centro',
    'agenda.presenze': 'centro',
    'agenda.attese': 'centro',
    'dashboard.personali': 'centro',
    'dashboard.centro': 'centro',
    'telefono.chiama': 'centro',
    'telefono.registro': 'centro',
    'automazioni.vedi': 'centro',
    'social.bozze': 'centro',
    'social.pubblica': 'centro',
    'sito.gestisci': 'centro',
    'fatture.vedi': 'centro',
  },
  commerciale: {
    'persone.vedi': 'team',
    'trattative.vedi': 'team',
    'conversazioni.usa': 'team',
    'note.vedi': 'team',
    'agenda.vedi': 'libero_occupato',
    'agenda.attese': 'team',
    'dashboard.personali': 'centro',
    'telefono.chiama': 'centro',
    'telefono.registro': 'team',
    'automazioni.vedi': 'centro',
    'social.bozze': 'centro',
  },
  direzione: {
    'persone.vedi': 'centro',
    'agenda.vedi': 'centro',
    'dashboard.personali': 'centro',
  },
  marketing: {
    'persone.vedi': 'mascherato',
    'trattative.vedi': 'centro',
    'dashboard.personali': 'centro',
    'automazioni.vedi': 'centro',
    'social.bozze': 'centro',
    'social.pubblica': 'centro',
    'sito.gestisci': 'centro',
  },
  amministrazione: {
    'persone.vedi': 'centro',
    'trattative.vedi': 'centro',
    'agenda.vedi': 'centro',
    'dashboard.personali': 'centro',
    'fatture.vedi': 'centro',
  },
}

function sessione(livello, { telefono = true } = {}) {
  const capacita = LIVELLI[livello]
  return {
    puo: (nome) => nome in capacita,
    puoUno: (nomi) => nomi.some((nome) => nome in capacita),
    ambito: (nome) => capacita[nome] || null,
    telefono,
  }
}

// the menu as words: group label (or "-" for the day) and its entries
function parole(menu) {
  return menu.map((gruppo) => [
    gruppo.label || '-',
    gruppo.entries.map((voce) => voce.label),
  ])
}

describe('the main menu', () => {
  it("gives the manager the day's work in one group, then marketing", () => {
    expect(parole(menuDi(sessione('manager')))).toEqual([
      [
        '-',
        [
          'Agenda',
          'People',
          'Conversations',
          'Tasks',
          'Deals',
          'Invoices',
          'Dashboard',
        ],
      ],
      ['Marketing', ['Automations', 'Social Planner', 'Site']],
    ])
  })

  it('gives the front desk its day, the people and their deals', () => {
    expect(parole(menuDi(sessione('segreteria')))).toEqual([
      [
        '-',
        [
          'Agenda',
          'People',
          'Conversations',
          'Tasks',
          'Deals',
          'Invoices',
          'Dashboard',
        ],
      ],
    ])
  })

  it('gives a practitioner their day and their people, not the register of invoices', () => {
    expect(parole(menuDi(sessione('operatore')))).toEqual([
      [
        '-',
        ['Agenda', 'People', 'Conversations', 'Tasks', 'Deals', 'Dashboard'],
      ],
    ])
  })

  it('opens on the numbers where the day does not open on the reception desk', () => {
    expect(parole(menuDi(sessione('marketing')))).toEqual([
      ['-', ['Dashboard', 'People', 'Tasks', 'Deals']],
      ['Marketing', ['Automations', 'Social Planner', 'Site']],
    ])
    expect(parole(menuDi(sessione('amministrazione')))).toEqual([
      ['-', ['Dashboard', 'Agenda', 'People', 'Tasks', 'Deals', 'Invoices']],
    ])
    expect(parole(menuDi(sessione('direzione')))).toEqual([
      ['-', ['Dashboard', 'Agenda', 'People', 'Tasks']],
    ])
  })

  it('keeps the phone out of the menu: it is at the top of every page', () => {
    for (const livello of Object.keys(LIVELLI)) {
      const chiavi = menuDi(sessione(livello)).flatMap((gruppo) =>
        gruppo.entries.map((voce) => voce.key),
      )
      expect(chiavi).not.toContain('Dialer')
      expect(chiavi).not.toContain('Call Logs')
    }
  })

  it('has no entry for what lives inside another one', () => {
    const chiavi = MENU.flatMap((gruppo) => gruppo.entries.map((v) => v.key))
    for (const dentro of ['Organizations', 'Notes', 'Waiting List', 'Today'])
      expect(chiavi).not.toContain(dentro)
  })

  it('draws no group nobody sees', () => {
    const nessuno = {
      puo: () => false,
      puoUno: () => false,
      ambito: () => null,
      telefono: false,
    }
    expect(menuDi(nessuno)).toEqual([])
  })

  it('opens each page once, with an icon the sidebar knows', () => {
    const voci = MENU.flatMap((gruppo) => gruppo.entries)
    const chiavi = voci.map((voce) => voce.key)
    expect(new Set(chiavi).size).toBe(chiavi.length)
    const icone = fs.readFileSync(
      path.resolve(import.meta.dirname, '../../src/components/Icons/menu.js'),
      'utf8',
    )
    for (const voce of voci) {
      expect(icone, voce.icon).toMatch(new RegExp(`^\\s*${voce.icon}:`, 'm'))
    }
  })

  it('names pages the router has', () => {
    const router = fs.readFileSync(
      path.resolve(import.meta.dirname, '../../src/router.js'),
      'utf8',
    )
    for (const voce of MENU.flatMap((gruppo) => gruppo.entries)) {
      expect(router, voce.key).toContain(`name: '${voce.key}'`)
    }
  })
})

describe("the phone's bar", () => {
  const barra = (livello, opzioni) =>
    barraDelTelefono(menuDi(sessione(livello, opzioni))).map((voce) => voce.key)

  it('puts the agenda, the people and the conversations under the thumb', () => {
    // the reception desk is in the agenda: its place goes to the invoices, or
    // to what is left to do where the level has no register of invoices
    expect(barra('manager')).toEqual([
      'Calendar',
      'Leads',
      'Conversations',
      'Invoices',
    ])
    expect(barra('segreteria')).toEqual([
      'Calendar',
      'Leads',
      'Conversations',
      'Invoices',
    ])
    expect(barra('operatore')).toEqual([
      'Calendar',
      'Leads',
      'Conversations',
      'Tasks',
    ])
  })

  it('fills the places a level does not have with what it opens', () => {
    expect(barra('amministrazione')).toEqual([
      'Calendar',
      'Leads',
      'Invoices',
      'Dashboard',
    ])
    expect(barra('marketing')).toEqual(['Leads', 'Dashboard', 'Tasks', 'Deals'])
  })

  it('never has more than four places', () => {
    for (const livello of Object.keys(LIVELLI)) {
      expect(barra(livello).length).toBeLessThanOrEqual(4)
    }
    expect(PREFERITI_DEL_TELEFONO[0]).toBe('Calendar')
    expect(PREFERITI_DEL_TELEFONO).not.toContain('Today')
  })
})

describe('the pages that live together', () => {
  const chiavi = (pagina, livello) =>
    paginaSorelle(pagina, sessione(livello)).map((p) => p.key)

  it('puts the companies beside the people, the notes beside the tasks', () => {
    expect(chiavi('Leads', 'manager')).toEqual(['Leads', 'Organizations'])
    expect(chiavi('Organizations', 'manager')).toEqual([
      'Leads',
      'Organizations',
    ])
    expect(chiavi('Notes', 'segreteria')).toEqual(['Tasks', 'Notes'])
  })

  it('leaves out what the level does not open: no switch of one', () => {
    expect(chiavi('Tasks', 'marketing')).toEqual(['Tasks'])
    expect(chiavi('Tasks', 'direzione')).toEqual(['Tasks'])
  })

  it('is nothing for a page that lives alone', () => {
    expect(chiavi('Invoices', 'manager')).toEqual([])
  })

  it('names pages the router has', () => {
    const router = fs.readFileSync(
      path.resolve(import.meta.dirname, '../../src/router.js'),
      'utf8',
    )
    for (const pagine of SORELLE)
      for (const pagina of pagine)
        expect(router, pagina.key).toContain(`name: '${pagina.key}'`)
  })
})

describe("a page's name, for its tab", () => {
  it('says the menu’s words, never the route’s', () => {
    expect(nomeDellaPagina('Leads')).toBe('People')
    expect(nomeDellaPagina('Calendar')).toBe('Agenda')
    expect(nomeDellaPagina('Waiting List')).toBe('Waiting list')
    expect(nomeDellaPagina('Organizations')).toBe('Organizations')
    expect(nomeDellaPagina('Call Logs')).toBe('Calls')
    expect(nomeDellaPagina('Lead')).toBe('People')
  })

  it('is nothing for a page with no name', () => {
    expect(nomeDellaPagina('Home')).toBe('')
    expect(nomeDellaPagina(undefined)).toBe('')
  })

  it('names pages the router has', () => {
    const router = fs.readFileSync(
      path.resolve(import.meta.dirname, '../../src/router.js'),
      'utf8',
    )
    for (const pagina of Object.keys(ALTRE_PAGINE))
      expect(router, pagina).toContain(`name: '${pagina}'`)
  })
})
