// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  cosaMancaPerMandare,
  problemaDelFile,
  statoDellaRichiesta,
} from '@/utils/numeri'
import {
  moduloDi,
  nomeDellOperatore,
  rigaDellOperatore,
} from '@/utils/operatori'
import {
  chiPaga,
  cosaManca,
  inArrivo,
  pubblicaValida,
  pulito,
  quantiNellaVoce,
  righeDelControllo,
  scadeIlGettone,
} from '@/utils/telnyx'

// The centre's Telnyx account (doc 64): the page checks here what the server
// checks in crm/telephony/telnyx/regole.py, before Telnyx is asked.

const CHIAVE = 'KEY0123456789ABCDEF0123_abcdEFGH-12'
// 32 bytes in base64, as the portal shows the account's public key
const PUBBLICA = 'A'.repeat(43) + '='

describe('the two codes', () => {
  it('taken as copied, spaces and lines left out', () => {
    expect(pulito(`  ${CHIAVE}\n`)).toBe(CHIAVE)
    expect(pulito('AAAA AAAA\nAAAA')).toBe('AAAAAAAAAAAA')
    expect(pulito(null)).toBe('')
  })

  it('a public key is 32 bytes in base64', () => {
    expect(pubblicaValida(PUBBLICA)).toBe(true)
    expect(
      pubblicaValida(` ${PUBBLICA.slice(0, 20)}\n${PUBBLICA.slice(20)}`),
    ).toBe(true)
    // 16 bytes, a key of another kind
    expect(pubblicaValida('A'.repeat(22) + '==')).toBe(false)
    expect(pubblicaValida('not base64!')).toBe(false)
  })

  it('says what is missing, one thing at a time', () => {
    expect(cosaManca('', PUBBLICA)).toBe('Paste the API key.')
    expect(cosaManca('abc', PUBBLICA)).toContain('starts with KEY')
    expect(cosaManca(CHIAVE, '')).toBe('Paste the public key.')
    expect(cosaManca(CHIAVE, 'xyz')).toContain('44 letters')
    expect(cosaManca(CHIAVE, PUBBLICA)).toBe('')
  })

  it('who pays, by whose account it is', () => {
    expect(chiPaga('Centre')).toBe('The centre, to Telnyx')
    expect(chiPaga('Agency')).toBe('The agency')
    expect(chiPaga('')).toBe('')
  })
})

describe('what «Check» found', () => {
  it('nothing to say on a failed check', () => {
    expect(righeDelControllo({ ok: false })).toEqual([])
  })

  it('everything in place', () => {
    expect(righeDelControllo({ ok: true })).toEqual([
      ['Everything is in place.', 0],
    ])
  })

  it('numbers put back, numbers that stay elsewhere', () => {
    expect(
      righeDelControllo({ ok: true, repaired: ['+3902'], trunked: [] }),
    ).toEqual([
      ['One number changed in the portal is pointed at {brand} again.', 1],
    ])
    const righe = righeDelControllo({
      ok: true,
      repaired: ['+3902', '+3906'],
      trunked: ['+3911', '+3912', '+3913'],
    })
    expect(righe.map((r) => r[1])).toEqual([2, 3])
    expect(righe[1][0]).toContain('stay as they are')
  })
})

describe('this month, by kind', () => {
  it('calls with their minutes where Telnyx counted them', () => {
    expect(quantiNellaVoce({ key: 'calls', count: 4, minutes: 12 })).toEqual([
      '{0} calls · {1} min',
      [4, 12],
    ])
    expect(quantiNellaVoce({ key: 'calls', count: 1, minutes: 3 })).toEqual([
      'One call · {0} min',
      [3],
    ])
    // no minutes in the report: the calls alone, never «0 min»
    expect(quantiNellaVoce({ key: 'calls', count: 4, minutes: null })).toEqual([
      '{0} calls',
      [4],
    ])
  })

  it('SMS and numbers; nothing for none', () => {
    expect(quantiNellaVoce({ key: 'sms', count: 20 })).toEqual([
      '{0} SMS',
      [20],
    ])
    expect(quantiNellaVoce({ key: 'numbers', count: 1 })).toEqual([
      'One number',
      [],
    ])
    expect(quantiNellaVoce({ key: 'recordings', count: 3 })).toBeNull()
    expect(quantiNellaVoce({ key: 'sms', count: 0 })).toBeNull()
  })
})

describe('the browser’s phone', () => {
  it('a call ringing the browser', () => {
    expect(inArrivo({ direction: 'inbound', state: 'ringing' })).toBe(true)
    expect(inArrivo({ direction: 'inbound', state: 'active' })).toBe(false)
    expect(inArrivo({ direction: 'outbound', state: 'ringing' })).toBe(false)
    expect(inArrivo(null)).toBe(false)
  })

  it('the token about to end', () => {
    expect(scadeIlGettone({ warning: { code: 34001 } })).toBe(true)
    expect(scadeIlGettone({ warning: { code: '34001' } })).toBe(true)
    expect(scadeIlGettone({ warning: { code: 33002 } })).toBe(false)
    expect(scadeIlGettone({})).toBe(false)
  })
})

describe('the carriers, one at a time', () => {
  it('each with its calls on the server', () => {
    expect(moduloDi('telnyx', 'numeri')).toBe('crm.telephony.telnyx.numeri')
    expect(moduloDi('twilio', 'verificati')).toBe('crm.telephony.verificati')
    // an unknown name is Twilio's, as before there were two
    expect(moduloDi('', 'trasloco')).toBe('crm.telephony.trasloco')
  })

  it('named as people read them', () => {
    expect(nomeDellOperatore('telnyx')).toBe('Telnyx')
    expect(nomeDellOperatore('altro')).toBe('')
  })

  it('what the telephony page says of each', () => {
    expect(rigaDellOperatore('telnyx', '', true)).toEqual([
      'Connected: calls and messages go through {0}.',
      ['Telnyx'],
    ])
    expect(rigaDellOperatore('telnyx', 'Twilio')).toEqual([
      'The phone goes through {0} now: disconnect it to use {1} instead.',
      ['Twilio', 'Telnyx'],
    ])
    expect(rigaDellOperatore('twilio')[1]).toEqual(['Twilio'])
  })
})

describe('a new number from Telnyx', () => {
  const REGOLE = { extensions: ['pdf'], max_mb: 20 }

  it('only a PDF, up to 20 MB', () => {
    expect(problemaDelFile('visura.pdf', 1024, REGOLE)).toBe('')
    expect(problemaDelFile('foto.png', 1024, REGOLE)).toEqual([
      'The document has to be a PDF.',
      [],
    ])
    expect(problemaDelFile('visura.pdf', 21 * 1024 * 1024, REGOLE)).toEqual([
      'The document is larger than {0} MB: the carrier does not take it.',
      [20],
    ])
  })

  it('Twilio’s rules where the server says none', () => {
    expect(problemaDelFile('foto.png', 1024)).toBe('')
    expect(problemaDelFile('foto.png', 6 * 1024 * 1024)).toEqual([
      'The document is larger than {0} MB: the carrier does not take it.',
      [5],
    ])
  })

  it('no email asked when the carrier writes to nobody', () => {
    expect(cosaMancaPerMandare({ chiedeEmail: false })).toBe('')
    expect(cosaMancaPerMandare({})).toContain('email')
  })

  it('in review, named Telnyx', () => {
    const stato = statoDellaRichiesta({ status: 'In review' }, 'Telnyx')
    expect(stato.label).toBe('In review')
    expect(stato.riga[1]).toEqual(['Telnyx'])
  })
})
