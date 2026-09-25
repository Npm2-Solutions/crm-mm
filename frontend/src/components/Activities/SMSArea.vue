<template>
  <div>
    <div
      v-for="sms in messages"
      :key="sms.name"
      class="activity group flex gap-2"
      :class="[
        bare ? '' : 'mb-3',
        sms.type == 'Outgoing' && !bare ? 'flex-row-reverse' : '',
      ]"
    >
      <div
        :id="sms.name"
        class="relative min-w-0 max-w-full break-words text-base text-ink-gray-9"
        :class="
          bare
            ? 'w-full'
            : [
                'rounded-md p-1.5 pl-2 shadow-sm',
                sms.type == 'Outgoing'
                  ? 'bg-surface-gray-2'
                  : 'bg-surface-gray-1',
              ]
        "
      >
        <Badge
          v-if="['Failed', 'Undelivered'].includes(sms.status)"
          theme="red"
          :label="__(sms.status)"
          class="absolute -top-2 right-0"
        />
        <div class="whitespace-pre-wrap break-words">{{ sms.message }}</div>
        <div
          class="mt-1 flex items-center justify-end gap-1 text-xs text-ink-gray-4"
        >
          <!--
            An SMS bubble is grey, and so is a lot of other things: the icon is
            how it says which channel it is, now that the stream no longer
            writes a line of text under every message to say so.
          -->
          <SMSIcon class="size-3" />
          <!-- the clock, like every other bubble: the day is on the date chip
             above, and «23 hours ago» beside «11:07 am» is two units for one
             question -->
          <Tooltip :text="formatDate(sms.creation)">
            <span>{{ formatDate(sms.creation, 'hh:mm a') }}</span>
          </Tooltip>
          <span v-if="sms.type == 'Outgoing'">· {{ __(sms.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import { formatDate } from '@/utils'
import { Tooltip } from 'frappe-ui'

defineProps({
  messages: { type: Array, default: () => [] },
  // the house component draws the bubble in the mixed chat
  bare: { type: Boolean, default: false },
})
</script>
