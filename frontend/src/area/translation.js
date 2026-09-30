// The area speaks the patient's language: Italian here, whatever the staff's
// CRM is translated into. A word missing from the dictionary shows in English.
import it from './it'

const lang = (window.AREA?.lang || 'it').slice(0, 2)
const words = lang === 'it' ? it : {}

export const locale = lang === 'it' ? 'it-IT' : lang

export function translate(message, replace) {
  const values = Array.isArray(replace)
    ? replace
    : replace == null
      ? []
      : [replace]
  const text = words[message] || message
  return text.replace(/{(\d+)}/g, (match, number) =>
    typeof values[number] !== 'undefined' ? String(values[number]) : match,
  )
}
