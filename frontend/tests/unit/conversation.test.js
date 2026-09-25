import { describe, expect, it } from 'vitest'
import {
  CHANNELS,
  buildStream,
  channelOf,
  countByChannel,
  dayLabel,
  directionOf,
  groupByDay,
  isConversational,
  isStageChange,
  speakerOf,
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

describe('groupByDay', () => {
  const row = (name, at) => ({ key: `k:${name}`, at })

  it('cuts the stream where the day changes, and only there', () => {
    const days = groupByDay([
      row('a', '2026-09-22 10:00:00'),
      row('b', '2026-09-22 18:00:00'),
      row('c', '2026-09-23 09:00:00'),
    ])
    expect(days.map((g) => g.day)).toEqual(['2026-09-22', '2026-09-23'])
    expect(days[0].rows.map((r) => r.key)).toEqual(['k:a', 'k:b'])
    expect(days[1].rows.map((r) => r.key)).toEqual(['k:c'])
  })

  it('gives each group its own key, so a day seen twice is two groups', () => {
    // newest-first and oldest-first both go through here, and a stream that is
    // not sorted must not collapse two runs of the same day into one key
    const days = groupByDay([
      row('a', '2026-09-22 10:00:00'),
      row('b', '2026-09-23 09:00:00'),
      row('c', '2026-09-22 11:00:00'),
    ])
    expect(days).toHaveLength(3)
    expect(new Set(days.map((g) => g.key)).size).toBe(3)
  })

  it('does not invent a day for a row that has no time', () => {
    const days = groupByDay([row('a', null), row('b', '2026-09-22 10:00:00')])
    expect(days.map((g) => g.day)).toEqual(['', '2026-09-22'])
  })

  it('survives nothing at all', () => {
    expect(groupByDay()).toEqual([])
    expect(groupByDay(null)).toEqual([])
  })
})

describe('what happened, as opposed to what was said', () => {
  it('knows the things that are not messages', () => {
    expect(channelOf({ activity_type: 'appointment' })).toBe('appointment')
    expect(channelOf({ activity_type: 'task' })).toBe('task')
    expect(channelOf({ activity_type: 'note' })).toBe('note')
    expect(channelOf({ activity_type: 'event' })).toBe('event')
  })

  it('gives none of them a side, because none is addressed to anybody', () => {
    for (const type of ['appointment', 'task', 'note', 'event']) {
      expect(directionOf({ activity_type: type })).toBe('internal')
    }
  })

  it('tells a move down the pipeline from a phone number being corrected', () => {
    expect(
      isStageChange({ activity_type: 'changed', data: { field: 'status' } }),
    ).toBe(true)
    expect(
      isStageChange({ activity_type: 'changed', data: { field: 'mobile_no' } }),
    ).toBe(false)
    expect(isStageChange({ activity_type: 'comment' })).toBe(false)
    expect(isStageChange(undefined)).toBe(false)
  })
})

describe('who said it', () => {
  it('is us when it went out, whatever channel it left by', () => {
    expect(
      speakerOf({ activity_type: 'whatsapp', type: 'Outgoing' }, 'Marco'),
    ).toBe('Marco')
    expect(speakerOf({ activity_type: 'sms', type: 'Outgoing' })).toBe('You')
  })

  it('is them, by whatever name the channel knows them', () => {
    expect(
      speakerOf({
        activity_type: 'whatsapp',
        type: 'Incoming',
        profile_name: 'Mario Rossi',
      }),
    ).toBe('Mario Rossi')
    expect(
      speakerOf({
        activity_type: 'communication',
        data: {
          sent_or_received: 'Received',
          sender_full_name: 'Anna Bianchi',
        },
      }),
    ).toBe('Anna Bianchi')
  })

  it('is whoever wrote it, for something addressed to nobody', () => {
    expect(speakerOf({ activity_type: 'comment', owner_name: 'Giulia' })).toBe(
      'Giulia',
    )
  })

  it('says nothing rather than something wrong', () => {
    expect(speakerOf({ activity_type: 'whatsapp', type: 'Incoming' })).toBe('')
    expect(speakerOf({})).toBe('')
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

describe('CHANNELS', () => {
  it('offers a view for every channel a row can belong to', () => {
    // The selector and `channelOf` have to agree: a channel that rows can be
    // sorted into but that the selector never offers is a pile of messages
    // nobody can reach — which is what the call register was when it lived one
    // level up, in a tab of its own.
    const offered = new Set(CHANNELS.map((c) => c.key))
    for (const key of ['email', 'whatsapp', 'sms', 'comment', 'call']) {
      expect(offered.has(key)).toBe(true)
    }
  })

  it('opens on everything', () => {
    expect(CHANNELS[0].key).toBe('all')
  })
})
