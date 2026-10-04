// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Where a linked document opens from the delete dialog (src/utils/collegati.js)
import { indirizzoDelCollegato } from '@/utils/collegati'

const di = (reference_doctype, reference_docname = 'X-1') => ({
  reference_doctype,
  reference_docname,
})

describe('indirizzoDelCollegato', () => {
  it('opens what has a page of its own in DottorCloud', () => {
    expect(indirizzoDelCollegato(di('CRM Deal', 'CRM-DEAL-2026-00033'))).toBe(
      '/crm/deals/CRM-DEAL-2026-00033',
    )
    expect(indirizzoDelCollegato(di('CRM Lead'))).toBe('/crm/leads/X-1')
    expect(indirizzoDelCollegato(di('Contact', 'Anna Bianchi'))).toBe(
      '/crm/contacts/Anna%20Bianchi',
    )
    expect(indirizzoDelCollegato(di('CRM Organization'))).toBe(
      '/crm/organizations/X-1',
    )
    expect(indirizzoDelCollegato(di('CRM Appointment', 'APT-7'))).toBe(
      '/crm/calendar?appointment=APT-7',
    )
  })

  it('gives nothing where there is no page, never the Desk', () => {
    for (const doctype of [
      'CRM Task',
      'FCRM Note',
      'CRM Call Log',
      'CRM Notification',
      'CRM Automation Enrollment',
    ]) {
      expect(indirizzoDelCollegato(di(doctype)), doctype).toBeNull()
    }
    expect(indirizzoDelCollegato(di('CRM Deal', ''))).toBeNull()
    expect(indirizzoDelCollegato(null)).toBeNull()
  })
})
