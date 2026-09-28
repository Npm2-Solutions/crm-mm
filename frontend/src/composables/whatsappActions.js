import { markAnswered } from '@/composables/conversationState'
import { formatWhatsAppMessage } from '@/utils/whatsappText'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

/**
 * What can be done to a WhatsApp message once it is on screen: answer it, react
 * to it, send it again.
 *
 * One copy, used by the WhatsApp view and by the mixed chat. They each had
 * their own — or rather the mixed chat borrowed the WhatsApp view's by putting
 * the whole message component inside its bubble, badge and buttons included,
 * which is how a failed message came to have «failed · Retry» pinned over its
 * first word.
 *
 * @param {{ list: import('vue').Ref, reply: import('vue').Ref }} models
 *   the messages resource (reloaded after a change) and the message being
 *   answered, as the composer reads it
 */
export function useWhatsAppActions({ list, reply }) {
  const { capture } = useTelemetry()

  // the one being sent again, so only its button waits
  const retrying = ref('')

  function retry(message) {
    if (retrying.value) return
    retrying.value = message.name
    createResource({
      url: 'crm.api.whatsapp.retry_whatsapp_message',
      params: { name: message.name },
      auto: true,
      onSuccess: () => {
        retrying.value = ''
        toast.success(__('Sent'))
        list.value?.reload?.()
      },
      onError: (error) => {
        retrying.value = ''
        // Meta's own reason, which is the whole point of retrying by hand
        toast.error(error.messages?.[0] || __('It failed again'))
      },
    })
  }

  function react(message, emoji) {
    if (!emoji) return
    createResource({
      url: 'crm.api.whatsapp.react_on_whatsapp_message',
      params: { emoji, reply_to_name: message.name },
      auto: true,
      onSuccess() {
        capture('whatsapp_react_on_message')
        list.value?.reload?.()
        // a 👍 on their message is an answer to it
        markAnswered(message.reference_doctype, message.reference_name)
      },
      onError(error) {
        toast.error(
          error.messages?.[0] || __('Failed to add reaction to the message'),
        )
      },
    })
  }

  function answer(message) {
    reply.value = {
      ...message,
      message: formatWhatsAppMessage(message.message),
    }
  }

  return { retrying, retry, react, answer }
}
