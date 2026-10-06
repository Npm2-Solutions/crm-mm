// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// A WhatsApp template's codes in words: the category Meta files it under, with
// the line on when it is the right one, and where Meta's review stands. What is
// stored stays Meta's code (MARKETING, APPROVED); Meta writes it in capitals, a
// template saved before may hold it as a word (Approved).

const codice = (valore) => String(valore || '').toUpperCase()

// without a translator, the words as they are with their places filled
function formato(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}

export function categoria(valore, t = (s) => s) {
  switch (codice(valore)) {
    case 'UTILITY':
      return {
        label: t('Utility', null, 'WhatsApp template'),
        description: t(
          'About something the person asked for or booked: a confirmation, a reminder, a change of time.',
        ),
      }
    case 'MARKETING':
      return {
        label: t('Marketing', null, 'WhatsApp template'),
        description: t(
          'Offers, news, an invitation to come back: what the person did not ask for.',
        ),
      }
    case 'AUTHENTICATION':
      return {
        label: t('Authentication', null, 'WhatsApp template'),
        description: t('A code to sign in, and nothing else.'),
      }
    default:
      return { label: valore || '', description: '' }
  }
}

// the choices of the dialog, in the order the server gives them
export function categorie(valori = [], t = (s) => s) {
  return valori.map((valore) => ({
    value: valore,
    label: categoria(valore, t).label,
  }))
}

export function stato(valore, t = (s) => s) {
  switch (codice(valore)) {
    case 'APPROVED':
      return { label: t('Approved', null, 'WhatsApp template'), theme: 'green' }
    case 'PENDING':
      return {
        label: t('In review', null, 'WhatsApp template'),
        theme: 'orange',
      }
    case 'IN_APPEAL':
      return {
        label: t('Appeal in progress', null, 'WhatsApp template'),
        theme: 'orange',
      }
    case 'PAUSED':
      return { label: t('Paused', null, 'WhatsApp template'), theme: 'orange' }
    case 'REJECTED':
      return { label: t('Rejected', null, 'WhatsApp template'), theme: 'red' }
    case 'DISABLED':
      return { label: t('Disabled', null, 'WhatsApp template'), theme: 'red' }
    // deleted in WhatsApp Manager: kept here for the messages that name it
    case 'PENDING_DELETION':
    case 'DELETED':
      return {
        label: t('Deleted on Meta', null, 'WhatsApp template'),
        theme: 'gray',
      }
    default:
      return { label: valore || '', theme: 'gray' }
  }
}

// What a button does, in the order a template has them: Meta wants the quick
// replies first, then the links and the call.
export const TIPI_DI_PULSANTE = ['QUICK_REPLY', 'URL', 'PHONE_NUMBER']

export function tipiDiPulsante(t = (s) => s) {
  return [
    { value: 'QUICK_REPLY', label: t('Quick reply', null, 'WhatsApp button') },
    { value: 'URL', label: t('Opens a link', null, 'WhatsApp button') },
    { value: 'PHONE_NUMBER', label: t('Calls', null, 'WhatsApp button') },
  ]
}

// A template's buttons in a row's line: their words, in quotes, one after the
// other («Confermo» · «Devo disdire»)
export function parolePulsanti(pulsanti = []) {
  return pulsanti
    .filter((pulsante) => pulsante.text)
    .map((pulsante) => `«${pulsante.text}»`)
    .join(' · ')
}

// The number a page opens on: the one that sends, else the first in use, else
// the first
export function numeroIniziale(numeri = []) {
  return (
    numeri.find((numero) => numero.sends)?.name ||
    numeri.find((numero) => numero.active)?.name ||
    numeri[0]?.name ||
    null
  )
}

// The templates a number can send: its account's (`numbers`, from the server)
export function modelliDelNumero(modelli = [], numero = null) {
  if (!numero) return modelli
  return modelli.filter((modello) => (modello.numbers || []).includes(numero))
}

// What a number is, in one line under its name: whether its templates can be
// sent now. DottorCloud sends from one number (Settings > WhatsApp > Numbers),
// and every number of the same WhatsApp Business account sends the same ones.
export function lineaDelNumero(numero, numeri = [], t = formato) {
  if (!numero) return ''
  if (!numero.active)
    return t('Not in use: its templates can no longer be sent.')
  const chiInvia = numeri.find((altro) => altro.sends)
  const condivisi = numero.shares || []
  if (numero.sends || !chiInvia) {
    const frase = t('Messages go out from this number.')
    return condivisi.length
      ? `${frase} ${t('It shares its templates with {0}.', [condivisi.join(', ')])}`
      : frase
  }
  if (condivisi.includes(chiInvia.label))
    return t('Messages go out from {0}, which can send these templates too.', [
      chiInvia.label,
    ])
  return t(
    'Messages go out from {0}: these templates can be sent once this number is the one that sends.',
    [chiInvia.label],
  )
}
