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
 * Whether a cell has something to show under its label: not nothing, not an
 * empty list, not a link without a name, not an amount of zero (a company's
 * revenue nobody wrote is not «€ 0.00»).
 */
export function haValore(valore, column = {}) {
  if (valore === null || valore === undefined || valore === '') return false
  if (Array.isArray(valore)) return valore.length > 0
  if (typeof valore === 'object')
    return ['label', 'timeAgo', 'value', 'name'].some(
      (chiave) =>
        valore[chiave] !== undefined &&
        valore[chiave] !== '' &&
        valore[chiave] !== null,
    )
  if (column.type === 'Currency' && Number(valore) === 0) return false
  return true
}
