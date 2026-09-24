/**
 * Split a list view's columns into the three slots a phone card has.
 *
 * A desktop row is a grid: every column gets its own labelled slice and the
 * header above says what each one is. A card has no header, so the first column
 * becomes the card's title, `modified` goes top-right as a timestamp (the way
 * every mail and chat list does it), and everything else is rendered with its
 * own label underneath.
 *
 * Returns the columns tagged with their original index, because the cell
 * renderers in each *ListView are handed `idx` and pass it back up in
 * `applyFilter`.
 */
export function splitColumnsForCard(columns = []) {
  const indexed = columns.map((column, _idx) => ({ ...column, _idx }))

  const title = indexed[0] || null
  const trailing = indexed.find((column) => column.key === 'modified') || null

  const details = indexed.filter(
    (column) => column !== title && column.key !== trailing?.key,
  )

  return { title, trailing, details }
}

/**
 * Does this cell have anything to say?
 *
 * On a desktop an empty cell is a gap in a row you are scanning across, and it
 * costs nothing. On a card it is a labelled line saying "Organization" with
 * nothing under it — three of those and one person fills a quarter of the
 * screen without telling you anything. So empty details are left out.
 *
 * Cell values arrive in whatever shape the list view's own renderer wants:
 * a string, a number, a `{ label }`, a user's `{ full_name }`, or a list of
 * avatars.
 */
export function hasCellValue(item) {
  if (item === null || item === undefined || item === '') return false
  if (typeof item === 'number') return true
  if (typeof item === 'boolean') return item
  if (Array.isArray(item)) return item.length > 0
  if (typeof item === 'object') {
    const meaningful = ['label', 'full_name', 'value', 'name', 'timeAgo']
    return meaningful.some((key) => hasCellValue(item[key]))
  }
  return String(item).trim().length > 0
}
