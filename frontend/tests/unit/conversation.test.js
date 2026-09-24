import { describe, expect, it } from 'vitest'
import {
  buildStream,
  channelOf,
  countByChannel,
  dayLabel,
  directionOf,
  isConversational,
  withDayMarkers,
} from '@/utils/conversation'

const wa = (name, type, creation) => ({
  name,
  activity_type: 'whatsapp',
  type,
  creation,
})
const email = (name, sent_or_received, creation) => ({
  name,
  activity_type: 'communication',
  creation,
  data: { sent_or_received },
})
const comment = (name, creation) => ({
  name,
  activity_type: 'comment',
  creation,
})

describe('channelOf', () => {
  it('knows the four channels and the calls', () => {
    expect(channelOf({ activity_type: 'whatsapp' })).toBe('whatsapp')
    expect(channelOf({ activity_type: 'sms' })).toBe('sms')
    expect(channelOf({ activity_type: 'communication' })).toBe('email')
    expect(channelOf({ activity_type: 'comment' })).toBe('comment')
    expect(channelOf({ activity_type: 'incoming_call' })).toBe('call')
    expect(channelOf({ activity_type: 'outgoing_call' })).toBe('call')
  })

  it('says nothing for a field that changed', () => {
    expect(channelOf({ activity_type: 'changed' })).toBe('')
    expect(channelOf({})).toBe('')
    expect(channelOf(null)).toBe('')
  })
})

describe('directionOf', () => {
  it('reads each channel with its own word for it', () => {
    // a message says `type`…
    expect(directionOf(wa('1', 'Outgoing'))).toBe('out')
    expect(directionOf(wa('2', 'Incoming'))).toBe('in')
    // …an email says `sent_or_received`…
    expect(directionOf(email('3', 'Sent'))).toBe('out')
    expect(directionOf(email('4', 'Received'))).toBe('in')
    // …and a call says it the other way round from a message
    expect(
      directionOf({ activity_type: 'incoming_call', type: 'Incoming' }),
    ).toBe('in')
    expect(
      directionOf({ activity_type: 'outgoing_call', type: 'Outgoing' }),
    ).toBe('out')
  })

  it('puts a call on its side even when only one field says which', () => {
    // the backend derives activity_type from type, so a row can arrive with
    // either one of them; neither alone may put an incoming call on the right
    expect(directionOf({ activity_type: 'incoming_call' })).toBe('in')
    expect(directionOf({ activity_type: 'outgoing_call' })).toBe('out')
    expect(channelOf({ type: 'Incoming', duration: 42 })).toBe('call')
    expect(directionOf({ type: 'Incoming', duration: 42 })).toBe('in')
    expect(directionOf({ type: 'Outgoing', duration: 42 })).toBe('out')
  })

  it('gives a comment no side, because it was sent to nobody', () => {
    expect(directionOf(comment('5'))).toBe('internal')
    expect(directionOf({ activity_type: 'changed' })).toBe('internal')
    expect(isConversational(comment('5'))).toBe(false)
    expect(isConversational(wa('6', 'Outgoing'))).toBe(true)
  })

  it('reads an old email without the field as arriving', () => {
    // being wrong the other way would put somebody else's words in our name
    expect(directionOf({ activity_type: 'communication', data: {} })).toBe('in')
    expect(
      directionOf({
        activity_type: 'communication',
        communication_type: 'Automated Message',
        data: {},
      }),
    ).toBe('out')
  })
})

describe('buildStream', () => {
  const items = [
    wa('w1', 'Incoming', '2026-09-01 10:00:00'),
    email('e1', 'Sent', '2026-09-01 11:00:00'),
    comment('c1', '2026-09-01 12:00:00'),
    { name: 'v1', activity_type: 'changed', creation: '2026-09-01 13:00:00' },
  ]

  it('keeps everything in the mixed view, in time order', () => {
    expect(buildStream(items).map((r) => r.key)).toEqual([
      'whatsapp:w1',
      'email:e1',
      'comment:c1',
      'changed:v1',
    ])
  })

  it('keeps only its own channel when one is picked', () => {
    expect(
      buildStream(items, { channel: 'whatsapp' }).map((r) => r.key),
    ).toEqual(['whatsapp:w1'])
    expect(
      buildStream(items, { channel: 'comment' }).map((r) => r.key),
    ).toEqual(['comment:c1'])
  })

  it('reads either way round', () => {
    const newest = buildStream(items, { newestFirst: true })
    expect(newest[0].key).toBe('changed:v1')
  })

  it('carries the channel and the direction on every row', () => {
    const row = buildStream(items, { channel: 'email' })[0]
    expect(row.channel).toBe('email')
    expect(row.direction).toBe('out')
    expect(row.at).toBe('2026-09-01 11:00:00')
  })

  it('survives nothing at all', () => {
    expect(buildStream()).toEqual([])
    expect(buildStream(null, { channel: 'sms' })).toEqual([])
  })
})

