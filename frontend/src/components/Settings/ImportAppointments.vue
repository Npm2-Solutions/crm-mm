<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Your data: the appointments and their history brought
  over from the previous software (crm/importazione/appuntamenti.py). The sheet is
  read and shown row by row; what each service, professional and room it names is
  here is chosen before anything is written; a job brings them in, once, and says
  how it went.
-->
<template>
  <section class="flex flex-col gap-3">
    <h3 class="text-base-semibold text-ink-gray-8">
      {{ __('Bring your appointments over') }}
    </h3>
    <p class="text-p-sm text-ink-gray-6">
      {{
        __(
          'Export the agenda from the previous software as Excel or CSV, the past with the appointments to come. {brand} finds each person as it does when bringing people over, shows what it read, and asks what each service, professional and room is here before writing anything. What is past counts as attended unless the sheet says it was cancelled or missed; nobody is written to, and the same sheet brought in again doubles nothing.',
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
          <span v-if="foglio" class="min-w-0 truncate text-sm text-ink-gray-7">
            {{ foglio.file_name }}
          </span>
        </div>
      </template>
    </FileUploader>

    <LoadingIndicator v-if="anteprima.loading" class="size-4" />
    <div v-else-if="anteprima.data" class="flex flex-col gap-4">
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
      <ul class="flex flex-col gap-0.5 text-p-sm text-ink-gray-7">
        <li>
          {{
            __('{0} rows: {1} to bring in, {2} already brought in.', [
              anteprima.data.total,
              anteprima.data.to_bring,
              anteprima.data.already,
            ])
          }}
        </li>
        <li v-if="anteprima.data.new_people">
          {{
            __('New people, by fiscal code, email or mobile: {0}.', [
              anteprima.data.new_people,
            ])
          }}
        </li>
        <li v-if="anteprima.data.left_out" class="text-ink-amber-8">
          {{
            __('Left out: {0} (no person, day or start time).', [
              anteprima.data.left_out,
            ])
          }}
        </li>
      </ul>

      <!-- what the sheet calls a service, a professional, a room, here -->
      <div
        v-for="tipo in TIPI.filter((t) => anteprima.data[t.chiave]?.length)"
        :key="tipo.chiave"
        class="flex flex-col gap-2"
      >
        <h4 class="text-base-medium text-ink-gray-8">{{ tipo.titolo }}</h4>
        <div
          class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
        >
          <div
            v-for="voce in anteprima.data[tipo.chiave]"
            :key="voce.name"
            class="grid grid-cols-2 items-center gap-3 py-2 impostazioni-strette:grid-cols-1 impostazioni-strette:gap-1.5"
          >
            <span class="min-w-0 text-p-base text-ink-gray-8">
              {{ voce.name || tipo.vuoto }}
              <span class="text-p-sm text-ink-gray-5">
                ·
                {{
                  voce.rows === 1 ? __('1 row') : __('{0} rows', [voce.rows])
                }}
              </span>
            </span>
            <FormControl
              v-model="voce.choice"
              type="select"
              :aria-label="__('What «{0}» is here', [voce.name || tipo.vuoto])"
              :options="
                scelteDi(tipo.chiave, anteprima.data.options[tipo.chiave], __)
              "
            />
          </div>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full min-w-[40rem] text-left text-p-sm">
          <thead class="text-ink-gray-6">
            <tr>
              <th class="py-1 pr-3 font-normal">{{ __('Row') }}</th>
              <th class="py-1 pr-3 font-normal">{{ __('Person') }}</th>
              <th class="py-1 pr-3 font-normal">{{ __('When') }}</th>
              <th class="py-1 pr-3 font-normal">{{ __('Service') }}</th>
              <th class="py-1 pr-3 font-normal">{{ __('How it went') }}</th>
              <th class="py-1 font-normal">{{ __('What happens') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-gray-1 text-ink-gray-8">
            <tr v-for="riga in anteprima.data.rows" :key="riga.row">
              <td class="py-1.5 pr-3 text-ink-gray-6">{{ riga.row }}</td>
              <td class="whitespace-nowrap py-1.5 pr-3">{{ riga.name }}</td>
              <td class="whitespace-nowrap py-1.5 pr-3">
                {{
                  riga.starts_on
                    ? formatDate(riga.starts_on, 'D MMM YYYY, HH:mm')
                    : ''
                }}
              </td>
              <td class="py-1.5 pr-3">
                {{ riga.service }}
                <span v-if="riga.professional" class="text-ink-gray-6">
                  · {{ riga.professional }}
                </span>
              </td>
              <td class="py-1.5 pr-3">
                {{
                  riga.starts_on ? statoDellAppuntamento(riga.status, __) : ''
                }}
              </td>
              <td class="py-1.5">
                <span
                  :class="
                    riga.outcome === 'left_out' ||
                    riga.outcome === 'nobody' ||
                    riga.problems.length
                      ? 'text-ink-amber-8'
                      : 'text-ink-gray-6'
                  "
                >
                  {{ esitoDellaRiga(riga, __) }}
                </span>
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
          :disabled="importando || !anteprima.data.to_bring"
          @click="porta"
        />
        <span v-if="importando" class="text-p-sm text-ink-gray-6">
          {{ __('Bringing them in… you can keep working.') }}
        </span>
      </div>
    </div>

    <div
      v-if="rapporto && !importando"
      class="flex flex-col gap-1.5 rounded-lg bg-surface-gray-2 px-4 py-3"
      role="status"
    >
      <span class="text-base-medium text-ink-gray-8">
        {{ __('The last sheet brought in') }}
      </span>
      <span class="text-p-sm text-ink-gray-7">{{ rapporto.frase }}</span>
      <ul
        v-if="rapporto.errori.length"
        class="flex flex-col gap-0.5 text-p-sm text-ink-amber-8"
      >
        <li v-for="errore in rapporto.errori.slice(0, 10)" :key="errore">
          {{ errore }}
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  CAMPI,
  esitoDellaRiga,
  resoconto,
  scelteDaMandare,
  scelteDi,
  statoDellAppuntamento,
} from '@/utils/importaAppuntamenti'
import {
  Badge,
  Button,
  createResource,
  FileUploader,
  FormControl,
  LoadingIndicator,
  toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const EVENTO = 'crm_importazione_appuntamenti'

const TIPI = [
  {
    chiave: 'services',
    titolo: __('The services of the sheet'),
    vuoto: __('No service written'),
  },
  {
    chiave: 'professionals',
    titolo: __('The professionals of the sheet'),
    vuoto: '',
  },
  { chiave: 'rooms', titolo: __('The rooms of the sheet'), vuoto: '' },
]

const foglio = ref(null)
const importando = ref(false)
const ultimo = ref(null)

const anteprima = createResource({
  url: 'crm.importazione.appuntamenti.preview',
  onSuccess(data) {
    importando.value = Boolean(data.running)
    ultimo.value = data.last || ultimo.value
  },
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

const rapporto = computed(() => resoconto(ultimo.value, __))

// a sheet still being brought in, and how the last one went, before any file
createResource({
  url: 'crm.importazione.appuntamenti.get_state',
  auto: true,
  onSuccess(data) {
    importando.value = Boolean(data.running)
    ultimo.value = data.last
  },
})

function scelto(file) {
  foglio.value = file
  anteprima.submit({ file_url: file.file_url })
}

const avvia = createResource({
  url: 'crm.importazione.appuntamenti.start',
  onSuccess() {
    importando.value = true
    ultimo.value = null
  },
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

function porta() {
  avvia.submit({
    file_url: foglio.value.file_url,
    choices: JSON.stringify(scelteDaMandare(anteprima.data)),
  })
}

function portati(dati) {
  if (dati.state !== 'done') return
  importando.value = false
  ultimo.value = dati
  toast.success(resoconto(dati, __).frase)
  // the preview again: what was brought in is «already brought in» now
  if (foglio.value) anteprima.submit({ file_url: foglio.value.file_url })
}

onMounted(() => globalStore().$socket.on(EVENTO, portati))
onBeforeUnmount(() => globalStore().$socket.off(EVENTO, portati))
</script>
