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

const CARTELLA = '/frappe-ui/src/components/'

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

/** The files the build rewrites, as their path under frappe-ui's components. */
export const FILE = Object.keys(SOSTITUZIONI)

/** The module's code in the user's language, or null when it is not one to rewrite. */
export function traduciFrappeUi(codice, id) {
  // a .vue file's style or template part comes with a query: only the file itself
  if (id.includes('?')) return null
  const dove = id.indexOf(CARTELLA)
  if (dove < 0) return null
  const file = id.slice(dove + CARTELLA.length)
  const sostituzioni = SOSTITUZIONI[file]
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
