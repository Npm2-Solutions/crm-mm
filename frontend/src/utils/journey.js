/**
 * The tracking history of a lead, arranged for reading.
 *
 * Kept out of the component because the arrangement is the substance: what goes
 * on the timeline, in which order, and what is left off it.
 *
 * It used to be three things on one screen — the ad in a card, the two
 * attribution snapshots in two more, and a timeline of visits below them. Three
 * boxes, three readings, and the one question anybody actually asks — *what
 * happened, in what order* — answered by none of them. There is one stream now,
 * and nothing on it is placed by what kind of thing it is: everything sits at
 * the moment it happened, the record's own arrival included.
 */

/**
 * Same timestamp, different things: the order they belong in.
 *
 * Only a tie-break. A lead from an ad form has its ad, its attribution and its
 * arrival all stamped at the same second, and this is the sequence they
 * actually occurred in: the ad was seen, it was credited, the record appeared.
 */
const RANK = { ad: 0, touch: 1, visit: 2, event: 3, record: 4 }

function oldest(...times) {
  const known = times.flat().filter(Boolean)
  if (!known.length) return null
  return known.reduce((a, b) => (String(b) < String(a) ? b : a))
}

/**
 * One stream: the ad, the two touches, every visit and every event, in the
 * order they happened.
 *
 * Flat rather than nested. A page view is grouped under the visit that produced
 * it only to say which campaign it belonged to, and in a list ordered by time a
 * visit already sits immediately beside its own events — so the grouping was
 * paying for context that time gives away for free. It also had a flaw: an
 * event whose visit fell off the end of the response needed a fictional visit
 * to hang from. Here it simply appears where it happened.
 *
 * @param {object} journey  as returned by `crm.api.tracking.get_journey`, plus
 *   an optional `ad` from `crm.integrations.meta.api.get_record_ad`
 * @param {{ newestFirst?: boolean }} options  direction, from the CRM's own
 *   timeline preference, so this reads the same way round as the Activity tab
 * @returns {Array<{key: string, kind: string, at: string|null, data: object}>}
 */
export function buildTimeline(journey = {}, options = {}) {
  const sessions = journey.sessions || []
  const events = journey.events || []
  const firstTouch = journey.first_touch || {}
  const lastTouch = journey.last_touch || {}
  const ad = journey.ad || {}

  const rows = []

  if (ad.ad_id) {
    // Meta never says when the ad was *seen*, and that is not the useful moment
    // anyway. The useful moment is when it brought this person here: the touch
    // it produced, or — for a lead that arrived straight from an ad form, with
    // no browsing behind it — the instant the record was created, which is the
    // same event described from this side.
    //
    // It is placed by that time like everything else. It was pinned to the top
    // at first, on the assumption that the ad always comes first; it does not.
    // Somebody can read a page, leave, and meet the ad a week later.
    rows.push({
      key: `ad:${ad.ad_id}`,
      kind: 'ad',
      at:
        firstTouch.on ||
        journey.created_on ||
        oldest(
          sessions.map((s) => s.started_on),
          events.map((e) => e.occurred_on),
        ),
      data: ad,
    })
  }

  if (firstTouch.on || firstTouch.category) {
    rows.push({
      key: 'touch:first',
      kind: 'touch',
      at: firstTouch.on || null,
      data: { ...firstTouch, which: 'first' },
    })
  }

  // Only when it is a different moment. A lead that arrived and never came back
  // has both snapshots pointing at the same visit, and a timeline that says the
  // same thing twice in a row reads as a bug.
  const lastIsSeparate =
    (lastTouch.on || lastTouch.category) &&
    (lastTouch.on !== firstTouch.on || lastTouch.session !== firstTouch.session)
  if (lastIsSeparate) {
    rows.push({
      key: 'touch:last',
      kind: 'touch',
      at: lastTouch.on || null,
      data: { ...lastTouch, which: 'last' },
    })
  }

  for (const visit of sessions) {
    rows.push({
      key: `visit:${visit.name}`,
      kind: 'visit',
      at: visit.started_on || null,
      data: visit,
    })
  }

  for (const event of events) {
    rows.push({
      key: `event:${event.name}`,
      kind: 'event',
      at: event.occurred_on || null,
      data: event,
    })
  }

  // When it landed here. For a lead off an ad form this is the whole journey —
  // there is no browsing behind it — and even where there is, it is the line
  // that says when the browsing stopped being anonymous.
  if (journey.created_on) {
    rows.push({
      key: 'record',
      kind: 'record',
      at: journey.created_on,
      data: { doctype: journey.doctype || '' },
    })
  }

  const direction = options.newestFirst ? -1 : 1
  return rows.sort((a, b) => {
    // Nothing here is placed by what kind of thing it is. A row with no time at
    // all cannot be placed, so it goes to the end rather than jumping a queue
    // it has no claim on.
    if (!a.at && !b.at) return RANK[a.kind] - RANK[b.kind]
    if (!a.at) return 1
    if (!b.at) return -1
    if (a.at === b.at) return RANK[a.kind] - RANK[b.kind]
    return direction * (new Date(a.at) - new Date(b.at))
  })
}

/** Seconds as something a person reads: `45s`, `2m 10s`, `1h 05m`. */
export function readableDuration(seconds) {
  const total = Number(seconds) || 0
  if (total < 60) return `${total}s`
  const minutes = Math.floor(total / 60)
  if (minutes < 60) return `${minutes}m ${total % 60}s`
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}m`
}
