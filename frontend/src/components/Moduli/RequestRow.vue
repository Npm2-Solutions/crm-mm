<!--
  A form sent to fill on their own: where it went, where it is now, and what
  the desk can do about it (withdraw it, or sign what was filled at home).
-->
<template>
  <div
    class="flex min-w-0 items-center gap-3 rounded px-2 py-2.5 hover:bg-surface-gray-2 max-md:flex-wrap"
  >
    <component
      :is="request.channel === 'Tablet' ? LucideTablet : LucideMail"
      class="size-4 shrink-0 text-ink-gray-5"
    />
    <div class="min-w-0 flex-1">
      <div class="truncate text-base text-ink-gray-8">{{ request.title }}</div>
      <div class="text-sm text-ink-gray-5">{{ said }}</div>
    </div>
    <div class="flex shrink-0 items-center gap-1.5">
      <Badge
        :label="status.label"
        :theme="status.theme"
        variant="subtle"
        size="sm"
      />
      <Button
        v-if="request.status === 'Filled' && request.form"
        size="sm"
        variant="solid"
        :label="__('Sign')"
        @click="emit('open', request.form)"
      />
      <Button
        v-else-if="canFill && ['Sent', 'Opened'].includes(request.status)"
        class="touch-target"
        size="sm"
        variant="ghost"
        :label="__('Withdraw')"
        @click="emit('withdraw', request)"
      />
    </div>
  </div>
</template>

<script setup>
import { formatDate } from '@/utils'
import LucideMail from '~icons/lucide/mail'
import LucideTablet from '~icons/lucide/tablet'
import { Badge, Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  request: { type: Object, required: true },
  canFill: { type: Boolean, default: false },
})
const emit = defineEmits(['withdraw', 'open'])

const STATUS = {
  Sent: () => ({ label: __('Sent'), theme: 'gray' }),
  Opened: () => ({ label: __('Opened'), theme: 'blue' }),
  Filled: () => ({ label: __('To sign at the desk'), theme: 'orange' }),
  // a survey is answered, never signed
  Signed: (request) => ({
    label: request.without_code ? __('Answered', null, 'Survey') : __('Signed'),
    theme: 'green',
  }),
  Expired: () => ({ label: __('Expired'), theme: 'gray' }),
  Cancelled: () => ({ label: __('Withdrawn'), theme: 'gray' }),
}
const status = computed(() =>
  (
    STATUS[props.request.status] ||
    (() => ({ label: props.request.status, theme: 'gray' }))
  )(props.request),
)

const said = computed(() => {
  const request = props.request
  const when = formatDate(request.sent_on, 'D MMM, HH:mm')
  const parts = [
    request.channel === 'Tablet'
      ? __('tablet handed over {0}', [when])
      : __('sent {0} to {1}', [when, request.sent_to || '']),
  ]
  if (request.sent_by_name) parts.push(__('by {0}', [request.sent_by_name]))
  if (
    ['Sent', 'Opened'].includes(request.status) &&
    request.channel === 'Link'
  ) {
    parts.push(__('until {0}', [formatDate(request.expires_on, 'D MMM')]))
  }
  if (request.sign_at_desk && request.status !== 'Signed') {
    parts.push(__('signed at the desk'))
  }
  return parts.join(' · ')
})
</script>
