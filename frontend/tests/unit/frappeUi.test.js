// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// frappe-ui in the user's language: the build rewrites the components that write
// English whatever the user reads (frontend/vite/frappeUi.js). These read the
// frappe-ui this app pins, so an upgrade that moves the lines fails here, not on
// screen.
import fs from 'node:fs'
import path from 'node:path'
import {
  FILE,
  FILE_FRAPPE,
  FILE_MOLECOLE,
  NOMI,
  traduciFrappeUi,
} from '../../vite/frappeUi.js'

const COMPONENTI = path.resolve(
  import.meta.dirname,
  '../../node_modules/frappe-ui/src/components',
)
const FRAPPE = path.resolve(
  import.meta.dirname,
  '../../node_modules/frappe-ui/frappe',
)
const MOLECOLE = path.resolve(
  import.meta.dirname,
  '../../node_modules/frappe-ui/src/molecules',
)

function tradotto(file, cartella = COMPONENTI) {
  const id = path.join(cartella, file)
  return traduciFrappeUi(fs.readFileSync(id, 'utf8'), id)
}

function nomi(lang) {
  window.lang = lang
  return new Function(`${NOMI}; return { nomiDeiMesi, nomiDeiGiorni }`)()
}

describe('frappe-ui in the user’s language', () => {
  afterEach(() => {
    delete window.lang
  })

  it('finds every line it rewrites in the frappe-ui this app pins', () => {
    for (const file of FILE) {
      expect(() => tradotto(file), file).not.toThrow()
      expect(tradotto(file), file).not.toBeNull()
    }
    for (const file of FILE_FRAPPE) {
      expect(() => tradotto(file, FRAPPE), file).not.toThrow()
      expect(tradotto(file, FRAPPE), file).not.toBeNull()
    }
    for (const file of FILE_MOLECOLE) {
      expect(() => tradotto(file, MOLECOLE), file).not.toThrow()
      expect(tradotto(file, MOLECOLE), file).not.toBeNull()
    }
  })

  it("takes the editor toolbar's labels through the translator", () => {
    const menu = tradotto('editor/MenuItems.vue', MOLECOLE)
    expect(menu).toContain('return (globalThis.__ || String)(item.label)')
    expect(menu).toContain(':text="__(groupItem.label)"')
    expect(menu).not.toContain(':label="item.label"')
  })

  it('takes the data import pages through the translator', () => {
    const lista = tradotto('DataImport/DataImportList.vue', FRAPPE)
    expect(lista).toContain(`{{ __('Data Import') }}`)
    expect(lista).toContain(`:placeholder="__('Search imported files')"`)
    expect(lista).toContain(`:label="__(dataImport.status)"`)
    const carica = tradotto('DataImport/UploadStep.vue', FRAPPE)
    // written twice, both through the translator
    expect(
      carica.match(/__\('Google Sheet', null, 'Data import'\)/g),
    ).toHaveLength(2)
    expect(carica).not.toMatch(/>\s*Google Sheet\s*</)
    const anteprima = tradotto('DataImport/PreviewStep.vue', FRAPPE)
    expect(anteprima).toContain('Rows imported: {0}. Rows not imported: {1}.')
    expect(anteprima).not.toContain('imported successfully')
  })

  it('sends the words through the translator', () => {
    const piede = tradotto('ListView/ListFooter.vue')
    expect(piede).toContain(`:label="__('Load More')"`)
    expect(piede).toContain(`{{ __('of') }}`)
    expect(tradotto('Autocomplete/Autocomplete.vue')).toContain(
      `:placeholder="__('Search')"`,
    )
    expect(tradotto('DatePicker/DatePicker.vue')).toContain(
      `:today-label="__('Today')"`,
    )
    for (const file of [
      'Calendar/CalendarWeekly.vue',
      'Calendar/CalendarDaily.vue',
    ]) {
      expect(tradotto(file)).toContain(`{{ __('All day') }}`)
      expect(tradotto(file)).not.toMatch(/>\s*All day\s*</)
    }
  })

  it('makes the defaults when the component is, through the translator', () => {
    const select = tradotto('Select/Select.vue')
    expect(select).toContain(
      "emptyText: () => (globalThis.__ || String)('No options'),",
    )
    expect(select).not.toContain("emptyText: 'No options',")
    const traduci = globalThis.__ || String
    expect(traduci('No options')).toBe('No options')
  })

  it('takes the calendar’s names from the language instead of English lists', () => {
    const codice = tradotto('Calendar/calendarUtils.ts')
    expect(codice).toContain('export const monthList = nomiDeiMesi()')
    expect(codice).toContain("export const daysList = nomiDeiGiorni('short')")
    expect(codice).toContain(
      "export const daysListFull = nomiDeiGiorni('long')",
    )
    expect(codice).not.toContain("'en-US'")
    expect(codice).not.toContain("'September'")
  })

  it('names months and days in Italian for an Italian user', () => {
    const { nomiDeiMesi, nomiDeiGiorni } = nomi('it')
    expect(nomiDeiMesi()[8]).toBe('Settembre')
    // the calendar cuts them to three for a week across two months: «Set - Ott»
    expect(nomiDeiMesi().map((mese) => mese.slice(0, 3))[9]).toBe('Ott')
    expect(nomiDeiGiorni('short')[0]).toBe('Dom')
    expect(nomiDeiGiorni('short')[1]).toBe('Lun')
    expect(nomiDeiGiorni('long')[3]).toBe('Mercoledì')
  })

  it('stays as it was for an English user', () => {
    const { nomiDeiMesi, nomiDeiGiorni } = nomi('en')
    expect(nomiDeiMesi()[0]).toBe('January')
    expect(nomiDeiGiorni('short')).toEqual([
      'Sun',
      'Mon',
      'Tue',
      'Wed',
      'Thu',
      'Fri',
      'Sat',
    ])
  })

  it('leaves the other files, and the parts of a .vue file, alone', () => {
    const piede = path.join(COMPONENTI, 'ListView/ListFooter.vue')
    expect(
      traduciFrappeUi('x', path.join(COMPONENTI, 'Calendar/Calendar.vue')),
    ).toBe(null)
    expect(traduciFrappeUi('x', `${piede}?vue&type=style&index=0`)).toBe(null)
    expect(traduciFrappeUi('x', '/src/pages/Calendar.vue')).toBe(null)
  })

  it('stops the build when frappe-ui no longer writes what it replaces', () => {
    expect(() =>
      traduciFrappeUi(
        'nothing to see',
        path.join(COMPONENTI, 'ListView/ListFooter.vue'),
      ),
    ).toThrow(/ListFooter.vue/)
  })
})
