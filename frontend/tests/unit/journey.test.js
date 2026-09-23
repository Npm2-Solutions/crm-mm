import { describe, expect, it } from 'vitest'
import { buildTimeline, readableDuration } from '@/utils/journey'

const visit = (name, started_on, extra = {}) => ({
  name,
  started_on,
  ...extra,
})
const event = (name, occurred_on, extra = {}) => ({
  name,
  occurred_on,
  event_type: 'Page View',
  ...extra,
})

describe('buildTimeline', () => {
  it('puts everything on one stream, in the order it happened', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      events: [
        event('e2', '2026-09-01 10:05:00'),
        event('e1', '2026-09-01 10:01:00'),
      ],
      first_touch: { on: '2026-09-01 10:00:00', category: 'Paid Social' },
    })
    expect(rows.map((r) => r.kind)).toEqual([
      'touch',
      'visit',
      'event',
      'event',
    ])
    expect(rows.map((r) => r.at)).toEqual([
      '2026-09-01 10:00:00',
      '2026-09-01 10:00:00',
      '2026-09-01 10:01:00',
      '2026-09-01 10:05:00',
    ])
  })

  it('opens with the ad, because that is what happened first', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      events: [],
      first_touch: { on: '2026-09-01 10:00:00', category: 'Paid Social' },
      ad: { ad_id: '123', creative_title: 'Promo' },
    })
    expect(rows[0].kind).toBe('ad')
    expect(rows[0].data.creative_title).toBe('Promo')
    // pinned to the touch it produced, so it sorts with everything else
    expect(rows[0].at).toBe('2026-09-01 10:00:00')
  })

  it('falls back to the earliest thing known when there is no touch date', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-02 08:00:00')],
      events: [event('e1', '2026-09-01 07:00:00')],
      ad: { ad_id: '123' },
    })
    expect(rows[0].kind).toBe('ad')
    expect(rows[0].at).toBe('2026-09-01 07:00:00')
  })

  it('leaves the ad out when Meta said nothing', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      ad: {},
    })
    expect(rows.some((r) => r.kind === 'ad')).toBe(false)
  })

  it('does not say the same touch twice', () => {
    // a lead that arrived and never came back has both snapshots on one visit
    const touch = { on: '2026-09-01 10:00:00', session: 's1', source: 'meta' }
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      first_touch: touch,
      last_touch: { ...touch },
    })
    expect(rows.filter((r) => r.kind === 'touch')).toHaveLength(1)
  })

  it('keeps the last touch when it is a different visit', () => {
    const rows = buildTimeline({
      sessions: [],
      first_touch: { on: '2026-09-01 10:00:00', session: 's1' },
      last_touch: { on: '2026-09-05 09:00:00', session: 's2' },
    })
    const touches = rows.filter((r) => r.kind === 'touch')
    expect(touches).toHaveLength(2)
    expect(touches.map((t) => t.data.which)).toEqual(['first', 'last'])
  })

  it('reads either way round', () => {
    const journey = {
      sessions: [
        visit('s1', '2026-09-01 10:00:00'),
        visit('s2', '2026-09-05 10:00:00'),
      ],
      events: [],
    }
    expect(buildTimeline(journey).map((r) => r.key)).toEqual([
      'visit:s1',
      'visit:s2',
    ])
    expect(
      buildTimeline(journey, { newestFirst: true }).map((r) => r.key),
    ).toEqual(['visit:s2', 'visit:s1'])
  })

  it('shows an event whose visit is no longer listed', () => {
    // the journey returns the most recent visits, so older ones fall off the
    // end — the event still belongs on the stream, at the time it happened
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-05 10:00:00')],
      events: [event('e1', '2026-09-01 09:00:00', { session: 'gone' })],
    })
    expect(rows.map((r) => r.key)).toEqual(['event:e1', 'visit:s1'])
  })

  it('does not mutate what it was given', () => {
    const sessions = [visit('s1', '2026-09-01 10:00:00')]
    const events = [event('e1', '2026-09-01 10:01:00')]
    buildTimeline({ sessions, events })
    expect(sessions[0].events).toBeUndefined()
  })

  it('survives an empty journey', () => {
    expect(buildTimeline()).toEqual([])
    expect(buildTimeline({})).toEqual([])
    expect(buildTimeline({ sessions: null, events: null })).toEqual([])
  })
})

describe('readableDuration', () => {
  it('reads seconds, minutes and hours', () => {
    expect(readableDuration(45)).toBe('45s')
    expect(readableDuration(130)).toBe('2m 10s')
    expect(readableDuration(3900)).toBe('1h 05m')
  })

  it('treats nothing as zero', () => {
    expect(readableDuration()).toBe('0s')
    expect(readableDuration(null)).toBe('0s')
  })
})
