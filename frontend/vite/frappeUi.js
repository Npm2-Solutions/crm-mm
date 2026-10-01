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
  'Calendar/CalendarWeekly.vue': [testo('All day')],
  'Calendar/CalendarDaily.vue': [testo('All day')],
  'ListView/ListFooter.vue': [attributo('label', 'Load More'), testo('of')],
  'Autocomplete/Autocomplete.vue': [
    attributo('placeholder', 'Search'),
    attributo('label', 'Select All'),
    attributo('label', 'Clear All'),
    attributo('label', 'Clear'),
  ],
  'DatePicker/DatePicker.vue': [
    attributo('today-label', 'Today'),
    predefinito('placeholder', 'Select date'),
  ],
  'DatePicker/DateTimePicker.vue': [
    attributo('today-label', 'Now'),
    attributo('placeholder', 'Select time'),
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

// frappe-ui/src/molecules: the editor's toolbar, its labels in the tooltips
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
}

const RADICI = {
  '/frappe-ui/src/components/': SOSTITUZIONI,
  '/frappe-ui/src/molecules/': SOSTITUZIONI_MOLECOLE,
  '/frappe-ui/frappe/': SOSTITUZIONI_FRAPPE,
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
  return file === 'Calendar/calendarUtils.ts' ? codice + NOMI : codice
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
