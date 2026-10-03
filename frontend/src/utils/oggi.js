// The desk's day (docs/gestionale-medico, «La giornata della segreteria»): who is
// coming, who is waiting and since when, what the last days left open. Pure, so
// the page only draws and the rules are tested.

/** What the desk may say next of a participant, in the order it is offered. */
export const NEXT = {
  Booked: ['Arrived', 'No Show'],
  Arrived: ['Attended', 'Booked'],
  Attended: ['Booked'],
  'No Show': ['Booked'],
}

/**
 * The outcomes to offer next. A day gone by asks whether they came: nobody is
 * checked into a waiting room days later.
 */
export function prossimiEsiti(status, passato = false) {
  if (passato && status === 'Booked') return ['Attended', 'No Show']
  return NEXT[status] || []
}

/** Whole minutes since `arrivedAt`, never negative. */
export function minutesWaiting(arrivedAt, now = new Date()) {
  if (!arrivedAt) return 0
  const since = new Date(String(arrivedAt).replace(' ', 'T'))
  if (Number.isNaN(since.getTime())) return 0
  return Math.max(0, Math.floor((now - since) / 60000))
}

/** «12 min», «1 h 5 min»: how long somebody has been in the waiting room. */
export function waitingLabel(minutes) {
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours} h ${rest} min` : `${hours} h`
}

/** The people in the waiting room, who arrived first first. */
export function waitingRoom(appointments = []) {
  const waiting = []
  for (const appointment of appointments) {
    for (const participant of appointment.participants || []) {
      if (participant.status === 'Arrived')
        waiting.push({ appointment, participant })
    }
  }
  return waiting.sort((a, b) =>
    String(a.participant.arrived_at || '').localeCompare(
      String(b.participant.arrived_at || ''),
    ),
  )
}

/** How the day stands: still to come, waiting, came, did not come. */
export function summarize(appointments = []) {
  const counts = { coming: 0, waiting: 0, came: 0, noShow: 0 }
  for (const appointment of appointments) {
    for (const participant of appointment.participants || []) {
      if (participant.status === 'Booked') counts.coming++
      else if (participant.status === 'Arrived') counts.waiting++
      else if (participant.status === 'Attended') counts.came++
      else if (participant.status === 'No Show') counts.noShow++
    }
  }
  return counts
}

/** The past appointments nobody closed, grouped by their day, the latest first. */
export function byDay(appointments = []) {
  const days = new Map()
  for (const appointment of appointments) {
    const day = String(appointment.starts_on || '').slice(0, 10)
    if (!days.has(day)) days.set(day, [])
    days.get(day).push(appointment)
  }
  return [...days.entries()]
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([day, items]) => ({ day, appointments: items }))
}

/**
 * The first `quanti` people still without an outcome, in their days: the groups
 * of `byDay` cut after them, each appointment with only the ones still expected.
 */
export function firstOfPast(groups = [], quanti = 4) {
  const shown = []
  let left = quanti
  for (const group of groups) {
    if (left <= 0) break
    const appointments = []
    for (const appointment of group.appointments) {
      if (left <= 0) break
      const expected = (appointment.participants || []).filter(
        (p) => p.status === 'Booked',
      )
      if (!expected.length) continue
      const taken = expected.slice(0, left)
      left -= taken.length
      appointments.push({ ...appointment, participants: taken })
    }
    if (appointments.length) shown.push({ day: group.day, appointments })
  }
  return shown
}

/** «09:30» from a stored datetime, «» from anything else. */
export function timeOf(datetime) {
  const match = /[ T](\d{2}):(\d{2})/.exec(String(datetime ?? ''))
  return match ? `${match[1]}:${match[2]}` : ''
}

/** «2026-09-30» moved by `days`, at noon so no clock change can skip a day. */
export function shiftDay(isoDate, days) {
  if (!isoDate) return null
  const d = new Date(`${isoDate}T12:00:00`)
  d.setDate(d.getDate() + days)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
