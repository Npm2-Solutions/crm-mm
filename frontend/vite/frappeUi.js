// Copyright (c) 2026, NPM2 Solutions Srl and contributors
/**
 * frappe-ui in the user's language.
 *
 * Some of frappe-ui's components write their words in English whatever the user
 * reads, and offer no way to change them: «Load More» and «20 of 870» under every
 * list, «Search» in every link field, «Sun 27», «Sep - Oct 2026» and «All day»
 * over the agenda. The build hands them the user's language: the words go
 * through the app's translator (`__`, the same catalog as every other word), the
 * calendar's names of months and days come from Intl in the boot's language
 * (`window.lang`).
 *
 * Every replacement must find what it replaces: a frappe-ui that writes these
 * lines differently stops the build (and the unit test) instead of going back to
 * English in silence.
 *
 * The same door mends what frappe-ui draws wrong for everybody: the calendar's
 * weeks from Monday, the switch's value and name. And it cuts what frappe-ui
 * makes every phone download for nobody: the editor's code colours, its emoji
 * list before anybody asks, a Markdown format nobody uses.
 */

// Appended to the calendar's calendarUtils.ts: function declarations, hoisted, so
// the lists at the top of the module can call them while it loads.
export const NOMI = `
// DottorCloud: the names in the user's language (frontend/vite/frappeUi.js)
function linguaDelCalendario() {
  const lingua =
    typeof window === 'undefined' ? '' : String(window.lang || '').replace(/_/g, '-')
  try {
    return lingua && Intl.DateTimeFormat.supportedLocalesOf([lingua]).length
      ? lingua
      : undefined
  } catch {
    return undefined
  }
}
function conLaMaiuscola(nome) {
  return nome.charAt(0).toLocaleUpperCase() + nome.slice(1)
}
function nomiDeiMesi() {
  const formato = new Intl.DateTimeFormat(linguaDelCalendario(), { month: 'long' })
  return Array.from({ length: 12 }, (_, mese) =>
    conLaMaiuscola(formato.format(new Date(2000, mese, 1))),
  )
}
function nomiDeiGiorni(stile) {
  const formato = new Intl.DateTimeFormat(linguaDelCalendario(), { weekday: stile })
  // 2 January 2000 was a Sunday: the lists start on Sunday, as getDay() counts
  return Array.from({ length: 7 }, (_, giorno) =>
    conLaMaiuscola(formato.format(new Date(2000, 0, 2 + giorno))),
  )
}
`

// Appended to the date picker's utils.ts. DottorCloud's weeks start on Monday
// (the phone's week, the dashboard's periods, the agenda): the grid starts
// there for everybody, and the letters over its columns are read from the
// same day. frappe-ui's grid followed dayjs's language (Monday in Italian) while
// its letters were an English list from Sunday, which put «S» (Saturday) over
// Sunday the 4th.
export const SELETTORE = `
// DottorCloud: the picker in the user's language (frontend/vite/frappeUi.js)
function linguaDelSelettore() {
  const lingua =
    typeof window === 'undefined' ? '' : String(window.lang || '').replace(/_/g, '-')
  try {
    return lingua && Intl.DateTimeFormat.supportedLocalesOf([lingua]).length
      ? lingua
      : undefined
  } catch {
    return undefined
  }
}
function mesiDelSelettore() {
  const formato = new Intl.DateTimeFormat(linguaDelSelettore(), { month: 'short' })
  return Array.from({ length: 12 }, (_, mese) => {
    const nome = formato.format(new Date(2000, mese, 1))
    return nome.charAt(0).toLocaleUpperCase() + nome.slice(1)
  })
}
export function dalLunedi(giorno) {
  return giorno.subtract((giorno.day() + 6) % 7, 'day')
}
export function inizialiDeiGiorni() {
  const formato = new Intl.DateTimeFormat(linguaDelSelettore(), { weekday: 'narrow' })
  // 3 January 2000 was a Monday
  return Array.from({ length: 7 }, (_, giorno) =>
    formato.format(new Date(2000, 0, 3 + giorno)),
  )
}
`

/** An attribute of a template, `label="Load More"`, bound to its translation. */
function attributo(nome, testo) {
  return [`${nome}="${testo}"`, `:${nome}="__('${testo}')"`]
}

