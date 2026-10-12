// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  etaENascita,
  giornoInBreve,
  indirizzoTel,
  mascherato,
  modiDiChiamare,
  chiDellAppuntamento,
  nomeDellAppuntamento,
  numeriDi,
  prossimoAppuntamento,
  quandoInBreve,
  soloCifre,
  titoloSenzaPersona,
} from '@/utils/schedaPersona'

describe('soloCifre', () => {
  it('keeps the digits and the leading +', () => {
    expect(soloCifre('+39 340 111 2233')).toBe('+393401112233')
    expect(soloCifre('0039 340-111-2233')).toBe('+393401112233')
    expect(soloCifre('(02) 1234 5678')).toBe('0212345678')
    expect(soloCifre('')).toBe('')
    expect(soloCifre(null)).toBe('')
  })
})

describe('indirizzoTel', () => {
  it('is what the device dialer opens', () => {
    expect(indirizzoTel('+39 340 111 2233')).toBe('tel:+393401112233')
    expect(indirizzoTel('   ')).toBe('')
  })
})

describe('numeriDi', () => {
  it('lists the mobile first, then the phone', () => {
    expect(
      numeriDi({ mobile_no: '+39 340 1112233', phone: '02 123456' }),
    ).toEqual([
      { campo: 'mobile_no', label: 'Mobile', numero: '+39 340 1112233' },
      { campo: 'phone', label: 'Phone', numero: '02 123456' },
    ])
  })

  it('counts the same number written twice once', () => {
    expect(
      numeriDi({ mobile_no: '+39 340 1112233', phone: '3401112233' }),
    ).toHaveLength(1)
    expect(
      numeriDi({ mobile_no: '0039 340 1112233', phone: '+393401112233' }),
    ).toHaveLength(1)
  })

  it('has nothing without numbers', () => {
    expect(numeriDi({})).toEqual([])
    expect(numeriDi(null)).toEqual([])
    expect(numeriDi({ mobile_no: ' ' })).toEqual([])
  })

  it('leaves out a number that came masked', () => {
    expect(numeriDi({ mobile_no: '+39XXXXXX', phone: '+1-XXXXXX' })).toEqual([])
  })
})

describe('mascherato', () => {
  it('knows the placeholder of a masked value', () => {
    expect(mascherato('+39XXXXXX')).toBe(true)
    expect(mascherato('XXXXXXXX')).toBe(true)
    expect(mascherato('+393401112233')).toBe(false)
    expect(mascherato('Xavier')).toBe(false)
    expect(mascherato('')).toBe(false)
  })
})

describe('modiDiChiamare', () => {
  const numeri = [
    { campo: 'mobile_no', label: 'Mobile', numero: '+39 340 1112233' },
  ]

  it('goes through the centre when its telephony is on, on a computer', () => {
    expect(modiDiChiamare(numeri, { telefonia: true })).toEqual([
      { via: 'centro', ...numeri[0] },
    ])
  })

  it('offers the phone own dialer too on a phone', () => {
    expect(
      modiDiChiamare(numeri, { telefonia: true, telefono: true }).map(
        (m) => m.via,
      ),
    ).toEqual(['centro', 'dispositivo'])
  })

  it('leaves only through the device without telephony', () => {
    expect(modiDiChiamare(numeri).map((m) => m.via)).toEqual(['dispositivo'])
  })

  it('has no way without a number', () => {
    expect(modiDiChiamare([], { telefonia: true })).toEqual([])
  })
})

describe('prossimoAppuntamento', () => {
  const adesso = new Date('2026-10-02T12:00:00')

  it('is the first still to start', () => {
    const lista = [
      { name: 'C', starts_on: '2026-10-20 09:00:00', status: 'Scheduled' },
      { name: 'B', starts_on: '2026-10-05 10:00:00', status: 'Confirmed' },
      { name: 'A', starts_on: '2026-09-28 10:00:00', status: 'Completed' },
    ]
    expect(prossimoAppuntamento(lista, adesso).name).toBe('B')
  })

  it('skips the cancelled and the missed ones', () => {
    const lista = [
      { name: 'X', starts_on: '2026-10-03 09:00:00', status: 'Cancelled' },
      { name: 'Y', starts_on: '2026-10-04 09:00:00', status: 'No Show' },
      { name: 'Z', starts_on: '2026-10-09 09:00:00', status: 'Scheduled' },
    ]
    expect(prossimoAppuntamento(lista, adesso).name).toBe('Z')
  })

  it('is never one already done, whatever the clock says', () => {
    // done this morning, and the phone's clock behind the centre's
    const lista = [
      { name: 'F', starts_on: '2026-10-02 13:00:00', status: 'Completed' },
      { name: 'G', starts_on: '2026-10-06 09:00:00', status: 'Scheduled' },
    ]
    expect(prossimoAppuntamento(lista, adesso).name).toBe('G')
  })

  it('is nothing when all are past', () => {
    expect(
      prossimoAppuntamento(
        [{ name: 'A', starts_on: '2026-09-01 10:00:00', status: 'Completed' }],
        adesso,
      ),
    ).toBeNull()
    expect(prossimoAppuntamento(undefined, adesso)).toBeNull()
  })
})

