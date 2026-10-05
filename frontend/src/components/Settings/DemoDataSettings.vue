<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Demo data (doc 53): what the demo holds, loading it (a
  job, its progress by the socket), the parts a module switched on later adds,
  and taking it all away in one tap.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Demo data') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'A centre full of people, appointments and deals to try {brand} on. Taken away in one tap, without a trace.',
            )
          }}
        </p>
      </div>
      <AzioneImpostazioni
        v-if="daFare && !inCorso"
        class="shrink-0"
        :label="caricati ? __('Add the new parts') : __('Load the demo data')"
        @click="loadDemoData"
      />
    </div>

    <div
      v-if="stato.data"
      class="flex flex-1 flex-col gap-8 overflow-y-auto px-2 pb-2"
    >
      <!-- a job is making them -->
      <section
        v-if="inCorso"
        class="flex flex-col gap-3 rounded-lg bg-surface-gray-2 px-4 py-4"
        role="status"
      >
        <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
          <LoadingIndicator class="size-4 shrink-0" />
          <span>{{ __('Making the demo data…') }}</span>
        </div>
        <div v-if="avanzamento?.total" class="flex flex-col gap-1.5">
          <div
            class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-4"
          >
            <div
              class="h-full rounded-full bg-[var(--brand-segno,currentColor)] transition-[width] duration-500"
              :style="{ width: `${percentuale}%` }"
            />
          </div>
          <span class="text-p-sm text-ink-gray-6">
            {{ avanzamento.part }}
            <template v-if="avanzamento.step"
              >· {{ avanzamento.step }}</template
            >
          </span>
        </div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'It takes a couple of minutes: you can keep working, {brand} tells you when they are ready.',
            )
          }}
        </p>
      </section>

      <!-- what is in -->
      <section v-if="caricati && !inCorso" class="flex flex-col gap-3">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __('The demo data are in') }}
        </h3>
        <div class="grid grid-cols-4 gap-3 max-md:grid-cols-2">
          <StatTile
            blocco
            :label="__('People')"
            :value="stato.data.counts?.people || 0"
          />
          <StatTile
            :label="__('Appointments')"
            :value="stato.data.counts?.appointments || 0"
          />
          <StatTile
            :label="__('Deals')"
            :value="stato.data.counts?.deals || 0"
          />
          <StatTile
            :label="__('Colleagues')"
            :value="stato.data.counts?.team || 0"
          />
        </div>
      </section>

      <!-- the parts -->
      <section class="flex flex-col gap-3">
        <div class="flex flex-col gap-0.5">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ caricati ? __('What they hold') : __('What you will find') }}
          </h3>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Each module you switch on adds its own part: load again to add it.',
              )
            }}
          </p>
        </div>
        <ul class="flex flex-col divide-y divide-outline-gray-1">
          <li
            v-for="parte in partiVisibili"
            :key="parte.key"
            class="flex items-start gap-3 py-3"
          >
            <!-- a tick once the part is in; before, only a dot: nothing to
                 choose here, the button makes them all -->
            <span
              v-if="parte.made"
              class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-6"
              :aria-label="__('This part is in')"
              role="img"
            >
              <FeatherIcon name="check" class="size-3" />
            </span>
            <span
              v-else
              class="mt-0.5 flex size-5 shrink-0 items-center justify-center"
              :aria-label="__('This part is not in yet')"
              role="img"
            >
              <span class="size-1.5 rounded-full bg-surface-gray-4" />
            </span>
            <div class="flex min-w-0 flex-col gap-0.5">
              <span class="text-base-medium text-ink-gray-8">
                {{ parte.label }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{ parte.description }}
              </span>
            </div>
          </li>
        </ul>
      </section>

      <!-- nobody is written to -->
      <section
        class="flex items-start gap-3 rounded-lg bg-surface-gray-2 px-4 py-3"
      >
        <FeatherIcon
          name="shield"
          class="mt-0.5 size-4 shrink-0 text-ink-gray-6"
        />
        <div class="flex min-w-0 flex-col gap-0.5">
          <span class="text-base-medium text-ink-gray-8">
            {{ __('Nobody receives anything') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "The demo's people are made up: their addresses receive no email, and {brand} never writes, messages or calls them. Visitors of your booking page do not see the demo's services.",
              )
            }}
          </span>
        </div>
      </section>

      <!-- taking them away -->
      <section
        v-if="caricati && !inCorso"
        class="flex items-center justify-between gap-4 rounded-lg border border-outline-red-2 px-4 py-3 max-md:flex-col max-md:items-stretch"
      >
        <div class="flex min-w-0 flex-col gap-0.5">
          <span class="text-base-medium text-ink-gray-8">
            {{ __('Remove the demo data') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Everything the demo made goes, in a few seconds: you start again from an empty centre.',
              )
            }}
          </span>
        </div>
        <Button
          class="shrink-0"
          theme="red"
          variant="subtle"
          :label="togliendo ? __('Removing…') : __('Remove', null, 'Demo data')"
          :loading="togliendo"
          @click="clearDemoData"
        />
      </section>
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-6 text-ink-gray-5" />
    </div>
  </div>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import StatTile from '@/components/Espresso/StatTile.vue'
import { useDemoData } from '@/composables/demoData'
import { FeatherIcon, LoadingIndicator } from 'frappe-ui'
import { computed, onMounted } from 'vue'

const { stato, avanzamento, togliendo, ascolta, loadDemoData, clearDemoData } =
  useDemoData()

onMounted(() => {
  ascolta()
  stato.reload()
})

const caricati = computed(() => Boolean(stato.data?.demo_data_created))
const inCorso = computed(
  () => Boolean(avanzamento.value) || Boolean(stato.data?.working),
)
const daFare = computed(() => (stato.data?.to_make || []).length > 0)
// the parts of the modules that are on; the others come when their module does
const partiVisibili = computed(() =>
  (stato.data?.parts || []).filter((parte) => parte.available || parte.made),
)
const percentuale = computed(() => {
  const a = avanzamento.value
  if (!a?.total) return 5
  return Math.max(5, Math.round((100 * a.done) / a.total))
})
</script>
