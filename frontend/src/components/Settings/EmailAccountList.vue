<template>
  <div class="flex min-h-0 flex-1 flex-col gap-6 text-ink-gray-8">
    <!-- header -->
    <div
      class="flex justify-between gap-4 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Email Accounts') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              "The centre's mailboxes in {brand}: the emails people write arrive on their page, and you answer them from there.",
            )
          }}
        </p>
      </div>
      <Button
        class="shrink-0"
        :label="__('Add a mailbox')"
        variant="solid"
        icon-left="lucide-plus"
        @click="emit('update:step', 'email-add', { servizio: attivo })"
      />
    </div>

    <div class="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto">
      <SendingService :stato="servizio" />

      <section class="flex flex-col gap-2">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __("The centre's mailboxes") }}
        </h3>
        <div
          v-if="emailAccounts.data?.length"
          class="flex flex-col divide-y divide-outline-gray-1"
        >
          <!-- the agency's mailboxes, with servers of their own, are shown and
               not opened: the page could not save them -->
          <EmailAccountCard
            v-for="emailAccount in emailAccounts.data"
            :key="emailAccount.name"
            :emailAccount="emailAccount"
            :servizio="attivo"
            @click="
              emailAccount.editable &&
                emit('update:step', 'email-edit', {
                  ...emailAccount,
                  servizio: attivo,
                })
            "
          />
        </div>
        <EmptyState
          v-else-if="!emailAccounts.loading"
          :title="__('No mailbox yet')"
          :text="
            __(
              'Add the centre’s mailbox: the emails people write arrive on their page in {brand}.',
            )
          "
        >
          <Button
            variant="solid"
            :label="__('Add a mailbox')"
            @click="emit('update:step', 'email-add', { servizio: attivo })"
          />
        </EmptyState>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Button, createResource } from 'frappe-ui'
import { computed } from 'vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import EmailAccountCard from './EmailAccountCard.vue'
import SendingService from './SendingService.vue'

const emit = defineEmits(['update:step'])

// Email Account is a core document Frappe keeps to System Manager: the server
// lists the centre's mailboxes to whoever has the capability (doc 30), never
// {brand}'s sending service, which is the agency's (doc 51)
const emailAccounts = createResource({
  url: 'crm.api.settings.get_email_accounts',
  cache: 'crm-email-accounts',
  auto: true,
  transform: (accounts) =>
    accounts.map((account) => ({
      ...account,
      enable_incoming: Boolean(account.enable_incoming),
      enable_outgoing: Boolean(account.enable_outgoing),
      default_incoming: Boolean(account.default_incoming),
      default_outgoing: Boolean(account.default_outgoing),
      create_lead_from_incoming_email: Boolean(
        account.create_lead_from_incoming_email,
      ),
    })),
})

const servizio = createResource({
  url: 'crm.posta.servizio.get_sending_service',
  cache: 'crm-sending-service',
  auto: true,
})

const attivo = computed(() => Boolean(servizio.data?.active))
</script>
