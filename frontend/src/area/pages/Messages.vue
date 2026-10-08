<!--
  The board with the centre, both ways: the centre's messages, each a card, who
  wrote it in the brand's cloud - opening it reads what was new - and what the
  person writes, on their side, with whether the centre read it (crm.area.messaggi).
  They write at the top: words, and maybe a photo or a PDF; the answer comes as a
  message. Never in the centre's preview.
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
    <!-- the person writes to the centre -->
    <form
      v-if="!anteprima"
      class="area-card flex flex-col gap-3"
      @submit.prevent="send"
    >
      <FormControl
        v-model="draft"
        type="textarea"
        :rows="3"
        :maxlength="4000"
        :label="__('Write to the centre')"
        :placeholder="__('A question, a document to send…')"
        :disabled="busy"
      />
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'The centre answers here. For an emergency do not write: call 112.',
          )
        }}
      </p>
      <div
        v-if="file"
        class="flex min-w-0 items-center gap-2 rounded-lg bg-surface-gray-2 px-3 py-2"
      >
        <LucidePaperclip
          class="size-4 shrink-0 text-ink-gray-6"
          aria-hidden="true"
        />
        <span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-8">
          {{ file.name }}
        </span>
        <span class="shrink-0 text-p-sm text-ink-gray-6">
          {{ quantoPesa(file.size, locale) }}
        </span>
        <Button
          variant="ghost"
          class="touch-target shrink-0"
          icon="x"
          :aria-label="__('Remove the file')"
          @click="clearFile"
        />
      </div>
      <ErrorMessage :message="error" />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <Button
          size="md"
          class="touch-target"
          :label="__('Attach a photo or a PDF')"
          :disabled="busy"
          @click="picker?.click()"
        >
          <template #prefix>
            <LucidePaperclip class="size-4" aria-hidden="true" />
          </template>
        </Button>
        <Button
          size="md"
          variant="solid"
          type="submit"
          class="touch-target ml-auto"
          :label="__('Send')"
          :loading="busy"
          :disabled="!draft.trim() && !file"
        />
      </div>
      <input
        ref="picker"
        type="file"
        class="hidden"
        :accept="ACCETTA"
        @change="choose"
      />
    </form>
    <template
      v-for="message in messages.data?.messages || []"
      :key="message.name"
    >
      <HiddenCard v-if="message.hidden" />
      <!-- the person's own, on their side, in the brand's soft green -->
      <article
        v-else-if="message.from_person"
        class="ml-10 flex flex-col gap-1.5 rounded-[16px_16px_2px_16px] bg-[var(--brand-subtle)] px-4 py-3"
      >
        <span class="area-label text-[var(--on-brand-subtle)]">
          {{
            message.kind === 'Question'
              ? __('Your question')
              : __('Your message')
          }}
        </span>
        <p
          v-if="message.body"
          class="whitespace-pre-line break-words text-p-base text-ink-gray-9"
        >
          {{ message.body }}
        </p>
        <span
          v-if="message.attachment_name"
          class="flex min-w-0 items-center gap-1.5 text-p-sm text-ink-gray-8"
        >
          <LucidePaperclip class="size-4 shrink-0" aria-hidden="true" />
          <span class="min-w-0 truncate">{{ message.attachment_name }}</span>
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ day(message.posted_on) }} ·
          {{
            message.kind === 'Question'
              ? message.read_on
                ? __('read by the centre')
                : __('not read by the centre yet')
              : message.read_on
                ? __('seen by the centre')
                : __('not seen by the centre yet')
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
import {
  Button,
  ErrorMessage,
  FormControl,
  call,
  createResource,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import LucidePaperclip from '~icons/lucide/paperclip'
import { ACCETTA, MAX_MB, cosaNonVa, quantoPesa } from '../allegato'
import { anteprima } from '../anteprima'
import AreaChip from '../components/AreaChip.vue'
import HiddenCard from '../components/HiddenCard.vue'
import NoticeCard from '../components/NoticeCard.vue'
import { day } from '../dates'
import { area, messageOf } from '../store'
import { locale } from '../translation'

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

// what the person writes: words, and one file read in the browser
const draft = ref('')
const file = ref(null)
const picker = ref(null)
const busy = ref(false)
const error = ref('')

function choose(event) {
  const chosen = event.target.files?.[0] || null
  event.target.value = ''
  if (!chosen) return
  const problema = cosaNonVa(chosen)
  if (problema) {
    error.value = __(problema, [MAX_MB])
    return
  }
  error.value = ''
  file.value = chosen
}

function clearFile() {
  file.value = null
}

function asDataUrl(chosen) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(chosen)
  })
}

async function send() {
  if (busy.value || (!draft.value.trim() && !file.value)) return
  busy.value = true
  error.value = ''
  try {
    const params = { person: area.person, body: draft.value }
    if (file.value) {
      params.attachment = await asDataUrl(file.value)
      params.attachment_name = file.value.name
    }
    messages.data = await call('crm.area.messaggi.send_message', params)
    draft.value = ''
    file.value = null
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
