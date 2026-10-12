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
  FILE_ICONE,
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
const ICONE = path.resolve(
  import.meta.dirname,
  '../../node_modules/frappe-ui/icons',
)

function tradotto(file, cartella = COMPONENTI) {
  const id = path.join(cartella, file)
  return traduciFrappeUi(fs.readFileSync(id, 'utf8'), id)
}

function nomi(lang) {
  window.lang = lang
  return new Function(`${NOMI}; return { nomiDeiMesi, nomiDeiGiorni }`)()
}

// the date picker's names, its Monday and a day typed by hand
function selettore(lang) {
  window.lang = lang
  return new Function(
    `${SELETTORE.replace(/^export /gm, '')}; return { mesiDelSelettore, inizialiDeiGiorni, dalLunedi, giornoScritto }`,
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
    for (const file of FILE_ICONE) {
      expect(() => tradotto(file, ICONE), file).not.toThrow()
      expect(tradotto(file, ICONE), file).not.toBeNull()
    }
  })

  it("names the boxes that choose a list's rows", () => {
    const riga = tradotto('ListView/ListRow.vue')
    expect(riga).toContain(':aria-label="nomeDellaRiga()"')
    expect(riga).toContain("t('Select {0}', [String(nome)])")
    expect(tradotto('ListView/ListHeader.vue')).toContain(
      `:aria-label="__('Select all')"`,
    )
  })

  it("takes a click on a row box's cell as the box's, around it", () => {
    const riga = tradotto('ListView/ListRow.vue')
    // the cell reaches 8px on each side of the 14px box: 30px wide
    expect(riga).toContain(
      'class="w-fit -ms-2 ps-2 pe-2 py-3 flex cursor-pointer"',
    )
    // what the box does, shift and all, never the row's link nor its click
    expect(riga).toMatch(
      /@click\.stop\.prevent="handleCheckboxClick"\s+@dblclick\.stop/,
    )
    expect(riga).not.toMatch(/@click\.stop\.prevent\s/)
    // the box keeps its own click, which stops there: one toggle, not two
    expect(riga).toContain('@click.stop="handleCheckboxClick"')
  })

  it("takes the icon picker's words through the translator", () => {
    const codice = tradotto('IconPicker.vue', ICONE)
    expect(codice).toContain(`__('No icons found for "{0}"', [searchTerm])`)
    expect(codice).toContain(`{{ __('No icons available.') }}`)
    expect(codice).toContain(`placeholder || __('Select an icon...')`)
    expect(codice).not.toMatch(/>\s*No icons/)
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
    // found by its Italian words too, named by them for a reader in Italian
    expect(emoji).toContain("from '@/utils/emoji'")
    expect(emoji).toContain('caricaLeParole()')
    expect(emoji).toContain('cercaLeEmoji(await EMOJIS(), query).slice(0, 5)')
    expect(emoji).not.toContain('filterByQuery(EMOJIS')
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

  it('says the chosen rows of a list in the reader’s words', () => {
    const barra = tradotto('ListView/ListSelectBanner.vue')
    expect(barra).toContain(`{{ __('Select all') }}`)
    expect(barra).not.toMatch(/>\s*Select all\s*</)
    const lista = tradotto('ListView/ListView.vue')
    expect(lista).not.toContain('rows selected`')
    const testo = lista.match(/\(\(val\) => val === 1 \?[^\n]*\)\)/)[0]
    // without the app's translator, the English with its number
    const scelte = new Function(`return ${testo}`)()
    expect(scelte(1)).toBe('1 row selected')
    expect(scelte(3)).toBe('3 rows selected')
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

  it('reads a day typed by hand the day first, before frappe-ui’s American reading', () => {
    const composable = tradotto('DatePicker/composables.ts')
    expect(composable).toContain(
      "import { giornoScritto, monthStart, getDateValue } from './utils'",
    )
    expect(composable).toContain(
      "import { adessoDelCentro } from '@/utils/scheduler'",
    )
    // the field's own format first, then the day typed, and only then
    // dayjs(raw); the centre's clock handed over, asked only when needed
    const scritto = composable.indexOf(
      'giornoScritto(raw, format, adessoDelCentro)',
    )
    expect(scritto).toBeGreaterThan(
      composable.indexOf('dayjs(raw, format, true)'),
    )
    expect(scritto).toBeLessThan(
      composable.indexOf('const dLoose = dayjs(raw)'),
    )
    const { giornoScritto } = selettore('it')
    // the centre's now, 12 October 2026: how many times it was asked
    let chiesto = 0
    const adesso = () => (chiesto++, new Date(2026, 9, 12))
    const giorno = (testo, formato = 'DD/MM/YYYY') =>
      giornoScritto(testo, formato, adesso)
    for (const testo of [
      '1/10/2026',
      '1-10-2026',
      '1.10.2026',
      '01.10.2026',
      '1 10 2026',
      '1.10.26',
      ' 1/10/2026 ',
    ]) {
      expect(giorno(testo), testo).toBe('2026-10-01')
    }
    expect(giorno('12/10/26 9:30')).toBe('2026-10-12 09:30:00')
    expect(giorno('12/10/2026 9.30')).toBe('2026-10-12 09:30:00')
    expect(giorno('12/10/2026 09:30:15')).toBe('2026-10-12 09:30:15')
    // two digits of a year: the one within the next twenty years and the last
    // eighty (a birth in 1958, never 2058); none, this year
    expect(giorno('1/2/80')).toBe('1980-02-01')
    expect(giorno('12/3/58')).toBe('1958-03-12')
    expect(giorno('1/2/68')).toBe('1968-02-01')
    expect(giorno('1/2/47')).toBe('1947-02-01')
    expect(giorno('1/2/46')).toBe('2046-02-01')
    expect(giorno('1/10/26')).toBe('2026-10-01')
    expect(giorno('1/10/00')).toBe('2000-10-01')
    expect(
      giornoScritto('1/10', 'DD/MM/YYYY', () => new Date(2027, 0, 5)),
    ).toBe('2027-10-01')
    expect(
      giornoScritto('1/10/05', 'DD/MM/YYYY', () => new Date(2090, 0, 5)),
    ).toBe('2105-10-01')
    // the clock is asked only for a year missing or of two digits, never for
    // a value from the server, which every picker reads this way too
    chiesto = 0
    giorno('1/10/2026')
    giorno('2026-10-01 09:30:00')
    expect(chiesto).toBe(0)
    giorno('1/10')
    expect(chiesto).toBe(1)
    // with no format, or the server's, the day first as well
    expect(giorno('1/10/2026', undefined)).toBe('2026-10-01')
    expect(giorno('1/10/2026', 'YYYY-MM-DD')).toBe('2026-10-01')
    // the month first only where the field's format starts with it
    expect(giorno('1/10/2026', 'MM/DD/YYYY')).toBe('2026-01-10')
    expect(giorno('10-1-2026', 'MM-DD-YYYY HH:mm')).toBe('2026-10-01')
    // a day that does not exist is no day, never the next one
    for (const testo of [
      '31/02/2026',
      '29/02/2027',
      '0/10/2026',
      '1/13/2026',
      '1/10/202',
      '1/10/2026 24:00',
      '1/10/2026 9:60',
      '1/10/2026 dopo',
    ]) {
      expect(giorno(testo), testo).toBeNull()
    }
    expect(giorno('29/02/2028')).toBe('2028-02-29')
    // what is not written so goes on to frappe-ui: the server's value, a month
    // in words, a time alone
    for (const testo of [
      '2026-10-01',
      '2026-10-01 09:30:00',
      '2026-10-01 09:30:00.123456',
      '1 Oct 2026',
      '9:30',
      '',
      null,
    ]) {
      expect(giorno(testo), testo).toBeUndefined()
    }
    // dayjs reads what it gives as the day typed
    expect(dayjs(giorno('1/10/2026')).format('YYYY-MM-DD')).toBe('2026-10-01')
    expect(dayjs(giorno('12/10/26 9:30')).format('DD/MM/YYYY HH:mm')).toBe(
      '12/10/2026 09:30',
    )
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

  it('names for a screen reader, in the user’s language, what reka and frappe-ui name in English', () => {
    const scelta = tradotto('Combobox/Combobox.vue')
    expect(scelta).toContain(`:aria-label="__('Show the choices')"`)
    expect(tradotto('Toast/Toast.vue')).toContain(`:aria-label="__('Close')"`)
    expect(tradotto('Toast/Toast.vue')).not.toContain('aria-label="Close"')
    expect(tradotto('Spinner/Spinner.vue')).toContain(
      `:aria-label="__('Loading')"`,
    )
    const calendario = tradotto('DatePicker/CalendarPanel.vue')
    expect(calendario).not.toContain('cycle-calendar-view')
    expect(tradotto('InputLabeling/RequiredIndicator.vue')).toContain(
      `{{ __('(required)') }}`,
    )
    expect(tradotto('Menu/Menu.vue')).toContain(`{{ __('No options') }}`)
  })

  it('mounts a dialog and a menu’s content at their first opening', () => {
    const finestra = tradotto('Dialog/Dialog.vue')
    expect(finestra).toContain(
      '<DialogRoot v-if="giaAperta" v-model:open="isOpen">',
    )
    expect(finestra).toContain('const giaAperta = ref(isOpen.value)')
    expect(finestra).toContain('useSlots, watch, watchEffect }')
    const menu = tradotto('Dropdown/Dropdown.vue')
    expect(menu).toContain(
      '<DropdownMenuPortal v-if="giaAperto" :to="portalTo">',
    )
    expect(menu).toContain('const giaAperto = ref(openModel.value)')
    expect(menu).toContain(
      'import { computed, ref, useAttrs, useSlots, watch }',
    )
  })

  it('builds the table toolbar’s buttons the first time a table is entered', () => {
    const tabella = tradotto('editor/EditorTableMenu.vue', MOLECOLE)
    expect(tabella).toContain(
      '<MenuItems v-if="editor && giaVisto" :editor="editor" :items="tableToolbar" />',
    )
    expect(tabella).toContain('const giaVisto = ref(false)')
    expect(tabella).toContain('if (si) giaVisto.value = true')
  })

  it('draws a tooltip only where a pointer rests over things', () => {
    const suggerimento = tradotto('Tooltip/Tooltip.vue')
    expect(suggerimento).toContain('<slot v-if="disabled || !siPosa" />')
    expect(suggerimento).toContain("import { siPosa } from '@/utils/puntatore'")
    const pulsante = tradotto('Button/Button.vue')
    expect(pulsante).toContain(
      'if (!hasTooltip.value || !siPosa.value) return button',
    )
    expect(pulsante).toContain("import { siPosa } from '@/utils/puntatore'")
  })

  it('places a select’s list on a phone as the sheet takes it, where a finger scrolls it', () => {
    const selettore = tradotto('Select/Select.vue')
    expect(selettore).toContain(
      'props.offset !== undefined ||\n    isMobileView.value,\n)',
    )
    // the list placed and sized by that one condition
    expect(selettore).toContain(
      `:position="usesPopperPosition ? 'popper' : 'item-aligned'"`,
    )
    expect(selettore).toContain(
      "import { isMobileView } from '@/composables/breakpoints'",
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
