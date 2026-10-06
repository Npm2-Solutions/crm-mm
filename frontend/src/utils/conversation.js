// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * One conversation out of four channels, arranged for reading.
 *
 * Email, WhatsApp, SMS and comments each had a tab of their own, so the one
 * question anybody asks of a record — *what has been said to this person, and in
 * what order* — could only be answered by opening four tabs and holding three of
 * them in your head.
 *
 * The arrangement lives here rather than in the component because the
 * arrangement is the decision: what counts as a channel, which way a message
 * went, and which things have a direction at all.
 */

/**
 * The channels the selector offers.
 *
 * `bubbles` is the one that matters. A message between two people has a
 * direction, and a chat reads it at a glance. A comment, a note, a field that
 * changed — those are not addressed to anybody: giving them a side would invent
 * a sender and a recipient that do not exist, so they take the full width.
 */
//
// In the order they are used. WhatsApp first, because on this CRM it is the
// channel a conversation usually happens on, not the third one; the note last,
// because it is the one thing here nobody outside will ever read. The composer
// offers its ways in the same order (WAYS, below), so the pill you read by and
// the tab you write in sit in the same place.
export const CHANNELS = [
  { key: 'all', label: 'All' },
  { key: 'whatsapp', label: 'WhatsApp', bubbles: true },
  { key: 'email', label: 'Email', bubbles: true },
  { key: 'sms', label: 'SMS', bubbles: true },
  // The call register, which was a tab of its own. What somebody asks of a
  // record is what has been said to this person and in what order, and a phone
  // call is one of the things said — it does not belong one level up from the
  // conversation it is part of.
  { key: 'call', label: 'Calls' },
  // what colleagues write for each other: the person never reads it
  { key: 'comment', label: 'Internal notes' },
]

/**
 * The bare file name, from a path, a full URL or a name on its own.
 *
 * Outgoing media no longer travels as `/files/…`: it goes through the signed
 * endpoint that tells Meta what the file is, and the real name is a query
 * parameter there. Reading only the path would give `media` for every one of
 * them, and every voice note would go back to appearing twice.
 */
