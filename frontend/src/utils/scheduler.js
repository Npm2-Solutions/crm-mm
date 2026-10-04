// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Pure geometry for the resource scheduler grid.
 *
 * The grid is a plain CSS box: one column per professional or per room, one
 * vertical minute axis. Everything below turns appointments into `top/height/
 * left/width` percentages — no DOM, no Vue, no network, so it can be unit
 * tested on its own.
 */

export const MINUTES_IN_DAY = 24 * 60

/** Minutes since local midnight of the day the date falls in. */
export function minutesFromMidnight(date) {
  const d = date instanceof Date ? date : new Date(date)
  if (Number.isNaN(d.getTime())) return 0
  return d.getHours() * 60 + d.getMinutes()
}

/** Round a minute offset to the nearest `step`, clamped inside the day. */
export function snapMinutes(minutes, step = 15) {
  const snapped = Math.round(minutes / step) * step
  return Math.min(Math.max(snapped, 0), MINUTES_IN_DAY)
}

/**
 * Hour marks for the time gutter.
 * `[{ minutes, label }]` from `startHour` to `endHour` inclusive.
 */
export function buildTimeAxis(startHour = 7, endHour = 21) {
  const marks = []
  for (let hour = startHour; hour <= endHour; hour++) {
    marks.push({
      minutes: hour * 60,
      label: `${String(hour).padStart(2, '0')}:00`,
    })
  }
  return marks
}

/**
 * The visible window, widened so nothing is ever cut off.
 *
 * Default office hours are the starting point; an appointment that starts at
 * 06:30 or ends at 23:00 pulls the window open rather than being clipped.
 */
export function visibleWindow(items, startHour = 7, endHour = 21) {
  let first = startHour * 60
  let last = endHour * 60
  for (const item of items || []) {
    if (Number.isFinite(item.startMinutes)) {
      first = Math.min(first, Math.floor(item.startMinutes / 60) * 60)
    }
    if (Number.isFinite(item.endMinutes)) {
      last = Math.max(last, Math.ceil(item.endMinutes / 60) * 60)
    }
  }
  return {
    startMinutes: Math.max(0, first),
    endMinutes: Math.min(MINUTES_IN_DAY, Math.max(last, first + 60)),
  }
}

/**
 * Side-by-side layout for overlapping appointments in one column.
 *
 * Items are grouped into clusters that transitively overlap; inside a cluster
 * each item takes the first lane whose last item has already finished. The
 * cluster's lane count decides the width, so two overlapping appointments show
 * as two half-width blocks instead of hiding one another.
 *
 * Returns the same objects with `lane` and `lanes` attached.
 */
export function layoutLanes(items) {
  const sorted = [...(items || [])].sort(
    (a, b) => a.startMinutes - b.startMinutes || a.endMinutes - b.endMinutes,
  )
  const laid = []
  let cluster = []
  let clusterEnd = -Infinity

  const flush = () => {
    const lanes = cluster.reduce((max, item) => Math.max(max, item.lane + 1), 0)
    cluster.forEach((item) => {
      item.lanes = lanes
    })
    laid.push(...cluster)
    cluster = []
    clusterEnd = -Infinity
  }

  for (const item of sorted) {
    if (cluster.length && item.startMinutes >= clusterEnd) flush()
    const laneEnds = []
    cluster.forEach((existing) => {
      laneEnds[existing.lane] = Math.max(
        laneEnds[existing.lane] ?? -Infinity,
        existing.endMinutes,
      )
    })
    let lane = laneEnds.findIndex((end) => end <= item.startMinutes)
    if (lane === -1) lane = laneEnds.length
    cluster.push({ ...item, lane })
    clusterEnd = Math.max(clusterEnd, item.endMinutes)
  }
  if (cluster.length) flush()
  return laid
}

/**
 * CSS box for one appointment inside the grid, as percentages.
 * A very short appointment still gets a clickable minimum height.
 */
export function blockStyle(item, window, minHeightPercent = 1.6) {
  const span = Math.max(window.endMinutes - window.startMinutes, 1)
  const top = ((item.startMinutes - window.startMinutes) / span) * 100
  const rawHeight = ((item.endMinutes - item.startMinutes) / span) * 100
  const lanes = item.lanes || 1
  const width = 100 / lanes
  return {
    top: `${Math.max(top, 0)}%`,
    height: `${Math.max(rawHeight, minHeightPercent)}%`,
    left: `${width * (item.lane || 0)}%`,
    width: `${width}%`,
  }
}

/** Turn a click at `offsetRatio` (0..1) of the grid height into a snapped time. */
export function minutesAtRatio(ratio, window, step = 15) {
  const span = window.endMinutes - window.startMinutes
  return snapMinutes(window.startMinutes + ratio * span, step)
}