/** A text between two tags, `<div>of</div>`, through the translator. */
function testo(parola) {
  return [new RegExp(`>\\s*${parola}\\s*<`), `>{{ __('${parola}') }}<`]
}

/**
 * A sentence between two tags, however the template spaces it; `tutte` for one
 * written more than once.
 */
function frase(testo, { tutte = false, contesto = null } = {}) {
  const cerca = testo
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/ /g, '\\s+')
  const chiamata = contesto
    ? `__('${testo}', null, '${contesto}')`
    : `__('${testo.replace(/'/g, "\\'")}')`
  return [
    new RegExp(`>(\\s*)${cerca}(\\s*)<`, tutte ? 'g' : ''),
    `>$1{{ ${chiamata} }}$2<`,
  ]
}

/** A word in the component's script, through the translator once the app has it. */
const TRADUCI = '(globalThis.__ || String)'

/**
 * A default of `withDefaults`, `placeholder: 'Select option'`, made when the
 * component is: by then the app's translator is there.
 */
function predefinito(nome, testo) {
  return [
    `${nome}: '${testo}',`,
    `${nome}: () => (globalThis.__ || String)('${testo}'),`,
  ]
}

const SOSTITUZIONI = {
  'Calendar/calendarUtils.ts': [
    // the month's grid, and so its weeks, from Monday
    [
      'let leftPadding = firstDay.getDay()',
      'let leftPadding = (firstDay.getDay() + 6) % 7',
    ],
    [
      /export const monthList = \[[^\]]*\]/,
      'export const monthList = nomiDeiMesi()',
    ],
    [
      /export const daysList = \[[^\]]*\]/,
      "export const daysList = nomiDeiGiorni('short')",
    ],
    [
      /export const daysListFull = \[[^\]]*\]/,
      "export const daysListFull = nomiDeiGiorni('long')",
    ],
    [
      "toLocaleDateString('en-US', options)",
      'toLocaleDateString(linguaDelCalendario(), options)',
    ],
  ],
  // «All day» beside the hours: a class of ours lets it take two short lines
  // on a phone, where the column is narrower than the words
  'Calendar/CalendarWeekly.vue': [
    [
      /class="text-sm text-ink-gray-6 h-\[29px\] inline-flex items-center"\s*>\s*All day\s*</,
      `class="dc-tutto-il-giorno text-sm text-ink-gray-6 h-[29px] inline-flex items-center">{{ __('All day') }}<`,
    ],
    [
      `:label="fullDayEvents[parseDate(date)]?.length - 2 + ' more'"`,
      `:label="__('{0} more', [fullDayEvents[parseDate(date)]?.length - 2])"`,
    ],
  ],
  // the month's header from Monday, as its grid
  'Calendar/CalendarMonthly.vue': [
    [
      'v-for="day in daysList"',
      'v-for="day in [...daysList.slice(1), daysList[0]]"',
    ],
  ],
  // an event dragged across the week stays in it: Monday to Sunday
  'Calendar/CalendarWeekDayEvent.vue': [
    [
      'const leftBoundary = currentDate.getDay()',
      'const leftBoundary = (currentDate.getDay() + 6) % 7',
    ],
    [
      'const rightBoundary = 6 - currentDate.getDay()',
      'const rightBoundary = 6 - ((currentDate.getDay() + 6) % 7)',
    ],
  ],
  'Calendar/CalendarDaily.vue': [
    [
      /class="text-sm text-ink-gray-6 h-7 inline-flex items-center"\s*>\s*All day\s*</,
      `class="dc-tutto-il-giorno text-sm text-ink-gray-6 h-7 inline-flex items-center">{{ __('All day') }}<`,
    ],
    [
      `:label="dayFullDayEvents.length - 4 + ' more'"`,
      `:label="__('{0} more', [dayFullDayEvents.length - 4])"`,
    ],
  ],
  // «4 more» under a full day of the month
  'Calendar/ShowMoreCalendarEvent.vue': [
    [
      /\{\{\s*totalEventsCount - 2\s*\}\}\s*more/,
      "{{ __('{0} more', [totalEventsCount - 2]) }}",
    ],
  ],
  'ListView/ListFooter.vue': [attributo('label', 'Load More'), testo('of')],
  'Autocomplete/Autocomplete.vue': [
    attributo('placeholder', 'Search'),
    attributo('label', 'Select All'),
    attributo('label', 'Clear All'),
    attributo('label', 'Clear'),
  ],
  'DatePicker/utils.ts': [
    [
      /export const months: string\[\] = \[[^\]]*\]/,
      'export const months: string[] = mesiDelSelettore()',
    ],
    [
      "const start = monthStart(year, monthIndex).startOf('week')",
      'const start = dalLunedi(monthStart(year, monthIndex))',
    ],
  ],
  'DatePicker/CalendarPanel.vue': [
    [
      "import { months } from './utils'",
      "import { dalLunedi, inizialiDeiGiorni, months } from './utils'",
    ],
    [
      "const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S']",
      'const WEEKDAYS = inizialiDeiGiorni()',
    ],
    // Home and End go to the first and last column: Monday and Sunday
    [
      "shiftFocus(cell.date.subtract(cell.date.day(), 'day'), -1)",
      'shiftFocus(dalLunedi(cell.date), -1)',
    ],
    [
      "shiftFocus(cell.date.add(6 - cell.date.day(), 'day'), 1)",
      "shiftFocus(dalLunedi(cell.date).add(6, 'day'), 1)",
    ],
    // what a screen reader says of the arrows and the grid
    [/(\s)label="previous"/g, `$1:label="__('Previous month')"`],
    [/(\s)label="next"/g, `$1:label="__('Next month')"`],
    attributo('aria-label', 'Calendar dates'),
    attributo('aria-label', 'Select month and year'),
    attributo('aria-label', 'Select year'),
    attributo('aria-label', 'Select month'),
    [
      "(cell.isToday ? ' (Today)' : '')",
      "(cell.isToday ? ' (' + (globalThis.__ || String)('Today') + ')' : '')",
    ],
  ],
  'DatePicker/DatePicker.vue': [
    attributo('today-label', 'Today'),
    predefinito('placeholder', 'Select date'),
  ],
  'DatePicker/DateTimePicker.vue': [
    attributo('today-label', 'Now'),
    attributo('placeholder', 'Select time'),
    predefinito('placeholder', 'Select date & time'),
  ],
  'DatePicker/DateRangePicker.vue': [
    predefinito('placeholder', 'Select range'),
  ],
  'TimePicker/TimePicker.vue': [predefinito('placeholder', 'Select time')],
  'Select/Select.vue': [
    predefinito('placeholder', 'Select option'),
    predefinito('emptyText', 'No options'),
  ],
  'Combobox/Combobox.vue': [
    predefinito('placeholder', 'Select option'),
    predefinito('emptyText', 'No results'),
  ],
  'MultiSelect/MultiSelect.vue': [
    predefinito('placeholder', 'Select option'),
    predefinito('emptyText', 'No results'),
  ],
  // the switch, mended. A check field comes from the server as 0 or 1 and
  // reka's SwitchRoot is on only for `true`: a setting saved on was drawn off.
  // An `aria-label` stayed on the outer box, where no screen reader looks, and
  // VoiceOver read «switch» and nothing else. The value is read as a number,
  // the name goes to the button.
  'Switch/Switch.vue': [
    [
      '<template>\n  <div class="flex flex-col">',
      '<template>\n  <div class="flex flex-col" v-bind="senzaIlNome($attrs)">',
    ],
    [
      'v-model="model"',
      `:model-value="Boolean(Number(model))"
        :aria-label="$attrs['aria-label']"
        :aria-labelledby="$attrs['aria-labelledby']"
        @update:model-value="(acceso) => (model = acceso)"`,
    ],
    [
      'const attrs = useAttrs()',
      `const attrs = useAttrs()
// DottorCloud (frontend/vite/frappeUi.js): the name is the button's
defineOptions({ inheritAttrs: false })
function senzaIlNome(tutti: Record<string, unknown>) {
  const { 'aria-label': _nome, 'aria-labelledby': _da, ...resto } = tutti
  return resto
}`,
    ],
  ],
  // the toasts' region and their ×, in the user's language: «Notifications
  // alt+T» and «Close toast» to a screen reader, in English
  'Toast/ToastProvider.vue': [
    [
      ':visible-toasts="3"',
      `:visible-toasts="3"
    :container-aria-label="__('Notifications')"`,
    ],
    [
      'unstyled: true,',
      `unstyled: true,
      closeButtonAriaLabel: __('Close'),`,
    ],
  ],
  // the dialog, named. One that draws its own body (`#body`, `#body-header`)
  // has no DialogTitle, and VoiceOver read «dialog» and nothing else: its
  // first heading names it, else the title it was given. Its close button
  // said «Close» in English to a screen reader.
  'Dialog/Dialog.vue': [
    [/label="Close"/g, `:label="__('Close')"`],
    [
      'function handleOpenAutoFocus(event: Event) {',
      `// DottorCloud (frontend/vite/frappeUi.js): the dialog's name
function nominaLaFinestra(finestra: HTMLElement | null, titolo?: string) {
  if (!finestra) return
  const per = finestra.getAttribute('aria-labelledby')
  if (per && document.getElementById(per)?.textContent?.trim()) return
  const intestazione = finestra.querySelector('h1, h2, h3, h4') as HTMLElement | null
  if (intestazione?.textContent?.trim()) {
    if (!intestazione.id) intestazione.id = (finestra.id || 'finestra') + '-intestazione'
    finestra.setAttribute('aria-labelledby', intestazione.id)
  } else if (titolo) {
    finestra.removeAttribute('aria-labelledby')
    finestra.setAttribute('aria-label', titolo)
  }
}

function handleOpenAutoFocus(event: Event) {
  nominaLaFinestra(event.target as HTMLElement | null, resolved.value.title)`,
    ],
  ],
}