describe('quandoInBreve', () => {
  const adesso = new Date('2026-10-02T12:00:00')

  it('says the day and the hour on the 24-hour clock', () => {
    expect(quandoInBreve('2026-10-09 10:00:00', 'it-IT', adesso)).toBe(
      'ven 9 ott, 10:00',
    )
    expect(quandoInBreve('2026-10-09 15:30:00', 'en-GB', adesso)).toBe(
      'Fri 9 Oct, 15:30',
    )
  })

  it('names the year only when it is another', () => {
    expect(quandoInBreve('2027-01-12 09:00:00', 'it-IT', adesso)).toBe(
      'mar 12 gen 2027, 09:00',
    )
  })

  it('is empty for no date', () => {
    expect(quandoInBreve('', 'it-IT', adesso)).toBe('')
  })
})

describe('giornoInBreve', () => {
  it('says a day with its month in words', () => {
    expect(giornoInBreve('2026-09-29', 'it-IT')).toBe('29 set 2026')
    expect(giornoInBreve('2026-09-29 21:42:36.710954', 'it-IT')).toBe(
      '29 set 2026',
    )
    expect(giornoInBreve('', 'it-IT')).toBe('')
  })
})

describe('titoloSenzaPersona', () => {
  it('takes the person name away from the title', () => {
    expect(
      titoloSenzaPersona('Fisioterapia — Laura Consenso', 'Laura Consenso'),
    ).toBe('Fisioterapia')
    expect(titoloSenzaPersona('Controllo - Marco Conti', 'Marco Conti')).toBe(
      'Controllo',
    )
  })

  it('leaves any other title as it is', () => {
    expect(titoloSenzaPersona('Pilates di gruppo', 'Laura Consenso')).toBe(
      'Pilates di gruppo',
    )
    expect(titoloSenzaPersona('Visita', '')).toBe('Visita')
  })
})

describe('nomeDellAppuntamento', () => {
  it('names an appointment by its service, never by the others in a class', () => {
    expect(
      nomeDellAppuntamento(
        {
          service: 'Pilates di gruppo',
          title: 'Pilates di gruppo — Sofia Pellegrini, Marco Conti +3',
        },
        'Francesca Marchetti',
      ),
    ).toBe('Pilates di gruppo')
  })

  it('without a service, the title without the person', () => {
    expect(
      nomeDellAppuntamento(
        { title: 'Fisioterapia — Laura Consenso' },
        'Laura Consenso',
      ),
    ).toBe('Fisioterapia')
    expect(nomeDellAppuntamento(null, 'Laura')).toBe('')
  })
})

describe('chiDellAppuntamento', () => {
  it('names who comes, the service taken off', () => {
    expect(
      chiDellAppuntamento({
        title: 'Seduta di fisioterapia — Fabio Marchetti',
        service: 'Seduta di fisioterapia',
      }),
    ).toBe('Fabio Marchetti')
    expect(
      chiDellAppuntamento({
        title: 'Pilates — Sofia Palumbo, Marco Conti +3',
        service: 'Pilates',
      }),
    ).toBe('Sofia Palumbo, Marco Conti +3')
  })

  it('is empty when the title names nobody', () => {
    expect(
      chiDellAppuntamento({ title: 'Pilates di gruppo', service: 'Pilates' }),
    ).toBe('')
    expect(chiDellAppuntamento({ title: 'Visita — Anna Neri' })).toBe('')
    expect(chiDellAppuntamento(null)).toBe('')
  })
})

describe('etaENascita', () => {
  const oggi = new Date(2026, 9, 10)
  it('counts the full years and says the day', () => {
    expect(etaENascita('1961-06-02', oggi, 'it-IT')).toEqual({
      anni: 65,
      nascita: '2 giu 1961',
    })
  })
  it('does not count a birthday still to come this year', () => {
    expect(etaENascita('1990-10-11', oggi, 'it-IT').anni).toBe(35)
    expect(etaENascita('1990-10-10', oggi, 'it-IT').anni).toBe(36)
  })
  it('says nothing without a date or with one to come', () => {
    expect(etaENascita('', oggi)).toBeNull()
    expect(etaENascita(null, oggi)).toBeNull()
    expect(etaENascita('2027-01-01', oggi)).toBeNull()
  })
  it('takes a date with its hour', () => {
    expect(etaENascita('2018-03-03 00:00:00', oggi, 'it-IT').anni).toBe(8)
  })
})
