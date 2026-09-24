/**
 * WhatsApp's own way of writing, turned into HTML.
 *
 * WhatsApp has no markdown: it has five inline marks (`_italic_`, `*bold*`,
 * `~struck~`, backticks) and three kinds of list, and people use them because
 * the phone keyboard offers them. A message arrives as plain text with those
 * marks still in it, so the bubble has to read them.
 *
 * The lists are why this is a file of its own. They were built by turning every
 * `* item` line into a bare `<li>` with no list around it, and a stray `<li>`
 * is a paragraph as far as the browser is concerned: it draws the bullet
 * *outside* the content box, which put the dot outside the bubble, in the
 * margin, next to it. A list item belongs to a list, so the lines are read as
 * blocks first and the marks applied inside them.
 */
// straight from the library rather than through `@/utils`, which is a barrel of
// components and icons: this file is plain text handling, and it stays testable
// on its own
import DOMPurify from 'dompurify'

// A bullet: `* item` or `- item`. The space is what makes it a list rather than
// an emphasis mark, which is how WhatsApp itself tells them apart.
const BULLET = /^\s*[*-]\s+(.+)$/
// `1. item`, `2) item`
const NUMBERED = /^\s*\d+[.)]\s+(.+)$/
// `> quoted`
const QUOTED = /^\s*>\s+(.+)$/

/** The five marks that live inside a line and never cross one. */
function marks(line) {
  return (
    line
      .replace(/_(.*?)_/g, '<i>$1</i>')
      .replace(/\*(.*?)\*/g, '<b>$1</b>')
      .replace(/~(.*?)~/g, '<s>$1</s>')
      // the fence first, so its three backticks are not read as one
      .replace(/```(.*?)```/g, '<code>$1</code>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
  )
}

/**
 * The message as blocks: runs of text, lists, quotes.
 *
 * Exported unsanitized for the tests, which are about the shape of the HTML.
 * Everything that reaches a bubble goes through `formatWhatsAppMessage`.
 */
export function whatsAppBlocks(message) {
  const text = String(message ?? '')
  const out = []
  let open = null
  let paragraph = []

  const closeList = () => {
    if (open) out.push(`</${open}>`)
    open = null
  }
  const closeParagraph = () => {
    // the lines of one run are separated, not spaced apart: a single `<br>`
    // between them is what WhatsApp shows
    if (paragraph.length) out.push(paragraph.join('<br>'))
    paragraph = []
  }

  for (const line of text.split('\n')) {
    const bullet = BULLET.exec(line)
    const numbered = bullet ? null : NUMBERED.exec(line)
    const wanted = bullet ? 'ul' : numbered ? 'ol' : null

    if (wanted) {
      closeParagraph()
      // a bulleted run and a numbered run are two lists, not one
      if (open !== wanted) {
        closeList()
        out.push(`<${wanted} class="wa-list">`)
        open = wanted
      }
      out.push(`<li>${marks((bullet || numbered)[1])}</li>`)
      continue
    }

    closeList()

    const quoted = QUOTED.exec(line)
    if (quoted) {
      closeParagraph()
      out.push(`<blockquote>${marks(quoted[1])}</blockquote>`)
      continue
    }

    paragraph.push(marks(line))
  }

  closeList()
  closeParagraph()
  return out.join('')
}

/** The bubble's HTML: the blocks above, then the sanitizer. */
export function formatWhatsAppMessage(message) {
  return DOMPurify.sanitize(whatsAppBlocks(message))
}
