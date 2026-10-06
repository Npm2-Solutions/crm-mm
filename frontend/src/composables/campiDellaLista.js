// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { createResource, getCachedResource } from 'frappe-ui'

// the framework's own columns, a list's and never a document's field: a quick
// filter is a field of the document
const STANDARD = [
  '_assign',
  'owner',
  'creation',
  'modified_by',
  'modified',
  '_liked_by',
]

/**
 * What a list offers as a column, on a board's card, as a quick filter (`uso`
 * «colonna»), or what a record's layout editors offer («scheda»):
 * `crm.api.doc.get_list_fields`, the rule in crm/liste/regole.py. Each field
 * once, in the reader's words, told apart from another of the same name.
 * Asked the first time a picker opens, never while the list loads, and once
 * per document type and use.
 */
export function useCampiDellaLista(doctype, uso = 'colonna') {
  const chiave = ['listFields', doctype, uso]
  const campi =
    getCachedResource(chiave) ||
    createResource({
      url: 'crm.api.doc.get_list_fields',
      cache: chiave,
      params: { doctype, uso },
    })

  function carica() {
    if (!campi.data && !campi.loading) campi.fetch()
  }

  return { campi, carica }
}

/** A quick filter is one of the document's own fields. */
export function delDocumento(campo) {
  return !STANDARD.includes(campo?.fieldname)
}

/**
 * A field's name as the list or the layout offers it, else its own words:
 * a layout keeps the fields with the label their document gives them.
 */
export function nomeDelCampo(campi, campo, t = (testo) => testo) {
  const offerto = (campi || []).find((c) => c.fieldname === campo?.fieldname)
  return offerto?.label || t(campo?.label || '')
}
