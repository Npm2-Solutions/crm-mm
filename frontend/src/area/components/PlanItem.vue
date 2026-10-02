<!--
  An item of the plan as the patient reads it, and one tap to say it is done: the
  cloud at its side fills with the brand's colour; tapped again, the answer is
  taken back. Done partly, or skipped, is said just below. What is shown is what
  is left to do, never what went wrong: no red.
-->
<template>
  <article class="flex flex-col gap-2 py-3 first:pt-2 last:pb-0">
    <div class="flex items-start gap-3">
      <img
        v-if="item.kind === 'Exercise' && item.image"
        :src="item.image"
        alt=""
        class="size-16 shrink-0 rounded-[12px_12px_12px_2px] bg-[var(--cat-violet-subtle)] object-cover"
        loading="lazy"
      />
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <p class="text-[16px] font-semibold leading-snug text-ink-gray-9">
          {{ describe(item) }}
        </p>
        <p v-if="item.alternatives" class="text-p-sm text-ink-gray-6">
          {{ __('Or instead: {0}', [item.alternatives]) }}
        </p>
        <p v-if="item.kcal" class="text-p-sm text-ink-gray-5">
          {{ item.kcal }} kcal
        </p>
        <p
          v-if="item.note"
          class="whitespace-pre-line text-p-sm text-ink-gray-6"
        >
          {{ item.note }}
        </p>
        <p v-if="item.left_this_week != null" class="text-p-sm text-ink-gray-6">
          {{
            item.left_this_week
              ? __('Still {0} this week', [item.left_this_week])
              : __('Done for this week')
          }}
        </p>
        <span
          v-if="!canLog && STATI[item.outcome]"
          class="area-state mt-1 w-fit"
          :class="STATI[item.outcome]"
        >
          {{ labels[item.outcome] }}
        </span>
      </div>
      <button
        v-if="canLog"
        type="button"
        class="area-check touch-target"
        :class="{ 'is-done': item.outcome === 'Done' }"
        :aria-pressed="item.outcome === 'Done'"
        :aria-label="labels.Done"
        :disabled="busy"
        @click="$emit('log', item.outcome === 'Done' ? null : 'Done')"
      >
        <LucideCheck aria-hidden="true" />
      </button>
      <span
        v-else-if="item.outcome === 'Done'"
        class="area-check is-done"
        role="img"
        :aria-label="labels.Done"
      >
        <LucideCheck aria-hidden="true" />
      </span>
    </div>

    <!-- not quite: partly, or skipped - a fact, not a fault; once done, the
         tick alone says it, and tapped again it gives these back -->
    <div
      v-if="canLog && item.outcome !== 'Done'"
      class="flex flex-wrap gap-1.5"
    >
      <button
        v-for="outcome in ['Partly', 'Skipped']"
        :key="outcome"
        type="button"
        class="area-answer touch-target"
        :class="item.outcome === outcome ? STATI[outcome] : ''"
        :aria-pressed="item.outcome === outcome"
        :disabled="busy"
        @click="$emit('log', item.outcome === outcome ? null : outcome)"
      >
        {{ labels[outcome] }}
      </button>
    </div>

    <!-- an exchange diet: the patient chooses, a portion each -->
    <details v-if="item.choices?.length" class="text-p-sm text-ink-gray-7">
      <summary class="area-link cursor-pointer">
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
      <summary class="area-link cursor-pointer">
        {{ __('How to do it') }}
      </summary>
      <div class="mt-2 flex flex-col gap-2">
        <img
          v-if="item.image"
          :src="item.image"
          alt=""
          class="max-h-56 w-full rounded-[16px_16px_16px_2px] bg-[var(--cat-violet-subtle)] object-contain"
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
          class="area-link w-fit"
        >
          {{ __('Watch the video') }}
        </a>
        <p v-if="item.attribution" class="text-p-xs text-ink-gray-5">
          {{ item.attribution }}
        </p>
      </div>
    </details>
  </article>
</template>

<script setup>
import { descrivi } from '@/utils/piani'
import LucideCheck from '~icons/lucide/check'

defineProps({
  item: { type: Object, required: true },
  canLog: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
})
defineEmits(['log'])

const labels = {
  Done: __('Done'),
  Partly: __('Partly'),
  Skipped: __('Skipped'),
}

// the look of an answer that is not "done", whole for the build to keep it
const STATI = {
  Partly: 'area-state--partly',
  Skipped: 'area-state--skipped',
}

function describe(item) {
  return descrivi(item, (text, args) => __(text, args))
}
</script>
