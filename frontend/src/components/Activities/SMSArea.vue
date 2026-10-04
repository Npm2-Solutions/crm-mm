<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <div>
    <!-- inside the mixed chat the house bubble draws the frame, the clock and
       a failure; what is left is what was written -->
    <template v-if="bare">
      <div
        v-for="sms in messages"
        :id="sms.name"
        :key="sms.name"
        class="whitespace-pre-wrap break-words"
      >
        {{ sms.message }}
      </div>
    </template>

    <template v-else>
      <div
        v-for="(sms, index) in messages"
        :key="sms.name"
        class="activity flex"
        :class="sms.type == 'Outgoing' ? 'justify-end' : 'justify-start'"
      >
        <div
          :id="sms.name"
          class="bubble-lift relative min-w-0 max-w-full rounded-2xl px-3 pb-1.5 pt-2 text-base text-ink-gray-9"
          :class="[
            sms.type == 'Outgoing'
              ? 'bg-surface-blue-3'
              : 'bg-surface-elevation-2 dark:bg-surface-gray-2',
            tailOf(index)
              ? sms.type == 'Outgoing'
                ? 'bubble-tail-out rounded-tr-none'
                : 'bubble-tail-in rounded-tl-none'
              : '',
            failed(sms) ? 'ring-1 ring-inset ring-outline-red-3' : '',
          ]"
        >
          <div class="flex flex-wrap items-end gap-x-2">
            <div class="min-w-0 whitespace-pre-wrap break-words">
              {{ sms.message }}
            </div>
            <div
              class="-mb-0.5 ml-auto flex shrink-0 items-center gap-1 pt-0.5 text-p-xs leading-none text-ink-gray-5"
            >
              <!-- what the carrier said, in its own space rather than on a
                 badge pinned over the words -->
              <Tooltip
                v-if="failed(sms)"
                :text="
                  sms.error_message || __('The message did not reach them')
                "
              >
                <span class="flex items-center gap-1 text-ink-red-6">
                  <span
                    class="lucide-circle-alert size-3.5"
                    aria-hidden="true"
                  />
                  {{ __(sms.status) }}
                </span>
              </Tooltip>
              <Tooltip :text="formatDate(sms.creation, 'ddd, D MMM YYYY')">
                <span class="tabular-nums">{{ clockOf(sms.creation) }}</span>
              </Tooltip>
              <span
                v-if="sms.type == 'Outgoing' && !failed(sms) && sms.status"
                class="text-ink-gray-5"
              >
                · {{ __(sms.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script setup>
import { formatDate } from '@/utils'
import { clockOf as clock, hasFailed, opensRun } from '@/utils/conversation'
import { Tooltip, dayjsLocal } from 'frappe-ui'
import { appLocale } from '@/utils/locale'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  // the house component draws the bubble in the mixed chat
  bare: { type: Boolean, default: false },
  // whether the bubble carries its tail, when the caller knows; left out, each
  // message works it out from the one before it
  tail: { type: Boolean, default: null },
})

function tailOf(index) {
  return props.tail ?? opensRun(props.messages, index)
}

function failed(sms) {
  return hasFailed({ ...sms, activity_type: 'sms' })
}

function clockOf(at) {
  return at
    ? clock(dayjsLocal(at).format('YYYY-MM-DD HH:mm:ss'), appLocale())
    : ''
}
</script>
