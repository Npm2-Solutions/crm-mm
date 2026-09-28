/**
 * Where a form's cursor belongs when it opens.
 *
 * The first place somebody can type, rather than the first thing that takes
 * focus: the first control of a form is often a picker — «Salutation» on a
 * person, the organization on a deal — and a cursor on a picker is a cursor
 * nobody can type into.
 */

// somewhere to type
const TYPABLE = [
  'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="button"]):not([type="submit"]):not([disabled]):not([readonly])',
  'textarea:not([disabled]):not([readonly])',
  '[contenteditable="true"]',
].join(', ')

// anything that takes focus, the way frappe-ui's Dialog picks it
const FOCUSABLE = [
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'button:not([disabled])',
  'a[href]',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

/**
 * Not hidden by an ancestor: a tab that is not the open one, a section folded
 * away. Read from the markup (`hidden`, `inert`, an inline `display: none`,
 * which is what `v-show` writes) rather than from layout, so it answers the
 * same in a test as on screen.
 */
function shown(element) {
  return !element.closest(
    '[hidden], [inert], [style*="display: none"], [style*="display:none"]',
  )
}

function first(root, selector) {
  if (!root) return null
  return [...root.querySelectorAll(selector)].find(shown) || null
}

// the same, inside a field the form cannot be saved without (`Field.vue`
// marks it `data-required`)
const REQUIRED = TYPABLE.split(', ')
  .map((selector) => `[data-required] ${selector}`)
  .join(', ')

/**
 * The first field somebody can type into, or `null` — a required one first.
 *
 * A person's form puts «Salutation» and «Email» on its first row and «First
 * Name» under them; the name is the field nobody can save without, and the one
 * everybody types first.
 */
export function firstTypable(root) {
  return first(root, REQUIRED) || first(root, TYPABLE)
}

/** The first thing that takes focus at all, or `null`. */
export function firstFocusable(root) {
  return first(root, FOCUSABLE)
}
