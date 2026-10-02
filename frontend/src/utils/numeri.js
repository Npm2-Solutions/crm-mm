// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A new Italian number from the centre's Twilio space (doc 52), without a page:
 * a month's price in the reader's money words, where a request is and what can
 * be done with it, an area's prefix as the server reads it
 * (`crm/telephony/numeri_regole.py`), the files Twilio takes, what is still
 * missing before sending, and what the page sends. The words are English,
 * translated where they are drawn.
 */

/** What Twilio takes as a document's file: as `numeri_regole.ESTENSIONI`. */
export const ESTENSIONI = ['pdf', 'jpg', 'jpeg', 'png']
export const MASSIMO = 5 * 1024 * 1024

/** A month of a number, in the reader's language: '' when Twilio gave none. */
export function prezzoAlMese(prezzo, valuta = 'USD', lingua = 'it') {
  if (prezzo === null || prezzo === undefined || prezzo === '') return ''
  try {
    return new Intl.NumberFormat(lingua || 'it', {
      style: 'currency',
      currency: valuta || 'USD',
    }).format(Number(prezzo))
  } catch {
    return `${Number(prezzo).toFixed(2)} ${valuta || ''}`.trim()
  }
}

/** An area's prefix as written - 02, +39 06, 0039 011 - as its digits; '' when it is none. */
export function prefisso(valore) {
  let cifre = String(valore || '').replace(/\D/g, '')
  if (cifre.startsWith('0039')) cifre = cifre.slice(4)
  else if (cifre.startsWith('39') && cifre.length > 2) cifre = cifre.slice(2)
  return /^0\d{1,3}$/.test(cifre) ? cifre : ''
}

/** What is wrong with a file before it is uploaded; '' when nothing. */
export function fileAccettato(nome, dimensione) {
  const estensione = String(nome || '').includes('.')
    ? String(nome).split('.').pop().toLowerCase()
    : ''
  if (!ESTENSIONI.includes(estensione)) {
    return 'The document has to be a PDF, a JPEG or a PNG.'
  }
  if ((dimensione || 0) > MASSIMO) {
    return 'The document is larger than 5 MB: Twilio does not take it.'
  }
  return ''
}

/**
 * Where a request is, as its row says it: the badge's word and colour, and the
 * line under it. `[sentence, args]` pairs, translated where drawn.
 */
export function statoDellaRichiesta(riga) {
  const stato = riga?.status
  if (stato === 'In review') {
    return {
      label: 'In review',
      theme: 'orange',
      riga: [
        'Twilio checks the documents, usually within a few working days, and writes to {0}. You will find its answer among the notifications.',
        [riga.email || ''],
      ],
    }
  }
  if (stato === 'Approved') {
    return {
      label: 'Approved',
      theme: 'green',
      riga: riga.numbers?.length
        ? ['The documents are good for another number of this kind too.', []]
        : ['The documents are approved: choose the number.', []],
    }
  }
  if (stato === 'Rejected') {
    return {
      label: 'Refused',
      theme: 'red',
      riga: [
        'Twilio refused the documents. Put them right and send them again.',
        [],
      ],
    }
  }
  return {
    label: 'Draft',
    theme: 'gray',
    riga: ['Not sent: Twilio found something missing.', []],
  }
}

/** The kind's name with its area, for a geographic one: "Geographic number 02". */
export function nomeDellaRichiesta(riga) {
  return riga?.area_code ? `${riga.kind} ${riga.area_code}` : riga?.kind || ''
}

/**
 * The fields a document asks that whose the number is does not already: the
 * document's own (its number, its issue date), written once.
 */
export function campiDelDocumento(accettato, campiDelTitolare = []) {
  const gia = new Set((campiDelTitolare || []).map((c) => c.name))
  return (accettato?.inputs || []).filter((c) => !gia.has(c.name))
}

/** The document chosen for each requirement: the first accepted, unless one was picked. */
export function documentoScelto(requisito, scelte = {}) {
  const accettati = requisito?.accepted || []
  return (
    accettati.find((d) => d.type === scelte[requisito.requirement]) ||
    accettati[0] ||
    null
  )
}

/** Whether the documents chosen need the office's address. */
export function chiedeIndirizzo(documenti = [], scelte = {}) {
  return documenti.some((requisito) =>
    (documentoScelto(requisito, scelte)?.fields || []).includes('address_sids'),
  )
}

/**
 * What stops sending, before Twilio is asked: a document without its file, the
 * address when it is needed, the email. '' when nothing does.
 */
export function cosaMancaPerMandare({
  documenti = [],
  scelte = {},
  file = {},
  indirizzo = {},
  email = '',
}) {
  for (const requisito of documenti) {
    const documento = documentoScelto(requisito, scelte)
    if (documento && !documento.address && !file[requisito.requirement]) {
      return 'Upload the file of every document.'
    }
  }
  if (
    chiedeIndirizzo(documenti, scelte) &&
    !['street', 'city', 'postal_code'].every((k) =>
      String(indirizzo[k] || '').trim(),
    )
  ) {
    return "Write the office's address: street, city and postal code."
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || '').trim())) {
    return 'Write the email Twilio writes to about the documents.'
  }
  return ''
}

/** The documents as the server takes them: the one chosen, its values, its file. */
export function documentiDaMandare({
  documenti = [],
  scelte = {},
  file = {},
  valori = {},
}) {
  return documenti
    .map((requisito) => {
      const documento = documentoScelto(requisito, scelte)
      if (!documento) return null
      const propri = {}
      for (const campo of documento.inputs || []) {
        const valore = valori[`${requisito.requirement}:${campo.name}`]
        if (valore !== undefined && String(valore).trim()) {
          propri[campo.name] = String(valore).trim()
        }
      }
      return {
        requirement: requisito.requirement,
        type: documento.type,
        fields: documento.fields,
        address: documento.address,
        values: propri,
        file: documento.address
          ? null
          : file[requisito.requirement]?.name || null,
      }
    })
    .filter(Boolean)
}