// frappe-ui/frappe: the data import pages, written with no translator at all
const SOSTITUZIONI_FRAPPE = {
  'DataImport/DataImport.vue': [
    ["label: 'Data Import',", `label: ${TRADUCI}('Data Import'),`],
    [
      'label: `Importing ${doctypeTitle.value}`,',
      `label: ${TRADUCI}('Importing {0}', [doctypeTitle.value]),`,
    ],
  ],
  'DataImport/DataImportList.vue': [
    frase('Data Import'),
    frase('Import data into your system using CSV files.'),
    frase('Import'),
    frase('Name'),
    frase('Status'),
    frase('Load More'),
    frase('No data imports found.'),
    attributo('placeholder', 'Search imported files'),
    attributo('label', 'Choose a Document Type to import'),
    ["title: 'New Data Import',", "title: __('New Data Import'),"],
    ["label: 'Continue',", "label: __('Continue'),"],
    [':label="dataImport.status"', ':label="__(dataImport.status)"'],
    [
      '{{ dataImport.reference_doctype }}',
      '{{ __(dataImport.reference_doctype) }}',
    ],
    [
      '({ label: option, value: option })',
      `({ label: ${TRADUCI}(option), value: option })`,
    ],
  ],
  'DataImport/ImportSteps.vue': [
    frase('Upload File'),
    frase('Map Data'),
    frase('Review & Import'),
  ],
  'DataImport/MappingStep.vue': [
    frase('Map Data'),
    frase(
      'Change the mapping of columns from your file to fields in the system',
    ),
    frase('Fields in File'),
    frase('Fields in System'),
    attributo('label', 'Reset Mapping'),
    attributo('label', 'Continue'),
    attributo('placeholder', 'Select field'),
    ['{{ data?.status }}', '{{ __(data?.status) }}'],
    ['? f.label', `? ${TRADUCI}(f.label)`],
    ['`${f.label} (', `\`\${${TRADUCI}(f.label)} (`],
  ],
  'DataImport/PreviewStep.vue': [
    frase('Review and Import'),
    frase('Verify the data before starting the import process'),
    frase('Column Mapping'),
    frase('Warnings'),
    frase('Import Logs'),
    frase('Row no.'),
    frase('Message'),
    frase('Failed to import'),
    frase('Successfully imported'),
    frase('No logs to display.'),
    attributo('label', 'Done'),
    ['{{ data.status }}', '{{ __(data.status) }}'],
    [
      `:label="data.status != 'Pending' ? 'Retry' : 'Import'"`,
      `:label="data.status != 'Pending' ? __('Retry') : __('Import')"`,
    ],
    [
      "{{ importSuccessCount }} {{ importSuccessCount == 1 ? 'row' : 'rows' }} imported successfully, {{ importErrorCount }} {{ importErrorCount == 1 ? 'row' : 'rows' }} failed.",
      "{{ __('Rows imported: {0}. Rows not imported: {1}.', [importSuccessCount, importErrorCount]) }}",
    ],
    [
      "{ label: 'All', value: 'all' }",
      `{ label: ${TRADUCI}('All'), value: 'all' }`,
    ],
    [
      "{ label: 'Successful', value: 'successful' }",
      `{ label: ${TRADUCI}('Successful'), value: 'successful' }`,
    ],
    [
      "{ label: 'Failed', value: 'failed' }",
      `{ label: ${TRADUCI}('Failed'), value: 'failed' }`,
    ],
    ['`Column ${index + 1}`', `${TRADUCI}('Column {0}', [index + 1])`],
  ],
  'DataImport/TemplateModal.vue': [
    ["title: 'Export Data',", "title: __('Export Data'),"],
    attributo('label', 'File Type'),
    frase('Select the fields you want to include in the template.'),
    attributo('label', 'Select All'),
    attributo('label', 'Select Mandatory Fields'),
    attributo('label', 'Unselect All'),
    attributo('label', 'Export'),
    attributo('label', 'Cancel'),
    ['{{ doctype }}', '{{ __(doctype) }}'],
    [
      '{{ field.label || field.fieldname }}',
      '{{ __(field.label) || field.fieldname }}',
    ],
  ],
  // a link field with no placeholder of its own said «Search doctype» (the
  // data import's «what to import»): «Search», whatever it links to
  'Link/Link.vue': [
    [
      ':placeholder="placeholder ?? `Search ${doctype.toLowerCase()}`"',
      `:placeholder="placeholder ?? __('Search')"`,
    ],
  ],
  'DataImport/UploadStep.vue': [
    frase('Choose Import'),
    frase('Continue'),
    frase('Import data into your system using CSV files or Google Sheets.'),
    frase('Drag and drop a CSV file, or upload from your'),
    // the pieces of one sentence: "…caricalo dal tuo dispositivo o da un foglio Google"
    frase('Device', { contesto: 'Data import' }),
    frase('or', { contesto: 'Data import' }),
    frase('Google Sheet', { tutte: true, contesto: 'Data import' }),
    frase('Make sure the link is publically accessible to fetch the data.'),
    frase('Download CSV Template'),
    attributo('placeholder', 'Add Google Sheets Link'),
    ['{{ data?.status }}', '{{ __(data?.status) }}'],
    ['}} of {{', "}} {{ __('of') }} {{"],
    ["label: 'Mandatory Fields',", "label: __('Mandatory Fields'),"],
    ["label: 'All Fields',", "label: __('All Fields'),"],
    ["label: 'Custom Template',", "label: __('Custom Template'),"],
    [
      "toast.error('Please upload a valid CSV file.')",
      `toast.error(${TRADUCI}('Please upload a valid CSV file.'))`,
    ],
  ],
}

