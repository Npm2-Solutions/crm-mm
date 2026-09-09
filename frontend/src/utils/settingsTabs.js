/**
 * Turn a DocType's own field list into the tab/section/column shape FieldLayout
 * wants.
 *
 * Doing it from the meta rather than from a hand-written layout is what keeps a
 * settings screen honest: the sections, the order, the `depends_on` and above all
 * the field descriptions are the ones on the DocType, so a rule explained once in
 * the JSON is explained in the interface too, and cannot drift away from it.
 */
export function buildTabs(fields) {
  if (!fields) return []
  const tabs = []

  if (fields[0]?.fieldtype !== 'Tab Break') {
    const sections = []
    if (fields[0]?.fieldtype !== 'Section Break') {
      sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    tabs.push({ name: 'first_tab', sections })
  }

  let counter = 0
  const unique = (prefix) => `${prefix}_${(counter += 1)}`

  fields.forEach((field) => {
    const lastTab = tabs[tabs.length - 1]
    const sections = tabs.length ? lastTab.sections : []
    if (field.fieldtype === 'Tab Break') {
      tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: unique('section'),
            columns: [{ name: unique('column'), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: unique('column'), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      sections[sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      const lastSection = sections[sections.length - 1]
      const lastColumn = lastSection.columns[lastSection.columns.length - 1]
      lastColumn.fields.push(field)
    }
  })

  return tabs
}
