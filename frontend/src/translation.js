import { getConfig } from 'frappe-ui'

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

  const hasPlaceholders = /{\d+}/.test(message)
  if (!hasPlaceholders) {
    return translatedMessage
  }

  return format(translatedMessage, replace)
}
