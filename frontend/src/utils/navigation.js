// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Where the router's idea of "where am I" and the nav's idea of it are
 * reconciled.
 *
 * Keeping it here means the sidebar and the phone's tab bar cannot drift apart
 * on what counts as being «in» a section.
 */

// A section is its own page and the ones inside it: a record of its list, the
// pages that live with it behind a switch in their header (utils/menu.js,
// SORELLE), the reception desk and the waiting list behind the agenda. Both
// the sidebar and the phone's bar keep the section lit there: an entry going
// dark because you opened a record, or the companies of the people, would read
// as broken. A person's form being filled is the person's.
const DENTRO = {
  Leads: [
    'Lead',
    'Contacts',
    'Contact',
    'Organizations',
    'Organization',
    'FormFill',
  ],
  Deals: ['Deal'],
  Calendar: ['Today', 'Waiting List'],
  Tasks: ['Notes'],
  Automations: ['Automation'],
  Website: ['WebsitePage'],
}

// the tabs the bar had before it followed the menu (utils/menu.js)
const TAB_DI_SEMPRE = ['Leads', 'Deals', 'Tasks', 'Conversations']

/** The section a page lives in: the one it is inside, else its own. */
export function sezioneDi(name) {
  if (!name) return name
  return Object.keys(DENTRO).find((key) => DENTRO[key].includes(name)) || name
}

/**
 * The sidebar's notion: a saved view wins over the route it is a view of; a
 * page inside a section lights the section.
 */
export function currentNavKey(route) {
  return route?.query?.view || sezioneDi(route?.name)
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
