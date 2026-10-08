// Copyright (c) 2026, NPM2 Solutions Srl and contributors
import {
  canali,
  fonteDellaLista,
  quantiSaltati,
  righeDeiSalti,
  senzaRecapito,
  vieDellaCampagna,
} from '@/utils/campagne'

describe('a campaign in words', () => {
  it('reads the ways it writes by, as the server does', () => {
    const passi = [
      { type: 'add_tag', tag: 'x' },
      {
        type: 'if_else',
        branches: [{ steps: [{ type: 'send_sms', message: 'ciao' }] }],
        else_steps: [{ type: 'send_email' }],
      },
      {
        type: 'split',
        paths: [{ steps: [{ type: 'send_form', via: 'whatsapp' }] }],
      },
      null,
    ]
    expect(canali(passi)).toEqual(['email', 'sms', 'whatsapp'])
    expect(canali([{ type: 'send_form' }])).toEqual(['email'])
    expect(canali(undefined)).toEqual([])
  })

  it('says what a person without an address lacks, by the ways it writes', () => {
    expect(senzaRecapito(['email'])).toBe('No email address')
    expect(senzaRecapito(['sms'])).toBe('No mobile number')
    expect(senzaRecapito(['whatsapp', 'email'])).toBe(
      'No email nor mobile number',
    )
  })

  it("lists the reasons in the server's order, only those that happened", () => {
    const righe = righeDeiSalti({ stop: 2, already: 1, consent: 0, nuovo: 3 }, [
      'sms',
    ])
    expect(righe.map((r) => r.chiave)).toEqual(['already', 'stop', 'nuovo'])
    expect(righe[1]).toEqual({
      chiave: 'stop',
      testo: "Wrote STOP to the centre's SMS",
      quanti: 2,
    })
    expect(righe[2].testo).toBe('nuovo')
    expect(righeDeiSalti(null, [])).toEqual([])
  })

  it('counts who was left out', () => {
    expect(quantiSaltati({ stop: 2, already: 1 })).toBe(3)
    expect(quantiSaltati(undefined)).toBe(0)
  })

  it('says the ways in one line', () => {
    expect(vieDellaCampagna(['sms', 'email'])).toBe('By email and SMS')
    expect(vieDellaCampagna(['whatsapp', 'sms', 'email'])).toBe(
      'By email, SMS and WhatsApp',
    )
    expect(vieDellaCampagna(['email'])).toBe('By email')
    expect(vieDellaCampagna([])).toBe('It writes to nobody: tasks, tags, notes')
  })

  it('names the list', () => {
    expect(fonteDellaLista({ scelti: 1 })).toBe('1 person chosen')
    expect(fonteDellaLista({ scelti: 12, vista: 'X' })).toBe('12 people chosen')
    expect(fonteDellaLista({ vista: 'Clienti' })).toBe('The view «Clienti»')
    expect(fonteDellaLista()).toBe('The list on screen')
  })
})
