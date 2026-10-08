// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  datiDaInviare,
  fraseDeiSolleciti,
  righeDeiTotali,
  rigaVuota,
  titoloDellaFattura,
} from '@/utils/fattura'

// The invoice made inside DottorCloud: the dialog sends only what it may write,
// shows the totals worth a line and is called by what the document is.

describe('the invoice dialog', () => {
  it('sends the client, the payment and the lines that have a service', () => {
    const vista = {
      name: 'INV-1',
      client: {
        party_type: 'CRM Lead',
        party: 'L-1',
        billing_name: 'Mario Rossi',
        party_label: 'Mario',
      },
      payment: { payment_method: 'MP08', payment_date: '2026-10-02' },
      items: [
        {
          billable_service: 'Seduta',
          service_provider: 'P-1',
          qty: '2',
          rate: '50',
          amount: 100,
          service_label: 'Seduta',
        },
        { billable_service: '', service_provider: 'P-1', qty: 1, rate: 0 },
      ],
      totals: { grand_total: 100 },
    }
    const dati = datiDaInviare(vista)
    expect(dati.party).toBe('L-1')
    expect(dati.party_label).toBeUndefined()
    expect(dati.payment_method).toBe('MP08')
    expect(dati.items).toEqual([
      {
        billable_service: 'Seduta',
        service_provider: 'P-1',
        description: '',
        qty: 2,
        rate: 50,
      },
    ])
    expect(dati.totals).toBeUndefined()
    expect(dati.appointment).toBeUndefined()
  })

  it('keeps the appointment a new invoice comes from', () => {
    const vista = {
      appointment: 'APPT-1',
      client: { party_type: 'CRM Lead', party: 'L-1' },
      payment: {},
      items: [
        { billable_service: 'Seduta', service_provider: '', qty: 1, rate: 50 },
      ],
    }
    const dati = datiDaInviare(vista)
    expect(dati.appointment).toBe('APPT-1')
    // the professional still to choose goes as it is: the server says it is missing
    expect(dati.items[0].service_provider).toBe('')
  })

  it('shows the totals worth a line', () => {
    const righe = righeDeiTotali({
      net_total: 100,
      fund_contribution: 2,
      vat_total: 0,
      stamp_duty: 2,
      grand_total: 104,
      withholding: 0,
      net_payable: 104,
    })
    expect(righe.map((r) => r.chiave)).toEqual([
      'net_total',
      'fund_contribution',
      'stamp_duty',
      'grand_total',
    ])
    const conRitenuta = righeDeiTotali({
      net_total: 100,
      grand_total: 100,
      withholding: 20,
      net_payable: 80,
    })
    expect(conRitenuta.map((r) => r.chiave)).toEqual([
      'net_total',
      'grand_total',
      'withholding',
      'net_payable',
    ])
    expect(righeDeiTotali({}).map((r) => r.chiave)).toEqual(['grand_total'])
  })

  it('is called by what the document is', () => {
    expect(titoloDellaFattura({})).toBe('New invoice')
    expect(titoloDellaFattura({ is_note: true })).toBe('New credit note')
    expect(titoloDellaFattura({ name: 'X' })).toBe('Draft invoice')
    expect(titoloDellaFattura({ name: 'X', document_number: '2026/S/1' })).toBe(
      'Invoice {0}',
    )
    expect(
      titoloDellaFattura({
        name: 'X',
        is_note: true,
        document_number: '2026/S/2',
      }),
    ).toBe('Credit note {0}')
  })

  it('starts a line with the only professional', () => {
    expect(rigaVuota('P-1')).toEqual({
      billable_service: '',
      service_provider: 'P-1',
      description: '',
      qty: 1,
      rate: 0,
    })
    expect(rigaVuota().service_provider).toBe('')
  })
})

describe('the reminders of an invoice still to pay', () => {
  const t = (testo, valori) =>
    testo.replace(/\{(\d)\}/g, (_, i) => String(valori[i]))
  const giorno = (valore) => `[${valore}]`

  it('says nothing of an invoice never reminded', () => {
    expect(fraseDeiSolleciti(null, t, giorno)).toBe('')
    expect(fraseDeiSolleciti({ count: 0, last: null }, t, giorno)).toBe('')
  })

  it('says how many times, and the last day', () => {
    expect(fraseDeiSolleciti({ count: 1, last: '2026-10-08' }, t, giorno)).toBe(
      'Reminded once, on [2026-10-08]',
    )
    expect(fraseDeiSolleciti({ count: 2, last: '2026-10-22' }, t, giorno)).toBe(
      'Reminded 2 times, the last on [2026-10-22]',
    )
  })
})
