// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// What a page shows, asked again when the app is back in touch
// (utils/inLinea.js): back in sight after a while away, or the realtime
// connection back after a break - the events of the time between never came.

import { globalStore } from '@/stores/global'
import { daRiprendere, giaRipreso } from '@/utils/inLinea'
import { onBeforeUnmount, onMounted } from 'vue'

export function useDiNuovoInLinea(aggiorna) {
  const { $socket } = globalStore()
  let nascosta = null
  let caduta = false
  let ultima = null

  function riprendi() {
    const adesso = Date.now()
    if (giaRipreso(ultima, adesso)) return
    ultima = adesso
    aggiorna()
  }

  function alCambio() {
    if (document.visibilityState === 'hidden') {
      nascosta = Date.now()
      return
    }
    if (daRiprendere(nascosta, Date.now())) riprendi()
    nascosta = null
  }

  const allaCaduta = () => (caduta = true)
  function alRitorno() {
    if (!caduta) return
    caduta = false
    riprendi()
  }

  onMounted(() => {
    if (document.visibilityState === 'hidden') nascosta = Date.now()
    document.addEventListener('visibilitychange', alCambio)
    $socket?.on('disconnect', allaCaduta)
    $socket?.on('connect', alRitorno)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', alCambio)
    $socket?.off('disconnect', allaCaduta)
    $socket?.off('connect', alRitorno)
  })
}
