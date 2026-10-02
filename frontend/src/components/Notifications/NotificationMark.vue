<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The mark of a notification: its kind in a whole cloud of its category's
  colour (utils/notifiche.js). Small on the corner of the face of whoever sent
  it; in mint on the toast's deep block.
-->
<template>
  <span
    class="dc-segno"
    :class="[CLASSI[segno.colore], TAGLIE[taglia]]"
    aria-hidden="true"
  >
    <WhatsAppIcon v-if="segno.icona === 'whatsapp'" />
    <component :is="ICONE[segno.icona] || LucideBell" v-else />
  </span>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { aspetto } from '@/utils/notifiche'
import { computed } from 'vue'
import LucideAtSign from '~icons/lucide/at-sign'
import LucideBell from '~icons/lucide/bell'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideMail from '~icons/lucide/mail'
import LucideMessageCircleQuestion from '~icons/lucide/message-circle-question'
import LucideMessageSquareText from '~icons/lucide/message-square-text'
import LucidePhone from '~icons/lucide/phone'
import LucideReceiptText from '~icons/lucide/receipt-text'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucideSquareX from '~icons/lucide/square-x'
import LucideUserCheck from '~icons/lucide/user-check'
import LucideUserX from '~icons/lucide/user-x'
import LucideVoicemail from '~icons/lucide/voicemail'
import LucideZap from '~icons/lucide/zap'

const props = defineProps({
  kind: { type: String, default: 'other' },
  // 'md' alone, 'sm' on a face's corner, 'toast' on the deep block
  taglia: { type: String, default: 'md' },
})

const segno = computed(() => aspetto(props.kind))

// whole, for the build to keep them
const CLASSI = {
  brand: 'dc-segno--brand',
  amber: 'dc-segno--amber',
  blue: 'dc-segno--blue',
  violet: 'dc-segno--violet',
  green: 'dc-segno--green',
  rose: 'dc-segno--rose',
  gray: '',
}
const TAGLIE = { md: '', sm: 'dc-segno--piccolo', toast: 'dc-segno--toast' }

const ICONE = {
  'at-sign': LucideAtSign,
  bell: LucideBell,
  'calendar-clock': LucideCalendarClock,
  mail: LucideMail,
  'message-circle-question': LucideMessageCircleQuestion,
  'message-square-text': LucideMessageSquareText,
  phone: LucidePhone,
  'receipt-text': LucideReceiptText,
  'square-check': LucideSquareCheck,
  'square-x': LucideSquareX,
  'user-check': LucideUserCheck,
  'user-x': LucideUserX,
  voicemail: LucideVoicemail,
  zap: LucideZap,
}
</script>
