// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  chiPaga,
  cosaManca,
  pulito,
  righeDelControllo,
  statoDelConto,
} from '@/utils/twilio'

// The centre's Twilio account (doc 52): the two codes are checked here as the
// server checks them, before anything is asked of Twilio.

const SID = 'AC' + '0123456789abcdef'.repeat(2)
const TOKEN = 'fedcba9876543210'.repeat(2)

describe('the two codes', () => {
  it('pass as the console gives them', () => {
    expect(cosaManca(SID, TOKEN)).toBe('')
  })

  it('do not count the spaces and lines copied around them', () => {
    expect(pulito(`  ${SID}\n`)).toBe(SID)
    expect(cosaManca(` ${SID} `, `\n${TOKEN} `)).toBe('')
  })

  it('say what is wrong before Twilio is asked', () => {
    expect(cosaManca('', TOKEN)).toBe('Paste the Account SID.')
    expect(cosaManca('SK' + SID.slice(2), TOKEN)).toContain('starts with AC')
    expect(cosaManca(SID.slice(0, -1), TOKEN)).toContain('starts with AC')
    expect(cosaManca(SID, '')).toBe('Paste the Auth Token.')
    expect(cosaManca(SID, TOKEN + '0')).toContain('32 letters and digits')
    expect(cosaManca(SID, 'z'.repeat(32))).toContain('32 letters and digits')
  })
})

describe('the connection in words', () => {
  it('says who pays', () => {
    expect(chiPaga('Centre')).toBe('The centre, to Twilio')
    expect(chiPaga('Agency')).toBe('The agency')
    expect(chiPaga('Manual')).toContain('by hand')
    expect(chiPaga('')).toBe('')
  })

  it('says how the account is', () => {
    expect(statoDelConto('active')).toBe('Active')
    expect(statoDelConto('suspended')).toBe('Suspended')
    expect(statoDelConto('mai visto')).toBe('')
  })

  it('says what «Check» found', () => {
    expect(righeDelControllo({ ok: false })).toEqual([])
    expect(righeDelControllo({ ok: true, repaired: [], trunked: [] })).toEqual([
      ['Everything is in place.', 0],
    ])
    const righe = righeDelControllo({
      ok: true,
      repaired: ['+393331234567', '+390612345678'],
      trunked: ['+390287654321'],
    })
    expect(righe[0]).toEqual([
      '{0} numbers changed in the console are pointed at {brand} again.',
      2,
    ])
    expect(righe[1][0]).toContain('One number goes to a SIP trunk')
  })
})
