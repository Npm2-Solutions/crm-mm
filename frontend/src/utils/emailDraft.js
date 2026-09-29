/**
 * An email being written, and what is added to it on its way out.
 *
 * The signature used to be put into the editor the moment the email line was
 * clicked: the box grew by four lines before a word had been written and —
 * being a draft now, with the signature in it — stayed that tall until
 * somebody pressed Discard. What is in the box is now only what was written;
 * the signature goes on when the email leaves, under what was written and
 * above the message being answered, which is where a signature goes.
 *
 * Parsed with DOMParser, never with `innerHTML` on an element of the page: a
 * reply carries the customer's email, and a detached element of a live
 * document still loads the images in it — and runs their `onerror`.
 */

// the paragraph a reply puts between what is written and the email it quotes
// (EmailArea.vue sets it, EmailContent.vue folds what follows it away)
const QUOTE = 'p.reply-to-content'

function parse(html) {
  return new DOMParser().parseFromString(
    `<!doctype html><body>${html || ''}</body>`,
    'text/html',
  ).body
}

// its words, for comparing what two pieces of HTML say
function words(html) {
  return (parse(html).textContent || '').replace(/\s+/g, ' ').trim()
}

/** A signature as HTML: kept when it is HTML, its lines kept when it is text. */
export function signatureHTML(signature) {
  if (!signature || !String(signature).trim()) return ''
  const text = String(signature)
  return /<[a-z][\s\S]*>/i.test(text) ? text : text.replace(/\n/g, '<br>')
}

/**
 * The signature in one line, for saying which one will be added:
 * «Mario Rossi · MM Web Agency · +39 …».
 */
export function signaturePreview(signature) {
  const html = signatureHTML(signature)
  if (!html) return ''
  const broken = html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|li|h[1-6]|tr)>/gi, '\n')
  return (parse(broken).textContent || '')
    .split('\n')
    .map((line) => line.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .join(' · ')
}

/**
 * What was written, without the email it answers: a reply is a draft from the
 * moment Reply is pressed, but there is nothing to send until something has
 * been written above the quote.
 */
export function written(html) {
  if (!html || !html.includes('reply-to-content')) return html || ''
  const body = parse(html)
  const quote = body.querySelector(QUOTE)
  if (!quote) return html
  let next = quote
  while (next) {
    const after = next.nextSibling
    next.remove()
    next = after
  }
  return body.innerHTML
}

/** Whether a draft answers an email, carrying it quoted under what is written. */
export function quotes(html) {
  return Boolean(html && html.includes('reply-to-content'))
}

/**
 * The email as it leaves: what was written, the signature under it, and the
 * email being answered under that. Nothing is added when there is no
 * signature, or when it is already there — a draft from before this change
 * carries one, and so may a template.
 */
export function signed(html, signature) {
  const sig = signatureHTML(signature)
  const text = words(sig)
  if (!text) return html || ''
  if (words(html).includes(text)) return html || ''
  const block = `<p><br></p><div class="signature">${sig}</div>`
  if (!quotes(html)) return `${html || ''}${block}`
  const body = parse(html)
  const quote = body.querySelector(QUOTE)
  if (!quote) return `${html}${block}`
  quote.insertAdjacentHTML('beforebegin', block)
  return body.innerHTML
}

/**
 * A reply's draft: what was already written — Reply used to wipe it — then the
 * marker, then the email being answered, quoted.
 */
export function replyDraft(draft, quoted) {
  const kept = written(draft)
  const something =
    (parse(kept).textContent || '').trim() ||
    /<(img|video|iframe|table|hr)\b/i.test(kept)
  return `${something ? kept : '<p></p>'}<p class="reply-to-content"></p><blockquote>${quoted || ''}</blockquote>`
}

// «Mario Rossi <mario@x.it>» → «mario@x.it», for comparing
function address(value) {
  const text = String(value || '').trim()
  const inAngles = text.match(/<([^>]+)>/)
  return (inAngles ? inAngles[1] : text).trim().toLowerCase()
}

function addresses(value) {
  return String(value || '')
    .split(',')
    .map(address)
    .filter(Boolean)
}

/**
 * Who a reply goes to, and from which of our addresses.
 *
 * To whoever wrote it — unless it is one of ours, and then again to whom it
 * went: answering one's own email used to address it to oneself. From the
 * address of ours it reached, so a conversation stays on one mailbox; the
 * reply used to take the sender's address as its From, which for a customer's
 * email meant writing as the customer. Reply-all copies everybody else it
 * went to, never us.
 *
 * @param {object} email  `sender`, `recipients`, `cc`, `bcc` as the timeline has them
 * @param {string[]} ours  our addresses: the user's, and the accounts they send from
 * @param {boolean} all  reply-all
 */
export function replyAddresses(email = {}, ours = [], all = false) {
  const mine = new Map(
    ours.filter(Boolean).map((one) => [address(one), String(one).trim()]),
  )
  const sender = address(email.sender)
  const recipients = addresses(email.recipients)
  const cc = addresses(email.cc)
  const outgoing = mine.has(sender)

  let to = outgoing ? recipients.filter((one) => !mine.has(one)) : [sender]
  if (!to.length) to = sender ? [sender] : []

  const reached = [sender, ...recipients, ...cc].find((one) => mine.has(one))
  const copies = all
    ? [...new Set([...recipients, ...cc])].filter(
        (one) => !mine.has(one) && !to.includes(one),
      )
    : []
  const bcc =
    all && outgoing ? addresses(email.bcc).filter((one) => !mine.has(one)) : []

  return {
    from: reached ? mine.get(reached) : '',
    to: to.filter(Boolean),
    cc: copies,
    bcc,
  }
}

/** «Re: …» once, however many times it is answered. */
export function replySubject(subject) {
  const text = String(subject || '').trim()
  return /^re:/i.test(text) ? text : `Re: ${text}`
}
