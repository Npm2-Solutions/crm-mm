// The area speaks its people's language: Italian here, whatever the staff's
// DottorCloud is translated into. A word missing from the dictionary shows in
// English. The vertical the plan has on says some words its own way first -
// with the clinic, the centre's clients are its patients (crm.verticali).
import it from './it'

const lang = (window.AREA?.lang || 'it').slice(0, 2)
const words = lang === 'it' ? it : {}
const vertical = window.AREA?.words || {}

export const locale = lang === 'it' ? 'it-IT' : lang

export function translate(message, replace) {
  const values = Array.isArray(replace)
    ? replace
    : replace == null
      ? []
      : [replace]
  const said = vertical[message] || message
  const text = words[said] || said
  return text.replace(/{(\d+)}/g, (match, number) =>
    typeof values[number] !== 'undefined' ? String(values[number]) : match,
  )
}
