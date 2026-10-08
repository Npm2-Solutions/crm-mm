<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Your data: people and appointments brought over from
  the previous software, a sheet read and shown row by row before anything is
  written (crm/importazione, ImportAppointments.vue); everything the centre
  keeps taken away in one archive
  (crm/esportazione), made in a job, its progress by the socket and asked again
  while it runs, kept a week for whoever asked.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div class="flex min-w-0 flex-col gap-1 px-2">
      <h2
        class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
      >
        {{ __('Your data') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            "The centre's data are the centre's: bring them over from the previous software, take them all away whenever you want.",
          )
        }}
      </p>
    </div>

    <div class="flex flex-1 flex-col gap-10 overflow-y-auto px-2 pb-2">
      <!-- the previous software's people, in -->
      <section v-if="puo('persone.importa')" class="flex flex-col gap-3">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __('Bring your people over') }}
        </h3>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Export the patients or clients from the previous software as Excel or CSV, and upload the file here. {brand} recognises the columns, shows what it found row by row, and writes nothing until you confirm. Somebody already here, by fiscal code, email or mobile, is not made twice.',
            )
          }}
        </p>
        <FileUploader
          :uploadArgs="{ private: true }"
          :fileTypes="['.xlsx', '.xls', '.csv', '.txt']"
          @success="scelto"
        >
          <template #default="{ openFileSelector, uploading, progress }">
            <div class="flex min-w-0 flex-wrap items-center gap-2">
              <Button
                icon-left="upload"
                :label="
                  uploading
                    ? __('Uploading {0}%', [progress])
                    : foglio
                      ? __('Choose another file')
                      : __('Choose the file')
                "
                :disabled="importando"
                @click="openFileSelector"
              />
              <span
                v-if="foglio"
                class="min-w-0 truncate text-sm text-ink-gray-7"
              >
                {{ foglio.file_name }}
              </span>
            </div>
          </template>
        </FileUploader>

        <LoadingIndicator v-if="anteprima.loading" class="size-4" />
        <div v-else-if="anteprima.data" class="flex flex-col gap-3">
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="colonna in anteprima.data.columns"
              :key="colonna.name"
              :theme="colonna.field ? 'green' : 'gray'"
              :label="
                colonna.field
                  ? `${colonna.name} → ${__(CAMPI[colonna.field])}`
                  : __('{0}: not read', [colonna.name])
              "
            />
          </div>
          <p class="text-p-sm text-ink-gray-7">
            {{
              __(
                '{0} rows: {1} already here, completed only where empty; {2} with something to check.',
                [
                  anteprima.data.total,
                  anteprima.data.found,
                  anteprima.data.with_problems,
                ],
              )
            }}
          </p>
          <div class="overflow-x-auto">
            <table class="w-full min-w-[36rem] text-left text-p-sm">
              <thead class="text-ink-gray-6">
                <tr>
                  <th class="py-1 pr-3 font-normal">{{ __('Row') }}</th>
                  <th class="py-1 pr-3 font-normal">{{ __('Name') }}</th>
                  <th class="py-1 pr-3 font-normal">{{ __('Contacts') }}</th>
                  <th class="py-1 pr-3 font-normal">
                    {{ __('Fiscal code') }}
                  </th>
                  <th class="py-1 font-normal">{{ __('What happens') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1 text-ink-gray-8">
                <tr v-for="riga in anteprima.data.rows" :key="riga.row">
                  <td class="py-1.5 pr-3 text-ink-gray-6">{{ riga.row }}</td>
                  <td class="py-1.5 pr-3">{{ riga.name }}</td>
                  <td class="py-1.5 pr-3">
                    {{ [riga.email, riga.mobile].filter(Boolean).join(' · ') }}
                  </td>
                  <td class="py-1.5 pr-3">{{ riga.fiscal_code }}</td>
                  <td class="py-1.5">
                    <span v-if="riga.problems.length" class="text-ink-amber-8">
                      {{ riga.problems.join('; ') }}
                    </span>
                    <span v-else-if="riga.found" class="text-ink-gray-6">
                      {{ __('Already here') }}
                    </span>
                    <span v-else class="text-ink-gray-6">{{ __('New') }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <Button
              variant="solid"
              :label="__('Bring them in')"
              :loading="avvia.loading"
              :disabled="importando"
              @click="avvia.submit({ file_url: foglio.file_url })"
            />
            <span v-if="importando" class="text-p-sm text-ink-gray-6">
              {{ __('Bringing them in… you can keep working.') }}
            </span>
          </div>
        </div>
      </section>

      <!-- the previous software's agenda, in -->
      <ImportAppointments v-if="puo('persone.importa')" />

      <!-- everything, out -->
      <section
        v-if="puo('dati.esporta') && exports.data"
        class="flex flex-col gap-4"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex min-w-[15rem] flex-1 flex-col gap-1">
            <h3 class="text-base-semibold text-ink-gray-8">
              {{ __("Take the centre's data away") }}
            </h3>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'One archive with people, appointments, records, documents, invoices and their files, in formats any program reads.',
                )
              }}
            </p>
          </div>
          <Button
            v-if="!exports.data.running"
            class="shrink-0"
            :label="__('Make the archive')"
            :loading="start.loading"
            @click="start.submit({ with_files: conFile ? 1 : 0 })"
          />
        </div>

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

        <div
          v-if="exports.data.running"
          class="flex flex-col gap-3 rounded-lg bg-surface-gray-2 px-4 py-4"
          role="status"
        >
          <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
            <LoadingIndicator class="size-4 shrink-0" />
            <span>{{ __('Making the archive…') }}</span>
          </div>
          <div
            v-if="exports.data.running.total"
            class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-4"
          >
            <div
              class="h-full rounded-full bg-[var(--brand-segno,currentColor)] transition-[width] duration-500"
              :style="{ width: `${percentuale}%` }"
            />
          </div>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'You can keep working: the archive appears here when it is ready.',
              )
            }}
          </p>
        </div>

        <div class="flex flex-col gap-2">
          <h4 class="text-base-medium text-ink-gray-8">
            {{ __('Archives ready') }}
          </h4>
          <p
            v-if="!exports.data.ready.length"
            class="text-p-sm text-ink-gray-6"
          >
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
                  {{
                    __('kept until {0}', [formatDate(pronto.until, 'D MMM')])
                  }}
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
        </div>

        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'The archive holds health data: keep it as you keep the clinical record. Each archive made stays in the access log, and goes after {0} days.',
              [exports.data.days],
            )
          }}
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import ImportAppointments from '@/components/Settings/ImportAppointments.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { spazio } from '@/utils/funzionalita'
import { appLocale } from '@/utils/locale'
import {
  Badge,
  Button,
  createResource,
  FileUploader,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const EVENTO = 'crm_esportazione'
const EVENTO_IMPORTAZIONE = 'crm_importazione'
const { puo } = usersStore()

// a person's field, as the preview names a column it recognised
const CAMPI = {
  full_name: 'Full name',
  first_name: 'First name',
  last_name: 'Last name',
  email: 'Email',
  mobile_no: 'Mobile',
  phone: 'Phone',
  fiscal_code: 'Fiscal code',
  birth_date: 'Date of birth',
  sex: 'Sex',
  address_line: 'Address',
  civic_number: 'Street number',
  postal_code: 'Postal code',
  city: 'City',
  province: 'Province',
  notes: 'Notes',
  external_id: 'Code in the previous software',
}

// ------------------------------------------------------------------ in

const foglio = ref(null)
const importando = ref(false)

const anteprima = createResource({
  url: 'crm.importazione.importa.preview',
  onSuccess(data) {
    importando.value = Boolean(data.running)
  },
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

function scelto(file) {
  foglio.value = file
  anteprima.submit({ file_url: file.file_url })
}

const avvia = createResource({
  url: 'crm.importazione.importa.start',
  onSuccess() {
    importando.value = true
  },
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

function importati(dati) {
  if (dati.state !== 'done') return
  importando.value = false
  toast.success(
    __('{0} new people, {1} completed, {2} rows left out, {3} not brought in', [
      dati.created,
      dati.updated,
      dati.skipped,
      dati.errors?.length || 0,
    ]),
  )
}

// ------------------------------------------------------------------ out

const conFile = ref(true)

const exports = createResource({
  url: 'crm.esportazione.esporta.get_exports',
  auto: puo('dati.esporta'),
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
  globalStore().$socket.on(EVENTO_IMPORTAZIONE, importati)
  timer = setInterval(() => {
    if (exports.data?.running) exports.reload()
  }, 10000)
})

onBeforeUnmount(() => {
  globalStore().$socket.off(EVENTO, ascolta)
  globalStore().$socket.off(EVENTO_IMPORTAZIONE, importati)
  clearInterval(timer)
})
</script>
