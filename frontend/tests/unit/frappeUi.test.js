// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// frappe-ui in the user's language: the build rewrites the components that write
// English whatever the user reads (frontend/vite/frappeUi.js). These read the
// frappe-ui this app pins, so an upgrade that moves the lines fails here, not on
// screen.
import fs from 'node:fs'
import path from 'node:path'
import dayjs from 'dayjs/esm'
import {
  FILE,
  FILE_FRAPPE,
  FILE_MOLECOLE,
  NOMI,
  SELETTORE,
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

// the date picker's names and its Monday
function selettore(lang) {
  window.lang = lang
  return new Function(
    `${SELETTORE.replace(/^export /gm, '')}; return { mesiDelSelettore, inizialiDeiGiorni, dalLunedi }`,
  )()
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

  it('draws the code block without highlight.js and its picker of languages', () => {
    const blocco = tradotto(
      'editor/extensions/code-block/code-block.ts',
      MOLECOLE,
    )
    expect(blocco).toContain(
      "import { CodeBlock } from '@tiptap/extension-code-block'",
    )
    expect(blocco).toContain('CodeBlock.extend({')
    expect(blocco).not.toContain('lowlight')
    expect(blocco).not.toContain('CodeBlockLowlight')
    // TipTap's own keys (Enter three times, the arrow down) still leave it
    expect(blocco).toMatch(/return \{\n\s+\.\.\.this\.parent\?\.\(\),\n\s+Tab:/)
    const vista = tradotto(
      'editor/extensions/code-block/CodeBlockComponent.vue',
      MOLECOLE,
    )
    expect(vista).not.toMatch(/<Combobox\s/)
    expect(vista).toContain("import type { createLowlight } from 'lowlight'")
    expect(vista).not.toContain("props.node.attrs.language || 'auto'")
    expect(vista).toContain(':label="__(\'Copy code\')"')
    expect(vista).toContain("__('Copied!')")
    // the copy button is still there, with its tooltip
    expect(vista).toContain('@click.stop="copyCode"')
    expect(vista).toContain('<TooltipBubble')
  })

  it('brings the emoji list when somebody types one, and no markdown', () => {
    const emoji = tradotto(
      'editor/extensions/emoji/emoji-extension.ts',
      MOLECOLE,
    )
    expect(emoji).not.toContain("import _EMOJIS from './emojis.json'")
    expect(emoji).toContain("import('./emojis.json')")
    expect(emoji).toContain("filterByQuery(await EMOJIS(), query, 'name')")
    const estensioni = tradotto('editor/extensions.ts', MOLECOLE)
    expect(estensioni).not.toContain('@tiptap/markdown')
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
      // its two short lines on a phone are ours (espresso-componenti.css)
      expect(tradotto(file)).toContain('dc-tutto-il-giorno')
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

  it('starts the date picker’s weeks on Monday, its letters with them', () => {
    const utils = tradotto('DatePicker/utils.ts')
    expect(utils).toContain(
      'export const months: string[] = mesiDelSelettore()',
    )
    expect(utils).toContain(
      'const start = dalLunedi(monthStart(year, monthIndex))',
    )
    expect(utils).not.toContain("startOf('week')")
    expect(utils).not.toContain("'Oct'")
    expect(utils.endsWith(SELETTORE)).toBe(true)
    const pannello = tradotto('DatePicker/CalendarPanel.vue')
    expect(pannello).toContain('const WEEKDAYS = inizialiDeiGiorni()')
    expect(pannello).not.toContain("['S', 'M', 'T'")
    // Home and End go to Monday and Sunday
    expect(pannello).toContain('shiftFocus(dalLunedi(cell.date), -1)')
    expect(pannello).not.toContain('cell.date.day()')
    // the arrows and the grid are named in the user's language too
    expect(pannello.match(/:label="__\('Previous month'\)"/g)).toHaveLength(2)
    expect(pannello.match(/:label="__\('Next month'\)"/g)).toHaveLength(2)
    expect(pannello).not.toMatch(/\slabel="(previous|next)"/)
    expect(pannello).toContain(`:aria-label="__('Select month and year')"`)
    expect(pannello).not.toContain("' (Today)'")
  })

  it('names the picker’s months and days in Italian, from Monday', () => {
    const { mesiDelSelettore, inizialiDeiGiorni, dalLunedi } = selettore('it')
    expect(mesiDelSelettore()[9]).toBe('Ott')
    expect(inizialiDeiGiorni()).toEqual(['L', 'M', 'M', 'G', 'V', 'S', 'D'])
    // Sunday 4 October 2026 is in the week of Monday 28 September
    expect(dalLunedi(dayjs('2026-10-04')).format('YYYY-MM-DD')).toBe(
      '2026-09-28',
    )
    expect(dalLunedi(dayjs('2026-09-28')).format('YYYY-MM-DD')).toBe(
      '2026-09-28',
    )
  })

  it('starts the week on Monday in English too, in English words', () => {
    const { mesiDelSelettore, inizialiDeiGiorni } = selettore('en')
    expect(mesiDelSelettore()[9]).toBe('Oct')
    expect(inizialiDeiGiorni()).toEqual(['M', 'T', 'W', 'T', 'F', 'S', 'S'])
  })

  it('says how many more events a day holds in the user’s language', () => {
    expect(tradotto('Calendar/ShowMoreCalendarEvent.vue')).toContain(
      "{{ __('{0} more', [totalEventsCount - 2]) }}",
    )
    expect(tradotto('Calendar/CalendarWeekly.vue')).not.toContain("+ ' more'")
    expect(tradotto('Calendar/CalendarDaily.vue')).not.toContain("+ ' more'")
  })

  it('starts the agenda’s weeks on Monday, in the month and the week', () => {
    const utili = tradotto('Calendar/calendarUtils.ts')
    expect(utili).toContain('let leftPadding = (firstDay.getDay() + 6) % 7')
    const mese = tradotto('Calendar/CalendarMonthly.vue')
    expect(mese).toContain('v-for="day in [...daysList.slice(1), daysList[0]]"')
    const evento = tradotto('Calendar/CalendarWeekDayEvent.vue')
    expect(evento).toContain(
      'const leftBoundary = (currentDate.getDay() + 6) % 7',
    )
    expect(evento).toContain(
      'const rightBoundary = 6 - ((currentDate.getDay() + 6) % 7)',
    )
  })

  it('draws a check field saved on as on, and names the switch’s button', () => {
    const interruttore = tradotto('Switch/Switch.vue')
    expect(interruttore).toContain(':model-value="Boolean(Number(model))"')
    expect(interruttore).not.toContain('v-model="model"')
    expect(interruttore).toContain(`:aria-label="$attrs['aria-label']"`)
    expect(interruttore).toContain('defineOptions({ inheritAttrs: false })')
    expect(interruttore).toContain('v-bind="senzaIlNome($attrs)"')
    // 1 from the server is on, 0, null and nothing are off
    const acceso = (valore) => Boolean(Number(valore))
    expect([1, true, '1', 0, false, null, undefined].map(acceso)).toEqual([
      true,
      true,
      true,
      false,
      false,
      false,
      false,
    ])
  })

  it('names a dialog by its first heading, and says «Close» in the user’s language', () => {
    const finestra = tradotto('Dialog/Dialog.vue')
    expect(finestra).not.toContain('label="Close"')
    expect(finestra).toContain(`:label="__('Close')"`)
    expect(finestra).toContain('function nominaLaFinestra(')
    expect(finestra).toContain(
      'nominaLaFinestra(event.target as HTMLElement | null, resolved.value.title)',
    )
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