// frappe-ui/src/molecules: the editor - its toolbar's labels in the tooltips, its
// code block, its emoji, its Markdown
const SOSTITUZIONI_MOLECOLE = {
  'editor/MenuItems.vue': [
    [
      'return item.getLabel(props.editor)',
      `return ${TRADUCI}(item.getLabel(props.editor))`,
    ],
    ['  return item.label\n}', `  return ${TRADUCI}(item.label)\n}`],
    [':label="item.label"', ':label="__(item.label)"'],
    [/\{\{\s*item\.label\s*\}\}/, '{{ __(item.label) }}'],
    [':text="groupItem.label"', ':text="__(groupItem.label)"'],
    [':label="groupItem.label"', ':label="__(groupItem.label)"'],
  ],
  // The code block (``` in a note or an email) without highlight.js: its 37
  // languages and its engine were a third of the editor's download, every time
  // an editor opened, to colour code nobody writes at a centre. TipTap's own
  // code block has the same options; its text stays as it was written, and
  // with no language to choose there is no picker of them.
  'editor/extensions/code-block/code-block.ts': [
    ["import { common, createLowlight } from 'lowlight'\n", ''],
    [
      "import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'",
      "import { CodeBlock } from '@tiptap/extension-code-block'",
    ],
    ['const lowlight = createLowlight(common)\n', ''],
    ['CodeBlockLowlight.extend({', 'CodeBlock.extend({'],
    ['}).configure({ lowlight })', '})'],
    // its keys over TipTap's, not instead of them: Enter three times, or the
    // arrow down at its end, leave the block again (stuck in it before, with
    // no way out on a phone), Backspace empties it
    [
      'addKeyboardShortcuts() {\n    return {\n      Tab: () => {',
      'addKeyboardShortcuts() {\n    return {\n      ...this.parent?.(),\n      Tab: () => {',
    ],
  ],
  // The emoji after ":" (":smile", in English): their list, 66 KB, comes
  // the first time somebody types one, not with every editor
  'editor/extensions/emoji/emoji-extension.ts': [
    ["import _EMOJIS from './emojis.json'\n", ''],
    [
      'const EMOJIS = _EMOJIS as EmojiItem[]',
      `let elencoDelleEmoji: Promise<EmojiItem[]> | undefined
const EMOJIS = () =>
  (elencoDelleEmoji ||= import('./emojis.json').then(
    (modulo) => modulo.default as EmojiItem[],
  ))`,
    ],
    [
      "items: ({ query }: { query: string }) => {\n    return filterByQuery(EMOJIS, query, 'name')",
      "items: async ({ query }: { query: string }) => {\n    return filterByQuery(await EMOJIS(), query, 'name')",
    ],
  ],
  // Markdown as the editor's format (`format: 'markdown'`): nobody here writes
  // it. Re-exported for whoever imports it, the build kept it all the same, with
  // the half of marked only it used (58 KB). Markdown pasted is still made into
  // formatting (content-paste, with the rest of marked).
  'editor/extensions.ts': [
    [
      "export { Markdown, type MarkdownExtensionOptions } from '@tiptap/markdown'",
      '',
    ],
  ],
  'editor/extensions/code-block/CodeBlockComponent.vue': [
    [/<Combobox\s+v-if="isEditable"[\s\S]*?<\/span>/, ''],
    [
      "import { createLowlight } from 'lowlight'",
      "import type { createLowlight } from 'lowlight'",
    ],
    ['label="Copy code"', ':label="__(\'Copy code\')"'],
    [
      ":text=\"copied ? 'Copied!' : 'Copy code'\"",
      ":text=\"copied ? __('Copied!') : __('Copy code')\"",
    ],
  ],
}

