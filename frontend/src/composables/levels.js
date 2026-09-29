import { createResource } from 'frappe-ui'

/**
 * The levels a manager may give on this site, with the optional capabilities
 * each one offers (doc 30). Asked of the server, which knows which modules the
 * plan has: Medical Director appears only where the clinic is on.
 *
 * Managers only - the pages that use it are theirs.
 */
export function useLevels() {
  return createResource({
    url: 'crm.api.user.get_levels',
    cache: 'crm-levels',
    auto: true,
  })
}

/** The label of each level key, for chips and lists. */
export function levelLabels(levels) {
  return Object.fromEntries((levels || []).map((l) => [l.key, l.label]))
}
