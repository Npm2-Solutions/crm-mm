// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Notifications as they arrive, wherever one is in DottorCloud: the count and
// the panel follow at once, and a new one shows itself in a toast - the
// brand's deep block - with what it says and a way to open it, unless the
// panel or the notifications' page is already in front of the reader.
//
// Listened to once per layout (GlobalModals): the panel and the phone's page
// used to listen themselves, so on a phone the count stood still until the
// page was opened, and a calendar reminder never came at all.

import { apriImpostazioni } from '@/composables/settings'
import { useEventNotificationAlert } from '@/data/notifications'
import { globalStore } from '@/stores/global'
import { useDiNuovoInLinea } from '@/composables/diNuovoInLinea'
import {
  notifications,
  notificationsStore,
  visible,
} from '@/stores/notifications'
import NotificationMark from '@/components/Notifications/NotificationMark.vue'
import { soloTesto } from '@/utils/notifiche'
import { toast } from 'frappe-ui'
import { h, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'

/** Opening a notification: read, the panel closed, where it leads. */
export function useApriNotifica() {
  const router = useRouter()
  const { segnaLetta, close } = notificationsStore()

  return function apri(riga) {
    segnaLetta(riga)
    close()
    if (riga.route) router.push(riga.route)
    else if (riga.settings) apriImpostazioni(riga.settings)
  }
}

// The toast's words as a link to what it is about, lying over the whole toast
// (its `::after`), as a row of the panel opens from anywhere on it: a tap on
// the toast opens it. A finger that swiped the toast away opens nothing; a
// click that asks for a new tab is the browser's.
function paroleCheAprono(testo, indirizzo, apri) {
  let inizio = null
  return () =>
    h(
      'a',
      {
        href: indirizzo,
        class: "after:absolute after:inset-0 after:content-['']",
        style: { color: 'inherit', textDecoration: 'none' },
        onPointerdown: (evento) => {
          inizio = [evento.clientX, evento.clientY]
        },
        onClick: (evento) => {
          if (evento.metaKey || evento.ctrlKey || evento.shiftKey) return
          evento.preventDefault()
          const [x, y] = inizio || [evento.clientX, evento.clientY]
          inizio = null
          if (Math.hypot(evento.clientX - x, evento.clientY - y) > 10) return
          apri()
        },
      },
      testo,
    )
}

export function useAscoltoNotifiche() {
  const { $socket } = globalStore()
  const router = useRouter()
  const apri = useApriNotifica()
  const { handleEventNotification } = useEventNotificationAlert()

  async function arrivata(data) {
    await notifications.reload()
    if (data?.event !== 'new') return
    // the list is in front of them: it has just grown
    if (visible.value || router.currentRoute.value.name === 'Notifications')
      return
    const riga = notifications.data?.rows?.find((r) => r.name === data.name)
    if (!riga) return
    const testo = soloTesto(riga.text)
    const apribile = Boolean(riga.route || riga.settings)
    const avviso = toast(
      apribile
        ? paroleCheAprono(testo, indirizzoDi(riga), () => {
            toast.dismiss(avviso)
            apri(riga)
          })
        : testo,
      {
        description: riga.excerpt || undefined,
        duration: 6000,
        // the kind's mark, as in the panel, in mint on the brand's deep block
        icon: {
          render: () =>
            h(NotificationMark, { kind: riga.kind, taglia: 'toast' }),
        },
        action: apribile
          ? {
              label: __('Open', null, 'Toast action'),
              onClick: () => apri(riga),
            }
          : undefined,
        // its buttons above the words that open it
        classes: {
          actionButton: 'relative z-10',
          closeButton: 'relative z-10',
        },
      },
    )
  }

  // Where a notification opens, as an address: for a new tab, or a long press
  function indirizzoDi(riga) {
    if (riga.route) return router.resolve(riga.route).href
    const { page, step } = riga.settings
    return router.resolve({
      path: router.currentRoute.value.path,
      query: { settings: page, ...(step ? { step } : {}) },
    }).href
  }

  // the count and the panel put right when the app is back in touch: what
  // arrived while the phone kept it asleep never came as an event
  useDiNuovoInLinea(() => notifications.reload())

  onMounted(() => {
    $socket.on('crm_notification', arrivata)
    $socket.on('event_notification', handleEventNotification)
  })

  onBeforeUnmount(() => {
    $socket.off('crm_notification', arrivata)
    $socket.off('event_notification', handleEventNotification)
  })
}
