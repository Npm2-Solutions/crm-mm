// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  ALTEZZE,
  chiusure,
  colonneDelGiorno,
  coloreDelBlocco,
  cosePerColonna,
  cosePerGiorno,
  daDisegnare,
  etichettaDelPeriodo,
  finestraDellaGiornata,
  formaDelBlocco,
  giornoDelMese,
  giorniDellaSettimana,
  lavora,
  meseDi,
  orarioDelGiorno,
  paroleDelBlocco,
  periodoDi,
  righeDelBlocco,
  segniDelBlocco,
  spostaPeriodo,
  statoDelBlocco,
  sulGiorno,
  testoDelBlocco,
} from '@/utils/agenda'

const visita = {
  name: 'APP-1',
  service: 'Controllo nutrizionale',
  status: 'Scheduled',
  starts_on: '2026-10-06 09:00:00',
  ends_on: '2026-10-06 09:30:00',
  staff: [{ user: 'elena@example.com' }],
  resources: [{ resource: 'Studio 1' }],
  participants: [{ participant_name: 'Mario Rossi', status: 'Booked' }],
}

describe('righeDelBlocco', () => {
  it('gives a half-hour two whole lines at the normal height, never half of one', () => {
    // 30 minutes at 1.6px are 48px: two lines of 16px and the padding
    expect(righeDelBlocco(30, ALTEZZE.normale)).toBe(2)
    expect(righeDelBlocco(60, ALTEZZE.normale)).toBe(5)
    expect(righeDelBlocco(30, ALTEZZE.ampia)).toBe(4)
  })

  it('calls a block shorter than a line a sliver', () => {
    expect(righeDelBlocco(10, ALTEZZE.normale)).toBe(0)
    expect(righeDelBlocco(15, ALTEZZE.normale)).toBe(1)
    expect(righeDelBlocco(undefined, ALTEZZE.normale)).toBe(0)
  })
})

describe('formaDelBlocco', () => {
  it('lays the words out by the lines there are', () => {
    expect(formaDelBlocco(0).forma).toBe('sottile')
    expect(formaDelBlocco(1).forma).toBe('una')
    expect(formaDelBlocco(2).forma).toBe('due')
    expect(formaDelBlocco(3).forma).toBe('tre')
    expect(formaDelBlocco(6)).toEqual({ forma: 'piena', note: 2 })
  })
})

describe('testoDelBlocco', () => {
  it('names the person first, then what and where', () => {
    expect(testoDelBlocco(visita)).toEqual({
      chi: 'Mario Rossi',
      cosa: 'Controllo nutrizionale',
      dove: 'Studio 1',
      dettagli: 'Controllo nutrizionale · Studio 1',
    })
  })

  it("names the professionals in a room's column", () => {
    const testo = testoDelBlocco(visita, {
      modo: 'resource',
      nomeDi: () => 'Elena Galli',
    })
    expect(testo.dove).toBe('Elena Galli')
    expect(testo.dettagli).toBe('Controllo nutrizionale · Elena Galli')
  })

  it('names a class by its service and counts its people', () => {
    const classe = {
      ...visita,
      service: 'Pilates di gruppo',
      participants: [
        { participant_name: 'Anna' },
        { participant_name: 'Bruno' },
        { participant_name: 'Carla' },
      ],
    }
    const testo = testoDelBlocco(classe, {
      t: (s, v) => s.replace('{0}', v[0]),
    })
    expect(testo.chi).toBe('Pilates di gruppo')
    expect(testo.cosa).toBe('3 people')
  })

  it('keeps a cancelled appointment naming whom it was for', () => {
    const annullato = {
      ...visita,
      status: 'Cancelled',
      participants: [{ participant_name: 'Mario Rossi', status: 'Cancelled' }],
    }
    expect(testoDelBlocco(annullato).chi).toBe('Mario Rossi')
  })
})

