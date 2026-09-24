// The dashboard's pure logic: periods, number formats, the grid, the catalogue.
// No Vue, no network — everything here is unit-tested (tests/unit/dashboard.test.js).

export const GRID_COLUMNS = 20
export const ROW_HEIGHT = 42

// -- periods -----------------------------------------------------------------

// The keys the server stores as a dashboard's default period (crm/dashboard/store.py).
export const PERIODS = [
  'today',
  'yesterday',
  'this_week',
  'last_7_days',
  'this_month',
  'last_month',
  'last_30_days',
  'last_90_days',
  'this_quarter',
  'this_year',
]

export const DEFAULT_PERIOD = 'last_30_days'

export function periodLabel(key) {
  const labels = {
    today: __('Today'),
    yesterday: __('Yesterday'),
    this_week: __('This week'),
    last_7_days: __('Last 7 days'),
    this_month: __('This month'),
    last_month: __('Last month'),
    last_30_days: __('Last 30 days'),
    last_90_days: __('Last 90 days'),
    this_quarter: __('This quarter'),
    this_year: __('This year'),
    custom: __('Custom range'),
  }
  return labels[key] || labels[DEFAULT_PERIOD]
}

export function toISODate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function addDays(date, days) {
  const copy = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  copy.setDate(copy.getDate() + days)
  return copy
}

// [from, to] as ISO dates, both included, for a period key. `weekStartsOn` is
// 1 for Monday (the default here), 0 for Sunday.
export function periodRange(key, today = new Date(), weekStartsOn = 1) {
  const day = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const range = (from, to) => [toISODate(from), toISODate(to)]
  switch (key) {
    case 'today':
      return range(day, day)
    case 'yesterday':
      return range(addDays(day, -1), addDays(day, -1))
    case 'this_week': {
      const offset = (day.getDay() - weekStartsOn + 7) % 7
      return range(addDays(day, -offset), day)
    }
    case 'last_7_days':
      return range(addDays(day, -6), day)
    case 'this_month':
      return range(new Date(day.getFullYear(), day.getMonth(), 1), day)
    case 'last_month':
      return range(
        new Date(day.getFullYear(), day.getMonth() - 1, 1),
        new Date(day.getFullYear(), day.getMonth(), 0),
      )
    case 'last_90_days':
      return range(addDays(day, -89), day)
    case 'this_quarter': {
      const first = Math.floor(day.getMonth() / 3) * 3
      return range(new Date(day.getFullYear(), first, 1), day)
    }
    case 'this_year':
      return range(new Date(day.getFullYear(), 0, 1), day)
    case 'last_30_days':
    default:
      return range(addDays(day, -29), day)
  }
}

// "1 – 30 set" / "15 dic 2025 – 14 gen 2026": short, and the year only when it
// is not this one.
export function formatRange(from, to, locale, today = new Date()) {
  if (!from || !to) return ''
  const start = parseISODate(from)
  const end = parseISODate(to)
  const withYear = (date) => date.getFullYear() !== today.getFullYear()
  const format = (date, year) =>
    new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'short',
      year: year ? 'numeric' : undefined,
    }).format(date)
  if (from === to) return format(start, withYear(start))
  const year = withYear(start) || withYear(end)
  return `${format(start, year)} – ${format(end, year)}`
}

export function parseISODate(value) {
  const [y, m, d] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(y, (m || 1) - 1, d || 1)
}

// -- numbers -----------------------------------------------------------------

function number(locale, options) {
  return new Intl.NumberFormat(locale, options)
}

function durationParts(seconds) {
  const total = Math.round(Math.abs(seconds))
  return {
    days: Math.floor(total / 86400),
    hours: Math.floor((total % 86400) / 3600),
    minutes: Math.floor((total % 3600) / 60),
    seconds: total % 60,
  }
}

function unit(value, name, locale) {
  return number(locale, {
    style: 'unit',
    unit: name,
    unitDisplay: 'short',
    maximumFractionDigits: 1,
  }).format(value)
}

// A duration in seconds as the two most significant units: "45 sec", "12 min",
// "3 hr 20 min", "2 days 4 hr" — in the reader's language.
export function formatDuration(seconds, locale) {
  if (seconds == null || isNaN(seconds)) return '–'
  const { days, hours, minutes, seconds: rest } = durationParts(seconds)
  if (days)
    return joinUnits([
      unit(days, 'day', locale),
      hours && unit(hours, 'hour', locale),
    ])
  if (hours)
    return joinUnits([
      unit(hours, 'hour', locale),
      minutes && unit(minutes, 'minute', locale),
    ])
  if (minutes) return unit(minutes, 'minute', locale)
  return unit(rest, 'second', locale)
}

function joinUnits(parts) {
  return parts.filter(Boolean).join(' ')
}

