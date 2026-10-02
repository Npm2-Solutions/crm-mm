<template>
  <!-- a row, not a button: the brand's button styles would draw it as one -->
  <div
    :role="emailAccount.editable ? 'button' : undefined"
    :tabindex="emailAccount.editable ? 0 : undefined"
    class="flex w-full items-center justify-between gap-3 rounded px-2 py-3 text-left max-md:flex-col max-md:items-start"
    :class="{
      'cursor-pointer hover:bg-surface-gray-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3':
        emailAccount.editable,
    }"
    @click="emailAccount.editable && $emit('click')"
    @keydown.enter.prevent="emailAccount.editable && $emit('click')"
    @keydown.space.prevent="emailAccount.editable && $emit('click')"
  >
    <div class="flex min-w-0 items-center gap-3">
      <EmailProviderIcon
        :logo="logoDi[emailAccount.provider]"
        :name="fornitore(emailAccount.provider)?.nome || ''"
      />
      <div class="flex min-w-0 flex-col">
        <span class="truncate text-p-base text-ink-gray-8">
          {{ emailAccount.email_account_name }}
        </span>
        <span class="truncate text-p-sm text-ink-gray-5">
          {{ emailAccount.email_id }}
        </span>
      </div>
    </div>
    <!-- what it does, in words; and whose it is when it is the agency's -->
    <div class="flex shrink-0 flex-wrap justify-end gap-1 max-md:justify-start">
      <Badge
        v-for="segno in segni(emailAccount, servizio)"
        :key="segno"
        variant="subtle"
        theme="gray"
        :label="__(segno)"
      />
    </div>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { fornitore, segni } from '@/utils/caselle'
import { logoDi } from './emailConfig'
import EmailProviderIcon from './EmailProviderIcon.vue'

defineEmits(['click'])
defineProps({
  emailAccount: { type: Object, required: true },
  // whether {brand}'s emails leave through the agency's service
  servizio: { type: Boolean, default: false },
})
</script>
