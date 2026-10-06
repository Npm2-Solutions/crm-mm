// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { describe, expect, it } from 'vitest'
import {
  categoria,
  categorie,
  lineaDelNumero,
  modelliDelNumero,
  numeroIniziale,
  parolePulsanti,
  stato,
  tipiDiPulsante,
} from '@/utils/modelliWhatsApp'

describe('a WhatsApp template in words', () => {
  it('names the category Meta files it under, with when it is the one', () => {
    expect(categoria('MARKETING').label).toBe('Marketing')
    expect(categoria('UTILITY').label).toBe('Utility')
    expect(categoria('UTILITY').description).toMatch(/asked for or booked/)
    expect(categoria('AUTHENTICATION').description).toMatch(/code to sign in/)
  })

  it('keeps the order the server gives and the stored value', () => {
    expect(categorie(['UTILITY', 'MARKETING'])).toEqual([
      { value: 'UTILITY', label: 'Utility' },
      { value: 'MARKETING', label: 'Marketing' },
    ])
  })

  it('reads a review state in capitals or as a word', () => {
    expect(stato('APPROVED')).toEqual({ label: 'Approved', theme: 'green' })
    expect(stato('Approved')).toEqual({ label: 'Approved', theme: 'green' })
    expect(stato('PENDING')).toEqual({ label: 'In review', theme: 'orange' })
    expect(stato('REJECTED').theme).toBe('red')
  })

  it('passes the context to the translator', () => {
    const visti = []
    const t = (testo, argomenti, contesto) => {
      visti.push([testo, contesto])
      return testo
    }
    stato('PAUSED', t)
    categoria('UTILITY', t)
    expect(visti).toContainEqual(['Paused', 'WhatsApp template'])
    expect(visti).toContainEqual(['Utility', 'WhatsApp template'])
  })

  it('shows what it does not know as it is', () => {
    expect(stato('LIMIT_EXCEEDED')).toEqual({
      label: 'LIMIT_EXCEEDED',
      theme: 'gray',
    })
    expect(categoria(null)).toEqual({ label: '', description: '' })
  })
})

describe('the templates of a number', () => {
  const numeri = [
    {
      name: 'Centro',
      label: 'Centro',
      active: true,
      sends: false,
      shares: ['Bis'],
    },
    {
      name: 'Bis',
      label: 'Bis',
      active: true,
      sends: true,
      shares: ['Centro'],
    },
    { name: 'Studio', label: 'Studio', active: true, sends: false, shares: [] },
    {
      name: 'Vecchio',
      label: 'Vecchio',
      active: false,
      sends: false,
      shares: [],
    },
  ]

  it('opens on the number that sends, else the first in use', () => {
    expect(numeroIniziale(numeri)).toBe('Bis')
    expect(numeroIniziale(numeri.map((n) => ({ ...n, sends: false })))).toBe(
      'Centro',
    )
    expect(numeroIniziale([{ name: 'Vecchio', active: false }])).toBe('Vecchio')
    expect(numeroIniziale([])).toBe(null)
  })

  it('shows the ones its account can send', () => {
    const modelli = [
      { name: 'a', numbers: ['Centro', 'Bis'] },
      { name: 'b', numbers: ['Studio'] },
      { name: 'c' },
    ]
    expect(modelliDelNumero(modelli, 'Bis').map((m) => m.name)).toEqual(['a'])
    expect(modelliDelNumero(modelli, 'Studio').map((m) => m.name)).toEqual([
      'b',
    ])
    expect(modelliDelNumero(modelli, null)).toHaveLength(3)
  })

  it('says whether its templates can be sent now', () => {
    expect(lineaDelNumero(numeri[1], numeri)).toBe(
      'Messages go out from this number. It shares its templates with Centro.',
    )
    expect(lineaDelNumero(numeri[0], numeri)).toBe(
      'Messages go out from Bis, which can send these templates too.',
    )
    expect(lineaDelNumero(numeri[2], numeri)).toMatch(
      /^Messages go out from Bis: these templates can be sent once/,
    )
    expect(lineaDelNumero(numeri[3], numeri)).toBe(
      'Not in use: its templates can no longer be sent.',
    )
    expect(lineaDelNumero(null, numeri)).toBe('')
  })

  it('names its buttons by their words, the kinds in the context', () => {
    expect(
      parolePulsanti([
        { type: 'QUICK_REPLY', text: 'Confermo' },
        { type: 'QUICK_REPLY', text: '' },
        { type: 'URL', text: 'Gestisci' },
      ]),
    ).toBe('«Confermo» · «Gestisci»')
    const visti = []
    tipiDiPulsante((testo, argomenti, contesto) => {
      visti.push(contesto)
      return testo
    })
    expect(new Set(visti)).toEqual(new Set(['WhatsApp button']))
    expect(tipiDiPulsante().map((tipo) => tipo.value)).toEqual([
      'QUICK_REPLY',
      'URL',
      'PHONE_NUMBER',
    ])
  })

  it('reads a template Meta no longer has', () => {
    expect(stato('DELETED')).toEqual({
      label: 'Deleted on Meta',
      theme: 'gray',
    })
    expect(stato('PENDING_DELETION').label).toBe('Deleted on Meta')
  })
})