describe('countByChannel', () => {
  it('counts each channel, and everything', () => {
    const tally = countByChannel([
      wa('w1', 'Incoming'),
      wa('w2', 'Outgoing'),
      comment('c1'),
      { name: 'v1', activity_type: 'changed' },
    ])
    expect(tally.whatsapp).toBe(2)
    expect(tally.comment).toBe(1)
    expect(tally.all).toBe(4)
    expect(tally.email).toBeUndefined()
  })
})

describe('a file that was sent is not also an attachment line', () => {
  it('drops the log line for a file that is already a message', () => {
    const rows = buildStream([
      {
        name: 'w1',
        activity_type: 'whatsapp',
        type: 'Outgoing',
        attach: '/files/voice-1790157621002.mp4',
        creation: '2026-09-23 12:00:00',
      },
      {
        name: 'a1',
        activity_type: 'attachment_log',
        data: { file_name: 'voice-1790157621002.mp4' },
        creation: '2026-09-23 12:00:01',
      },
    ])
    expect(rows.map((r) => r.key)).toEqual(['whatsapp:w1'])
  })

  it('matches through the signed media url the server now hands to Meta', () => {
    const rows = buildStream([
      {
        name: 'w1',
        activity_type: 'whatsapp',
        type: 'Outgoing',
        attach:
          'https://site/api/method/crm.api.whatsapp.media?file=%2Ffiles%2Fvoice-1.mp4&kind=audio&s=abc',
        creation: '2026-09-23 12:00:00',
      },
      {
        name: 'a1',
        activity_type: 'attachment_log',
        data: { file_name: 'voice-1.mp4' },
        creation: '2026-09-23 12:00:01',
      },
    ])
    expect(rows).toHaveLength(1)
  })

  it('keeps a file nobody sent as a message', () => {
    const rows = buildStream([
      {
        name: 'a1',
        activity_type: 'attachment_log',
        data: { file_name: 'contratto.pdf' },
        creation: '2026-09-23 12:00:00',
      },
    ])
    expect(rows.map((r) => r.key)).toEqual(['attachment_log:a1'])
  })
})

describe('withDayMarkers', () => {
  const row = (name, at) => ({ key: `k:${name}`, at })

  it('puts a marker where the day changes, and only there', () => {
    const marked = withDayMarkers([
      row('a', '2026-09-22 10:00:00'),
      row('b', '2026-09-22 18:00:00'),
      row('c', '2026-09-23 09:00:00'),
    ])
    expect(marked.map((r) => r.key)).toEqual([
      'day:2026-09-22',
      'k:a',
      'k:b',
      'day:2026-09-23',
      'k:c',
    ])
  })

  it('opens with one, because the first day is a change too', () => {
    const marked = withDayMarkers([row('a', '2026-09-22 10:00:00')])
    expect(marked[0].kind).toBe('day')
  })

  it('does not invent a day for a row that has no time', () => {
    const marked = withDayMarkers([
      row('a', null),
      row('b', '2026-09-22 10:00:00'),
    ])
    expect(marked.map((r) => r.kind)).toEqual([undefined, 'day', undefined])
  })

  it('survives nothing at all', () => {
    expect(withDayMarkers()).toEqual([])
    expect(withDayMarkers(null)).toEqual([])
  })
})

describe('dayLabel', () => {
  it('says Today and Yesterday, which is what a reader is actually asking', () => {
    expect(
      dayLabel('2026-09-23', '2026-09-23 11:00:00', '2026-09-22 11:00:00'),
    ).toBe('Today')
    expect(
      dayLabel('2026-09-22', '2026-09-23 11:00:00', '2026-09-22 11:00:00'),
    ).toBe('Yesterday')
  })

  it('gives the date itself for anything older', () => {
    expect(
      dayLabel('2026-04-01', '2026-09-23 11:00:00', '2026-09-22 11:00:00'),
    ).toBe('2026-04-01')
  })
})
