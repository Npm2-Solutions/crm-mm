// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The reminders of the appointments as the screens read them: an answer as a
// mark with its words, a reminder in one line, the templates that carry the
// answers, where DottorCloud's own template is with Meta.
import {
  modelliAdatti,
  problemaDelSecondo,
  rigaDelPromemoria,
  rispostaDellAppuntamento,
  segnoDelPromemoria,
  statoDelNostro,
} from '@/utils/promemoriaAppuntamenti'

describe('segnoDelPromemoria', () => {
  it('says each answer with its icon', () => {
    expect(segnoDelPromemoria({ status: 'Sent', answer: 'Confirmed' })).toEqual(
      {
        chiave: 'promemoria',
        icona: 'lucide-thumbs-up',
        testo: 'Confirmed they are coming',
      },
    )
    expect(
      segnoDelPromemoria({ status: 'Sent', answer: 'Cannot come' }).testo,
    ).toBe('Cannot come')
    expect(
      segnoDelPromemoria({
        status: 'Sent',
        answer: 'Cannot come',
        cancelled: true,
      }).testo,
    ).toBe('Cannot come: cancelled')
    expect(
      segnoDelPromemoria({ status: 'Sent', answer: 'Wants to move' }).icona,
    ).toBe('lucide-calendar-clock')
  })

  it('calls for a call when it did not arrive, nothing while it waits', () => {
    expect(segnoDelPromemoria({ status: 'Not delivered' }).icona).toBe(
      'lucide-bell-off',
    )
    expect(segnoDelPromemoria({ status: 'Not sent' }).testo).toBe(
      'Reminder not delivered',
    )
    expect(segnoDelPromemoria({ status: 'Sent', answer: '' })).toBeNull()
    expect(segnoDelPromemoria(null)).toBeNull()
  })

  it('goes through the translator it is given', () => {
    const t = (s) => `«${s}»`
    expect(segnoDelPromemoria({ answer: 'Confirmed' }, t).testo).toBe(
      '«Confirmed they are coming»',
    )
  })
})

describe('rispostaDellAppuntamento', () => {
  it('is the answer of its one person, for the grid and the phone alike', () => {
    const confermato = { status: 'Sent', answer: 'Confirmed' }
    expect(
      rispostaDellAppuntamento({ participants: [{ reminder: confermato }] })
        .icona,
    ).toBe('lucide-thumbs-up')
    // a class: each of its people answered on their own
    expect(
      rispostaDellAppuntamento({
        participants: [{ reminder: confermato }, { reminder: confermato }],
      }),
    ).toBe(null)
    expect(rispostaDellAppuntamento({ participants: [{}] })).toBe(null)
    expect(rispostaDellAppuntamento({})).toBe(null)
    expect(rispostaDellAppuntamento(null)).toBe(null)
  })
})

describe('rigaDelPromemoria', () => {
  it('says the way it left, and what was answered', () => {
    expect(rigaDelPromemoria({ status: 'Sent', channel: 'SMS' })).toBe(
      'Reminder sent by SMS',
    )
    expect(
      rigaDelPromemoria({
        status: 'Sent',
        channel: 'WhatsApp',
        answer: 'Confirmed',
      }),
    ).toBe('Reminder sent by WhatsApp · Confirmed they are coming')
    expect(rigaDelPromemoria({ status: 'Not sent', channel: '' })).toBe(
      'Reminder not delivered',
    )
    expect(rigaDelPromemoria(null)).toBe('')
  })

  it('says which reminder it is where the centre sends two', () => {
    expect(
      rigaDelPromemoria({ status: 'Sent', channel: 'Email', which: 'first' }),
    ).toBe('First reminder sent by email')
    expect(
      rigaDelPromemoria({
        status: 'Sent',
        channel: 'WhatsApp',
        which: 'second',
        answer: 'Wants to move',
      }),
    ).toBe('Second reminder sent by WhatsApp · Would like to move it')
    expect(rigaDelPromemoria({ status: 'Failed', which: 'second' })).toBe(
      'Second reminder not delivered',
    )
    // a way nobody named: the reminder, sent
    expect(rigaDelPromemoria({ status: 'Sent', which: 'first' })).toBe(
      'First reminder sent',
    )
  })
})

describe('modelliAdatti and statoDelNostro', () => {
  it('offers only the templates with the buttons', () => {
    expect(
      modelliAdatti([
        { name: 'a', suitable: true },
        { name: 'b', suitable: false },
      ]).map((m) => m.name),
    ).toEqual(['a'])
    expect(modelliAdatti(undefined)).toEqual([])
  })

  it('tells where our template is with Meta', () => {
    expect(statoDelNostro(null)).toBe('da_fare')
    expect(statoDelNostro({ status: 'PENDING' })).toBe('in_attesa')
    expect(statoDelNostro({ status: 'approved' })).toBe('approvato')
    expect(statoDelNostro({ status: 'REJECTED' })).toBe('rifiutato')
  })
})

describe('problemaDelSecondo', () => {
  it('takes none, or 1 to 12 hours fewer than the first', () => {
    expect(problemaDelSecondo('', 24)).toBe('')
    expect(problemaDelSecondo(null, 24)).toBe('')
    expect(problemaDelSecondo(0, 24)).toBe('')
    expect(problemaDelSecondo(3, 24)).toBe('')
    expect(problemaDelSecondo(13, 24)).toBe('From 1 to 12 hours before.')
    expect(problemaDelSecondo(1.5, 24)).toBe('From 1 to 12 hours before.')
    expect(problemaDelSecondo(4, 4)).toBe(
      'Fewer hours than the first reminder.',
    )
  })
})
