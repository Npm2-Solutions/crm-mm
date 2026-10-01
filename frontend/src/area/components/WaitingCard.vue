<!--
  What the person waits for. When a place freed up for them, it says which and
  until when it is theirs to take: yes books it, no gives it to the next one,
  and they stay on the list. They can leave it too. How it went, the page says.
-->
<template>
  <article
    class="flex flex-col gap-2 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <div class="flex items-start justify-between gap-2">
      <h3 class="min-w-0 text-base font-medium text-ink-gray-9">
        {{ entry.service }}
      </h3>
      <Badge
        class="shrink-0"
        variant="subtle"
        :theme="entry.offer?.can_answer ? 'blue' : 'orange'"
        :label="entry.offer?.can_answer ? __('A place for you') : __('Waiting')"
      />
    </div>
    <p class="text-p-sm text-ink-gray-6">
      {{ line }}
    </p>

    <div
      v-if="entry.offer?.can_answer"
      class="flex flex-col gap-2 rounded-md bg-surface-gray-2 p-3"
    >
      <span
        class="text-p-base font-medium text-ink-gray-9 first-letter:uppercase"
      >
        {{ when(entry.offer.starts_on) }}
      </span>
      <span v-if="entry.offer.staff" class="text-p-sm text-ink-gray-7">
        {{ __('With {0}', [entry.offer.staff]) }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __('It is yours if you confirm by {0}', [
            when(entry.offer.expires_on),
          ])
        }}
      </span>
      <div v-if="!anteprima" class="flex flex-wrap gap-2">
        <Button
          variant="solid"
          :label="__('Yes, book it')"
          :loading="busy === 'yes'"
          @click="answer('yes')"
        />
        <Button
          :label="__('No thanks')"
          :loading="busy === 'no'"
          @click="answer('no')"
        />
      </div>
    </div>
    <p v-else class="text-p-sm text-ink-gray-5">
      {{
        __(
          'When a place frees up we write to you: it goes to whoever confirms first.',
        )
      }}
    </p>

    <ErrorMessage :message="error" />
    <button
      v-if="!anteprima"
      type="button"
      class="touch-target w-fit text-p-sm text-ink-gray-6 underline underline-offset-2"
      :disabled="busy === 'leave'"
      @click="leave"
    >
      {{ __('Leave the waiting list') }}
    </button>
  </article>
</template>

<script setup>
import { quandoPuo } from '@/utils/attese'
import { Badge, Button, ErrorMessage, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { anteprima } from '../anteprima'
import { day, when } from '../dates'
import { area, messageOf } from '../store'
import { locale } from '../translation'

const props = defineProps({ entry: { type: Object, required: true } })
const emit = defineEmits(['changed'])

const busy = ref('')
const error = ref('')
const t = (text, args) => __(text, args)

const line = computed(() => {
  const parts = [
    props.entry.class_starts_on
      ? __('A seat in the class of {0}', [when(props.entry.class_starts_on)])
      : quandoPuo(props.entry, t, locale),
  ]
  if (props.entry.staff) parts.push(__('With {0}', [props.entry.staff]))
  if (props.entry.until) parts.push(__('until {0}', [day(props.entry.until)]))
  return parts.join(' · ')
})

const WORDS = {
  booked: 'Booked: you find it among your appointments.',
  taken:
    'Somebody confirmed before you: the place has gone. You are still on the list.',
  expired:
    'The time to answer has passed: the place went to the next person. You are still on the list.',
  declined:
    'Fine: the place goes to the next person. You keep your place on the list.',
}

async function answer(what) {
  busy.value = what
  error.value = ''
  try {
    const done = await call('crm.area.api.answer_waiting_offer', {
      person: area.person,
      entry: props.entry.name,
      answer: what,
    })
    // said by the page: a place booked takes the card away with it
    emit('changed', WORDS[done.result] ? __(WORDS[done.result]) : '')
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = ''
  }
}

async function leave() {
  busy.value = 'leave'
  error.value = ''
  try {
    await call('crm.area.api.leave_waiting_list', {
      person: area.person,
      entry: props.entry.name,
    })
    emit(
      'changed',
      __('You are no longer on the waiting list for {0}.', [
        props.entry.service,
      ]),
    )
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = ''
  }
}
</script>
