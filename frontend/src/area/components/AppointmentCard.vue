<!-- An appointment as the patient reads it: when, what, with whom, where. -->
<template>
  <div
    class="flex flex-col gap-2 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <div class="flex items-start justify-between gap-2">
      <span
        class="text-base font-medium text-ink-gray-9 first-letter:uppercase"
      >
        {{ when(appointment.starts_on) }}
      </span>
      <Badge
        v-if="appointment.status === 'Cancelled'"
        theme="red"
        variant="subtle"
        :label="__('Cancelled')"
      />
    </div>
    <span class="text-p-base text-ink-gray-8">{{ appointment.service }}</span>
    <span v-if="appointment.staff?.length" class="text-p-sm text-ink-gray-6">
      {{ __('With {0}', [appointment.staff.join(', ')]) }}
    </span>
    <span v-if="appointment.location" class="text-p-sm text-ink-gray-6">
      {{ appointment.location }}
    </span>
    <a
      v-if="appointment.manage_url"
      :href="appointment.manage_url"
      class="mt-1 w-fit text-p-sm font-medium text-ink-gray-9 underline underline-offset-2"
    >
      {{ __('Move or cancel') }}
    </a>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { when } from '../dates'

defineProps({ appointment: { type: Object, required: true } })
</script>
