<!--
  The centre's messages: a board, not a chat. Opening it reads what was new.
  The questions the person passed on from the chat are here too, with whether
  the centre read them; the answer comes as a message.
-->
<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between gap-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Messages') }}
      </h1>
      <router-link
        v-if="area.me?.chat"
        :to="{ name: 'Chat' }"
        class="shrink-0 text-p-sm text-ink-gray-7 underline underline-offset-2"
      >
        {{ __('Ask the assistant') }}
      </router-link>
    </div>
    <article
      v-for="message in messages.data?.messages || []"
      :key="message.name"
      class="flex flex-col gap-2 rounded-lg p-4 shadow-sm"
      :class="
        message.kind === 'Question'
          ? 'ml-8 bg-surface-gray-2'
          : 'bg-surface-elevation-1'
      "
    >
      <span
        v-if="message.kind === 'Question'"
        class="text-p-sm font-medium text-ink-gray-7"
      >
        {{ __('Your question') }}
      </span>
      <p class="whitespace-pre-line text-p-base text-ink-gray-9">
        {{ message.body }}
      </p>
      <span class="text-p-sm text-ink-gray-5">
        <template v-if="message.kind === 'Question'">
          {{ day(message.posted_on) }} ·
          {{
            message.read_on
              ? __('read by the centre')
              : __('not read by the centre yet')
          }}
        </template>
        <template v-else>
          {{ message.author_name }} · {{ day(message.posted_on) }}
        </template>
      </span>
    </article>
    <p
      v-if="messages.data && !messages.data.messages.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('Nothing here yet.') }}
    </p>
    <NoticeCard v-if="noticesOffered" />
  </div>
</template>

<script setup>
import { call, createResource } from 'frappe-ui'
import { computed } from 'vue'
import NoticeCard from '../components/NoticeCard.vue'
import { day } from '../dates'
import { area } from '../store'

// other channels than the email, where the centre offers them
const noticesOffered = computed(() => Boolean(area.me?.notices))

const messages = createResource({
  url: 'crm.area.messaggi.area_messages',
  params: { person: area.person },
  auto: true,
  onSuccess() {
    call('crm.area.messaggi.mark_read', { person: area.person })
      .then(() => {
        const who = (area.me?.people || []).find((p) => p.name === area.person)
        if (who) who.unread = 0
      })
      .catch(() => {})
  },
})
</script>