/** `540` → `"09:00"`. */
export function formatMinutes(minutes) {
  const total =
    ((Math.round(minutes) % MINUTES_IN_DAY) + MINUTES_IN_DAY) % MINUTES_IN_DAY
  const hours = Math.floor(total / 60)
  return `${String(hours).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

// `"09:30"` → `570`, or `null` for anything that is not a time
function clockMinutes(time) {
  const match = /^(\d{1,2}):(\d{2})/.exec(String(time ?? ''))
  if (!match) return null
  return Number(match[1]) * 60 + Number(match[2])
}

/**
 * `"09:30"` plus `45` minutes → `"10:15"` — the end of an appointment from its
 * start and its length. It stops at the end of the day: a booking made here
 * does not run past midnight.
 */
export function addMinutes(time, minutes) {
  const start = clockMinutes(time)
  if (start === null) return ''
  return formatMinutes(Math.min(start + (Number(minutes) || 0), 23 * 60 + 59))
}

/** Minutes from one `HH:MM` to a later one; `0` when it is not later. */
export function minutesBetween(from, to) {
  const start = clockMinutes(from)
  const end = clockMinutes(to)
  if (start === null || end === null) return 0
  return Math.max(end - start, 0)
}

/** `"2026-09-03"` + `585` → a local `Date`. */
export function dateAtMinutes(isoDate, minutes) {
  const [year, month, day] = String(isoDate).slice(0, 10).split('-').map(Number)
  return new Date(
    year,
    month - 1,
    day,
    Math.floor(minutes / 60),
    minutes % 60,
    0,
    0,
  )
}

/** Colour for an appointment: its own, else the service's, else per status. */
const STATUS_COLORS = {
  Scheduled: '#4C7EFF',
  Confirmed: '#30A66D',
  Completed: '#8B8B8B',
  Cancelled: '#E24C4C',
  'No Show': '#E8912D',
}

export function appointmentColor(appointment, serviceColors = {}) {
  return (
    appointment.color ||
    serviceColors[appointment.service] ||
    STATUS_COLORS[appointment.status] ||
    STATUS_COLORS.Scheduled
  )
}

export { STATUS_COLORS }

/**
 * Split appointments into the grid's columns.
 *
 * `mode` decides what a column is: a professional (`staff`) or a room/equipment
 * (`resource`). An appointment with two professionals genuinely belongs in two
 * columns, and appears in both — that is the whole point of the view.
 */
export function columnsFor(appointments, mode, columnKeys) {
  const buckets = new Map(columnKeys.map((key) => [key, []]))
  for (const appointment of appointments || []) {
    const keys =
      mode === 'resource'
        ? (appointment.resources || []).map((row) => row.resource)
        : (appointment.staff || []).map((row) => row.user)
    for (const key of new Set(keys)) {
      if (buckets.has(key)) buckets.get(key).push(appointment)
    }
  }
  return buckets
}

/** Appointments that would not appear in any column of the current view. */
export function unassigned(appointments, mode, columnKeys) {
  const known = new Set(columnKeys)
  return (appointments || []).filter((appointment) => {
    const keys =
      mode === 'resource'
        ? (appointment.resources || []).map((row) => row.resource)
        : (appointment.staff || []).map((row) => row.user)
    return !keys.some((key) => known.has(key))
  })
}

/**
 * A server time as `HH:MM` for a time input.
 *
 * Frappe sends Time columns as a timedelta string, so nine o'clock arrives as
 * `"9:00:00"` — cutting the first five characters gives `"9:00:"`, which a time
 * input silently shows as empty. Anything unreadable becomes `""`.
 */
export function hhmm(value) {
  const match = /^\s*(\d{1,2}):(\d{2})/.exec(String(value ?? ''))
  if (!match) return ''
  const hours = Number(match[1])
  if (hours > 23) return ''
  return `${String(hours).padStart(2, '0')}:${match[2]}`
}

/**
 * The free times found for a service, a day at a time, as a booking app shows
 * them: `[{ giorno, orari, altri }]` in the order the days came, `giorno` the
 * date the times start on (YYYY-MM-DD), `orari` the first `perGiorno` of them
 * and `altri` how many more that day has; no more than `giorni` days. A list
 * of buttons said the day on each one («Sun 4 Oct 09:00», «Sun 4 Oct 09:30»),
 * and the first 24 times could all be the first morning. `giornoDi` says the
 * day a time falls on: the centre's, for the UTC instants the server sends.
 */
export function orariPerGiorno(
  slots,
  {
    perGiorno = 12,
    giorni = 5,
    giornoDi = (slot) => String(slot?.start || '').slice(0, 10),
  } = {},
) {
  const tutti = new Map()
  for (const slot of slots || []) {
    const giorno = String(giornoDi(slot) || '')
    if (!/^\d{4}-\d{2}-\d{2}$/.test(giorno)) continue
    if (!tutti.has(giorno)) tutti.set(giorno, [])
    tutti.get(giorno).push(slot)
  }
  return [...tutti].slice(0, giorni).map(([giorno, orari]) => ({
    giorno,
    orari: orari.slice(0, perGiorno),
    altri: Math.max(orari.length - perGiorno, 0),
  }))
}

// ------------------------------------------------------------------ the centre's clock

const due = (n) => String(n).padStart(2, '0')

/**
 * An appointment's time as the centre's clock reads it, the way the server
 * keeps it and every page reads it back: «2026-09-29 10:00:00». `data` is a
 * Date built from what the form shows. A UTC instant was the phone's clock: on
 * a phone in another time zone than the centre's, or on a site whose own was
 * never set, every save moved the appointment (00:00 became 03:30).
 */
export function oraDelCentro(data) {
  const d = data instanceof Date ? data : new Date(data)
  if (Number.isNaN(d.getTime())) return null
  return (
    `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())} ` +
    `${due(d.getHours())}:${due(d.getMinutes())}:${due(d.getSeconds())}`
  )
}

/**
 * A free time comes from the server as a UTC instant: its day and hour on the
 * centre's clock (`fuso`, the site's time zone), as the agenda shows the
 * appointments - `{ giorno: '2026-09-29', ora: '10:00' }`, or null.
 */
export function sulCentro(istante, fuso) {
  const d = new Date(istante)
  if (!istante || Number.isNaN(d.getTime())) return null
  let parti
  try {
    parti = new Intl.DateTimeFormat('en-CA', {
      timeZone: fuso || undefined,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    }).formatToParts(d)
  } catch {
    // an unknown zone: the phone's own clock, as before
    return sulCentro(istante, null)
  }
  const p = Object.fromEntries(parti.map(({ type, value }) => [type, value]))
  return {
    giorno: `${p.year}-${p.month}-${p.day}`,
    ora: `${p.hour}:${p.minute}`,
  }
}
