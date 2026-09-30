// The area speaks its people's language: Italian here, whatever the staff's
// DottorCloud is translated into. A word missing from the dictionary shows in
// English. The vertical the plan has on says some words its own way first -
// with the clinic, the centre's clients are its patients (crm.verticali) - and
// a sentence that names the product gets its brand's name ("{brand}").
import it from './it'
import { conMarchio, marchio } from '@/utils/marchio'

const lang = (window.AREA?.lang || 'it').slice(0, 2)
const words = lang === 'it' ? it : {}
const vertical = window.AREA?.words || {}
const brand = marchio(window.AREA?.brand).name

export const locale = lang === 'it' ? 'it-IT' : lang

export function translate(message, replace) {
  const values = Array.isArray(replace)
    ? replace
    : replace == null
      ? []
      : [replace]
  const said = vertical[message] || message
  const text = conMarchio(words[said] || said, brand)
  return text.replace(/{(\d+)}/g, (match, number) =>
    typeof values[number] !== 'undefined' ? String(values[number]) : match,
  )
}
