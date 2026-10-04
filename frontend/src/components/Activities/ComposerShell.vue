<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<!--
  The box everything is written in, on every tab that writes.

  It says when it is being written in. Clicking into the WhatsApp line used to
  change nothing at all — the cursor appeared in a box that looked exactly as
  it had — and whether a click had landed was a matter of starting to type and
  seeing. Now the border takes the channel's colour, the same one its tab and
  its bubbles wear, with a soft ring round it and a little more lift: green for
  WhatsApp, blue for email, violet for SMS, amber for the note that the
  customer never sees.
-->
<template>
  <!-- data-compositore: where an open chat is the screen, the box is its
       bottom (telefono.css, «11»); on a phone it keeps less room round it -->
  <div
    data-compositore
    class="shrink-0 bg-surface-gray-2 px-3 pb-3 pt-2 dark:bg-surface-base sm:px-4 max-md:px-2 max-md:pb-2 max-md:pt-1.5"
  >
    <div
      class="overflow-hidden rounded-xl border shadow-sm transition-[border-color,box-shadow,background-color] duration-150 focus-within:shadow-md focus-within:ring-2"
      :class="[
        way === 'comment'
          ? 'border-outline-amber-3 bg-surface-amber-1'
          : 'border-outline-gray-2 bg-surface-elevation-2 dark:bg-surface-gray-1',
        LIT[way] || LIT.email,
      ]"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  // the way of writing it holds: whatsapp, email, sms or comment
  way: { type: String, default: 'email' },
})

// Written out, never assembled: Tailwind reads the source for class names and
// never sees one built from a variable.
const LIT = {
  whatsapp:
    'focus-within:border-outline-green-4 focus-within:ring-outline-green-2',
  email: 'focus-within:border-outline-blue-4 focus-within:ring-outline-blue-2',
  sms: 'focus-within:border-outline-violet-4 focus-within:ring-outline-violet-2',
  comment:
    'focus-within:border-outline-amber-5 focus-within:ring-outline-amber-2',
}
</script>
