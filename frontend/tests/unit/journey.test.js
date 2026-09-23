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

  it('carries the ad on the first touch, as one row and not two', () => {
    // the attribution *is* the ad arriving, written in another vocabulary:
    // a creative above, and a source/medium/campaign naming that same creative
    // below it with its own heading, read as two things having happened
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      events: [],
      first_touch: { on: '2026-09-01 10:00:00', category: 'Paid Social' },
      ad: { ad_id: '123', creative_title: 'Promo' },
    })
    expect(rows.filter((r) => r.kind === 'ad')).toHaveLength(0)
    const touch = rows.find((r) => r.kind === 'touch')
    expect(touch.data.ad.creative_title).toBe('Promo')
    expect(touch.at).toBe('2026-09-01 10:00:00')
  })

  it('does not put the ad first when the ad did not come first', () => {
    // somebody read a page, left, and met the ad a week later
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 09:00:00')],
      events: [event('e1', '2026-09-01 09:05:00')],
      first_touch: { on: '2026-09-08 11:00:00', category: 'Paid Social' },
      ad: { ad_id: '123' },
    })
    expect(rows.map((r) => r.kind)).toEqual(['visit', 'event', 'touch'])
    expect(rows[2].data.ad.ad_id).toBe('123')
  })

  it('an ad with no attribution to hang on still gets its own row', () => {
    const rows = buildTimeline({
      sessions: [],
      events: [],
      created_on: '2026-09-03 15:30:00',
      ad: { ad_id: '123' },
    })
    expect(rows.map((r) => r.kind)).toEqual(['ad', 'record'])
    expect(rows[0].data.ad.ad_id).toBe('123')
    expect(rows[0].at).toBe('2026-09-03 15:30:00')
  })

  it('falls back to the earliest thing known when nothing else has a date', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-02 08:00:00')],
      events: [event('e1', '2026-09-01 07:00:00')],
      ad: { ad_id: '123' },
    })
    expect(rows[0].kind).toBe('ad')
    expect(rows[0].at).toBe('2026-09-01 07:00:00')
  })

  it('a lead straight off an ad form is one row, then its arrival', () => {
    // no browsing at all: the ad, the attribution that names it, and the moment
    // it landed here
    const rows = buildTimeline({
      sessions: [],
      events: [],
      created_on: '2026-09-03 15:30:00',
      first_touch: {
        on: '2026-09-03 15:30:00',
        category: 'Paid Social',
        landing_page: 'lead_ad_form',
      },
      ad: { ad_id: '123', creative_title: 'Reformer' },
    })
    expect(rows.map((r) => r.kind)).toEqual(['touch', 'record'])
    expect(rows[0].data.ad.creative_title).toBe('Reformer')
  })

  it('says when the record landed in the CRM', () => {
    const rows = buildTimeline({
      sessions: [visit('s1', '2026-09-01 10:00:00')],
      events: [event('e1', '2026-09-01 10:02:00')],
      created_on: '2026-09-01 10:03:00',
      doctype: 'CRM Deal',
    })
    expect(rows.map((r) => r.kind)).toEqual(['visit', 'event', 'record'])
    expect(rows[2].data.doctype).toBe('CRM Deal')
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

  it('at the same instant, reads in the order things happened', () => {
    // a lead off an ad form stamps all three at the same second
    const at = '2026-09-03 15:30:00'
    const rows = buildTimeline({
      sessions: [],
      events: [],
      created_on: at,
      first_touch: { on: at, category: 'Paid Social' },
      ad: { ad_id: '123' },
    })
    expect(rows.map((r) => r.kind)).toEqual(['touch', 'record'])
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