describe('segniDelBlocco and statoDelBlocco', () => {
  it('says somebody is in the waiting room while the visit is still open', () => {
    const arrivato = {
      ...visita,
      participants: [{ participant_name: 'Mario Rossi', status: 'Arrived' }],
    }
    expect(statoDelBlocco(arrivato)).toBe('Arrived')
    expect(segniDelBlocco(arrivato).map((s) => s.icona)).toEqual([
      'lucide-armchair',
    ])
    // done is done, whoever sat in the waiting room
    expect(statoDelBlocco({ ...arrivato, status: 'Completed' })).toBe(
      'Completed',
    )
  })

  it('marks a conflict, a first visit and where it was booked, in words', () => {
    const segni = segniDelBlocco({
      ...visita,
      status: 'Confirmed',
      conflict_note: 'Studio 1 è già occupato',
      first_visit: true,
      source: 'External',
      external_platform: 'MioDottore',
    })
    expect(segni.map((s) => s.chiave)).toEqual([
      'conflitto',
      'stato',
      'prima',
      'piattaforma',
    ])
    expect(segni[0].testo).toBe('Studio 1 è già occupato')
    expect(segni.at(-1).testo).toBe('Booked on MioDottore')
  })

  it('reads the whole block for a screen reader', () => {
    expect(paroleDelBlocco({ ...visita, first_visit: true })).toBe(
      '09:00–09:30, Mario Rossi, Controllo nutrizionale, Studio 1, First visit',
    )
    expect(paroleDelBlocco({ ...visita, status: 'Cancelled' })).toContain(
      'Cancelled',
    )
  })
})

describe('coloreDelBlocco and daDisegnare', () => {
  it('colours by the service, or by how it is going', () => {
    expect(
      coloreDelBlocco(visita, {
        serviceColors: { 'Controllo nutrizionale': '#30A66D' },
      }),
    ).toBe('#30A66D')
    expect(
      coloreDelBlocco({ ...visita, status: 'No Show' }, { per: 'stato' }),
    ).toBe('var(--cat-rose)')
  })

  it('leaves a cancelled place free unless cancelled ones are asked for', () => {
    const giorno = [visita, { ...visita, name: 'APP-2', status: 'Cancelled' }]
    expect(daDisegnare(giorno).map((a) => a.name)).toEqual(['APP-1'])
    expect(daDisegnare(giorno, { annullati: true })).toHaveLength(2)
    expect(daDisegnare(giorno, { stati: ['Cancelled'] })).toHaveLength(2)
  })
})

describe('hours', () => {
  const turni = [
    [480, 780],
    [840, 1140],
  ]

  it("says a column's hours as its header does", () => {
    expect(orarioDelGiorno(turni)).toBe('08:00–13:00 · 14:00–19:00')
    expect(orarioDelGiorno([[0, 1440]])).toBe('')
    expect(orarioDelGiorno(null)).toBe('')
    expect(orarioDelGiorno([[540, 1440]])).toBe('09:00–24:00')
  })

  it('greys out what the shifts leave of the hours shown', () => {
    expect(chiusure(turni, { startMinutes: 420, endMinutes: 1200 })).toEqual([
      { from: 420, to: 480 },
      { from: 780, to: 840 },
      { from: 1140, to: 1200 },
    ])
    // a day off is closed all day; hours not known grey nothing
    expect(chiusure([], { startMinutes: 480, endMinutes: 1200 })).toEqual([
      { from: 480, to: 1200 },
    ])
    expect(chiusure(null, { startMinutes: 480, endMinutes: 1200 })).toEqual([])
  })

  it('shows the hours from the first opening to the last closing', () => {
    expect(finestraDellaGiornata([], [turni, [[510, 900]]])).toEqual({
      startMinutes: 480,
      endMinutes: 1140,
    })
    // widened, a whole hour, by what is booked outside them
    expect(
      finestraDellaGiornata(
        [{ startMinutes: 1170, endMinutes: 1215 }],
        [turni],
      ),
    ).toEqual({ startMinutes: 480, endMinutes: 1260 })
    // open around the clock says nothing: the usual hours
    expect(finestraDellaGiornata([], [[[0, 1440]]])).toEqual({
      startMinutes: 480,
      endMinutes: 1200,
    })
  })

  it('counts as working whoever has hours that day, or none were ever set', () => {
    const orari = { '2026-10-06': { open: turni }, '2026-10-07': { open: [] } }
    expect(lavora(orari, '2026-10-06')).toBe(true)
    expect(lavora(orari, '2026-10-07')).toBe(false)
    expect(lavora(null, '2026-10-07')).toBe(true)
    expect(lavora(undefined, '2026-10-07')).toBe(true)
  })
})

