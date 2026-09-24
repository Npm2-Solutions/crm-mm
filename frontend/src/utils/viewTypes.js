/**
 * Which ways of looking at a list are built in, per list.
 *
 * The router reads an unknown view type as the *name of a saved view*, and when
 * no view has that name it falls back to the list. So a built-in view type
 * missing from here does not fail loudly: clicking it looks like nothing
 * happening, because it lands back on the list it started from. Which is
 * exactly what the Inbox did.
 */

const EVERYWHERE = ['list', 'kanban', 'group_by']

// Nothing has a view type of its own at the moment. The shape stays because the
// rule is per list, and the Inbox proved what happens when a built-in view type
// is not named here: it reads as a saved view, finds none, and sends you back to
// the list — which looks like the click doing nothing at all.
const ONLY_HERE = {}

export function standardViewTypesFor(routeName) {
  return [...EVERYWHERE, ...(ONLY_HERE[routeName] || [])]
}

export function isStandardViewType(routeName, viewType) {
  return standardViewTypesFor(routeName).includes(viewType)
}
