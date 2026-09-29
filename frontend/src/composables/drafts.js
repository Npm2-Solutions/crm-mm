import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'

/**
 * What is being written to somebody, kept in this browser per user and per
 * record: an email, a note, a WhatsApp message, an SMS.
 *
 * The same key gives the same draft wherever it is asked for — the box that
 * writes it and the composer's tabs, which mark the channels holding one.
 *
 * @param {string} what  emailBoxContent, commentBoxContent, whatsappDraft, smsDraft…
 */
export function useDraft(what, doctype, name, initial = '', options) {
  const { getUser } = usersStore()
  return useStorage(
    `${what}-${getUser().email}-${doctype}-${name}`,
    initial,
    localStorage,
    options,
  )
}
