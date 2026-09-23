import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const whatsappEnabled = ref(false)
export const isWhatsappInstalled = ref(false)

const enabled = createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is Whatsapp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = Boolean(data)
  },
})

const installed = createResource({
  url: 'crm.api.whatsapp.is_whatsapp_installed',
  cache: 'Is Whatsapp Installed',
  auto: true,
  onSuccess: (data) => {
    isWhatsappInstalled.value = Boolean(data)
  },
})

/**
 * Ask the server again whether WhatsApp is usable.
 *
 * These two are read once, when the app loads, and everything WhatsApp-shaped
 * hangs off them: the tab on a lead, the button in the activity header, the box
 * in the communication area.
 *
 * That was fine while connecting a number meant leaving the page — the browser
 * came back to a fresh app and read them again. Connecting without leaving the
 * page does not, so a number could be connected, working, and invisible until
 * somebody thought to reload. Whoever changes the answer calls this.
 */
export function refreshWhatsappState() {
  enabled.reload()
  installed.reload()
}
