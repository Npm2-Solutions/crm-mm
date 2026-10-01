// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  MENU,
  PREFERITI_DEL_TELEFONO,
  barraDelTelefono,
  menuDi,
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
  it("gives the manager the centre's whole work, in four groups", () => {
    expect(parole(menuDi(sessione('manager')))).toEqual([
      [
        '-',
        [
          'Dashboard',
          'Today',
          'Agenda',
          'Waiting list',
          'People',
          'Conversations',
          'Tasks',
          'Invoices',
        ],
      ],
      ['Archive', ['Organizations', 'Notes']],
      ['Marketing', ['Deals', 'Automations', 'Social Planner', 'Site']],
      ['Phone', ['Call Logs', 'Dialer']],
    ])
  })

  it('gives the front desk its day, the people and the phone', () => {
    expect(parole(menuDi(sessione('segreteria')))).toEqual([
      [
        '-',
        [
          'Dashboard',
          'Today',
          'Agenda',
          'Waiting list',
          'People',
          'Conversations',
          'Tasks',
          'Invoices',
        ],
      ],
      ['Archive', ['Organizations', 'Notes']],
      ['Marketing', ['Deals']],
      ['Phone', ['Call Logs', 'Dialer']],
    ])
  })

  it('gives a practitioner their day and their people, not the register of invoices', () => {
    const menu = parole(menuDi(sessione('operatore')))
    expect(menu[0]).toEqual([
      '-',
      [
        'Dashboard',
        'Today',
        'Agenda',
        'Waiting list',
        'People',
        'Conversations',
        'Tasks',
      ],
    ])
    expect(menu[1]).toEqual(['Archive', ['Organizations', 'Notes']])
  })

  it('gives marketing its group and the people, masked, nothing of the day', () => {
    expect(parole(menuDi(sessione('marketing')))).toEqual([
      ['-', ['Dashboard', 'People', 'Tasks']],
      ['Archive', ['Organizations']],
      ['Marketing', ['Deals', 'Automations', 'Social Planner', 'Site']],
    ])
  })

  it('gives accounting the invoices and what they come from', () => {
    expect(parole(menuDi(sessione('amministrazione')))).toEqual([
      ['-', ['Dashboard', 'Agenda', 'People', 'Tasks', 'Invoices']],
      ['Archive', ['Organizations']],
      ['Marketing', ['Deals']],
    ])
  })

  it('gives the medical director the agenda and the patients', () => {
    expect(parole(menuDi(sessione('direzione')))).toEqual([
      ['-', ['Dashboard', 'Agenda', 'People', 'Tasks']],
      ['Archive', ['Organizations']],
    ])
  })

  it('leaves the dialer out where no telephony is on', () => {
    const menu = parole(menuDi(sessione('segreteria', { telefono: false })))
    expect(menu.at(-1)).toEqual(['Phone', ['Call Logs']])
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

  it('puts the day, the people and the conversations under the thumb', () => {
    expect(barra('manager')).toEqual([
      'Today',
      'Calendar',
      'Leads',
      'Conversations',
    ])
    expect(barra('segreteria')).toEqual([
      'Today',
      'Calendar',
      'Leads',
      'Conversations',
    ])
    expect(barra('operatore')).toEqual([
      'Today',
      'Calendar',
      'Leads',
      'Conversations',
    ])
  })

  it('fills the places a level does not have with what it opens', () => {
    expect(barra('amministrazione')).toEqual([
      'Calendar',
      'Leads',
      'Invoices',
      'Dashboard',
    ])
    expect(barra('marketing')).toEqual([
      'Leads',
      'Dashboard',
      'Tasks',
      'Organizations',
    ])
  })

  it('never has more than four places', () => {
    for (const livello of Object.keys(LIVELLI)) {
      expect(barra(livello).length).toBeLessThanOrEqual(4)
    }
    expect(PREFERITI_DEL_TELEFONO[0]).toBe('Today')
  })
})
