// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Notifications on this phone or computer, the browser's side
// (crm/notifiche/spinta.py): the service worker over /crm, the permission, the
// subscription the server keeps. Imported by the notifications' settings, once
// the app is idle where the person had turned them on already, and at a
// logout, to let the device go (stores/session.js, utils/esci.js).

import {
  AMBITO,
  MEMORIA,
  SERVICE_WORKER,
  chiaveDelServer,
  cosaSaFare,
  daChiedere,
  entroIlTempo,
  esadecimale,
  memoriaDi,
  memorieVecchie,
  statoDelDispositivo,
  tieneLAbbonamento,
} from '@/utils/spinta'
import { questoDispositivo } from '@/utils/installa'
import { sessionStore } from '@/stores/session'
import { call } from 'frappe-ui'
import { computed, ref } from 'vue'

const capacita = ref(cosaSaFare(window, questoDispositivo()))
// the subscription of this browser, if it has one: its address's fingerprint
const impronta = ref('')

/** How long a logout waits for the server, and for the browser, to let go. */
const ATTESA = 2000

// an opening's sync while it is on its way: a logout waits for it, or what it
// hands over would land after the logout let the device go
let inCorso = null

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

// The memo: whose the server knows this browser to be (utils/spinta.js)
function laMemoria() {
  try {
    return localStorage.getItem(MEMORIA)
  } catch {
    // a private window: asked every time, which is harmless
    return null
  }
}

function ricorda(segno) {
  try {
    localStorage.setItem(MEMORIA, memoriaDi(sessionStore().user, segno))
  } catch {
    // nothing kept: asked again at the next opening
  }
}

/** The memos older versions kept, one per person, go: one is the browser's. */
function togliLeVecchie() {
  try {
    const chiavi = Array.from({ length: localStorage.length }, (_, i) =>
      localStorage.key(i),
    )
    for (const chiave of memorieVecchie(chiavi)) localStorage.removeItem(chiave)
  } catch {
    // nothing kept, nothing to take away
  }
}

/** The memo goes, the old ones with it: the next opening asks the server. */
function dimentica() {
  togliLeVecchie()
  try {
    localStorage.removeItem(MEMORIA)
  } catch {
    // nothing kept, nothing to take away
  }
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
 * it - handing it to the session where somebody else had it. Answers what the
 * server says of the session's devices.
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
  const stato = await call('crm.notifiche.spinta.subscribe', {
    subscription: JSON.stringify(abbonamento),
    installed: questoDispositivo().installata ? 1 : 0,
  })
  // the server knows this browser as the session's now
  ricorda(impronta.value)
  return stato
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
  dimentica()
  return call('crm.notifiche.spinta.unsubscribe', { endpoint_hash: segno })
}

/**
 * At every opening where they were turned on: the server knows this browser
 * as this person's (another may have signed in on it, the site's key may be
 * new). One memo for the browser, never one per person: whoever signs in
 * after somebody else is asked about, and handed the device. Asks nothing of
 * the person.
 */
export function sincronizza() {
  inCorso ||= sincronizzaOra().finally(() => {
    inCorso = null
  })
  return inCorso
}

async function sincronizzaOra() {
  aggiorna()
  if (statoQui.value !== 'pronto' || Notification.permission !== 'granted')
    return
  togliLeVecchie()
  const abbonamento = await abbonamentoQui()
  if (!abbonamento) return
  if (!daChiedere(laMemoria(), sessionStore().user, impronta.value)) return
  const stato = await call('crm.notifiche.spinta.get_push')
  if (stato.devices.some((d) => d.endpoint_hash === impronta.value))
    ricorda(impronta.value)
  else await attiva(stato.public_key)
}

/**
 * At a logout, while the session is still there: this device stops receiving
 * the session's notifications. The server forgets it for the session, and the
 * browser keeps its subscription, so whoever signs in here next is handed it
 * at their first opening. Where the server does not answer within two
 * seconds, or the memo says somebody else was the last to sync it (what the
 * server forgot for this session was then not it), the browser lets go of it
 * instead: nothing reaches the device, its push service answers that it is
 * gone, and the server forgets it at its next notification. That waits for
 * the server to end the session: answered here as what is left to do then
 * (utils/esci.js), so that a logout it refuses leaves the device to the
 * session that goes on. The memo goes either way. Never throws, and never
 * waits long: the logout goes on.
 */
export async function lascia() {
  // the opening's sync still on its way lands first: what it hands over is
  // let go with the rest
  if (inCorso) await entroIlTempo(inCorso, ATTESA)
  const memoria = laMemoria()
  dimentica()
  const abbonamento = await abbonamentoQui().catch(() => null)
  if (!abbonamento) return null
  const segno = impronta.value
  const dimenticato = await entroIlTempo(
    call('crm.notifiche.spinta.unsubscribe', { endpoint_hash: segno }),
    ATTESA,
  )
  if (
    tieneLAbbonamento({
      memoria,
      utente: sessionStore().user,
      impronta: segno,
      dimenticato,
    })
  )
    return null
  return async () => {
    await entroIlTempo(
      Promise.resolve().then(() => abbonamento.unsubscribe()),
      ATTESA,
    )
    impronta.value = ''
  }
}

/**
 * A logout the server refused: the session goes on, and the device with it.
 * What `lascia` had the server forget is handed back now, not at the next
 * opening: the memo goes, so the server is asked.
 */
export function resta() {
  dimentica()
  return sincronizza()
}
