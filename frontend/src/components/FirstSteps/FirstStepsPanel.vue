<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The first steps (doc 37): what the centre does to start, in order, each saying
  what it is for and ticked by itself once the centre's data says it is done; a
  step opens where it is taken. Beside the page on a desktop, the whole screen
  on a phone.
-->
<template>
  <div
    v-if="aperto"
    class="fixed z-50 flex flex-col bg-surface-elevation-2 text-ink-gray-9 shadow-2xl"
    :class="
      isMobileView
        ? 'inset-0'
        : 'right-0 top-0 m-5 mt-[62px] h-[calc(100%_-_80px)] w-96 rounded-lg'
    "
    role="dialog"
    :aria-label="__('First steps')"
    @keydown.esc="aperto = false"
  >
    <div class="flex items-start justify-between gap-3 px-5 pb-3 pt-4">
      <div class="flex min-w-0 flex-col gap-1">
        <h2 class="text-lg-semibold text-ink-gray-9">
          {{ __('First steps') }}
        </h2>
        <p class="text-p-sm text-ink-gray-6">
          {{
            stato.finiti
              ? __('The centre is ready. Have a good day at work!')
              : __(
                  'What to do to start with {brand}: each step ticks itself once it is done.',
                )
          }}
        </p>
      </div>
      <Button
        ref="chiudi"
        variant="ghost"
        icon="x"
        class="shrink-0"
        :aria-label="__('Close')"
        @click="aperto = false"
      />
    </div>
    <div class="flex items-center gap-3 px-5 pb-3">
      <div
        class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-gray-3"
        role="progressbar"
        :aria-label="__('First steps')"
        :aria-valuenow="stato.percentuale"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          class="h-full rounded-full bg-[var(--brand-segno)] transition-[width] duration-300"
          :style="{ width: `${stato.percentuale}%` }"
        />
      </div>
      <span class="shrink-0 text-p-sm text-ink-gray-6">
        {{ __('{0} of {1} done', [stato.fatti, stato.totale]) }}
      </span>
    </div>
    <ol class="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-3">
      <li v-for="passo in passi.data?.steps || []" :key="passo.key">
        <button
          type="button"
          class="flex w-full items-start gap-3 rounded-md px-2 py-2.5 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
          :class="passo.key === stato.prossimo?.key && 'bg-surface-gray-1'"
          @click="fai(passo)"
        >
          <span
            class="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full"
            :class="
              passo.done
                ? 'bg-[var(--brand-segno)] text-ink-base'
                : 'border border-outline-gray-3'
            "
          >
            <LucideCheck
              v-if="passo.done"
              class="size-3.5"
              :aria-label="__('Done')"
            />
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span
              class="text-base-medium"
              :class="passo.done ? 'text-ink-gray-5' : 'text-ink-gray-8'"
            >
              {{ passo.title }}
            </span>
            <span class="text-p-sm text-ink-gray-5">{{ passo.why }}</span>
          </span>
          <span
            class="lucide-chevron-right mt-0.5 size-4 shrink-0 text-ink-gray-4"
            aria-hidden="true"
          />
        </button>
      </li>
    </ol>
    <div
      v-if="!stato.finiti"
      class="flex flex-col gap-1 border-t border-outline-gray-2 px-5 py-3"
    >
      <Button
        variant="ghost"
        class="self-start"
        :label="__('Hide the first steps')"
        @click="nascondi"
      />
      <p v-if="puo('piano.vedi')" class="text-p-sm text-ink-gray-5">
        {{ __('You will find them again in Settings, The centre, Features.') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import LucideCheck from '~icons/lucide/check'
import { isMobileView } from '@/composables/settings'
import { pannelloPrimiPassi, usePrimiPassi } from '@/composables/primiPassi'
import { usersStore } from '@/stores/users'
import { nextTick, ref, watch } from 'vue'

const { passi, stato, nascondi, fai } = usePrimiPassi()
const { puo } = usersStore()

const aperto = pannelloPrimiPassi
const chiudi = ref(null)

// the keyboard starts in the panel, on the way out
watch(aperto, async (si) => {
  if (!si) return
  await nextTick()
  chiudi.value?.$el?.focus?.()
})
</script>
