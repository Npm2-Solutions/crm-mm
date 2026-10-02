<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A kind of thing in a cloud of its category's colour (area.css, the design
  system's cat-*): a plan by its kind, a document, the centre's messages. The
  icons the area draws, by name; one it does not know is a list.
-->
<template>
  <span class="area-chip" :class="CLASSI[colore]" aria-hidden="true">
    <component :is="ICONE[icona] || LucideListChecks" />
  </span>
</template>

<script setup>
import LucideApple from '~icons/lucide/apple'
import LucideCalendar from '~icons/lucide/calendar'
import LucideClipboardList from '~icons/lucide/clipboard-list'
import LucideDumbbell from '~icons/lucide/dumbbell'
import LucideFileText from '~icons/lucide/file-text'
import LucideHourglass from '~icons/lucide/hourglass'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideMessageCircle from '~icons/lucide/message-circle'
import LucideMessageCircleQuestion from '~icons/lucide/message-circle-question'
import LucideReceipt from '~icons/lucide/receipt'
import LucideReceiptText from '~icons/lucide/receipt-text'
import LucideRepeat from '~icons/lucide/repeat'
import LucideSalad from '~icons/lucide/salad'
import LucideShoppingCart from '~icons/lucide/shopping-cart'
import LucideSprout from '~icons/lucide/sprout'
import LucideTicket from '~icons/lucide/ticket'

defineProps({
  // a category of the design system; empty, the brand's
  colore: { type: String, default: '' },
  icona: { type: String, default: '' },
})

// whole, for the build to keep them
const CLASSI = {
  amber: 'area-chip--amber',
  violet: 'area-chip--violet',
  blue: 'area-chip--blue',
  rose: 'area-chip--rose',
  green: 'area-chip--green',
}

const ICONE = {
  apple: LucideApple,
  calendar: LucideCalendar,
  'clipboard-list': LucideClipboardList,
  dumbbell: LucideDumbbell,
  'file-text': LucideFileText,
  hourglass: LucideHourglass,
  'list-checks': LucideListChecks,
  'message-circle': LucideMessageCircle,
  'message-circle-question': LucideMessageCircleQuestion,
  receipt: LucideReceipt,
  'receipt-text': LucideReceiptText,
  repeat: LucideRepeat,
  salad: LucideSalad,
  'shopping-cart': LucideShoppingCart,
  sprout: LucideSprout,
  ticket: LucideTicket,
}
</script>
