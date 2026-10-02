<!--
  The centre's messages: a board, not a chat - each one a card, who wrote it in
  the brand's cloud. Opening it reads what was new.
  The questions the person passed on from the chat are here too, with whether
  the centre read them; the answer comes as a message.
-->
<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-end justify-between gap-3">
      <h1 class="area-title">{{ __('Messages') }}</h1>
      <router-link
        v-if="area.me?.chat"
        :to="{ name: 'Chat' }"
        class="area-link shrink-0 pb-1"
      >
        {{ __('Ask the assistant') }}
      </router-link>
    </div>
    <template
      v-for="message in messages.data?.messages || []"
      :key="message.name"
    >
      <HiddenCard v-if="message.hidden" />
      <!-- the person's own question, on their side, in the brand's soft green -->
      <article
        v-else-if="message.kind === 'Question'"
        class="ml-10 flex flex-col gap-1.5 rounded-[16px_16px_2px_16px] bg-[var(--brand-subtle)] px-4 py-3"
      >
        <span class="area-label text-[var(--on-brand-subtle)]">
          {{ __('Your question') }}
        </span>
        <p class="whitespace-pre-line text-p-base text-ink-gray-9">
          {{ message.body }}
        </p>
        <span class="text-p-sm text-ink-gray-6">
          {{ day(message.posted_on) }} ·
          {{
            message.read_on
              ? __('read by the centre')
              : __('not read by the centre yet')
          }}
        </span>
      </article>
      <article v-else class="area-card flex flex-col gap-2">
        <div class="flex items-center gap-2.5">
          <AreaChip icona="message-circle" />
          <span class="min-w-0">
            <span class="area-row__title">{{ message.author_name }}</span>
            <span class="area-row__sub">{{ day(message.posted_on) }}</span>
          </span>
        </div>
        <p class="whitespace-pre-line text-p-base text-ink-gray-9">
          {{ message.body }}
        </p>
      </article>
    </template>
    <p
      v-if="messages.data && !messages.data.messages.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('Nothing here yet.') }}
    </p>
    <NoticeCard v-if="noticesOffered && !anteprima" />
  </div>
</template>

<script setup>
import { call, createResource } from 'frappe-ui'
import { computed } from 'vue'
import { anteprima } from '../anteprima'
import AreaChip from '../components/AreaChip.vue'
import HiddenCard from '../components/HiddenCard.vue'
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
    // the centre's preview reads nothing on the person's behalf
    if (anteprima) return
    call('crm.area.messaggi.mark_read', { person: area.person })
      .then(() => {
        const who = (area.me?.people || []).find((p) => p.name === area.person)
        if (who) who.unread = 0
      })
      .catch(() => {})
  },
})
</script>