const RADICI = {
  '/frappe-ui/src/components/': SOSTITUZIONI,
  '/frappe-ui/src/molecules/': SOSTITUZIONI_MOLECOLE,
  '/frappe-ui/frappe/': SOSTITUZIONI_FRAPPE,
}

/** What the build appends to a file it rewrites, after its own code. */
const CODA = {
  'Calendar/calendarUtils.ts': NOMI,
  'DatePicker/utils.ts': SELETTORE,
}

/** The files the build rewrites, as their path under frappe-ui's components. */
export const FILE = Object.keys(SOSTITUZIONI)

/** The same, under frappe-ui/frappe. */
export const FILE_FRAPPE = Object.keys(SOSTITUZIONI_FRAPPE)

/** The same, under frappe-ui's molecules. */
export const FILE_MOLECOLE = Object.keys(SOSTITUZIONI_MOLECOLE)

/** The module's code in the user's language, or null when it is not one to rewrite. */
export function traduciFrappeUi(codice, id) {
  // a .vue file's style or template part comes with a query: only the file itself
  if (id.includes('?')) return null
  const radice = Object.keys(RADICI).find((cartella) => id.includes(cartella))
  if (!radice) return null
  const file = id.slice(id.indexOf(radice) + radice.length)
  const sostituzioni = RADICI[radice][file]
  if (!sostituzioni) return null
  for (const [cerca, metti] of sostituzioni) {
    const trovato =
      typeof cerca === 'string' ? codice.includes(cerca) : cerca.test(codice)
    if (!trovato) {
      throw new Error(
        `frappeUi.js: frappe-ui's ${file} no longer has ${cerca}: see frontend/vite/frappeUi.js`,
      )
    }
    codice = codice.replace(cerca, metti)
  }
  return codice + (CODA[file] || '')
}

export default function frappeUiNellaLingua() {
  return {
    name: 'dottorcloud-frappe-ui-nella-lingua',
    // before the Vue plugin compiles the templates
    enforce: 'pre',
    transform(codice, id) {
      const tradotto = traduciFrappeUi(codice, id)
      return tradotto == null ? null : { code: tradotto, map: null }
    },
  }
}
