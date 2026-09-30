<!--
  An item of the plan as the patient reads it, and one tap to say how it went:
  done, partly, skipped. Tapped again, the answer is taken back. What is shown is
  what is left to do, never what went wrong.
-->
<template>
  <article
    class="flex flex-col gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <div class="flex flex-col gap-1">
      <p class="text-base text-ink-gray-9">{{ describe(item) }}</p>
      <p v-if="item.alternatives" class="text-p-sm text-ink-gray-6">
        {{ __('Or instead: {0}', [item.alternatives]) }}
      </p>
      <p v-if="item.kcal" class="text-p-sm text-ink-gray-5">
        {{ item.kcal }} kcal
      </p>
      <p v-if="item.note" class="whitespace-pre-line text-p-sm text-ink-gray-6">
        {{ item.note }}
      </p>
      <p v-if="item.left_this_week != null" class="text-p-sm text-ink-gray-6">
        {{
          item.left_this_week
            ? __('Still {0} this week', [item.left_this_week])
            : __('Done for this week')
        }}
      </p>
    </div>

    <!-- an exchange diet: the patient chooses, a portion each -->
    <details v-if="item.choices?.length" class="text-p-sm text-ink-gray-7">
      <summary class="cursor-pointer text-ink-gray-8">
        {{ __('Choose among') }}
      </summary>
      <ul class="mt-2 flex flex-col gap-1">
        <li v-for="choice in item.choices" :key="choice.food_name">
          {{ choice.food_name }}
          <span v-if="choice.portion_g" class="text-ink-gray-5">
            · {{ choice.portion_g }} g
          </span>
        </li>
      </ul>
    </details>

    <details
      v-if="
        item.kind === 'Exercise' &&
        (item.instructions || item.image || item.video_url)
      "
      class="text-p-sm text-ink-gray-7"
    >
      <summary class="cursor-pointer text-ink-gray-8">
        {{ __('How to do it') }}
      </summary>
      <div class="mt-2 flex flex-col gap-2">
        <img
          v-if="item.image"
          :src="item.image"
          alt=""
          class="max-h-48 w-fit rounded-md"
          loading="lazy"
        />
        <p v-if="item.instructions" class="whitespace-pre-line">
          {{ item.instructions }}
        </p>
        <a
          v-if="item.video_url"
          :href="item.video_url"
          target="_blank"
          rel="noopener noreferrer"
          class="w-fit text-ink-gray-9 underline underline-offset-2"
        >
          {{ __('Watch the video') }}
        </a>
        <p v-if="item.attribution" class="text-p-xs text-ink-gray-5">
          {{ item.attribution }}
        </p>
      </div>
    </details>

    <div v-if="canLog" class="grid grid-cols-3 gap-2">
      <button
        v-for="outcome in outcomes"
        :key="outcome"
        type="button"
        class="min-h-11 rounded-md px-2 text-p-sm font-medium transition-colors"
        :class="
          item.outcome === outcome
            ? chosen[outcome]
            : 'bg-surface-gray-2 text-ink-gray-7'
        "
        :aria-pressed="item.outcome === outcome"
        :disabled="busy"
        @click="$emit('log', item.outcome === outcome ? null : outcome)"
      >
        {{ labels[outcome] }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { ESITI, descrivi } from '@/utils/piani'

defineProps({
  item: { type: Object, required: true },
  canLog: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
})
defineEmits(['log'])

const outcomes = ESITI
const labels = {
  Done: __('Done'),
  Partly: __('Partly'),
  Skipped: __('Skipped'),
}
// no red: a skipped item is a fact, not a fault
const chosen = {
  Done: 'bg-surface-green-2 text-ink-green-8',
  Partly: 'bg-surface-amber-2 text-ink-amber-8',
  Skipped: 'bg-surface-gray-4 text-ink-gray-8',
}

function describe(item) {
  return descrivi(item, (text, args) => __(text, args))
}
</script>
