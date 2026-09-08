import { describe, expect, it } from 'vitest'
import { groupJourney, readableDuration } from '@/utils/journey'

const visit = (name, started_on, extra = {}) => ({
  name,
  started_on,
  source: 'google',
  medium: 'organic',
  ...extra,
})

const event = (name, session, occurred_on, extra = {}) => ({
  name,
  session,
  occurred_on,
  event_type: 'Page View',
  ...extra,
})

describe('groupJourney', () => {
  it('hangs each event off the visit it happened in', () => {
    const visits = groupJourney(
      [visit('s1', '2026-09-01 10:00:00'), visit('s2', '2026-09-05 10:00:00')],
      [
        event('e1', 's1', '2026-09-01 10:00:10'),
        event('e2', 's2', '2026-09-05 10:00:10'),
        event('e3', 's1', '2026-09-01 10:02:00'),
      ],
    )

    expect(visits.map((v) => v.name)).toEqual(['s1', 's2'])
    expect(visits[0].events.map((e) => e.name)).toEqual(['e1', 'e3'])
    expect(visits[1].events.map((e) => e.name)).toEqual(['e2'])
  })

  it('keeps a visit that produced no events', () => {
    const visits = groupJourney([visit('s1', '2026-09-01 10:00:00')], [])
    expect(visits).toHaveLength(1)
    expect(visits[0].events).toEqual([])
  })

  it('orders oldest first by default, newest first when asked', () => {
    const sessions = [
      visit('old', '2026-09-01 10:00:00'),
      visit('new', '2026-09-05 10:00:00'),
    ]
    const events = [
      event('e_old', 'old', '2026-09-01 10:05:00'),
      event('e_older', 'old', '2026-09-01 10:00:00'),
    ]

    const oldestFirst = groupJourney(sessions, events)
    expect(oldestFirst.map((v) => v.name)).toEqual(['old', 'new'])
    expect(oldestFirst[0].events.map((e) => e.name)).toEqual([
      'e_older',
      'e_old',
    ])

    const newestFirst = groupJourney(sessions, events, { newestFirst: true })
    expect(newestFirst.map((v) => v.name)).toEqual(['new', 'old'])
    expect(newestFirst[1].events.map((e) => e.name)).toEqual([
      'e_old',
      'e_older',
    ])
  })

  it('parks events whose visit is missing instead of dropping them', () => {
    // the journey returns the most recent visits, so older ones fall off the end
    const visits = groupJourney(
      [visit('s1', '2026-09-05 10:00:00')],
      [
        event('kept', 's1', '2026-09-05 10:00:10'),
        event('orphan', 's_gone', '2026-08-01 09:00:00'),
        event('orphan2', null, '2026-08-02 09:00:00'),
      ],
    )

    const unknown = visits.find((v) => v.unknown)
    expect(unknown).toBeTruthy()
    expect(unknown.events.map((e) => e.name)).toEqual(['orphan', 'orphan2'])
    // it sorts by its earliest event, so it lands before the visit we do know
    expect(visits.map((v) => v.name)).toEqual(['__unknown_visit__', 's1'])
  })

  it('adds no unknown bucket when every event has its visit', () => {
    const visits = groupJourney(
      [visit('s1', '2026-09-05 10:00:00')],
      [event('e1', 's1', '2026-09-05 10:00:10')],
    )
    expect(visits.some((v) => v.unknown)).toBe(false)
  })

  it('never mutates what it was handed', () => {
    const sessions = [visit('s1', '2026-09-05 10:00:00')]
    const events = [event('e1', 's1', '2026-09-05 10:00:10')]
    groupJourney(sessions, events)
    expect(sessions[0].events).toBeUndefined()
    expect(events).toHaveLength(1)
  })

  it('survives an empty or absent journey', () => {
    expect(groupJourney()).toEqual([])
    expect(groupJourney([], [])).toEqual([])
    expect(groupJourney(null, null)).toEqual([])
  })
})

describe('readableDuration', () => {
  it.each([
    [0, '0s'],
    [45, '45s'],
    [60, '1m 0s'],
    [130, '2m 10s'],
    [3600, '1h 00m'],
    [3900, '1h 05m'],
  ])('%is reads as %s', (seconds, expected) => {
    expect(readableDuration(seconds)).toBe(expected)
  })

  it('treats a missing duration as zero', () => {
    expect(readableDuration(undefined)).toBe('0s')
    expect(readableDuration(null)).toBe('0s')
  })
})
