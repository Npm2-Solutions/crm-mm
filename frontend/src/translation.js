import { getConfig } from 'frappe-ui'
import { conMarchio } from '@/utils/marchio'
import { conLApostrofo } from '@/utils/locale'

export default function translationPlugin(app) {
  app.config.globalProperties.__ = translate
  window.__ = translate
}

// A missing `replace` used to throw here, and a throw inside a render function
// blanks the whole page: one forgotten argument, an entire settings screen gone
// and a stack trace pointing at translation.js instead of at the call site.
// Leaving the placeholder in place is wrong on screen but wrong in one line.
function format(message, replace) {
  const values = Array.isArray(replace)
    ? replace
    : replace == null
      ? []
      : [replace]
  return message.replace(/{(\d+)}/g, function (match, number) {
    return typeof values[number] != 'undefined' ? String(values[number]) : match
  })
}

function translate(message, replace, context = null) {
  let translatedMessages = getConfig('translatedMessages') || {}
  let translatedMessage = ''

  if (context) {
    let key = `${message}:${context}`
    if (translatedMessages[key]) {
      translatedMessage = translatedMessages[key]
    }
  }

  if (!translatedMessage) {
    translatedMessage = translatedMessages[message] || message
  }

  // a sentence that names the product says "{brand}": the vertical's brand
  translatedMessage = conMarchio(translatedMessage)

  const hasPlaceholders = /{\d+}/.test(message)
  if (!hasPlaceholders) {
    return translatedMessage
  }

  // a date after «il» or «dal» is known only now: «dall'11 set», not «dal 11»
  return conLApostrofo(format(translatedMessage, replace))
}
