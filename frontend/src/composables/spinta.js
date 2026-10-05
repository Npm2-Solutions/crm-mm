// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Notifications on this phone or computer, the browser's side
// (crm/notifiche/spinta.py): the service worker over /crm, the permission, the
// subscription the server keeps. Imported by the notifications' settings and,
// once the app is idle, where the person had turned them on already.

import {
  AMBITO,
  SERVICE_WORKER,
  chiaveDelServer,
  cosaSaFare,
  esadecimale,
  statoDelDispositivo,
} from '@/utils/spinta'
import { questoDispositivo } from '@/utils/installa'
import { sessionStore } from '@/stores/session'
import { call } from 'frappe-ui'
import { computed, ref } from 'vue'

const capacita = ref(cosaSaFare(window, questoDispositivo()))
// the subscription of this browser, if it has one: its address's fingerprint
const impronta = ref('')

export const statoQui = computed(() => statoDelDispositivo(capacita.value))

function aggiorna() {
  capacita.value = cosaSaFare(window, questoDispositivo())
}

async function registrazione() {
  await navigator.serviceWorker.register(SERVICE_WORKER, { scope: AMBITO })
  // the subscription wants the worker active: `ready` waits for it
  return navigator.serviceWorker.ready
}

async function improntaDi(abbonamento) {
  if (!abbonamento) return ''
  const dati = new TextEncoder().encode(abbonamento.endpoint)
  return esadecimale(await crypto.subtle.digest('SHA-256', dati))
}

/** This browser's subscription, without asking anything of the person. */
export async function abbonamentoQui() {
  aggiorna()
  if (statoQui.value !== 'pronto') return null
  const registrata = await navigator.serviceWorker.getRegistration(AMBITO)
  const abbonamento = await registrata?.pushManager.getSubscription()
  impronta.value = await improntaDi(abbonamento)
  return abbonamento || null
}

export const improntaQui = computed(() => impronta.value)

/**
 * Turns them on here: the browser asks the person (a tap must have started
 * this), subscribes with the server's key, and the server keeps where to reach
 * it. Answers what the server says of the session's devices.
 */
export async function attiva(chiavePubblica) {
  const permesso = await Notification.requestPermission()
  aggiorna()
  if (permesso !== 'granted') return null
  const registrata = await registrazione()
  let abbonamento = await registrata.pushManager.getSubscription()
  const chiave = chiaveDelServer(chiavePubblica)
  // a subscription made with another key (the site's changed) is made again
  if (abbonamento && !stessaChiave(abbonamento, chiave)) {
    await abbonamento.unsubscribe()
    abbonamento = null
  }
  abbonamento ||= await registrata.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: chiave,
  })
  impronta.value = await improntaDi(abbonamento)
  return call('crm.notifiche.spinta.subscribe', {
    subscription: JSON.stringify(abbonamento),
    installed: questoDispositivo().installata ? 1 : 0,
  })
}

function stessaChiave(abbonamento, chiave) {
  const sua = abbonamento.options?.applicationServerKey
  if (!sua) return true
  const byte = new Uint8Array(sua)
  return byte.length === chiave.length && byte.every((b, i) => b === chiave[i])
}

/** Turns them off here: the browser lets go, the server forgets it. */
export async function disattiva() {
  const abbonamento = await abbonamentoQui()
  const segno = impronta.value
  await abbonamento?.unsubscribe()
  impronta.value = ''
  return call('crm.notifiche.spinta.unsubscribe', { endpoint_hash: segno })
}

/**
 * At every opening where they were turned on: the server knows this browser
 * as this person's (another may have signed in on it, the site's key may be
 * new). Asks nothing of the person.
 */
export async function sincronizza() {
  aggiorna()
  if (statoQui.value !== 'pronto' || Notification.permission !== 'granted')
    return
  const abbonamento = await abbonamentoQui()
  if (!abbonamento) return
  const chiave = `crm-spinta:${sessionStore().user || ''}`
  let ricordata = null
  try {
    ricordata = localStorage.getItem(chiave)
  } catch {
    // a private window: asked every time, which is harmless
  }
  if (ricordata === impronta.value) return
  const stato = await call('crm.notifiche.spinta.get_push')
  if (!stato.devices.some((d) => d.endpoint_hash === impronta.value)) {
    await attiva(stato.public_key)
  }
  try {
    localStorage.setItem(chiave, impronta.value)
  } catch {
    // nothing kept: asked again at the next opening
  }
}