export function fileNameOf(pathOrUrl) {
  const raw = String(pathOrUrl || '')
  const named = /[?&]file=([^&#]+)/.exec(raw)
  const clean = (named ? decodeURIComponent(named[1]) : raw)
    .split('?')[0]
    .split('#')[0]
  return decodeURIComponent(clean.split('/').pop() || '')
}

/** Which channel an item belongs to, or `''` for everything else. */
export function channelOf(item) {
  const type = item?.activity_type || ''
  if (type === 'whatsapp') return 'whatsapp'
  if (type === 'sms') return 'sms'
  if (type === 'communication') return 'email'
  if (type === 'comment') return 'comment'
  if (type === 'incoming_call' || type === 'outgoing_call') return 'call'
  // things that happened rather than things that were said. They take no side
  // — an appointment is addressed to nobody — but they are the half of the
  // history that says what was actually done between one message and the next.
  if (type === 'appointment') return 'appointment'
  if (type === 'event') return 'event'
  if (type === 'task') return 'task'
  if (type === 'note') return 'note'
  if (type === 'invoice') return 'invoice'
  // a visit: that it happened and who saw them, behind a padlock
  if (type === 'clinical') return 'clinical'
  // A call is the one row whose channel is derived rather than stored: without
  // a readable `type` the backend writes no `activity_type` at all, and the
  // call would quietly leave the conversation instead of taking a side in it.
  if (!type && (item?.telephony_medium || item?.duration !== undefined)) {
    if (item.type === 'Incoming' || item.type === 'Outgoing') return 'call'
  }
  return ''
}

/**
 * Which way it went: `out` from us, `in` from them, `internal` for neither.
 *
 * Each channel words this differently — `type` on a message, `sent_or_received`
 * on an email, nothing at all on a comment — and reading the wrong field is how
 * a reply ends up on the side it was sent from.
 */
export function directionOf(item) {
  const channel = channelOf(item)
  if (channel === 'whatsapp' || channel === 'sms')
    return item.type === 'Outgoing' ? 'out' : 'in'
  if (channel === 'call') {
    // The side says who picked up the phone, so it must not hang on a single
    // field. The backend words it twice — `activity_type` is derived from
    // `type` when the call is read — and a row that reached this stream by
    // another road may carry only one of them.
    if (item.activity_type === 'incoming_call') return 'in'
    if (item.activity_type === 'outgoing_call') return 'out'
    return item.type === 'Incoming' ? 'in' : 'out'
  }
  if (channel === 'email') {
    const said = item.data?.sent_or_received || item.sent_or_received || ''
    if (said) return said === 'Received' ? 'in' : 'out'
    // An older row without the field: an automated message is ours, and
    // anything else is safer read as arriving than as sent in our name.
    return item.communication_type === 'Automated Message' ? 'out' : 'in'
  }
  return 'internal'
}

/**
 * Who said it, for the line above the message.
 *
 * In a mixed history the side of the screen cannot carry this: left and right
 * mean «them» and «us» inside *one* conversation, and a history holds four of
 * them plus everything the record did to itself. So it is written, once, in
 * words — and the arrangement stops having to encode it.
 */
export function speakerOf(item, me = '', them = '') {
  const channel = channelOf(item)
  const direction = directionOf(item)
  if (direction === 'out') return me || 'You'
  if (channel === 'whatsapp' || channel === 'sms')
    // WhatsApp hands over a profile name only when the person publishes one, so
    // the usual fallback was the raw number — fifteen digits standing where a
    // name goes, on a record that knows perfectly well whose number it is. The
    // record's own name comes first; the number is what is left when nothing
    // else knows either.
    return item.profile_name || them || item.from || ''
  if (channel === 'email')
    return item.data?.sender_full_name || item.data?.sender || item.sender || ''
  if (channel === 'call') return item._caller?.label || ''
  return item.owner_name || item.owner || ''
}

/**
 * Did this change where the person stands in the pipeline?
 *
 * Every other field that changes is bookkeeping — a phone number corrected, a
 * source filled in — and reads as one quiet line. The stage is the one that is
 * the point of the whole record, so it is worth telling apart from the rest.
 */
const STAGE_FIELDS = new Set(['status', 'deal_status', 'lead_status'])

export function isStageChange(item) {
  if (item?.activity_type !== 'changed') return false
  return STAGE_FIELDS.has(item?.data?.field || item?.field || '')
}

/** Does this one read as a chat bubble, or as a full-width card? */
export function isConversational(item) {
  return directionOf(item) !== 'internal'
}

/**
 * The stream for one channel, or for all of them together.
 *
 * `all` keeps everything — the four channels, the calls, and the record's own
 * history — because that is the point of it. A single channel keeps only its
 * own, so the WhatsApp view is a WhatsApp conversation and nothing else.
 *
 * `localize` turns the server's clock into the reader's, when the two differ:
 * a message written at 23:30 in Rome belongs to the next day in London, and the
 * day it is filed under is the day the reader sees.
 *
 * @param {Array} items    activities, already merged by the caller
 * @param {{channel?: string, newestFirst?: boolean, localize?: Function}} options
 */
export function buildStream(items = [], options = {}) {
  const channel = options.channel || 'all'
  const direction = options.newestFirst ? -1 : 1
  const localize = options.localize || ((at) => at)

  // Every file sent as a message is also written down as an attachment on the
  // record, so in one stream a voice note appeared twice: once as the bubble
  // somebody sent, and once as a line saying a file was attached. The bubble is
  // the event; the log line is bookkeeping about it.
  const sentFiles = new Set()
  for (const item of items || []) {
    const attached = item?.attach || ''
    if (channelOf(item) && attached) sentFiles.add(fileNameOf(attached))
  }

  const kept = (items || []).filter((item) => {
    if (item?.activity_type === 'attachment_log') {
      const named = fileNameOf(
        item.data?.file_name || item.data?.file_url || '',
      )
      if (named && sentFiles.has(named)) return false
    }
    if (channel === 'all') return true
    return channelOf(item) === channel
  })

  const rows = kept
    .map((item, index) => {
      const kind = channelOf(item) || item.activity_type || 'item'
      const when = item.creation || item.communication_date || null
      const rowChannel = channelOf(item)
      const rowDirection = directionOf(item)
      return {
        // An email, a field that changed, the record being created: none of
        // them carries a `name`, so keying by it gave every email in a stream
        // the same key — and Vue, handed two rows with one key, patches the
        // wrong one when the list changes.
        key: item.name ? `${kind}:${item.name}` : `${kind}:${when}:${index}`,
        item,
        channel: rowChannel,
        direction: rowDirection,
        at: when ? localize(when) : null,
        // a balloon: something one side said to the other. A call has no words
        // and a note is addressed to nobody, so neither is one.
        bubble: rowDirection !== 'internal' && rowChannel !== 'call',
      }
    })
    // Compared as text, not as `new Date(text)`: the server writes
    // «2026-08-16 03:17:00», which is not a format the language promises to
    // read — older Safari answers Invalid Date, and a comparator fed NaN leaves
    // a conversation in no order at all. The text sorts in time order as it is.
    // A row with no time goes to the end, whichever way the stream reads: it
    // has no claim on a place in a queue ordered by time.
    .sort((a, b) => {
      if (!a.at || !b.at) return (a.at ? 0 : 1) - (b.at ? 0 : 1)
      return direction * compareTimes(a.at, b.at)
    })

  // Who said it, written once per run rather than once per message.
  //
  // Somebody sending four lines in a row is one person talking, and signing
  // each of the four with their name turns a two-word message into three
  // stacked rows — the name, the words, the clock — which is how a chat starts
  // reading like a table. A run breaks when the channel changes, when the side
  // changes, when something else happens in between, and at midnight: the date
  // marker between two days is something happening in between too.
  const continues = (a, b) =>
    Boolean(a && b && a.bubble && b.bubble) &&
    a.channel === b.channel &&
    a.direction === b.direction &&
    dayOf(a.at) === dayOf(b.at)
  rows.forEach((row, i) => {
    row.startsRun = !continues(rows[i - 1], row)
    row.endsRun = !continues(row, rows[i + 1])
  })
  return rows
}

/** Two timestamps in time order, as text: -1, 0 or 1. */
function compareTimes(a, b) {
  const x = timeKey(a)
  const y = timeKey(b)
  return x < y ? -1 : x > y ? 1 : 0
}

/**
 * A timestamp as a string that sorts in time order.
 *
 * The server writes «2026-08-16 03:17:00.123456»; the browser, when it writes
 * one back, puts a `T` where the space goes. Folded to one shape, the text
 * compares in the order the moments happened.
 */
export function timeKey(at) {
  return String(at || '').replace('T', ' ')
}

/** How many there are per channel, for the count beside each selector chip. */
export function countByChannel(items = []) {
  const tally = {}
  for (const item of items || []) {
    const channel = channelOf(item)
    if (channel) tally[channel] = (tally[channel] || 0) + 1
  }
  tally.all = (items || []).length
  return tally
}

/** The day part of a timestamp, as the string the rest of this file compares. */
function dayOf(at) {
  return String(at || '').slice(0, 10)
}

/**
 * Whether a message opens a run — one side speaking, on one day — and so
 * carries the bubble's tail. For the channel views, which draw one channel's
 * messages as a plain list rather than the mixed stream `buildStream` makes
 * (where `startsRun` says the same thing).
 */
export function opensRun(messages = [], index = 0) {
  const here = messages?.[index]
  if (!here) return false
  const before = messages[index - 1]
  if (!before) return true
  return (
    before.type !== here.type || dayOf(before.creation) !== dayOf(here.creation)
  )
}

/**
 * The same stream, cut into one group per day.
 *
 * A long conversation is a wall of times with no dates: «12:57» tells you
 * nothing about whether that was today or in April. Every messenger answers it
 * the same way — one marker where a day begins, and while you scroll, the day
 * you are looking at floats at the top.
 */
export function groupByDay(rows = []) {
  const out = []
  for (const row of rows || []) {
    const day = dayOf(row.at)
    const last = out[out.length - 1]
    if (last && last.day === day) {
      last.rows.push(row)
      continue
    }
    out.push({ key: `day:${day}:${out.length}`, day, rows: [row] })
  }
  return out
}

// -- time, in the reader's words ---------------------------------------------
//
// Everything below takes the moment it calls «now» as an argument instead of
// reading the clock, so «today» means the same thing in a test as on screen, and
// a locale, so the words are the reader's: callers pass `appLocale()`, the
// language the rest of the CRM speaks to them (`undefined` falls back to the
// browser's own).

/**
 * A timestamp as the server writes it, read into a `Date` on the wall clock.
 *
 * By its parts, not by handing the string to `new Date`: «2026-08-16 03:17:00»
 * is not a format the language promises to parse, and older Safari — on the
 * phones half of this CRM's users answer WhatsApp from — returns Invalid Date.
 */
export function wallClock(at) {
  if (at instanceof Date) return isNaN(at) ? null : at
  const parts =
    /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(
      String(at || ''),
    )
  if (!parts) return null
  const [, y, m, d, hh = 0, mm = 0, ss = 0] = parts
  return new Date(+y, +m - 1, +d, +hh, +mm, +ss)
}

function midnight(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

/** Whole days from `then` to `now`: 0 today, 1 yesterday, -1 tomorrow. */
function daysBetween(then, now) {
  // rounded, because a day with a clock change in it is 23 or 25 hours long
  return Math.round((midnight(now) - midnight(then)) / 86400000)
}

function capitalized(text, locale) {
  const value = String(text || '')
  return value.charAt(0).toLocaleUpperCase(locale) + value.slice(1)
}

function relativeDay(offset, locale) {
  // «oggi», «ieri», «domani» — the browser has the words in every language, so
  // they need no translation of ours (and «Yesterday» never had an Italian one)
  const words = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  return capitalized(words.format(offset, 'day'), locale)
}

/**
 * The label on a day's marker.
 *
 * «Oggi» and «Ieri», because that is what somebody looking at a date is really
 * asking. The weekday for the rest of the past week — «martedì» is nearer than
 * «22 settembre» when it was four days ago. The date for anything older, with
 * the weekday while it is this year and the year once it is not.
 */
export function dayLabel(day, today, locale) {
  const date = wallClock(day)
  const now = wallClock(today)
  if (!date || !now) return String(day || '')
  const offset = daysBetween(date, now)
  if (offset >= -1 && offset <= 1) return relativeDay(-offset, locale)
  if (offset > 1 && offset < 7) {
    return capitalized(
      new Intl.DateTimeFormat(locale, { weekday: 'long' }).format(date),
      locale,
    )
  }
  const thisYear = date.getFullYear() === now.getFullYear()
  return capitalized(
    new Intl.DateTimeFormat(locale, {
      weekday: thisYear ? 'long' : undefined,
      day: 'numeric',
      month: 'long',
      year: thisYear ? undefined : 'numeric',
    }).format(date),
    locale,
  )
}

/** The clock on a message: «14:05», the 24-hour clock in every language. */
export function clockOf(at, locale) {
  const date = wallClock(at)
  if (!date || !/\d{2}:\d{2}/.test(String(at))) return ''
  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(date)
}

/**
 * The time on a row of the conversation list, as short as it can be and still
 * be read without thinking: the clock today, «Ieri», the weekday this week, the
 * date after that. «3 days ago» on every row of a list says the same thing
 * forty times and tells nobody which of two rows came first.
 */
export function listTime(at, now, locale) {
  const date = wallClock(at)
  const reference = wallClock(now)
  if (!date || !reference) return ''
  const offset = daysBetween(date, reference)
  if (offset <= 0) return clockOf(at, locale)
  if (offset === 1) return relativeDay(-1, locale)
  if (offset < 7) {
    return new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(date)
  }
  if (date.getFullYear() === reference.getFullYear()) {
    return new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'short',
    }).format(date)
  }
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  }).format(date)
}

