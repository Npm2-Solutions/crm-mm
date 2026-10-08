// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A quote in the area: what its card offers.
import { describe, expect, it } from 'vitest'
import { cosaOffre, indirizzoDelPdf } from '@/area/preventivi'

const proposto = { name: 'Q-1', can_answer: true, has_pdf: true }

describe('cosaOffre', () => {
  it('a proposed quote is answered by who answers, a code first', () => {
    expect(cosaOffre(proposto, { rispondono: true })).toEqual({
      risponde: true,
      pdf: true,
      codicePerFirmare: true,
      codicePerIlPdf: false,
    })
    expect(
      cosaOffre(proposto, { rispondono: true, verificato: true })
        .codicePerFirmare,
    ).toBe(false)
  })

  it('whoever only follows, the preview and a quote past its day do not answer', () => {
    expect(cosaOffre(proposto, { rispondono: false }).risponde).toBe(false)
    const vista = cosaOffre(proposto, { rispondono: true, anteprima: true })
    expect(vista.risponde).toBe(false)
    expect(vista.pdf).toBe(false)
    expect(
      cosaOffre({ ...proposto, can_answer: false }, { rispondono: true })
        .risponde,
    ).toBe(false)
  })

  it('health data asks a code for the PDF too', () => {
    const cura = { ...proposto, clinical: 1 }
    expect(cosaOffre(cura, {}).codicePerIlPdf).toBe(true)
    expect(cosaOffre(cura, { verificato: true }).codicePerIlPdf).toBe(false)
    expect(cosaOffre({ ...cura, has_pdf: false }, {}).pdf).toBe(false)
  })

  it('a hidden quote offers nothing', () => {
    expect(cosaOffre({ hidden: 1 }, { rispondono: true }).risponde).toBe(false)
    expect(cosaOffre(null).pdf).toBe(false)
  })
})

describe('indirizzoDelPdf', () => {
  it('names the person and the quote', () => {
    expect(indirizzoDelPdf('CRM-LEAD-1', 'Q 1')).toBe(
      '/api/method/crm.preventivi.firma.area_quote_pdf?person=CRM-LEAD-1&quote=Q+1',
    )
  })
})