describe('colonneDelGiorno and giorniDellaSettimana', () => {
  const giorno = '2026-10-06'
  const orari = {
    anna: { [giorno]: { open: [[480, 780]] } },
    bruno: { [giorno]: { open: [] } },
    carla: { [giorno]: { open: [] } },
    dario: null,
  }
  const tutti = ['anna', 'bruno', 'carla', 'dario']

  it('shows who works that day or has something in it', () => {
    expect(
      colonneDelGiorno(tutti, { giorno, orari, occupati: new Set(['carla']) }),
    ).toEqual(['anna', 'carla', 'dario'])
    expect(
      colonneDelGiorno(tutti, { giorno, orari, mostraTutti: true }),
    ).toEqual(tutti)
    // whoever was chosen shows, working or not
    expect(
      colonneDelGiorno(tutti, { giorno, orari, scelti: ['bruno'] }),
    ).toEqual(['bruno'])
  })

  it("shows a week's weekend only when it works or holds something", () => {
    const sabato = '2026-10-10'
    expect(giorniDellaSettimana(giorno)).toEqual([
      '2026-10-05',
      '2026-10-06',
      '2026-10-07',
      '2026-10-08',
      '2026-10-09',
    ])
    expect(
      giorniDellaSettimana(giorno, {
        orari: { [sabato]: { open: [[480, 720]] } },
      }),
    ).toContain(sabato)
    expect(
      giorniDellaSettimana(giorno, { occupati: new Set(['2026-10-11']) }),
    ).toContain('2026-10-11')
  })
})

describe('periods', () => {
  it('covers a day, its Monday-to-Sunday week, its month in whole weeks', () => {
    expect(periodoDi('giorno', '2026-10-06')).toEqual({
      start: '2026-10-06',
      end: '2026-10-06',
    })
    expect(periodoDi('settimana', '2026-10-06')).toEqual({
      start: '2026-10-05',
      end: '2026-10-11',
    })
    expect(periodoDi('mese', '2026-10-06')).toEqual({
      start: '2026-09-28',
      end: '2026-11-01',
    })
    expect(meseDi('2026-10-06')).toHaveLength(5)
    expect(meseDi('2026-03-15')).toHaveLength(6)
  })

  it('moves a day, a week, a month, keeping the month inside itself', () => {
    expect(spostaPeriodo('giorno', '2026-10-06', -1)).toBe('2026-10-05')
    expect(spostaPeriodo('settimana', '2026-10-06', 1)).toBe('2026-10-13')
    expect(spostaPeriodo('mese', '2026-01-31', 1)).toBe('2026-02-28')
    expect(spostaPeriodo('mese', '2026-03-31', -1)).toBe('2026-02-28')
  })

  it('says the period as its heading does', () => {
    expect(etichettaDelPeriodo('giorno', '2026-10-06')).toBe(
      'Martedì 6 ottobre 2026',
    )
    expect(etichettaDelPeriodo('mese', '2026-10-06')).toBe('Ottobre 2026')
    expect(etichettaDelPeriodo('settimana', '2026-10-06')).toBe(
      '5 – 11 ottobre 2026',
    )
    expect(etichettaDelPeriodo('settimana', '2026-10-01')).toBe(
      '28 settembre – 4 ottobre 2026',
    )
  })
})

describe('giornoDelMese', () => {
  it('counts the appointments and shows the first few in order', () => {
    const cose = [
      { name: 'b', startMinutes: 600 },
      { name: 'a', startMinutes: 540 },
      { name: 'e', startMinutes: 700, tipo: 'evento' },
      { name: 'c', startMinutes: 660 },
    ]
    const giorno = giornoDelMese(cose, 2)
    expect(giorno.totale).toBe(3)
    expect(giorno.primi.map((c) => c.name)).toEqual(['a', 'b'])
    expect(giorno.altri).toBe(2)
  })
})

describe('sulGiorno', () => {
  it('cuts a span to the day it is drawn on', () => {
    expect(
      sulGiorno('2026-10-06 09:00:00', '2026-10-06 09:30:00', '2026-10-06'),
    ).toEqual([540, 570])
    expect(
      sulGiorno('2026-10-06 23:00:00', '2026-10-07 01:00:00', '2026-10-06'),
    ).toEqual([1380, 1440])
    expect(
      sulGiorno('2026-10-06 23:00:00', '2026-10-07 01:00:00', '2026-10-07'),
    ).toEqual([0, 60])
    // ending at midnight is nothing of the day after
    expect(
      sulGiorno('2026-10-06 22:00:00', '2026-10-07 00:00:00', '2026-10-07'),
    ).toBeNull()
    expect(
      sulGiorno('2026-10-06 09:00:00', '2026-10-06 09:00:00', '2026-10-06'),
    ).toEqual([540, 550])
  })
})

