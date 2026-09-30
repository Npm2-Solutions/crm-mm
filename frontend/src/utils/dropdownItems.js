/**
 * What the avatar menu may draw and open for a Home Action.
 *
 * A Sales Manager edits Home Actions and everyone opens the menu, System
 * Managers included, so a stored value is never read as markup or script: the
 * icon is a Feather name from the list the server checks too
 * (crm_dropdown_item.py), the route a path on this site or an http(s) link.
 * The server refuses anything else on save; this is the menu's own guard for
 * rows that got in some other way.
 */
import FEATHER_ICONS from '../../../crm/fcrm/feather_icons.json'

export const DEFAULT_DROPDOWN_ICON = 'external-link'

const ALLOWED_ICONS = new Set(FEATHER_ICONS)
const SAFE_PROTOCOLS = new Set(['http:', 'https:'])

export function isAllowedDropdownIcon(icon) {
  return typeof icon === 'string' && ALLOWED_ICONS.has(icon.trim())
}

/** The Feather name to draw: the stored one when it is one, else the default. */
export function safeDropdownIcon(icon) {
  return isAllowedDropdownIcon(icon) ? icon.trim() : DEFAULT_DROPDOWN_ICON
}

/**
 * The route to open, or null when opening it would run something instead of
 * navigating. Read by the browser's own URL parser, the one window.open uses,
 * so `JavaScript:`, `java\tscript:` and the like are seen for what they are.
 */
export function safeDropdownRoute(route) {
  if (typeof route !== 'string') return null
  const trimmed = route.trim()
  if (!trimmed || hasControlCharacter(trimmed)) return null
  try {
    // a relative route takes the base's https, an absolute one keeps its own
    const { protocol } = new URL(trimmed, 'https://crm.invalid/')
    return SAFE_PROTOCOLS.has(protocol) ? trimmed : null
  } catch {
    return null
  }
}

function hasControlCharacter(text) {
  for (const char of text) {
    const code = char.charCodeAt(0)
    if (code < 0x20 || code === 0x7f) return true
  }
  return false
}
