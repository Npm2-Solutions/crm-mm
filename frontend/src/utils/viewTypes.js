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

// The Inbox is People read as conversations — the same rows, ordered by who
// wrote last. No other list has a conversation on it, so no other list has it.
const ONLY_HERE = {
  Leads: ['inbox'],
}

export function standardViewTypesFor(routeName) {
  return [...EVERYWHERE, ...(ONLY_HERE[routeName] || [])]
}

export function isStandardViewType(routeName, viewType) {
  return standardViewTypesFor(routeName).includes(viewType)
}
