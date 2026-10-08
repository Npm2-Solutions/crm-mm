<!--
  The person's board in their area, both ways: what the centre writes to them,
  and what they write back from the area's Messages - words, maybe a photo or a
  PDF, opened from here - or pass on from its chat, marked: it is answered by
  writing to the person. The desk writes administrative messages; with the clinic
  on, a practitioner writes about the care, read like a visit. Who enters the
  area gets an email that says only that there is news.
-->
<template>
  <section
    v-if="board.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-col gap-0.5">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Messages in the area') }}
      </h3>
      <p class="text-p-sm text-ink-gray-5">
        {{
          board.data.kind === 'Care'
            ? __(
                'About their care: the person reads it in their area, your colleagues as they read your visits.',
              )
            : __(
                'From the desk: a reminder, a document to bring. The person reads it in their area, and writes back here.',
              )
        }}
      </p>
    </div>

    <p
      v-if="!board.data.has_area"
      class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
    >
      {{ __('The person has no area open: open it first, then write here.') }}
    </p>
    <template v-else>
      <Textarea
        v-model="draft"
        :rows="3"
        :placeholder="__('Write to the person')"
        :disabled="busy"
      />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="min-w-0 text-p-xs text-ink-gray-5">
          {{ __('The email says only that there is news in the area.') }}
        </span>
        <Button
          variant="solid"
          class="shrink-0"
          :label="__('Post')"
          :disabled="!draft.trim()"
          :loading="busy"
          @click="post"
        />
      </div>
      <ErrorMessage :message="error" />
    </template>

    <div
      v-for="message in board.data.messages"
      :key="message.name"
      class="flex flex-col gap-1 border-t border-outline-gray-1 pt-3"
    >
      <Badge
        v-if="message.from_person"
        class="w-fit"
        variant="subtle"
        theme="blue"
        :label="
          message.kind === 'Question'
            ? __('A question from the area')
            : __('Written in the area')
        "
      />
      <p
        v-if="message.body"
        class="whitespace-pre-line break-words text-p-base text-ink-gray-8"
      >
        {{ message.body }}
      </p>
      <a
        v-if="message.attachment_name"
        :href="attachmentUrl(message)"
        target="_blank"
        rel="noopener"
        class="flex w-fit min-w-0 max-w-full items-center gap-1.5 rounded-md bg-surface-gray-2 px-2.5 py-1.5 text-p-sm text-ink-gray-8 hover:bg-surface-gray-3 [@media(pointer:coarse)]:min-h-10"
      >
        <FeatherIcon name="paperclip" class="size-4 shrink-0" />
        <span class="min-w-0 truncate">{{ message.attachment_name }}</span>
      </a>
      <span class="text-p-xs text-ink-gray-5">
        {{ message.author_name }} ·
        {{ formatDate(message.posted_on, 'D MMM YYYY, HH:mm') }}
        <template v-if="message.from_person">
          · {{ __('answer by writing to the person') }}
        </template>
        <template v-else>
          · {{ message.kind === 'Care' ? __('Care') : __('Front desk') }} ·
          {{
            message.read_on
              ? __('read {0}', [formatDate(message.read_on, 'D MMM YYYY')])
              : __('not read yet')
          }}
        </template>
      </span>
    </div>
  </section>
</template>

<script setup>
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  ErrorMessage,
  FeatherIcon,
  Textarea,
  call,
  createResource,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const board = createResource({
  url: 'crm.area.messaggi.get_messages',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && board.reload(),
  { immediate: true },
)

const draft = ref('')
const busy = ref(false)
const error = ref('')

async function post() {
  busy.value = true
  error.value = ''
  try {
    board.data = await call('crm.area.messaggi.post_message', {
      lead: props.lead,
      body: draft.value,
    })
    draft.value = ''
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}

// the file the person attached, opened through the board's own call
function attachmentUrl(message) {
  return `/api/method/crm.area.messaggi.attachment?${new URLSearchParams({ message: message.name })}`
}
</script>
