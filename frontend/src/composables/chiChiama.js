// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Who calls, for the call's window: Twilio's and Telnyx's share it (docs/crm/52
// and 65). The number the call is about and whom the server finds for it,
// asked again at every call and every change of the number
// (`utils/chiamate.js`). The lookup was a resource kept for the page under the
// number the window started with (`cache: ['contact', '']`), so both windows
// had one, Twilio's: the last call's caller stayed on the next call while the
// server answered, and for the whole call where it did not; Telnyx's window
// asked about Twilio's number and never named anybody.

import { cercaChiChiama, nomeDiChiChiama } from '@/utils/chiamate'
import { call } from 'frappe-ui'
import { computed, ref } from 'vue'

export function useChiChiama() {
  const numero = ref('')
  const contatto = ref(null)
  const cercando = ref(false)

  const cerca = cercaChiChiama(
    (n) =>
      call('crm.integrations.api.get_contact_by_phone_number', {
        phone_number: n,
      }),
    (trovato, ancora) => {
      contatto.value = trovato
      cercando.value = ancora
    },
  )

  /** The number the call is about: a call starting, or its number changing. */
  function perIlNumero(nuovo) {
    numero.value = nuovo || ''
    cerca(numero.value)
  }

  // the name the window shows: nothing yet while the server is asked
  const nome = computed(() =>
    nomeDiChiChiama(contatto.value, cercando.value, __),
  )

  return { numero, contatto, nome, perIlNumero }
}
