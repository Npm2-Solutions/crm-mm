import { describe, expect, it } from 'vitest'
import {
  CHANNELS,
  TONES,
  WAYS,
  buildStream,
  channelOf,
  clockOf,
  colleagueOf,
  countByChannel,
  dayLabel,
  directionOf,
  groupByDay,
  hasFailed,
  initialsOf,
  isConversational,
  isStageChange,
  keepInPlace,
  laterLabel,
  listTime,
  momentLabel,
  newSince,
  replyChannel,
  smsSegments,
  speakerOf,
  timeKey,
  toneOf,
  wallClock,
  whyItLeft,
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

  it('a bare number is the last resort, not the first', () => {
    // WhatsApp supplies a profile name only when the person publishes one, so
    // incoming messages used to be signed «393295824118» on a record whose
    // whole point is knowing whose number that is.
    const incoming = {
      activity_type: 'whatsapp',
      type: 'Incoming',
      from: '393295824118',
    }
    expect(speakerOf(incoming, 'Marco', 'Mario Rossi')).toBe('Mario Rossi')
    expect(
      speakerOf(
        { ...incoming, profile_name: 'Mario R.' },
        'Marco',
        'Mario Rossi',
      ),
    ).toBe('Mario R.')
    expect(speakerOf(incoming, 'Marco')).toBe('393295824118')
  })

  it('our own messages are never signed with the other person', () => {
    expect(
      speakerOf(
        { activity_type: 'whatsapp', type: 'Outgoing' },
        'Marco',
        'Mario Rossi',
      ),
    ).toBe('Marco')
  })
})

