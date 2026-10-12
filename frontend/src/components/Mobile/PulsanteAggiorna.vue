<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The phone's «Refresh» at the top of a list (docs/crm/29): what pulling the
  list down from its top does (composables/tiraPerAggiornare), with one tap.
  VoiceOver scrolls without a touch on the list, a switch or a head pointer
  has no finger to pull with, and the browser's own pull is off: the pull
  alone left them no way to bring a list up to date (WCAG 2.5.1, 2.5.7). It
  turns while the list comes back, after a pull too, and a tap meanwhile asks
  for nothing more: one reload at a time.

  It turns without frappe-ui's `loading`, which disables the button: a key
  pressed from a keyboard (a page zoomed to 400% draws the phone's layout)
  lost its focus to the page's top at every press. The list's mark says
  «Updating the list…» to a screen reader (TiraPerAggiornare.vue), so the
  spinner here is for the eye only.
-->
<template>
  <Button
    v-if="tira"
    variant="ghost"
    :tooltip="__('Refresh')"
    :aria-label="__('Refresh')"
    @click="tira.aggiornaOra()"
  >
    <template #icon>
      <LoadingIndicator v-if="tira.inCorso" class="size-4" aria-hidden="true" />
      <span v-else class="lucide-refresh-ccw size-4" aria-hidden="true" />
    </template>
  </Button>
</template>

<script setup>
import { Button, LoadingIndicator } from 'frappe-ui'

// the list's pull, as useTiraPerAggiornare gives it back: there once the
// list is drawn
defineProps({ tira: { type: Object, default: null } })
</script>
