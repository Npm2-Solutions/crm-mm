// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { dividi, doveSiImposta } from '@/utils/funzionalita'
import { menuDi } from '@/utils/impostazioni'

// a manager with the clinic on, and what they do not see when told
function menu({ non = [] } = {}) {
  return menuDi({
    puo: (nome) => !non.includes(nome),
    ambito: (nome) => (non.includes(nome) ? null : 'centro'),
    whatsapp: true,
    verticale: 'clinica',
  })
}

describe('the features page', () => {
  it('puts what the product comprises first, then the extras, in order', () => {
    const moduli = [
      { key: 'base', included: true },
      { key: 'clinica', included: true },
      { key: 'marketing', included: false },
      { key: 'area', included: true },
      { key: 'assistente', included: false },
    ]
    const { compresi, extra } = dividi(moduli)
    expect(compresi.map((m) => m.key)).toEqual(['base', 'clinica', 'area'])
    expect(extra.map((m) => m.key)).toEqual(['marketing', 'assistente'])
    expect(dividi()).toEqual({ compresi: [], extra: [] })
  })

  it('links each module to the entries it is set up from', () => {
    const link = doveSiImposta(menu(), [
      'Services',
      'Hours & shifts',
      'Online booking',
      'Users',
    ])
    expect(link.map((l) => [l.page, l.label, l.tab, l.group])).toEqual([
      ['Services', 'Services', null, 'Agenda'],
      ['Hours & shifts', 'Hours & shifts', null, 'Agenda'],
      ['Online booking', 'Online booking', null, 'Agenda'],
      ['Users', 'Users', null, 'The centre'],
    ])
  })

  it("names the tab when the page is one of an entry's tabs", () => {
    expect(doveSiImposta(menu(), ['Price Lists'])).toEqual([
      {
        page: 'Price Lists',
        label: 'Services',
        tab: 'Price lists',
        group: 'Agenda',
      },
    ])
  })

  it("reads the names the menu gives: the entry, not the page's key", () => {
    const link = doveSiImposta(menu(), [
      'Meta connection',
      'Social profiles',
      'Call Scripts',
      'News in the client area',
    ])
    expect(link.map((l) => l.label)).toEqual([
      'Meta',
      'Social Planner',
      'Call scripts',
      'Client area',
    ])
  })

  it('leaves out the pages one does not see, and those there are not', () => {
    const link = doveSiImposta(menu({ non: ['sito.gestisci'] }), [
      'Tracking',
      'Website',
      'No such page',
    ])
    expect(link.map((l) => l.page)).toEqual(['Tracking'])
  })

  it('links a page once', () => {
    expect(doveSiImposta(menu(), ['Telephony', 'Telephony'])).toHaveLength(1)
  })
})
