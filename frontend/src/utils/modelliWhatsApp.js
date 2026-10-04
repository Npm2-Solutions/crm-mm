// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// A WhatsApp template's codes in words: the category Meta files it under, with
// the line on when it is the right one, and where Meta's review stands. What is
// stored stays Meta's code (MARKETING, APPROVED); Meta writes it in capitals, a
// template saved before may hold it as a word (Approved).

const codice = (valore) => String(valore || '').toUpperCase()

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
    default:
      return { label: valore || '', theme: 'gray' }
  }
}