// `value` in `format` (number, currency, percent, duration, days, ratio).
// Large numbers are compacted ("12.9K", "1,3 Mln") unless `compact` is false.
export function formatValue(value, format = 'number', options = {}) {
  const { currency, locale, compact = true } = options
  if (value == null || value === '' || isNaN(value)) return '–'
  const n = Number(value)
  switch (format) {
    case 'currency': {
      const big = compact && Math.abs(n) >= 100000
      try {
        return number(locale, {
          style: 'currency',
          currency: currency || 'EUR',
          notation: big ? 'compact' : 'standard',
          maximumFractionDigits: big ? 1 : Math.abs(n) >= 100 ? 0 : 2,
          minimumFractionDigits: 0,
        }).format(n)
      } catch {
        // an unknown currency code must not blank the widget
        return number(locale, { maximumFractionDigits: 2 }).format(n)
      }
    }
    case 'percent':
      return number(locale, {
        style: 'percent',
        maximumFractionDigits: 1,
      }).format(n / 100)
    case 'duration':
      return formatDuration(n, locale)
    case 'days':
      return unit(n, 'day', locale)
    case 'ratio':
      return `${number(locale, { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(n)}×`
    default: {
      const big = compact && Math.abs(n) >= 10000
      return number(locale, {
        notation: big ? 'compact' : 'standard',
        maximumFractionDigits: big || !Number.isInteger(n) ? 1 : 0,
      }).format(n)
    }
  }
}

// How a KPI moved: the text of the change and whether it is good news.
export function describeDelta(payload, locale) {
  if (!payload || payload.delta == null || isNaN(payload.delta)) return null
  const delta = Number(payload.delta)
  const sign = delta > 0 ? '+' : delta < 0 ? '−' : ''
  const magnitude = Math.abs(delta)
  let text
  if (payload.deltaUnit === 'points') {
    text = `${sign}${number(locale, { maximumFractionDigits: 1 }).format(magnitude)} ${__('pts')}`
  } else if (payload.deltaUnit === 'percent') {
    text = `${sign}${number(locale, { maximumFractionDigits: magnitude < 10 ? 1 : 0 }).format(magnitude)}%`
  } else {
    text = `${sign}${formatValue(magnitude, payload.format, { locale, currency: payload.currency })}`
  }
  let tone = 'neutral'
  if (delta !== 0) {
    const up = delta > 0
    tone = up !== Boolean(payload.negativeIsBetter) ? 'good' : 'bad'
  }
  return {
    text,
    tone,
    direction: delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat',
  }
}

// -- the grid ------------------------------------------------------------------

// The first free row under everything on the layout: where a new widget goes.
export function bottomOf(items) {
  return items.reduce(
    (lowest, item) =>
      Math.max(lowest, (item.layout?.y || 0) + (item.layout?.h || 0)),
    0,
  )
}

// A grid key no other item on the layout uses.
export function newKey(name, items, random = Math.random) {
  const taken = new Set(items.map((item) => item.layout?.i))
  let key
  do {
    key = `${name}_${random().toString(36).slice(2, 7)}`
  } while (taken.has(key))
  return key
}

// A new item for `widget`, placed at the bottom, its default size.
export function newItem(widget, items, random = Math.random) {
  const [w, h] = widget.size || [4, 3]
  return {
    name: widget.id,
    type: widget.kind,
    layout: {
      x: 0,
      y: bottomOf(items),
      w,
      h,
      i: newKey(widget.id, items, random),
    },
  }
}

// A copy of `item` right below the original.
export function duplicateItem(item, items, random = Math.random) {
  const copy = JSON.parse(JSON.stringify(stripItem(item)))
  copy.layout = {
    ...copy.layout,
    y: (item.layout?.y || 0) + (item.layout?.h || 0),
    i: newKey(item.name, items, random),
  }
  return copy
}

// What the server stores for an item: its place and settings, not what the
// browser learned while showing it.
export function stripItem(item) {
  const { name, type, layout, config } = item
  const out = { name, type, layout: { ...layout } }
  if (config && Object.keys(config).length) out.config = { ...config }
  return out
}

export function toSavedLayout(items) {
  return items.map(stripItem)
}

// The order a phone shows the grid in: top to bottom, left to right. Spacers
// only push things around a wide grid; stacked, they are blank gaps.
export function mobileOrder(items) {
  return items
    .filter((item) => item.name !== 'spacer')
    .slice()
    .sort(
      (a, b) =>
        (a.layout?.y || 0) - (b.layout?.y || 0) ||
        (a.layout?.x || 0) - (b.layout?.x || 0),
    )
}

// -- the catalogue -----------------------------------------------------------------

function fold(text) {
  return String(text || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

// The widgets matching every word of `query` (title, description, keywords),
// accents ignored; within `category` when one is given.
export function searchCatalog(widgets, query = '', category = '') {
  const words = fold(query).split(/\s+/).filter(Boolean)
  return widgets.filter((widget) => {
    if (category && widget.category !== category) return false
    if (!words.length) return true
    const haystack = fold(
      [widget.title, widget.description, ...(widget.keywords || [])].join(' '),
    )
    return words.every((word) => haystack.includes(word))
  })
}

// Widgets grouped in the catalogue's order of categories; empty groups dropped.
export function groupByCategory(widgets, order = []) {
  const groups = new Map(order.map((category) => [category, []]))
  for (const widget of widgets) {
    if (!groups.has(widget.category)) groups.set(widget.category, [])
    groups.get(widget.category).push(widget)
  }
  return [...groups.entries()]
    .filter(([, list]) => list.length)
    .map(([category, list]) => ({ category, widgets: list }))
}

// How many times each widget is already on the layout.
export function usage(items) {
  const counts = {}
  for (const item of items) counts[item.name] = (counts[item.name] || 0) + 1
  return counts
}

// -- safety --------------------------------------------------------------------

// Chart tooltips are HTML strings: anything that came from data (a campaign
// name a visitor typed into a URL) is escaped before it goes in.
export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
