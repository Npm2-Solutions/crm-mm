import { describe, expect, it } from 'vitest'
import {
  buildStream,
  channelOf,
  countByChannel,
  directionOf,
  isConversational,
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
