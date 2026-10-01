/**
 * Where the router's idea of "where am I" and the nav's idea of it are
 * reconciled.
 *
 * Keeping it here means the sidebar and the phone's tab bar cannot drift apart
 * on what counts as being «in» a section.
 */

// The tab bar is coarser than the sidebar on purpose: a detail page, and a saved
// view of a list, both keep their section lit. Five tabs going dark because you
// opened a record would read as broken. A section is its own page and these.
const DENTRO = {
  Leads: ['Lead', 'Contacts', 'Contact'],
  Deals: ['Deal'],
  Organizations: ['Organization'],
  Automations: ['Automation'],
  Website: ['WebsitePage'],
}

// the tabs the bar had before it followed the menu (utils/menu.js)
const TAB_DI_SEMPRE = ['Leads', 'Deals', 'Tasks', 'Conversations']

/** The sidebar's notion: a saved view wins over the route it is a view of. */
export function currentNavKey(route) {
  return route?.query?.view || route?.name
}

/** Which of the bar's tabs a route belongs to, or null for the ones with no tab. */
export function bottomNavTabFor(route, tabs = TAB_DI_SEMPRE) {
  const name = route?.name
  if (!name) return null
  return (
    tabs.find((key) => key === name || (DENTRO[key] || []).includes(name)) ||
    null
  )
}
