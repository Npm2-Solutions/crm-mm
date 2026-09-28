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

// And the other way round. People had a board grouped by the sale's status;
// the status moved onto the deal (doc 26) and the board went with it — the
// board is Deals, People is a list. Its switch was hidden, but the address
// still drew it, grouped by a field nobody fills any more, every card titled
// with the record's id. Not named here, «kanban» on People reads as a saved
// view, finds none, and lands on the list.
const NOT_HERE = { Leads: ['kanban'] }

export function standardViewTypesFor(routeName) {
  const excluded = NOT_HERE[routeName] || []
  return [...EVERYWHERE, ...(ONLY_HERE[routeName] || [])].filter(
    (type) => !excluded.includes(type),
  )
}

export function isStandardViewType(routeName, viewType) {
  return standardViewTypesFor(routeName).includes(viewType)
}
