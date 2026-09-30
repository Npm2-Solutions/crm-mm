<!--
  The centre's messages: a board, not a chat. Opening it reads what was new.
-->
<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Messages') }}</h1>
    <article
      v-for="message in messages.data?.messages || []"
      :key="message.name"
      class="flex flex-col gap-2 rounded-lg bg-surface-white p-4 shadow-sm"
    >
      <p class="whitespace-pre-line text-p-base text-ink-gray-9">
        {{ message.body }}
      </p>
      <span class="text-p-sm text-ink-gray-5">
        {{ message.author_name }} · {{ day(message.posted_on) }}
      </span>
    </article>
    <p
      v-if="messages.data && !messages.data.messages.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('Nothing here yet.') }}
    </p>
  </div>
</template>

<script setup>
import { call, createResource } from 'frappe-ui'
import { day } from '../dates'
import { area } from '../store'

const messages = createResource({
  url: 'crm.clinica.area.messaggi.area_messages',
  params: { person: area.person },
  auto: true,
  onSuccess() {
    call('crm.clinica.area.messaggi.mark_read', { person: area.person })
      .then(() => {
        const who = (area.me?.people || []).find((p) => p.name === area.person)
        if (who) who.unread = 0
      })
      .catch(() => {})
  },
})
</script>
