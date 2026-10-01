<!--
  The person's board in their area: what the centre writes to them. Not a chat -
  the person reads and does not answer here. The desk writes administrative
  messages; with the clinic on, a practitioner writes about the care, read like a
  visit. Who enters the area gets an email that says only that there is news.
  A question the person passed on from the area's chat shows here too, marked:
  it is answered by writing to the person.
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
                'From the desk: a reminder, a document to bring. The person reads it in their area.',
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
        v-if="message.kind === 'Question'"
        class="w-fit"
        variant="subtle"
        theme="blue"
        :label="__('A question from the area')"
      />
      <p class="whitespace-pre-line text-p-base text-ink-gray-8">
        {{ message.body }}
      </p>
      <span class="text-p-xs text-ink-gray-5">
        {{ message.author_name }} ·
        {{ formatDate(message.posted_on, 'D MMM YYYY, HH:mm') }}
        <template v-if="message.kind === 'Question'">
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
</script>
