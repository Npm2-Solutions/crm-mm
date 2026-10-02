// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  ALTRO,
  FORNITORI,
  daCorreggere,
  fornitore,
  iniziale,
  interruttori,
  rispostaDaSalvare,
  risposteSenzaCasella,
  sceltaDelleRisposte,
  segni,
} from '@/utils/caselle'

describe('the providers', () => {
  it('are the server’s, each with what it asks of the password', () => {
    expect(FORNITORI.map((f) => f.chiave)).toEqual([
      'gmail',
      'aruba',
      'libero',
      'virgilio',
      'tiscali',
      'icloud',
      'yahoo',
    ])
    for (const f of FORNITORI) expect(f.nota).toBeTruthy()
    expect(fornitore('gmail').link).toContain('support.google.com')
    expect(fornitore('outlook')).toBeNull()
  })

  it('without a picture, a letter', () => {
    expect(iniziale('Aruba')).toBe('A')
    expect(iniziale(' libero')).toBe('L')
    expect(iniziale('')).toBe('@')
  })
})

describe('a mailbox in words', () => {
  const segreteria = {
    enable_incoming: 1,
    enable_outgoing: 1,
    default_incoming: 1,
    default_outgoing: 1,
    editable: true,
  }

  it('says what it does', () => {
    expect(segni(segreteria, true)).toEqual([
      'Main mailbox',
      'Receives',
      'Sends',
    ])
    // without the agency's service, the centre's mailbox sends DottorCloud's emails
    expect(segni(segreteria, false)).toEqual([
      'Main mailbox',
      'Receives',
      'Sends',
      "Sends {brand}'s emails",
    ])
  })

  it('and whose it is', () => {
    expect(
      segni({ enable_incoming: 0, enable_outgoing: 0, editable: false }),
    ).toEqual(['Not in use', 'Set up by the agency'])
    expect(segni(null)).toEqual([])
  })
})

describe('the switches', () => {
  const campi = (stato, servizio) =>
    interruttori(stato, servizio).map((i) => i.campo)

  it('what is made of who writes only where the mailbox receives', () => {
    expect(campi({ enable_incoming: 0, enable_outgoing: 1 }, true)).toEqual([
      'enable_incoming',
      'enable_outgoing',
    ])
    expect(campi({ enable_incoming: 1, enable_outgoing: 1 }, true)).toEqual([
      'enable_incoming',
      'create_lead_from_incoming_email',
      'default_incoming',
      'enable_outgoing',
    ])
  })

  it('sending DottorCloud’s emails only where the agency’s service does not', () => {
    expect(campi({ enable_outgoing: 1 }, false)).toContain('default_outgoing')
    expect(campi({ enable_outgoing: 1 }, true)).not.toContain(
      'default_outgoing',
    )
    expect(campi({ enable_outgoing: 0 }, false)).not.toContain(
      'default_outgoing',
    )
  })
})

describe('what stops saving a mailbox', () => {
  const nuova = {
    provider: 'aruba',
    email_id: 'segreteria@aurora.it',
    password: 'x',
    enable_incoming: true,
    enable_outgoing: true,
  }

  it('a provider, an address, a password, something to do', () => {
    expect(daCorreggere(nuova)).toBe('')
    expect(daCorreggere({ ...nuova, provider: '' })).toBe(
      'Choose where the mailbox is.',
    )
    expect(daCorreggere({ ...nuova, email_id: ' ' })).toBe('Write the address.')
    expect(daCorreggere({ ...nuova, email_id: 'segreteria' })).toBe(
      'The address is not an email address.',
    )
    expect(daCorreggere({ ...nuova, password: '' })).toBe('Write the password.')
    expect(
      daCorreggere({
        ...nuova,
        enable_incoming: false,
        enable_outgoing: false,
      }),
    ).toBe('A mailbox receives, sends, or both.')
  })

  it('a mailbox already there keeps its password', () => {
    expect(daCorreggere({ ...nuova, password: '' }, true)).toBe('')
  })
})

describe('where the answers go', () => {
  const stato = {
    active: true,
    reply_to: 'segreteria@aurora.it',
    reply_to_chosen: null,
    reply_to_main: 'segreteria@aurora.it',
    inboxes: ['segreteria@aurora.it', 'info@aurora.it'],
  }

  it('the main mailbox, one the centre reads, or one typed', () => {
    expect(sceltaDelleRisposte(stato)).toEqual({ scelta: '', altro: '' })
    expect(
      sceltaDelleRisposte({ ...stato, reply_to_chosen: 'info@aurora.it' }),
    ).toEqual({ scelta: 'info@aurora.it', altro: '' })
    expect(
      sceltaDelleRisposte({ ...stato, reply_to_chosen: 'dott@studio.it' }),
    ).toEqual({ scelta: ALTRO, altro: 'dott@studio.it' })
  })

  it('saved as an address, or nothing for the main mailbox', () => {
    expect(rispostaDaSalvare('', '')).toBe('')
    expect(rispostaDaSalvare('info@aurora.it', 'x')).toBe('info@aurora.it')
    expect(rispostaDaSalvare(ALTRO, ' dott@studio.it ')).toBe('dott@studio.it')
  })

  it('nobody reads them: said', () => {
    expect(risposteSenzaCasella(stato)).toBe(false)
    expect(risposteSenzaCasella({ ...stato, reply_to: null })).toBe(true)
    // without the service, the centre's own mailbox sends and receives them
    expect(risposteSenzaCasella({ active: false, reply_to: null })).toBe(false)
  })
})