describe('cosePerColonna', () => {
  const giorno = '2026-10-06'
  const colonne = [
    { key: 'elena@example.com', data: giorno },
    { key: 'io@example.com', data: giorno },
  ]
  const evento = {
    id: 'EV-1',
    title: 'Riunione',
    fromDate: giorno,
    toDate: giorno,
    fromTime: '13:00',
    toTime: '14:00',
  }

  it("puts an appointment in its professional's column, one's events in one's own", () => {
    const mappa = cosePerColonna(colonne, {
      io: 'io@example.com',
      appuntamenti: [visita],
      eventi: [evento, { ...evento, id: 'EV-2', isFullDay: true }],
    })
    expect(mappa.get('elena@example.com').blocchi.map((b) => b.id)).toEqual([
      'appt:APP-1',
    ])
    expect(
      mappa.get('io@example.com').blocchi.map((b) => [b.id, b.startMinutes]),
    ).toEqual([['EV-1', 780]])
    expect(mappa.get('io@example.com').intere.map((b) => b.id)).toEqual([
      'EV-2',
    ])
  })

  it('draws busy time and the colleagues engagements as bands, never twice', () => {
    const mappa = cosePerColonna(colonne, {
      io: 'io@example.com',
      eventi: [evento],
      occupato: [
        {
          starts_on: `${giorno} 10:00:00`,
          ends_on: `${giorno} 11:00:00`,
          staff: [{ user: 'elena@example.com' }],
        },
      ],
      impegni: [
        {
          name: 'EV-1',
          users: ['elena@example.com', 'io@example.com'],
          starts_on: `${giorno} 13:00:00`,
          ends_on: `${giorno} 14:00:00`,
        },
      ],
    })
    expect(mappa.get('elena@example.com').bande.map((b) => b.tipo)).toEqual([
      'occupato',
      'impegno',
    ])
    // my meeting is drawn as itself in my column
    expect(mappa.get('io@example.com').bande).toEqual([])
  })

  it("lays a week out as one professional's days", () => {
    const settimana = [
      { key: giorno, data: giorno },
      { key: '2026-10-07', data: '2026-10-07' },
    ]
    const domani = {
      ...visita,
      name: 'APP-2',
      starts_on: '2026-10-07 10:00:00',
      ends_on: '2026-10-07 10:30:00',
    }
    const altro = {
      ...visita,
      name: 'APP-3',
      staff: [{ user: 'bruno@example.com' }],
    }
    const mappa = cosePerColonna(settimana, {
      settimana: true,
      chi: 'elena@example.com',
      appuntamenti: [visita, domani, altro],
    })
    expect(mappa.get(giorno).blocchi.map((b) => b.id)).toEqual(['appt:APP-1'])
    expect(mappa.get('2026-10-07').blocchi.map((b) => b.id)).toEqual([
      'appt:APP-2',
    ])
  })

  it("puts a room's appointments in the room's column", () => {
    const mappa = cosePerColonna([{ key: 'Studio 1', data: giorno }], {
      modo: 'resource',
      io: 'io@example.com',
      appuntamenti: [visita],
      eventi: [evento],
    })
    expect(mappa.get('Studio 1').blocchi.map((b) => b.id)).toEqual([
      'appt:APP-1',
    ])
  })
})

describe('cosePerGiorno', () => {
  it("files a month's appointments and events by the days they touch", () => {
    const giorni = ['2026-10-06', '2026-10-07']
    const mappa = cosePerGiorno(giorni, {
      appuntamenti: [visita],
      eventi: [
        {
          id: 'EV-1',
          title: 'Congresso',
          fromDate: '2026-10-06',
          toDate: '2026-10-07',
          isFullDay: true,
        },
      ],
    })
    expect(mappa.get('2026-10-06').map((c) => [c.id, c.startMinutes])).toEqual([
      ['appt:APP-1', 540],
      ['EV-1', -1],
    ])
    expect(mappa.get('2026-10-07').map((c) => c.id)).toEqual(['EV-1'])
  })
})
