import { describe, expect, it } from 'vitest'
import {
  NEXT,
  byDay,
  shiftDay,
  minutesWaiting,
  summarize,
  timeOf,
  waitingLabel,
  waitingRoom,
} from '@/utils/oggi'

const appointment = (starts_on, ...participants) => ({
  starts_on,
  participants,
})

describe('the waiting room', () => {
  it('counts whole minutes since the check-in', () => {
    const now = new Date('2026-09-29T10:30:40')
    expect(minutesWaiting('2026-09-29 10:18:00', now)).toBe(12)
    expect(minutesWaiting(null, now)).toBe(0)
    expect(minutesWaiting('2026-09-29 11:00:00', now)).toBe(0)
  })

  it('says minutes, then hours', () => {
    expect(waitingLabel(0)).toBe('0 min')
    expect(waitingLabel(59)).toBe('59 min')
    expect(waitingLabel(60)).toBe('1 h')
    expect(waitingLabel(65)).toBe('1 h 5 min')
  })

  it('lists who arrived first, first', () => {
    const day = [
      appointment('2026-09-29 10:00', {
        name: 'b',
        status: 'Arrived',
        arrived_at: '2026-09-29 10:05:00',
      }),
      appointment(
        '2026-09-29 09:30',
        { name: 'a', status: 'Arrived', arrived_at: '2026-09-29 09:20:00' },
        { name: 'c', status: 'Booked' },
      ),
    ]
    expect(waitingRoom(day).map((w) => w.participant.name)).toEqual(['a', 'b'])
  })
})

describe('the day', () => {
  it('counts who is coming, waiting, came and did not', () => {
    const day = [
      appointment(
        '2026-09-29 09:00',
        { status: 'Booked' },
        { status: 'Arrived' },
      ),
      appointment(
        '2026-09-29 10:00',
        { status: 'Attended' },
        { status: 'No Show' },
      ),
    ]
    expect(summarize(day)).toEqual({
      coming: 1,
      waiting: 1,
      came: 1,
      noShow: 1,
    })
  })

  it('offers checking in first, then came, and always a way back', () => {
    expect(NEXT.Booked[0]).toBe('Arrived')
    expect(NEXT.Arrived).toEqual(['Attended', 'Booked'])
    expect(NEXT['No Show']).toEqual(['Booked'])
  })

  it('groups the days left open, the latest first', () => {
    const open = [
      appointment('2026-09-27 09:00'),
      appointment('2026-09-28 11:00'),
      appointment('2026-09-28 09:00'),
    ]
    expect(byDay(open).map((d) => [d.day, d.appointments.length])).toEqual([
      ['2026-09-28', 2],
      ['2026-09-27', 1],
    ])
  })
})

describe('the times', () => {
  it('reads the hour of a stored datetime', () => {
    expect(timeOf('2026-09-29 09:30:00')).toBe('09:30')
    expect(timeOf('2026-09-29T14:05:00')).toBe('14:05')
    expect(timeOf(null)).toBe('')
  })
})

describe('moving between days', () => {
  it('crosses months and years, and keeps null for today', () => {
    expect(shiftDay('2026-09-30', 1)).toBe('2026-10-01')
    expect(shiftDay('2026-01-01', -1)).toBe('2025-12-31')
    expect(shiftDay(null, 1)).toBe(null)
  })
})
