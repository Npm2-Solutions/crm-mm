// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The centre's locations for every screen (docs/crm/62): the boot's list, empty
 * where the centre has one or none, and where the session usually works. The
 * settings page hands the list back when it changes, so the agenda and the desk
 * follow without a reload.
 */

import { piuSedi as ePiuSedi } from '@/utils/sedi'
import { computed, ref } from 'vue'

const sedi = ref(Array.isArray(window.sedi) ? window.sedi : [])
const sedeAbituale = ref(window.sede_abituale || '')

export function useSedi() {
  return {
    sedi,
    piuSedi: computed(() => ePiuSedi(sedi.value)),
    sedeAbituale,
  }
}

/** The locations as the server gives them now (after the settings changed them). */
export function aggiornaSedi(elenco) {
  sedi.value = Array.isArray(elenco) ? elenco : []
  if (!sedi.value.some((sede) => sede.name === sedeAbituale.value))
    sedeAbituale.value = ''
}

export function impostaSedeAbituale(nome) {
  sedeAbituale.value = nome || ''
}
