// The notifications: the page the panel shows, how many are unread, and
// reading them (crm/notifiche/api.py). One list for the panel, the phone's
// page and the sidebar's count; the server says what each one says and where
// it opens.

import { defineStore } from 'pinia'
import { call, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import { conteggio } from '@/utils/notifiche'

const PASSO = 30

/** The panel, open or not. */
export const visible = ref(false)
/** All of them, or only the unread ones. */
export const filtro = ref('all')
const quante = ref(PASSO)

export const notifications = createResource({
  url: 'crm.notifiche.api.get_notifications',
  makeParams: () => ({
    limit: quante.value,
    unread: filtro.value === 'unread' ? 1 : 0,
  }),
  initialData: { rows: [], unread: 0, more: false },
  auto: true,
})

/** The sidebar's count: «» when there is nothing to read, «99+» past ninety-nine. */
export const unreadNotificationsCount = computed(() =>
  conteggio(notifications.data?.unread),
)

export const notificationsStore = defineStore('crm-notifications', () => {
  function toggle() {
    visible.value = !visible.value
  }

  function close() {
    visible.value = false
  }

  function scegli(valore) {
    if (filtro.value === valore) return
    filtro.value = valore
    quante.value = PASSO
    notifications.reload()
  }

  function mostraAltre() {
    quante.value += PASSO
    notifications.reload()
  }

  // what the screen shows changes at once; the server's answer puts the count right
  function segna(righe, letta) {
    for (const riga of righe) riga.read = letta
    if (notifications.data) {
      const prima = notifications.data.unread || 0
      notifications.data.unread = Math.max(
        0,
        prima + (letta ? -righe.length : righe.length),
      )
    }
  }

  async function segnaLetta(riga) {
    if (riga.read) return
    segna([riga], true)
    const risposta = await call('crm.notifiche.api.mark_as_read', {
      names: [riga.name],
    })
    if (notifications.data) notifications.data.unread = risposta.unread
  }

  async function segnaDaLeggere(riga) {
    if (!riga.read) return
    segna([riga], false)
    const risposta = await call('crm.notifiche.api.mark_as_unread', {
      names: [riga.name],
    })
    if (notifications.data) notifications.data.unread = risposta.unread
  }

  async function segnaTutte() {
    const righe = (notifications.data?.rows || []).filter((r) => !r.read)
    segna(righe, true)
    if (notifications.data) notifications.data.unread = 0
    await call('crm.notifiche.api.mark_as_read')
    notifications.reload()
  }

  return {
    filtro,
    visible,
    toggle,
    close,
    scegli,
    mostraAltre,
    segnaLetta,
    segnaDaLeggere,
    segnaTutte,
  }
})
