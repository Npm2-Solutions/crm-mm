// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The invoice dialog, opened from anywhere (the console, the agenda, a cycle, a
 * subscription, a person's history) and mounted once in GlobalModals.
 */
import { reactive } from 'vue'

const stato = reactive({
  aperto: false,
  // the invoice to open, or nothing for a new one
  nome: null,
  // a new invoice's client: { party_type, party }
  cliente: null,
  // told when the invoice is saved, issued or thrown away
  alCambio: null,
  // one more each time somebody opens one: the dialog loads it then, and only then
  // (saving a new invoice gives it a name without opening it again)
  richiesta: 0,
})

export function useFattura() {
  return {
    stato,
    apriFattura(nome, { alCambio } = {}) {
      Object.assign(stato, { nome, cliente: null, alCambio: alCambio || null })
      stato.aperto = true
      stato.richiesta++
    },
    nuovaFattura(cliente = null, { alCambio } = {}) {
      Object.assign(stato, { nome: null, cliente, alCambio: alCambio || null })
      stato.aperto = true
      stato.richiesta++
    },
    chiudiFattura() {
      stato.aperto = false
    },
  }
}
