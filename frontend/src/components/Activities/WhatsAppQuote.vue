<!-- eslint-disable vue/no-v-html -->
<!--
  The message this one answers, quoted at its top. A click takes you to it.

  Tinted by who wrote the quoted message — theirs or ours — not by a colour of
  its own: the quote is a small copy of a bubble, and it should say whose
  bubble it is copying the way the bubbles themselves do.
-->
<template>
  <button
    class="mb-1 flex w-full min-w-0 cursor-pointer flex-col rounded-md border-l-4 bg-surface-alpha-gray-2 px-2 py-1.5 text-left"
    :class="
      message.reply_to_type == 'Incoming'
        ? 'border-outline-gray-4'
        : 'border-outline-blue-4'
    "
    @click="emit('jump', message.reply_to)"
  >
    <span
      class="text-p-xs font-medium"
      :class="
        message.reply_to_type == 'Incoming'
          ? 'text-ink-gray-7'
          : 'text-ink-blue-8'
      "
    >
      {{ message.reply_to_from || __('You') }}
    </span>
    <span
      class="line-clamp-2 text-p-sm text-ink-gray-6"
      v-html="formatWhatsAppMessage(message.reply_message)"
    />
  </button>
</template>

<script setup>
import { formatWhatsAppMessage } from '@/utils/whatsappText'

defineProps({
  message: { type: Object, required: true },
})

const emit = defineEmits(['jump'])
</script>
