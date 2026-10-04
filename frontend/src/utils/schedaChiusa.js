// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// What a record's page says when it does not open: a person one does not follow,
// a deal of somebody else's, one that is gone. The server's own sentence ("Not
// allowed via controller permission check") is the framework's, and the record's
// code in the title says nothing to whoever reads it.

const PAROLE = {
  'CRM Lead': {
    PermissionError: [
      'You do not follow this person',
      'Their page opens for whoever follows them. If you need it, ask the front desk or the manager.',
    ],
    DoesNotExistError: [
      'This person is no longer here',
      'They may have been deleted, or merged into another person.',
    ],
  },
  'CRM Deal': {
    PermissionError: [
      'This deal is not one of yours',
      'A deal opens for whoever follows it. If you need it, ask the front desk or the manager.',
    ],
    DoesNotExistError: [
      'This deal is no longer here',
      'It may have been deleted.',
    ],
  },
  Contact: {
    PermissionError: [
      'You do not follow this person',
      'Their page opens for whoever follows them. If you need it, ask the front desk or the manager.',
    ],
    DoesNotExistError: [
      'This contact is no longer here',
      'It may have been deleted, or merged into another.',
    ],
  },
  'CRM Organization': {
    PermissionError: [
      'You cannot open this company',
      'If you need it, ask the front desk or the manager.',
    ],
    DoesNotExistError: [
      'This company is no longer here',
      'It may have been deleted.',
    ],
  },
  // the sheet of a note or a task opened from its list (DoctypeModal.vue)
  'FCRM Note': {
    PermissionError: [
      'You cannot open this note',
      'A note opens for whoever follows the person or the deal it is about.',
    ],
    DoesNotExistError: [
      'This note is no longer here',
      'It may have been deleted.',
    ],
  },
  'CRM Task': {
    PermissionError: [
      'You cannot open this task',
      'A task opens for whoever follows the person or the deal it is about.',
    ],
    DoesNotExistError: [
      'This task is no longer here',
      'It may have been deleted.',
    ],
  },
}

// The word that names a record while it is not there to name itself.
const NOMI = {
  'CRM Lead': 'Person',
  'CRM Deal': 'Deal',
  Contact: 'Contact',
  'CRM Organization': 'Organization',
}

/**
 * Why the page of a ``doctype`` did not open, in words: ``{ titolo, testo }``,
 * or ``null`` when there is no error.
 */
export function schedaChiusa(errore, doctype) {
  if (!errore) return null
  const parole = PAROLE[doctype]?.[errore.exc_type]
  if (parole) return { titolo: __(parole[0]), testo: __(parole[1]) }
  return {
    titolo: __('Error Occurred'),
    testo: __(errore.messages?.[0] || 'An error occurred'),
  }
}

/** The page's title while the record is not loaded: a word, never its code. */
export function nomeInAttesa(doctype) {
  return __(NOMI[doctype] || 'Document')
}

export const PAROLE_DELLE_SCHEDE = PAROLE
