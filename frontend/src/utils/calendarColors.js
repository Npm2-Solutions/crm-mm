/**
 * Colours on the calendar.
 *
 * frappe-ui's calendar knows seven colours by name (amber, violet, pink, cyan,
 * blue, orange, green) and seven old hex values that stand for them. Anything
 * else it is given it draws green — and it was given little else. A service's
 * colour is any hex its settings page offers (a blue «#3b82f6» is not one of
 * the seven), and the event panel saved its pick as the CSS variable behind
 * the colour («var(--ink-amber-7)»), which is not a name either. So every
 * appointment and every coloured event came out green, and colour told
 * nothing apart.
 *
 * Here any of those becomes the name of the calendar colour nearest to it,
 * and the calendar learns two more: grey, for what no longer takes up the
 * time (a cancelled appointment), and red.
 */
import { appointmentColor } from '@/utils/scheduler'

// the hex each name is stored as — frappe-ui's own for its seven
export const NAMED_HEX = {
  amber: '#db7706',
  violet: '#6846e3',
  pink: '#e34aa6',
  cyan: '#3bbde5',
  blue: '#0289f7',
  orange: '#e86c13',
  green: '#30a66d',
  red: '#e03e3e',
  gray: '#8b8b8b',
}

const NAMES = Object.keys(NAMED_HEX)

// tokens that exist in the design system under a name the calendar lacks
const ALIASES = {
  yellow: 'amber',
  purple: 'violet',
  indigo: 'violet',
  teal: 'cyan',
}

function hexToRgb(value) {
  const match = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(
    String(value || '').trim(),
  )
  if (!match) return null
  const digits =
    match[1].length === 3
      ? [...match[1]].map((one) => one + one).join('')
      : match[1]
  return [0, 2, 4].map((at) => parseInt(digits.slice(at, at + 2), 16))
}

// hue in degrees, saturation 0..1 (HSL)
function hueAndSaturation([r, g, b]) {
  const [red, green, blue] = [r / 255, g / 255, b / 255]
  const max = Math.max(red, green, blue)
  const min = Math.min(red, green, blue)
  const delta = max - min
  const lightness = (max + min) / 2
  if (!delta) return { hue: 0, saturation: 0 }
  const saturation = delta / (1 - Math.abs(2 * lightness - 1))
  let hue
  if (max === red) hue = ((green - blue) / delta) % 6
  else if (max === green) hue = (blue - red) / delta + 2
  else hue = (red - green) / delta + 4
  hue *= 60
  return { hue: hue < 0 ? hue + 360 : hue, saturation }
}

// where each named colour sits on the wheel, read off its own hex
const HUES = Object.fromEntries(
  NAMES.filter((name) => name !== 'gray').map((name) => [
    name,
    hueAndSaturation(hexToRgb(NAMED_HEX[name])).hue,
  ]),
)

function distance(a, b) {
  const apart = Math.abs(a - b) % 360
  return apart > 180 ? 360 - apart : apart
}

/**
 * The calendar colour for a stored colour: a name, one of the old hex values,
 * a design-system variable, or any hex — the nearest by hue, grey when it has
 * hardly any colour at all.
 */
export function calendarColorName(value, fallback = 'green') {
  if (!value) return fallback
  const text = String(value).trim().toLowerCase()
  if (NAMES.includes(text)) return text
  if (ALIASES[text]) return ALIASES[text]

  const token = /^var\(--(?:ink|surface|outline)-([a-z]+)-\d+\)$/.exec(text)
  if (token) {
    const name = token[1]
    return NAMES.includes(name) ? name : ALIASES[name] || fallback
  }

  const exact = NAMES.find((name) => NAMED_HEX[name] === text)
  if (exact) return exact

  const rgb = hexToRgb(text)
  if (!rgb) return fallback
  const { hue, saturation } = hueAndSaturation(rgb)
  if (saturation < 0.18) return 'gray'
  let nearest = fallback
  let best = Infinity
  for (const [name, at] of Object.entries(HUES)) {
    const apart = distance(hue, at)
    if (apart < best) {
      best = apart
      nearest = name
    }
  }
  return nearest
}

/**
 * An appointment's colour on the calendar: its service's, and grey once it is
 * cancelled — the time is free again, and the calendar should say so at a
 * glance rather than in the details.
 */
export function appointmentCalendarColor(appointment, serviceColors = {}) {
  if (appointment?.status === 'Cancelled') return 'gray'
  return calendarColorName(appointmentColor(appointment, serviceColors), 'blue')
}

// `color` is the stored hex on purpose: the calendar matches a hex it does not
// know against each entry's `color`, so an event saved as red is drawn red
// straight away, before any reload has turned the hex into a name
function shade(name) {
  return {
    color: NAMED_HEX[name],
    border: `var(--ink-${name}-7)`,
    borderActive: `var(--outline-${name}-3)`,
    text: `var(--ink-${name}-7)`,
    textActive: `var(--ink-${name}-1)`,
    subtext: 'var(--ink-gray-6)',
    subtextActive: `var(--ink-${name}-1)`,
    bg: `var(--surface-${name}-1)`,
    bgHover: `var(--surface-${name}-2)`,
    bgActive: `var(--surface-${name}-7)`,
  }
}

/**
 * Teach the calendar the colours it lacks. Its colour table is one shared
 * object — for light and dark alike — so this adds to it once, and leaves
 * alone anything it already has.
 */
export function registerCalendarColors(colorMap) {
  if (!colorMap) return colorMap
  for (const name of ['gray', 'red']) {
    if (!colorMap[name]) colorMap[name] = shade(name)
  }
  return colorMap
}
