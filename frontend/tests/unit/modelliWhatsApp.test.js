// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import { describe, expect, it } from 'vitest'
import { categoria, categorie, stato } from '@/utils/modelliWhatsApp'

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
