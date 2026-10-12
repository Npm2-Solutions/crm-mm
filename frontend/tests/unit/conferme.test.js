// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A confirmation with only its red button gets «Cancel» in front of it.
import { describe, expect, it } from 'vitest'
import { conAnnulla } from '@/utils/conferme'

const elimina = {
  label: 'Elimina',
  theme: 'red',
  variant: 'solid',
  onClick: () => {},
}

describe('conAnnulla', () => {
  it('puts «Cancel» before a red action alone', () => {
    expect(conAnnulla([elimina], 'Annulla')).toEqual([
      { label: 'Annulla' },
      elimina,
    ])
  })

  it('gives «Cancel» no onClick: frappe-ui closes the dialog on it', () => {
    const [annulla] = conAnnulla([elimina], 'Annulla')
    expect(annulla.onClick).toBeUndefined()
  })

  it('puts it before two red actions too', () => {
    const togli = { label: 'Togli', theme: 'red' }
    expect(conAnnulla([togli, elimina], 'Annulla')).toEqual([
      { label: 'Annulla' },
      togli,
      elimina,
    ])
  })

  it('leaves a dialog that already offers a way back', () => {
    const azioni = [{ label: 'Annullalo invece' }, elimina]
    expect(conAnnulla(azioni, 'Annulla')).toBe(azioni)
  })

  it('leaves a confirmation that is not red', () => {
    const azioni = [{ label: 'Rinnova', variant: 'solid' }]
    expect(conAnnulla(azioni, 'Annulla')).toBe(azioni)
  })

  it('leaves a dialog without actions as it is', () => {
    expect(conAnnulla(undefined, 'Annulla')).toBeUndefined()
    expect(conAnnulla([], 'Annulla')).toEqual([])
  })
})
