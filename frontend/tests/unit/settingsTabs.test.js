import { buildTabs, valorePredefinito } from '@/utils/settingsTabs'

// The settings screens render a DocType's own layout, so the sections, the order
// and above all the field descriptions come from the DocType. This is the shape
// that makes that possible.

const campo = (fieldname, fieldtype = 'Data', extra = {}) => ({
  fieldname,
  fieldtype,
  label: fieldname,
  ...extra,
})

describe('buildTabs', () => {
  it('returns nothing for no fields', () => {
    expect(buildTabs(null)).toEqual([])
    expect(buildTabs(undefined)).toEqual([])
  })

  it('wraps loose fields in a first tab and section', () => {
    const tabs = buildTabs([campo('tax_id'), campo('fiscal_code')])
    expect(tabs).toHaveLength(1)
    expect(tabs[0].sections).toHaveLength(1)
    expect(
      tabs[0].sections[0].columns[0].fields.map((f) => f.fieldname),
    ).toEqual(['tax_id', 'fiscal_code'])
  })

  it('does not add an empty section when the layout opens with one', () => {
    const tabs = buildTabs([
      campo('identity_section', 'Section Break', { label: 'Issuer' }),
      campo('company_name'),
    ])
    expect(tabs[0].sections).toHaveLength(1)
    expect(tabs[0].sections[0].label).toBe('Issuer')
  })

  it('splits sections and columns', () => {
    const tabs = buildTabs([
      campo('a_section', 'Section Break'),
      campo('tax_id'),
      campo('col', 'Column Break'),
      campo('fiscal_code'),
      campo('b_section', 'Section Break'),
      campo('iban'),
    ])
    const [primo, secondo] = tabs[0].sections
    expect(primo.columns).toHaveLength(2)
    expect(primo.columns[1].fields.map((f) => f.fieldname)).toEqual([
      'fiscal_code',
    ])
    expect(secondo.columns[0].fields.map((f) => f.fieldname)).toEqual(['iban'])
  })

  it('starts a new tab on a tab break', () => {
    const tabs = buildTabs([
      campo('first_tab', 'Tab Break', { label: 'One' }),
      campo('tax_id'),
      campo('second_tab', 'Tab Break', { label: 'Two' }),
      campo('iban'),
    ])
    expect(tabs.map((t) => t.label)).toEqual(['One', 'Two'])
    expect(
      tabs[1].sections[0].columns[0].fields.map((f) => f.fieldname),
    ).toEqual(['iban'])
  })

  it('gives every generated section and column a distinct name', () => {
    const tabs = buildTabs([
      campo('a', 'Section Break'),
      campo('x'),
      campo('b', 'Section Break'),
      campo('y'),
    ])
    const colonne = tabs[0].sections.flatMap((s) =>
      s.columns.map((c) => c.name),
    )
    expect(new Set(colonne).size).toBe(colonne.length)
  })

  it('keeps the field objects, so descriptions and depends_on survive', () => {
    const tabs = buildTabs([
      campo('number_format', 'Data', {
        description: 'Validated against the Sistema TS alphabet',
        depends_on: 'eval:doc.enabled',
      }),
    ])
    const reso = tabs[0].sections[0].columns[0].fields[0]
    expect(reso.description).toContain('Sistema TS')
    expect(reso.depends_on).toBe('eval:doc.enabled')
  })

  it('folds the sections the DocType folds, and keeps when one applies', () => {
    const tabs = buildTabs([
      campo('identity', 'Section Break'),
      campo('company_name'),
      campo('registro', 'Section Break', { collapsible: 1 }),
      campo('rea_number'),
      campo('ts_section', 'Section Break', {
        depends_on: 'eval:doc.is_healthcare',
      }),
      campo('ts_expense_type', 'Select'),
      campo('options', 'Section Break'),
      campo('enabled', 'Check'),
    ])
    const [identita, registro, ts, opzioni] = tabs[0].sections
    expect(identita).not.toHaveProperty('opened')
    expect(registro.opened).toBe(false)
    expect(ts.dependsOn).toBe('eval:doc.is_healthcare')
    expect(ts.opened).toBeUndefined()
    expect(opzioni).not.toHaveProperty('opened')
    expect(opzioni).not.toHaveProperty('dependsOn')
  })

  it('never opens a tab on a folded section', () => {
    const [, sdi] = buildTabs([
      campo('tab_company', 'Tab Break'),
      campo('company_name'),
      campo('tab_sdi', 'Tab Break'),
      campo('sdi_section', 'Section Break', { collapsible: 1 }),
      campo('sdi_mode', 'Select'),
      campo('extra', 'Section Break', { collapsible: 1 }),
      campo('sdi_endpoint'),
    ])
    // the empty section a tab break opens with is not drawn
    const [canale, altro] = sdi.sections
    expect(sdi.sections).toHaveLength(2)
    expect(canale).not.toHaveProperty('opened')
    expect(altro.opened).toBe(false)
  })

  it('draws nothing of what the DocType hides, nor what is left empty', () => {
    const tabs = buildTabs([
      campo('tab_company', 'Tab Break', { label: 'Company' }),
      campo('company_name'),
      campo('preservation', 'Section Break'),
      campo('conservation_service', 'Select', { hidden: 1 }),
      campo('tab_sdi', 'Tab Break', { label: 'Transmission' }),
      campo('sdi_mode', 'Select', { hidden: 1 }),
      campo('col', 'Column Break'),
      campo('sdi_flow', 'Select', { hidden: 1 }),
    ])
    // the section with only hidden fields goes, and the tab with nothing left
    expect(tabs.map((t) => t.label)).toEqual(['Company'])
    expect(tabs[0].sections).toHaveLength(1)
    expect(
      tabs[0].sections[0].columns[0].fields.map((f) => f.fieldname),
    ).toEqual(['company_name'])
  })
})

describe('valorePredefinito', () => {
  it('starts a new record where the DocType says', () => {
    expect(valorePredefinito({ fieldtype: 'Select', default: 'export' })).toBe(
      'export',
    )
    expect(valorePredefinito({ fieldtype: 'Check', default: '1' })).toBe(1)
    expect(valorePredefinito({ fieldtype: 'Percent', default: '20' })).toBe(20)
    expect(valorePredefinito({ fieldtype: 'Data' })).toBeUndefined()
  })

  it("leaves the session's defaults to the server", () => {
    expect(valorePredefinito({ fieldtype: 'Date', default: 'Today' })).toBe(
      undefined,
    )
    expect(valorePredefinito({ fieldtype: 'Link', default: ':Company' })).toBe(
      undefined,
    )
    expect(valorePredefinito({ fieldtype: 'Link', default: '__user' })).toBe(
      undefined,
    )
  })
})
