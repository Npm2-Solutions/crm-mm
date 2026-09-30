<template>
  <div class="flex flex-col h-full">
    <!-- header -->
    <div
      class="flex justify-between text-ink-gray-8 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1 w-9/12 max-md:w-full">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Email Accounts') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Manage your email accounts to send and receive emails directly from {brand}. You can add multiple accounts and set one as default for incoming and outgoing emails.',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end max-md:w-auto max-md:justify-start"
      >
        <Button
          :label="__('Add Account')"
          theme="gray"
          variant="solid"
          icon-left="lucide-plus"
          @click="emit('update:step', 'email-add')"
        />
      </div>
    </div>

    <!-- list accounts -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="mt-4"
    >
      <div
        v-for="(emailAccount, i) in emailAccounts.data"
        :key="emailAccount.name"
      >
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
        <div
          v-if="emailAccounts.data.length !== i + 1"
          class="h-px border-t mx-2 border-outline-elevation-2"
        />
      </div>
    </div>
    <!-- fallback if no email accounts -->
    <EmptyState
      v-else
      name="Email Accounts"
      :description="__('Add one to get started.')"
      :icon="Email2Icon"
    />
  </div>
</template>

<script setup>
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmptyState from '../ListViews/EmptyState.vue'
import EmailAccountCard from './EmailAccountCard.vue'
import { createResource } from 'frappe-ui'

const emit = defineEmits(['update:step'])

// Email Account is a core document Frappe keeps to System Manager: the CRM
// lists the centre's accounts to whoever has the capability (doc 30)
const emailAccounts = createResource({
  url: 'crm.api.settings.get_email_accounts',
  cache: 'crm-email-accounts',
  auto: true,
  onSuccess: (accounts) => {
    // convert 0 to false to handle boolean fields
    accounts.forEach((account) => {
      account.enable_incoming = Boolean(account.enable_incoming)
      account.enable_outgoing = Boolean(account.enable_outgoing)
      account.default_incoming = Boolean(account.default_incoming)
      account.default_outgoing = Boolean(account.default_outgoing)
    })
  },
})
</script>
