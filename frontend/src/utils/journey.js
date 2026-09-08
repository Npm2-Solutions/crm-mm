/**
 * The tracking history of a lead, arranged for reading.
 *
 * Kept out of the component because the arrangement is the substance: which
 * events belong to which visit, what happens to the ones whose visit isn't in
 * the response, and which way round the whole thing reads.
 */

/**
 * Group a journey into one stream: every visit, with the events that happened
 * inside it hanging off it.
 *
 * Grouped by visit rather than a flat list of events, because a page view means
 * little without the campaign that produced the visit — "read the pricing page"
 * and "read the pricing page, having arrived from the summer ad" are different
 * facts.
 *
 * @param {Array} sessions  visits, as returned by `crm.api.tracking.get_journey`
 * @param {Array} events    tracking events, same source
 * @param {{ newestFirst?: boolean }} options  sort direction, from the CRM's
 *   own timeline preference so this reads the same way round as the Activity tab
 * @returns {Array} visits, each with an `events` array, sorted throughout
 */
export function groupJourney(sessions = [], events = [], options = {}) {
  const byName = new Map(
    (sessions || []).map((s) => [s.name, { ...s, events: [] }]),
  )
  const orphans = []

  for (const event of events || []) {
    const visit = byName.get(event.session)
    if (visit) visit.events.push(event)
    else orphans.push(event)
  }

  const visits = [...byName.values()]
  if (orphans.length) {
    // An event whose visit isn't in the response: the journey returns the most
    // recent visits, so older ones fall off the end. Showing the events anyway
    // beats letting them disappear from a timeline meant to be complete.
    visits.push({
      name: '__unknown_visit__',
      unknown: true,
      started_on: orphans.reduce(
        (earliest, e) => (e.occurred_on < earliest ? e.occurred_on : earliest),
        orphans[0].occurred_on,
      ),
      events: orphans,
    })
  }

  const direction = options.newestFirst ? -1 : 1
  const byTime = (field) => (a, b) =>
    direction * (new Date(a[field]) - new Date(b[field]))

  for (const visit of visits) visit.events.sort(byTime('occurred_on'))
  return visits.sort(byTime('started_on'))
}

/** Seconds as something a person reads: `45s`, `2m 10s`, `1h 05m`. */
export function readableDuration(seconds) {
  const total = Number(seconds) || 0
  if (total < 60) return `${total}s`
  const minutes = Math.floor(total / 60)
  if (minutes < 60) return `${minutes}m ${total % 60}s`
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}m`
}
