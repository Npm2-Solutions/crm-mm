<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Where a page that sends SMS says who they come from: the centre's one sender
  (doc 52), set on Twilio's page and the same for every SMS - the waiting list's
  offers, the client area's news, the automations, the ones written by hand.
-->
<template>
  <div class="flex flex-col gap-1.5 px-2">
    <div class="text-p-base-medium text-ink-gray-7">{{ __('SMS') }}</div>
    <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
      <span class="min-w-0 text-p-sm text-ink-gray-5">{{ riga }}</span>
      <Button
        v-if="twilio"
        variant="ghost"
        size="sm"
        class="shrink-0"
        :label="__('Change')"
        @click="
          apriImpostazioni({ page: 'Telephony', step: 'twilio-settings' })
        "
      />
    </div>
  </div>
</template>

<script setup>
import { apriImpostazioni } from '@/composables/settings'
import { computed } from 'vue'

const props = defineProps({
  // who the centre's SMS come from: its name or one of its numbers
  sender: { type: String, default: '' },
  // whether Twilio is connected at all
  twilio: { type: Boolean, default: false },
})

const riga = computed(() => {
  if (!props.twilio) return __('Twilio is not connected: SMS are not offered.')
  if (!props.sender) {
    return __('The centre has no SMS sender yet: SMS are not offered.')
  }
  return props.sender.startsWith('+')
    ? __('They leave from the centre’s number {0}: people can reply.', [
        props.sender,
      ])
    : __(
        'They leave with the centre’s name, {0}: nobody can reply to a name.',
        [props.sender],
      )
})
</script>