/**
 * A moment ahead, for a conversation put off until then: «09:00» later today,
 * «Domani 09:00», «lun 09:00» this week, «12 ott 09:00» after that.
 */
export function laterLabel(at, now, locale) {
  const date = wallClock(at)
  const reference = wallClock(now)
  if (!date || !reference) return ''
  const clock = clockOf(at, locale)
  const ahead = -daysBetween(date, reference)
  if (ahead <= 0) return clock
  if (ahead === 1) return `${relativeDay(1, locale)} ${clock}`
  const day =
    ahead < 7
      ? new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(date)
      : new Intl.DateTimeFormat(locale, {
          day: 'numeric',
          month: 'short',
        }).format(date)
  return `${day} ${clock}`
}

/**
 * A moment in full, for the one thing in a chat that is not filed under the day
 * it happened: an appointment is in the history when it was booked for, and
 * «mer 8 ott, 15:00» is the fact about it.
 */
export function momentLabel(at, locale) {
  const date = wallClock(at)
  if (!date) return ''
  const day = new Intl.DateTimeFormat(locale, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(date)
  const clock = clockOf(at, locale)
  return clock ? `${day}, ${clock}` : day
}

// -- answering ------------------------------------------------------------------

/** The ways somebody can write from the composer, in the order it offers them. */
export const WAYS = ['whatsapp', 'email', 'sms', 'comment']

/**
 * Which way the composer opens on: the channel they last wrote from.
 *
 * Doc 17 set the rule — in «All» the box starts on the channel of the last
 * message received, so you answer where you were written to without thinking
 * about it — and the composer never kept it: it opened on email whatever the
 * conversation was, and a customer who only ever writes on WhatsApp got «Write
 * an email…» under every one of their messages.
 *
 * Failing a message from them, where the conversation last went. Failing that,
 * the first way this site can write that the person can be reached by: no
 * number means no WhatsApp, however much the site would prefer it.
 *
 * @param {Array} items         the conversation, any order
 * @param {string[]} ways       what this site can write in, in order of preference
 * @param {{phone?: boolean, email?: boolean}} reachable  what the person has
 */
export function replyChannel(items = [], ways = WAYS, reachable = {}) {
  const writable = new Set(ways)
  let lastIn = null
  let lastAny = null
  for (const item of items || []) {
    const channel = channelOf(item)
    if (!writable.has(channel)) continue
    const direction = directionOf(item)
    if (direction === 'internal') continue
    const at = timeKey(item.creation || item.communication_date)
    if (direction === 'in' && (!lastIn || at >= lastIn.at))
      lastIn = { channel, at }
    if (!lastAny || at >= lastAny.at) lastAny = { channel, at }
  }
  if (lastIn) return lastIn.channel
  if (lastAny) return lastAny.channel
  const needs = { whatsapp: 'phone', sms: 'phone', email: 'email' }
  const open = ways.find((way) => reachable[needs[way]] !== false)
  return open || ways[0] || 'email'
}

/**
 * Did a message we sent fail to arrive? Each carrier says it in its own words:
 * Meta writes `failed` in lower case, a send that never left says `Failed`,
 * Twilio adds `Undelivered`, and an email says `Error`.
 */
export function hasFailed(item) {
  const channel = channelOf(item)
  const status = String(item?.status || '').toLowerCase()
  if (channel === 'whatsapp') return status === 'failed'
  if (channel === 'sms') return status === 'failed' || status === 'undelivered'
  if (channel === 'email')
    return (item?.data?.delivery_status || item?.delivery_status) === 'Error'
  return false
}

/**
 * Who on our side sent it, when that is worth saying: a colleague. Not the
 * reader — a chat that signs your own messages with your own name is a chat
 * nobody would use — and not the machine: a message from an automation or from
 * the phone has its own mark, and «Administrator» above it would be noise.
 */
export function colleagueOf(item, me = '') {
  if (directionOf(item) !== 'out') return ''
  if (item?.written_on_the_phone) return ''
  // an email says who sent it in `sender`, and carries no owner of its own
  const owner = item?.owner || item?.data?.sender || ''
  if (!owner || owner === me) return ''
  if (owner === 'Administrator' || owner === 'Guest') return ''
  return owner
}

// -- SMS ----------------------------------------------------------------------

// GSM 03.38, the alphabet an SMS is written in when it can be: one unit a
// character, and the second table two. Anything outside it — an emoji, but also
// an Italian «È», which GSM has only as «É» — turns the whole message into
// UCS-2, where a segment holds 70 instead of 160.
const GSM_BASIC =
  '@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?' +
  '¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà'
const GSM_EXTENDED = '^{}\\[~]|€\f'

/**
 * How long an SMS is, the way the carrier counts it: characters, how many
 * messages it will be billed as, and how many fit in each.
 *
 * Doc 17 asked for the counter because an SMS is the one message whose length
 * costs money: past 160 characters it is two messages, and one «È» — which the
 * GSM alphabet does not have — quietly makes a 100-character text two messages
 * as well.
 */
export function smsSegments(text) {
  const value = String(text || '')
  let units = 0
  let unicode = false
  for (const char of value) {
    if (GSM_BASIC.includes(char)) units += 1
    else if (GSM_EXTENDED.includes(char)) units += 2
    else {
      unicode = true
      break
    }
  }
  // UCS-2 counts UTF-16 code units, so an emoji is two
  if (unicode) units = value.length
  const single = unicode ? 70 : 160
  const multi = unicode ? 67 : 153
  const segments = !units ? 0 : units <= single ? 1 : Math.ceil(units / multi)
  return {
    characters: units,
    segments,
    perSegment: segments > 1 ? multi : single,
    unicode,
  }
}

// -- faces --------------------------------------------------------------------

/** How many tints a face without a photo can take. */
export const TONES = 8

/**
 * The tint of somebody's initials, the same every time for the same person.
 *
 * Forty grey circles with a letter in them is a column the eye has to read one
 * by one; a tint that stays with a person is how a list of chats lets you find
 * somebody before you have read their name.
 */
export function toneOf(seed) {
  let hash = 0
  for (const char of String(seed || '')) {
    hash = (hash * 31 + char.codePointAt(0)) >>> 0
  }
  return hash % TONES
}

/** «Alessandro Colombo» → «AC»; one word gives one letter. */
export function initialsOf(name) {
  const words = String(name || '')
    .trim()
    .split(/\s+/)
    .filter((word) => /\p{L}|\p{N}/u.test(word))
  if (!words.length) return ''
  const first = [...words[0]].find((char) => /\p{L}|\p{N}/u.test(char)) || ''
  if (words.length === 1) return first.toLocaleUpperCase()
  const lastWord = words[words.length - 1]
  const last = [...lastWord].find((char) => /\p{L}|\p{N}/u.test(char)) || ''
  return (first + last).toLocaleUpperCase()
}

// -- while somebody works through the list ------------------------------------

/**
 * The rows on screen after a reload, with the one being read kept where it was.
 *
 * A decision about the conversation you are in — handled, put off, read while
 * the list shows only the unread — takes it out of the view on the server.
 * Taking it off the screen as well, from under the pointer, is how a list
 * loses somebody: the row vanishes, the one below slides into its place, and
 * the next click lands on a person nobody chose. So it stays at the height it
 * had, marked as leaving, until you move on — another conversation, another
 * view, a search.
 *
 * @param {Array} next    the rows the server has just sent
 * @param {Array} shown   the rows on screen until now, a leaving one included
 * @param {string} active the conversation being read
 * @returns {Array} the rows to show; the kept one carries `leaving: true`
 */
export function keepInPlace(next = [], shown = [], active = '') {
  const rows = [...(next || [])]
  if (!active || rows.some((row) => row.name === active)) return rows
  const at = (shown || []).findIndex((row) => row.name === active)
  if (at < 0) return rows
  return [
    ...rows.slice(0, at),
    { ...shown[at], leaving: true },
    ...rows.slice(at),
  ]
}

/**
 * Why the conversation being read is no longer in the view on screen — the
 * words on the row it leaves behind. Empty when the view still holds it, or
 * when it only slid past the end of the page.
 *
 * @param {object} row          the conversation, as it is now
 * @param {string} view         open | unanswered | snoozed | handled
 * @param {boolean} onlyUnread  whether the list shows only the unread
 * @returns {'' | 'handled' | 'snoozed' | 'answered' | 'reopened' | 'read'}
 */
export function whyItLeft(row = {}, view = 'open', onlyUnread = false) {
  const handled = row?.conversation_status === 'Handled'
  const parked = Boolean(row?.conversation_snoozed_until)
  if (view === 'handled' && !handled) return 'reopened'
  if (view === 'snoozed' && !parked) return handled ? 'handled' : 'reopened'
  if (view === 'open' || view === 'unanswered') {
    if (handled) return 'handled'
    if (parked) return 'snoozed'
    if (
      view === 'unanswered' &&
      row?.last_conversation_direction !== 'Incoming'
    )
      return 'answered'
  }
  if (onlyUnread && !row?.conversation_unread) return 'read'
  return ''
}

/**
 * Where the new messages begin, for the line in the conversation that says so.
 *
 * New is what they wrote after the conversation was last read — the cutoff the
 * number on the row counts from. The caller measures it when the conversation
 * is opened and holds it there while it stays open, so reading it, or
 * answering, does not pull the line out from under the messages it points at.
 * Only theirs count: what we wrote in between is not news to us.
 *
 * The line goes on the time side of the oldest new message: above it when the
 * stream reads down, below it when the newest is on top.
 *
 * @param {Array} rows             the stream as shown (`buildStream`)
 * @param {string|null} since      the cutoff on the reader's clock; null = never read
 * @param {{newestFirst?: boolean}} options
 * @returns {{key: string, above: boolean, count: number, channels: string[]} | null}
 */
export function newSince(rows = [], since = null, options = {}) {
  const fresh = (rows || []).filter(
    (row) =>
      row.bubble &&
      row.direction === 'in' &&
      row.at &&
      (!since || timeKey(row.at) > timeKey(since)),
  )
  if (!fresh.length) return null
  const oldest = fresh.reduce((a, b) => (timeKey(b.at) < timeKey(a.at) ? b : a))
  return {
    key: oldest.key,
    above: !options.newestFirst,
    count: fresh.length,
    channels: [...new Set(fresh.map((row) => row.channel))],
  }
}

/**
 * Whether the channel being read hides every message the person sent since the
 * conversation was last read - the ones the conversations screen opened it to
 * show. The channel is remembered from the last record read: left on its notes,
 * a conversation opened on a new email showed «no notes yet» and nothing else.
 *
 * @param {Array} items            what the conversation is made of
 * @param {string} channel         the channel being read
 * @param {string|null} since      the cutoff on the reader's clock; null = never read
 * @param {{localize?: Function}} options  as `buildStream`'s
 */
export function hidesTheNew(
  items = [],
  channel = 'all',
  since = null,
  options = {},
) {
  if (!channel || channel === 'all') return false
  const newIn = (which) =>
    newSince(buildStream(items, { ...options, channel: which }), since)
  return Boolean(newIn('all')) && !newIn(channel)
}
