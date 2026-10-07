<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Your data: the manager takes everything the centre
  keeps away, in one archive (crm/esportazione). Made in a job, its progress by
  the socket and asked again while it runs; kept a week for whoever asked.
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
          {{ __('Your data') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              "The centre's data are the centre's. Take them all away in one archive, whenever you want: people, appointments, records, documents, invoices and their files.",
            )
          }}
        </p>
      </div>
      <AzioneImpostazioni
        v-if="exports.data && !exports.data.running"
        class="shrink-0"
        :label="__('Make the archive')"
        :loading="start.loading"
        @click="start.submit({ with_files: conFile ? 1 : 0 })"
      />
    </div>

    <div
      v-if="exports.data"
      class="flex flex-1 flex-col gap-6 overflow-y-auto px-2 pb-2"
    >
      <SettingsRow
        v-if="!exports.data.running"
        :label="__('With the files')"
        :description="
          __(
            'The attached files too: reports, signed forms, images. A centre with many takes longer.',
          )
        "
      >
        <Switch v-model="conFile" />
      </SettingsRow>

      <section
        v-if="exports.data.running"
        class="flex flex-col gap-3 rounded-lg bg-surface-gray-2 px-4 py-4"
        role="status"
      >
        <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
          <LoadingIndicator class="size-4 shrink-0" />
          <span>{{ __('Making the archive…') }}</span>
        </div>
        <div v-if="exports.data.running.total" class="flex flex-col gap-1.5">
          <div
            class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-4"
          >
            <div
              class="h-full rounded-full bg-[var(--brand-segno,currentColor)] transition-[width] duration-500"
              :style="{ width: `${percentuale}%` }"
            />
          </div>
        </div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'You can keep working: the archive appears here when it is ready.',
            )
          }}
        </p>
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __('Archives ready') }}
        </h3>
        <p v-if="!exports.data.ready.length" class="text-p-sm text-ink-gray-6">
          {{ __('None yet.') }}
        </p>
        <ul v-else class="flex flex-col divide-y divide-outline-gray-1">
          <li
            v-for="pronto in exports.data.ready"
            :key="pronto.name"
            class="flex flex-wrap items-center gap-3 py-3"
          >
            <div class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="truncate text-base-medium text-ink-gray-8">
                {{ formatDate(pronto.creation, 'D MMM YYYY, HH:mm') }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{ spazio(pronto.file_size, appLocale()) }} ·
                {{ __('kept until {0}', [formatDate(pronto.until, 'D MMM')]) }}
              </span>
            </div>
            <Button
              v-if="pronto.mine"
              class="shrink-0"
              :label="__('Download')"
              :link="pronto.file_url"
            />
            <span v-else class="shrink-0 text-p-sm text-ink-gray-6">
              {{ __('Made by a colleague') }}
            </span>
          </li>
        </ul>
      </section>

      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'The archive holds health data: keep it as you keep the clinical record. Each archive made stays in the access log, and goes after {0} days.',
            [exports.data.days],
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import { spazio } from '@/utils/funzionalita'
import { appLocale } from '@/utils/locale'
import {
  Button,
  createResource,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const EVENTO = 'crm_esportazione'
const conFile = ref(true)

const exports = createResource({
  url: 'crm.esportazione.esporta.get_exports',
  auto: true,
})

const start = createResource({
  url: 'crm.esportazione.esporta.start_export',
  onSuccess: (data) => exports.setData(data),
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

const percentuale = computed(() => {
  const { done = 0, total = 0 } = exports.data?.running || {}
  return total ? Math.round((done / total) * 100) : 0
})

// the job tells by the socket; asked again while it runs, the socket may not be there
let timer = null
function ascolta(dati) {
  if (dati.state === 'error') {
    toast.error(__('The archive could not be made: the agency has been told'))
  }
  exports.reload()
}

onMounted(() => {
  globalStore().$socket.on(EVENTO, ascolta)
  timer = setInterval(() => {
    if (exports.data?.running) exports.reload()
  }, 10000)
})

onBeforeUnmount(() => {
  globalStore().$socket.off(EVENTO, ascolta)
  clearInterval(timer)
})
</script>
