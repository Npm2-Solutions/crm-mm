/**
 * Where the router's idea of "where am I" and the nav's idea of it are
 * reconciled.
 *
 * The Inbox is not a route of its own — it is the People list read in a
 * different order, so it arrives as `Leads` with `viewType: 'inbox'`. Anything
 * that lights up a nav entry has to know that, or the People entry lights up
 * while you are looking at the Inbox. Keeping it here means the sidebar and the
 * phone's tab bar cannot drift apart on it.
 */
export const INBOX_VIEW_TYPE = 'inbox'

export function isInboxRoute(route) {
  return route?.name === 'Leads' && route?.params?.viewType === INBOX_VIEW_TYPE
}

/** The sidebar's notion: a saved view wins over the route it is a view of. */
export function currentNavKey(route) {
  if (isInboxRoute(route)) return 'Inbox'
  return route?.query?.view || route?.name
}

// The tab bar is coarser than the sidebar on purpose: a detail page, and a saved
// view of a list, both keep their section lit. Five tabs going dark because you
// opened a record would read as broken.
const BOTTOM_NAV_SECTIONS = {
  Leads: ['Leads', 'Lead'],
  Deals: ['Deals', 'Deal'],
  Tasks: ['Tasks'],
}

/** Which bottom-nav tab a route belongs to, or null for the ones with no tab. */
export function bottomNavTabFor(route) {
  if (isInboxRoute(route)) return 'Inbox'
  return (
    Object.keys(BOTTOM_NAV_SECTIONS).find((key) =>
      BOTTOM_NAV_SECTIONS[key].includes(route?.name),
    ) || null
  )
}