describe('dayLabel', () => {
  // Wednesday 23 September 2026, late morning
  const now = '2026-09-23 11:00:00'

  it('says Today and Yesterday, which is what a reader is actually asking', () => {
    expect(dayLabel('2026-09-23', now, 'en')).toBe('Today')
    expect(dayLabel('2026-09-22', now, 'en')).toBe('Yesterday')
    // in the reader's language, from the browser: «Yesterday» never had an
    // Italian translation in the catalogue, and «Ieri» needs none this way
    expect(dayLabel('2026-09-23', now, 'it')).toBe('Oggi')
    expect(dayLabel('2026-09-22', now, 'it')).toBe('Ieri')
  })

  it('says tomorrow for an appointment that is tomorrow', () => {
    expect(dayLabel('2026-09-24', now, 'it')).toBe('Domani')
  })

  it('gives the weekday for the rest of the past week', () => {
    expect(dayLabel('2026-09-19', now, 'it')).toBe('Sabato')
    expect(dayLabel('2026-09-17', now, 'en')).toBe('Thursday')
  })

  it('gives the date for anything older, with the year once it is not this one', () => {
    expect(dayLabel('2026-08-16', now, 'it')).toBe('Domenica 16 agosto')
    expect(dayLabel('2025-12-24', now, 'it')).toBe('24 dicembre 2025')
  })

  it('never shows the raw ISO date a reader has to decode', () => {
    expect(dayLabel('2026-04-01', now, 'it')).not.toMatch(/\d{4}-\d{2}/)
  })

  it('counts days by the calendar, not by 24-hour blocks', () => {
    // twenty minutes apart, and yet yesterday
    expect(dayLabel('2026-09-22 23:50:00', '2026-09-23 00:10:00', 'it')).toBe(
      'Ieri',
    )
  })

  it('falls back to what it was given rather than to nothing', () => {
    expect(dayLabel('', now, 'it')).toBe('')
    expect(dayLabel('not a date', now, 'it')).toBe('not a date')
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

describe('buildStream runs', () => {
  const at = (n) => `2026-09-24 11:0${n}:00`
  const wa = (n, type) => ({
    name: `m${n}`,
    activity_type: 'whatsapp',
    type,
    creation: at(n),
  })

  it('signs the first of a run and not the rest', () => {
    const rows = buildStream([
      wa(1, 'Incoming'),
      wa(2, 'Incoming'),
      wa(3, 'Incoming'),
    ])
    expect(rows.map((r) => r.startsRun)).toEqual([true, false, false])
  })

  it('a reply starts a new run, and so does the answer to it', () => {
    const rows = buildStream([
      wa(1, 'Incoming'),
      wa(2, 'Outgoing'),
      wa(3, 'Incoming'),
    ])
    expect(rows.map((r) => r.startsRun)).toEqual([true, true, true])
  })

  it('a change of channel breaks the run even on the same side', () => {
    const rows = buildStream([
      wa(1, 'Incoming'),
      { name: 's2', activity_type: 'sms', type: 'Incoming', creation: at(2) },
    ])
    expect(rows.map((r) => r.startsRun)).toEqual([true, true])
  })
})

describe('buildStream runs, across what breaks them', () => {
  const wa = (n, type, creation) => ({
    name: `m${n}`,
    activity_type: 'whatsapp',
    type,
    creation,
  })

  it('knows where a run ends as well as where it starts', () => {
    const rows = buildStream([
      wa(1, 'Incoming', '2026-09-24 11:01:00'),
      wa(2, 'Incoming', '2026-09-24 11:02:00'),
      wa(3, 'Outgoing', '2026-09-24 11:03:00'),
    ])
    expect(rows.map((r) => r.endsRun)).toEqual([false, true, true])
  })

  it('midnight breaks a run: the date marker sits between the two', () => {
    const rows = buildStream([
      wa(1, 'Incoming', '2026-09-23 23:58:00'),
      wa(2, 'Incoming', '2026-09-24 00:01:00'),
    ])
    expect(rows.map((r) => r.startsRun)).toEqual([true, true])
  })

  it('a call in the middle breaks a run: it is not a balloon', () => {
    const rows = buildStream([
      wa(1, 'Incoming', '2026-09-24 11:01:00'),
      {
        name: 'c1',
        activity_type: 'incoming_call',
        type: 'Incoming',
        creation: '2026-09-24 11:02:00',
      },
      wa(2, 'Incoming', '2026-09-24 11:03:00'),
    ])
    expect(rows.map((r) => r.bubble)).toEqual([true, false, true])
    expect(rows[2].startsRun).toBe(true)
  })
})

describe('buildStream keys and order', () => {
  it('gives every row its own key, even the ones without a name', () => {
    // an email, a field that changed: none of them carries a `name`, and two
    // rows with one key is how Vue patches the wrong one
    const rows = buildStream([
      email(undefined, 'Received', '2026-09-24 10:00:00'),
      email(undefined, 'Sent', '2026-09-24 10:05:00'),
      { activity_type: 'changed', creation: '2026-09-24 10:06:00' },
      { activity_type: 'changed', creation: '2026-09-24 10:06:00' },
    ])
    expect(new Set(rows.map((r) => r.key)).size).toBe(4)
  })

  it('sorts without asking the browser to parse a date', () => {
    // mixed shapes: microseconds, a `T`, none — all read the same way
    const rows = buildStream([
      comment('c', '2026-09-24T10:00:00'),
      comment('a', '2026-09-24 09:00:00.123456'),
      comment('b', '2026-09-24 09:30:00'),
    ])
    expect(rows.map((r) => r.item.name)).toEqual(['a', 'b', 'c'])
  })

  it('puts a row with no time at the end, whichever way it reads', () => {
    const items = [
      comment('late', '2026-09-24 10:00:00'),
      comment('none', null),
      comment('early', '2026-09-24 09:00:00'),
    ]
    expect(buildStream(items).map((r) => r.item.name)).toEqual([
      'early',
      'late',
      'none',
    ])
    expect(
      buildStream(items, { newestFirst: true }).map((r) => r.item.name),
    ).toEqual(['late', 'early', 'none'])
  })

  it('files a row under the reader’s day, not the server’s', () => {
    const rows = buildStream([comment('a', '2026-09-23 23:30:00')], {
      localize: () => '2026-09-24 00:30:00',
    })
    expect(groupByDay(rows)[0].day).toBe('2026-09-24')
  })
})

describe('timeKey and wallClock', () => {
  it('folds the two shapes of a timestamp into one that sorts', () => {
    expect(timeKey('2026-09-24T10:00:00')).toBe('2026-09-24 10:00:00')
    expect(timeKey(null)).toBe('')
  })

  it('reads the server’s timestamp by its parts', () => {
    const date = wallClock('2026-08-16 03:17:42.123456')
    expect(date.getFullYear()).toBe(2026)
    expect(date.getMonth()).toBe(7)
    expect(date.getDate()).toBe(16)
    expect(date.getHours()).toBe(3)
    expect(date.getMinutes()).toBe(17)
  })

  it('says nothing rather than something invented', () => {
    expect(wallClock('')).toBe(null)
    expect(wallClock('yesterday')).toBe(null)
  })
})

describe('clockOf', () => {
  it('is the time and nothing else: the day is on the marker', () => {
    expect(clockOf('2026-08-16 14:05:00', 'it')).toBe('14:05')
    expect(clockOf('2026-08-16 14:05:00', 'en-US')).toMatch(/02:05\sPM/)
  })

  it('has no clock to give for a bare date', () => {
    expect(clockOf('2026-08-16', 'it')).toBe('')
  })
})

describe('listTime', () => {
  const now = '2026-09-23 11:00:00'

  it('is the clock today, and a word for yesterday', () => {
    expect(listTime('2026-09-23 09:12:00', now, 'it')).toBe('09:12')
    expect(listTime('2026-09-22 18:00:00', now, 'it')).toBe('Ieri')
  })

  it('is the weekday this week and the date after that', () => {
    expect(listTime('2026-09-19 18:00:00', now, 'it')).toBe('sab')
    expect(listTime('2026-08-16 18:00:00', now, 'it')).toBe('16 ago')
    expect(listTime('2025-12-24 18:00:00', now, 'it')).toBe('24/12/25')
  })

  it('is empty rather than wrong', () => {
    expect(listTime('', now, 'it')).toBe('')
  })
})

describe('laterLabel', () => {
  const now = '2026-09-23 11:00:00'

  it('says when a conversation comes back, as briefly as it can', () => {
    expect(laterLabel('2026-09-23 17:00:00', now, 'it')).toBe('17:00')
    expect(laterLabel('2026-09-24 09:00:00', now, 'it')).toBe('Domani 09:00')
    expect(laterLabel('2026-09-26 09:00:00', now, 'it')).toBe('sab 09:00')
    expect(laterLabel('2026-10-12 09:00:00', now, 'it')).toBe('12 ott 09:00')
  })
})

describe('replyChannel', () => {
  it('answers where they last wrote from', () => {
    // doc 17's rule, which the composer never kept: it opened on email for a
    // customer who has only ever written on WhatsApp
    expect(
      replyChannel([
        email('e1', 'Received', '2026-09-20 10:00:00'),
        wa('w1', 'Incoming', '2026-09-22 10:00:00'),
        email('e2', 'Sent', '2026-09-23 10:00:00'),
      ]),
    ).toBe('whatsapp')
  })

  it('falls back to where the conversation last went', () => {
    expect(
      replyChannel([
        wa('w1', 'Outgoing', '2026-09-20 10:00:00'),
        email('e1', 'Sent', '2026-09-22 10:00:00'),
      ]),
    ).toBe('email')
  })

  it('never lands on a way this site cannot write in', () => {
    // WhatsApp switched off: its messages are history, not somewhere to answer
    expect(
      replyChannel(
        [
          email('e1', 'Received', '2026-09-20 10:00:00'),
          wa('w1', 'Incoming', '2026-09-22 10:00:00'),
        ],
        ['email', 'comment'],
      ),
    ).toBe('email')
  })

  it('does not take a note for a conversation', () => {
    expect(
      replyChannel([
        wa('w1', 'Incoming', '2026-09-20 10:00:00'),
        comment('c1', '2026-09-22 10:00:00'),
      ]),
    ).toBe('whatsapp')
  })

  it('with nothing said yet, opens on the first way the person can be reached by', () => {
    expect(replyChannel([], WAYS)).toBe('whatsapp')
    expect(replyChannel([], WAYS, { phone: false, email: true })).toBe('email')
    expect(replyChannel([], ['email', 'comment'])).toBe('email')
  })
})

describe('hasFailed', () => {
  it('reads each carrier’s own word for it', () => {
    expect(hasFailed({ activity_type: 'whatsapp', status: 'failed' })).toBe(
      true,
    )
    expect(hasFailed({ activity_type: 'whatsapp', status: 'Failed' })).toBe(
      true,
    )
    expect(hasFailed({ activity_type: 'sms', status: 'Undelivered' })).toBe(
      true,
    )
    expect(
      hasFailed({
        activity_type: 'communication',
        data: { delivery_status: 'Error' },
      }),
    ).toBe(true)
  })

  it('is not alarmed by a message that simply arrived', () => {
    expect(hasFailed({ activity_type: 'whatsapp', status: 'read' })).toBe(false)
    expect(hasFailed({ activity_type: 'comment', status: 'failed' })).toBe(
      false,
    )
  })
})

describe('colleagueOf', () => {
  const out = (owner, extra = {}) => ({
    activity_type: 'whatsapp',
    type: 'Outgoing',
    owner,
    ...extra,
  })

  it('names a colleague who answered', () => {
    expect(colleagueOf(out('giulia@studio.it'), 'marco@studio.it')).toBe(
      'giulia@studio.it',
    )
  })

  it('does not sign the reader’s own messages, nor the machine’s', () => {
    expect(colleagueOf(out('marco@studio.it'), 'marco@studio.it')).toBe('')
    expect(colleagueOf(out('Administrator'), 'marco@studio.it')).toBe('')
    expect(
      colleagueOf(
        out('giulia@studio.it', { written_on_the_phone: 1 }),
        'marco@studio.it',
      ),
    ).toBe('')
  })

  it('reads an email’s sender, which is all an email says about who wrote it', () => {
    expect(
      colleagueOf(
        {
          activity_type: 'communication',
          data: { sent_or_received: 'Sent', sender: 'giulia@studio.it' },
        },
        'marco@studio.it',
      ),
    ).toBe('giulia@studio.it')
  })

  it('has nothing to say about what they sent', () => {
    expect(
      colleagueOf({ activity_type: 'whatsapp', type: 'Incoming', owner: 'x' }),
    ).toBe('')
  })
})

describe('smsSegments', () => {
  it('counts a plain message as one', () => {
    expect(smsSegments('Ci vediamo domani alle 10')).toEqual({
      characters: 25,
      segments: 1,
      perSegment: 160,
      unicode: false,
    })
  })

  it('makes it two past 160, at 153 a piece', () => {
    const long = smsSegments('a'.repeat(161))
    expect(long.segments).toBe(2)
    expect(long.perSegment).toBe(153)
  })

  it('counts the euro and the brackets twice, as the carrier does', () => {
    expect(smsSegments('€10').characters).toBe(4)
  })

  it('knows an Italian È is not in the SMS alphabet', () => {
    // the one that costs money without anybody noticing: 70 a segment, not 160
    const text = smsSegments('È possibile prenotare?')
    expect(text.unicode).toBe(true)
    expect(text.perSegment).toBe(70)
    expect(smsSegments('è possibile').unicode).toBe(false)
  })

  it('counts an emoji as the two units it takes', () => {
    expect(smsSegments('ok 👍').characters).toBe(5)
  })

  it('is nothing for nothing', () => {
    expect(smsSegments('').segments).toBe(0)
  })
})

describe('faces', () => {
  it('gives the same person the same tint every time', () => {
    expect(toneOf('Alessandro Colombo')).toBe(toneOf('Alessandro Colombo'))
    const tones = new Set(
      ['Anna', 'Bruno', 'Carla', 'Dario', 'Elena', 'Fabio', 'Gina'].map(toneOf),
    )
    expect(tones.size).toBeGreaterThan(1)
    for (const tone of tones) expect(tone).toBeLessThan(TONES)
  })

  it('writes two initials, or one for one word', () => {
    expect(initialsOf('Alessandro Colombo')).toBe('AC')
    expect(initialsOf('Maria De Luca')).toBe('ML')
    expect(initialsOf('Atelier')).toBe('A')
    expect(initialsOf('  élodie   durand ')).toBe('ÉD')
    expect(initialsOf('')).toBe('')
    expect(initialsOf('+39 390 648')).toBe('36')
  })
})

describe('momentLabel', () => {
  it('says the whole moment, in the reader’s words', () => {
    expect(momentLabel('2026-10-07 15:00:00', 'it')).toBe('mer 7 ott, 15:00')
    expect(momentLabel('2026-10-07', 'it')).toBe('mer 7 ott')
    expect(momentLabel('', 'it')).toBe('')
  })
})

describe('keepInPlace', () => {
  const row = (name) => ({ name })
  const names = (rows) => rows.map((r) => (r.leaving ? `(${r.name})` : r.name))

  it('shows what the server sent when the one being read is still in it', () => {
    const next = [row('b'), row('a'), row('c')]
    expect(
      names(keepInPlace(next, [row('a'), row('b'), row('c')], 'a')),
    ).toEqual(['b', 'a', 'c'])
  })

  it('keeps the one being read at the height it had when it leaves', () => {
    const shown = [row('a'), row('b'), row('c'), row('d')]
    const next = [row('a'), row('c'), row('d')]
    expect(names(keepInPlace(next, shown, 'b'))).toEqual(['a', '(b)', 'c', 'd'])
  })

  it('keeps it there across the reloads that follow', () => {
    const shown = keepInPlace(
      [row('a'), row('c')],
      [row('a'), row('b'), row('c')],
      'b',
    )
    expect(
      names(keepInPlace([row('x'), row('a'), row('c')], shown, 'b')),
    ).toEqual(['x', '(b)', 'a', 'c'])
  })

  it('lets it go back to being an ordinary row when it comes back', () => {
    const shown = [row('a'), { ...row('b'), leaving: true }, row('c')]
    const back = keepInPlace([row('a'), row('b'), row('c')], shown, 'b')
    expect(back.find((r) => r.name === 'b').leaving).toBeUndefined()
  })

  it('keeps nothing for a row nobody is reading', () => {
    expect(names(keepInPlace([row('a')], [row('a'), row('b')], ''))).toEqual([
      'a',
    ])
    expect(names(keepInPlace([row('a')], [row('a'), row('b')], 'z'))).toEqual([
      'a',
    ])
  })

  it('puts it at the end when the list got shorter than where it was', () => {
    const shown = [row('a'), row('b'), row('c'), row('d')]
    expect(names(keepInPlace([row('a')], shown, 'd'))).toEqual(['a', '(d)'])
  })

  it('does not change the rows it was given', () => {
    const next = [row('a')]
    const shown = [row('a'), row('b')]
    keepInPlace(next, shown, 'b')
    expect(next).toHaveLength(1)
    expect(shown[1].leaving).toBeUndefined()
  })
})

describe('whyItLeft', () => {
  const open = {
    conversation_status: 'Open',
    conversation_snoozed_until: null,
    conversation_unread: 1,
    last_conversation_direction: 'Incoming',
  }

  it('says nothing while the view still holds it', () => {
    expect(whyItLeft(open, 'open')).toBe('')
    expect(whyItLeft(open, 'unanswered')).toBe('')
    expect(whyItLeft(open, 'open', true)).toBe('')
  })

  it('handled takes it out of the live views', () => {
    const handled = { ...open, conversation_status: 'Handled' }
    expect(whyItLeft(handled, 'open')).toBe('handled')
    expect(whyItLeft(handled, 'unanswered')).toBe('handled')
    expect(whyItLeft(handled, 'handled')).toBe('')
  })

  it('put off takes it out of the live views until it is back', () => {
    const parked = {
      ...open,
      conversation_snoozed_until: '2026-10-01 09:00:00',
    }
    expect(whyItLeft(parked, 'open')).toBe('snoozed')
    expect(whyItLeft(parked, 'snoozed')).toBe('')
    expect(whyItLeft(open, 'snoozed')).toBe('reopened')
  })

  it('put back takes it out of the handled ones', () => {
    expect(whyItLeft(open, 'handled')).toBe('reopened')
  })

  it('answered takes it out of the ones waiting for a reply', () => {
    const answered = { ...open, last_conversation_direction: 'Outgoing' }
    expect(whyItLeft(answered, 'unanswered')).toBe('answered')
    expect(whyItLeft(answered, 'open')).toBe('')
  })

  it('read takes it out of the unread, and only there', () => {
    const read = { ...open, conversation_unread: 0 }
    expect(whyItLeft(read, 'open', true)).toBe('read')
    expect(whyItLeft(read, 'open', false)).toBe('')
  })
})

describe('newSince', () => {
  const rows = (items, newestFirst = false) =>
    buildStream(items, { newestFirst })

  it('starts at the first thing they wrote after it was last read', () => {
    const stream = rows([
      wa('1', 'Incoming', '2026-09-28 09:00:00'),
      wa('2', 'Outgoing', '2026-09-28 09:05:00'),
      wa('3', 'Incoming', '2026-09-28 10:00:00'),
      wa('4', 'Incoming', '2026-09-28 10:01:00'),
    ])
    expect(newSince(stream, '2026-09-28 09:30:00')).toEqual({
      key: 'whatsapp:3',
      above: true,
      count: 2,
      channels: ['whatsapp'],
    })
  })

  it('does not count what we wrote', () => {
    const stream = rows([
      wa('1', 'Incoming', '2026-09-28 09:00:00'),
      wa('2', 'Outgoing', '2026-09-28 10:00:00'),
    ])
    expect(newSince(stream, '2026-09-28 09:30:00')).toBeNull()
  })

  it('counts everything they wrote when nobody has ever read it', () => {
    const stream = rows([
      wa('1', 'Incoming', '2026-09-20 09:00:00'),
      email('e', 'Received', '2026-09-21 09:00:00'),
    ])
    const line = newSince(stream, null)
    expect(line.key).toBe('whatsapp:1')
    expect(line.count).toBe(2)
    expect(line.channels.sort()).toEqual(['email', 'whatsapp'])
  })

  it('goes below the oldest new one when the newest is on top', () => {
    const stream = rows(
      [
        wa('1', 'Incoming', '2026-09-28 09:00:00'),
        wa('3', 'Incoming', '2026-09-28 10:00:00'),
        wa('4', 'Incoming', '2026-09-28 10:01:00'),
      ],
      true,
    )
    const line = newSince(stream, '2026-09-28 09:30:00', { newestFirst: true })
    expect(line.key).toBe('whatsapp:3')
    expect(line.above).toBe(false)
  })

  it('is nothing when nothing arrived since', () => {
    const stream = rows([wa('1', 'Incoming', '2026-09-28 09:00:00')])
    expect(newSince(stream, '2026-09-28 09:00:00')).toBeNull()
    expect(newSince([], null)).toBeNull()
  })
})
