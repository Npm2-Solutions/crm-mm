/**
 * Where the router's idea of "where am I" and the nav's idea of it are
 * reconciled.
 *
 * Keeping it here means the sidebar and the phone's tab bar cannot drift apart
 * on what counts as being «in» a section.
 */

// The tab bar is coarser than the sidebar on purpose: a detail page, and a saved
// view of a list, both keep their section lit. Five tabs going dark because you
// opened a record would read as broken.
const BOTTOM_NAV_SECTIONS = {
  Conversations: ['Conversations'],
  Calendar: ['Calendar'],
  Tasks: ['Tasks'],
  Deals: ['Deals', 'Deal'],
  Leads: ['Leads', 'Lead'],
}

/** The sidebar's notion: a saved view wins over the route it is a view of. */
export function currentNavKey(route) {
  return route?.query?.view || route?.name
}

/** Which bottom-nav tab a route belongs to, or null for the ones with no tab. */
export function bottomNavTabFor(route) {
  return (
    Object.keys(BOTTOM_NAV_SECTIONS).find((key) =>
      BOTTOM_NAV_SECTIONS[key].includes(route?.name),
    ) || null
  )
}
