// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { ultimaVisitaSu, vociDelleSchede } from '@/utils/cartella'

const records = [
  { name: 'R4', template: 'Fisio', docstatus: 0 },
  { name: 'R3', template: 'Fisio', docstatus: 1, addendum_to: 'R2' },
  { name: 'R2', template: 'Fisio', docstatus: 1 },
  { name: 'R1', template: 'Fisio', docstatus: 1 },
  { name: 'L1', template: null, docstatus: 1 },
]

describe('starting from the last visit', () => {
  it('is the newest signed visit on the same sheet, never a draft nor an addendum', () => {
    expect(ultimaVisitaSu(records, 'Fisio').name).toBe('R2')
    expect(ultimaVisitaSu(records, 'Dieta')).toBeNull()
    expect(ultimaVisitaSu(undefined, 'Fisio')).toBeNull()
  })

  it('is offered only after a sheet with one', () => {
    const fmt = (s, [x]) => s.replace('{0}', x)
    const voci = vociDelleSchede(
      [
        { name: 'Fisio', title: 'Fisioterapia' },
        { name: 'Dieta', title: 'Dietologia' },
      ],
      records,
      fmt,
    )
    expect(voci.map((v) => [v.label, v.fromLast])).toEqual([
      ['Fisioterapia', false],
      ['Fisioterapia: start from the last visit', true],
      ['Dietologia', false],
    ])
  })
})
