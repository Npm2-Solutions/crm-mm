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
export const CHANNELS = [
  { key: 'all', label: 'All' },
  { key: 'email', label: 'Email', bubbles: true },
  { key: 'whatsapp', label: 'WhatsApp', bubbles: true },
  { key: 'sms', label: 'SMS', bubbles: true },
  { key: 'comment', label: 'Comments' },
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
 * @param {Array} items    activities, already merged by the caller
 * @param {{channel?: string, newestFirst?: boolean}} options
 */
export function buildStream(items = [], options = {}) {
  const channel = options.channel || 'all'
  const direction = options.newestFirst ? -1 : 1

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

  return kept
    .map((item) => ({
      key: `${channelOf(item) || item.activity_type || 'item'}:${item.name}`,
      item,
      channel: channelOf(item),
      direction: directionOf(item),
      at: item.creation || item.communication_date || null,
    }))
    .sort((a, b) => direction * (new Date(a.at) - new Date(b.at)))
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
 * The same stream, with a marker wherever the day changes.
 *
 * A long conversation is a wall of times with no dates: «12:57» tells you
 * nothing about whether that was today or in April. Every messenger answers it
 * the same way — a date between the days, pinned to the top while its day is
 * the one on screen — and it costs one row rather than a date on every message.
 *
 * `today` is passed in rather than read from the clock, so «Today» means the
 * same thing in a test as it does on screen.
 */
export function withDayMarkers(rows = [], today = '') {
  const out = []
  let previous = null
  for (const row of rows || []) {
    const day = dayOf(row.at)
    if (day && day !== previous) {
      out.push({ key: `day:${day}`, kind: 'day', at: row.at, day })
      previous = day
    }
    out.push(row)
  }
  return out
}

/** `Today`, `Yesterday`, or the date itself — the label on a day marker. */
export function dayLabel(day, today = '', yesterday = '') {
  if (day && day === dayOf(today)) return 'Today'
  if (day && day === dayOf(yesterday)) return 'Yesterday'
  return day
}
