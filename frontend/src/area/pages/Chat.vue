<!--
  The centre's virtual assistant, an AI: hours, bookings and the centre's frequent
  questions, from what the centre wrote. It says so above the conversation and on
  every answer. Health is a person's: the question can be passed to the centre,
  whose answer comes in Messages; an emergency gets 112 at once. The conversation
  stays in this page: nothing of it is kept but each answer in the centre's
  register.
-->
<template>
  <div class="flex min-h-full flex-col gap-4">
    <div class="flex flex-col gap-1">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Ask the centre') }}
      </h1>
      <p
        class="rounded-lg bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
      >
        {{
          __(
            'This is the centre’s virtual assistant, an AI, not a person. It answers about opening hours, bookings and the centre’s frequent questions. It does not answer about your health: it offers to pass your question to a person. In an emergency call 112.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-col gap-3" aria-live="polite">
      <div
        v-for="(turn, index) in turns"
        :key="index"
        class="flex flex-col gap-1"
        :class="turn.role === 'person' ? 'items-end' : 'items-start'"
      >
        <div
          class="max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-p-base"
          :class="bubble(turn)"
        >
          {{ turn.text }}
          <a
            v-if="turn.kind === 'emergency'"
            href="tel:112"
            class="mt-2 block font-semibold underline"
          >
            {{ __('Call 112') }}
          </a>
        </div>
        <span
          v-if="turn.role === 'assistant'"
          class="px-1 text-p-xs text-ink-gray-5"
        >
          {{
            turn.kind === 'answer' ? __('AI answer') : __('Automatic answer')
          }}
        </span>
        <div v-if="turn.canPass" class="px-1">
          <Button
            v-if="!turn.passed"
            :label="__('Pass my question to the centre')"
            :loading="passing === index"
            @click="pass(index)"
          />
          <span v-else class="text-p-sm text-ink-gray-7">
            {{ __('Passed to the centre: the answer comes in') }}
            <router-link
              :to="{ name: 'Messages' }"
              class="underline underline-offset-2"
            >
              {{ __('Messages') }}
            </router-link>
          </span>
        </div>
      </div>
      <div v-if="asking" class="flex items-start">
        <div
          class="rounded-2xl bg-surface-elevation-1 px-4 py-2.5 text-p-base text-ink-gray-5 shadow-sm"
        >
          {{ __('Writing…') }}
        </div>
      </div>
    </div>
    <ErrorMessage :message="error" />

    <!-- the centre's preview asks nothing: a question would reach the model -->
    <p
      v-if="anteprima"
      class="mt-auto rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
    >
      {{ __('In the preview the chat does not answer.') }}
    </p>
    <form
      v-else
      class="sticky bottom-0 mt-auto flex items-end gap-2 bg-surface-gray-1 py-2"
      @submit.prevent="send"
    >
      <div class="min-w-0 flex-1">
        <Textarea
          v-model="draft"
          :rows="2"
          :maxlength="500"
          :placeholder="__('Your question about hours or bookings')"
          :aria-label="__('Your question')"
          @keydown.enter.exact.prevent="send"
        />
      </div>
      <Button
        type="submit"
        variant="solid"
        size="md"
        class="shrink-0"
        :label="__('Send')"
        :disabled="!draft.trim() || asking"
      />
    </form>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, Textarea, call } from 'frappe-ui'
import { ref } from 'vue'
import { anteprima } from '../anteprima'
import { area } from '../store'

const turns = ref([])
const draft = ref('')
const asking = ref(false)
const passing = ref(null)
const error = ref('')

function bubble(turn) {
  if (turn.role === 'person') return 'bg-surface-gray-3 text-ink-gray-9'
  if (turn.kind === 'emergency')
    return 'bg-surface-red-2 text-ink-red-4 font-medium'
  return 'bg-surface-elevation-1 text-ink-gray-9 shadow-sm'
}

async function send() {
  const question = draft.value.trim()
  if (!question || asking.value) return
  // what was said before goes with it: the words, not who said them
  const history = turns.value.map((t) => ({ role: t.role, text: t.text }))
  turns.value.push({ role: 'person', text: question })
  draft.value = ''
  asking.value = true
  error.value = ''
  try {
    const answer = await call('crm.area.chat.ask', {
      person: area.person,
      question,
      history: JSON.stringify(history),
    })
    turns.value.push({
      role: 'assistant',
      text: answer.answer,
      kind: answer.kind,
      canPass: answer.can_pass,
      question,
      passed: false,
    })
  } catch (e) {
    error.value = e.messages?.[0] || e.message
  } finally {
    asking.value = false
  }
}

async function pass(index) {
  const turn = turns.value[index]
  passing.value = index
  error.value = ''
  try {
    await call('crm.area.chat.pass_on', {
      person: area.person,
      question: turn.question,
    })
    turn.passed = true
  } catch (e) {
    error.value = e.messages?.[0] || e.message
  } finally {
    passing.value = null
  }
}
</script>
