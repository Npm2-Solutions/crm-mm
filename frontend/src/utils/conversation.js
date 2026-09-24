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

/** Which channel an item belongs to, or `''` for everything else. */
export function channelOf(item) {
  const type = item?.activity_type || ''
  if (type === 'whatsapp') return 'whatsapp'
  if (type === 'sms') return 'sms'
  if (type === 'communication') return 'email'
  if (type === 'comment') return 'comment'
  if (type === 'incoming_call' || type === 'outgoing_call') return 'call'
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
  if (channel === 'call') return item.type === 'Incoming' ? 'in' : 'out'
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

  const kept = (items || []).filter((item) => {
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
