// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The centre's mailboxes on Settings > Email > Accounts (doc 51), without a page.
 *
 * The providers the page offers, what each asks of the password, a mailbox's marks
 * in words, the switches it shows, what stops saving it, where the answers to
 * {brand}'s own emails go. The servers are the server's (`crm.api.settings.FORNITORI`):
 * here only the keys and the names. The words are English, translated where they
 * are drawn.
 */

const IMAP =
  "The mailbox's own password. If it is refused, check in the mailbox's settings that access from other programs (IMAP) is on."

/** The providers, in the order the page shows them: the keys are the server's. */
export const FORNITORI = [
  {
    chiave: 'gmail',
    nome: 'Gmail',
    nota: 'Gmail wants two-step verification and an app password, made in your Google account under Security.',
    link: 'https://support.google.com/accounts/answer/185833',
  },
  {
    chiave: 'aruba',
    nome: 'Aruba',
    nota: "The mailbox's own password, the one of Aruba's webmail. A certified (PEC) mailbox is not this one.",
  },
  { chiave: 'libero', nome: 'Libero', nota: IMAP },
  { chiave: 'virgilio', nome: 'Virgilio', nota: IMAP },
  { chiave: 'tiscali', nome: 'Tiscali', nota: IMAP },
  {
    chiave: 'icloud',
    nome: 'iCloud',
    nota: 'iCloud wants an app-specific password, made in your Apple account under Sign-In and Security.',
    link: 'https://support.apple.com/en-us/102654',
  },
  {
    chiave: 'yahoo',
    nome: 'Yahoo',
    nota: 'Yahoo wants an app password, made in your account under Security.',
    link: 'https://help.yahoo.com/kb/SLN15241.html',
  },
]

export function fornitore(chiave) {
  return FORNITORI.find((f) => f.chiave === chiave) || null
}

/** The letter on a provider's tile, where there is no picture. */
export function iniziale(nome) {
  return (nome || '').trim().charAt(0).toUpperCase() || '@'
}

/**
 * A mailbox's marks, in the order they read: what it does, then whose it is.
 * `servizio`: whether {brand}'s emails leave through the agency's service, so no
 * mailbox of the centre sends them.
 */
export function segni(casella, servizio = false) {
  if (!casella) return []
  const fatti = []
  if (casella.default_incoming && casella.enable_incoming)
    fatti.push('Main mailbox')
  if (casella.enable_incoming) fatti.push('Receives')
  if (casella.enable_outgoing) fatti.push('Sends')
  if (!servizio && casella.default_outgoing && casella.enable_outgoing) {
    fatti.push("Sends {brand}'s emails")
  }
  if (!casella.enable_incoming && !casella.enable_outgoing)
    fatti.push('Not in use')
  if (casella.editable === false) fatti.push('Set up by the agency')
  return fatti
}

/**
 * The switches a mailbox shows, with their words: what it receives and what is
 * made of who writes only where it receives; sending {brand}'s own emails from it
 * only where the agency's service does not.
 */
export function interruttori(stato, servizio = false) {
  const tutti = [
    {
      campo: 'enable_incoming',
      etichetta: 'Receives',
      descrizione:
        'The emails that arrive here are read in {brand}, on the page of whoever wrote them.',
    },
    {
      campo: 'create_lead_from_incoming_email',
      etichetta: 'A new person for whoever writes the first time',
      descrizione:
        'Somebody the centre does not know yet becomes a person. Never an automatic sender, nor somebody of the centre.',
      se: (s) => s.enable_incoming,
    },
    {
      campo: 'default_incoming',
      etichetta: 'Main mailbox',
      descrizione:
        "The answers to {brand}'s emails arrive here, when no other address is chosen.",
      se: (s) => s.enable_incoming,
    },
    {
      campo: 'enable_outgoing',
      etichetta: 'Sends',
      descrizione:
        'You write from this mailbox in {brand}, and the answers come back here.',
    },
    {
      campo: 'default_outgoing',
      etichetta: "Sends {brand}'s emails",
      descrizione:
        'Reminders, codes and confirmations leave from this mailbox.',
      se: (s) => !servizio && s.enable_outgoing,
    },
  ]
  return tutti.filter((i) => !i.se || i.se(stato || {}))
}

const INDIRIZZO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * What stops saving a mailbox, in words; '' when nothing does. `modifica`: the
 * mailbox keeps its password, typing one replaces it.
 */
export function daCorreggere(stato, modifica = false) {
  if (!stato?.provider) return 'Choose where the mailbox is.'
  if (!(stato.email_id || '').trim()) return 'Write the address.'
  if (!INDIRIZZO.test(stato.email_id.trim())) {
    return 'The address is not an email address.'
  }
  if (!modifica && !stato.password) return 'Write the password.'
  if (!stato.enable_incoming && !stato.enable_outgoing) {
    return 'A mailbox receives, sends, or both.'
  }
  return ''
}

/** The picker's choice for an address typed by hand. */
export const ALTRO = '__altro__'

/**
 * Where the answers to {brand}'s own emails go, for the picker: '' for the main
 * mailbox, an address the centre reads in {brand}, or ALTRO for one typed.
 */
export function sceltaDelleRisposte(stato) {
  const scelto = stato?.reply_to_chosen || ''
  if (!scelto) return { scelta: '', altro: '' }
  if ((stato.inboxes || []).includes(scelto))
    return { scelta: scelto, altro: '' }
  return { scelta: ALTRO, altro: scelto }
}

/** The address to save from the picker: '' gives the choice back to the main mailbox. */
export function rispostaDaSalvare(scelta, altro) {
  if (scelta === ALTRO) return (altro || '').trim()
  return scelta || ''
}

/** Whether the answers to {brand}'s emails reach nobody: no address, no mailbox that receives. */
export function risposteSenzaCasella(stato) {
  return Boolean(stato?.active) && !stato?.reply_to
}
