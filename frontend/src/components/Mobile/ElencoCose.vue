<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What is left to do, on a phone (docs/crm/29): one's own or
  everybody's, by when it is due - late, today, tomorrow, later, without a day
  - with whom it is about. One tap on the circle marks it done, with a moment
  to take it back; a tap on the words opens it.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TabButtons v-model="di" :options="opzioni" class="w-full" />
    </div>

    <div ref="contenitore" class="min-h-0 flex-1 overflow-y-auto pb-20">
      <!-- pulled down from the top, the list reloads -->
      <TiraPerAggiornare v-bind="tira" />
      <section v-for="gruppo in gruppi" :key="gruppo.key" class="pb-2">
        <!-- the second level, under the page's own name -->
        <h2
          class="sticky top-0 z-[1] bg-surface-base px-3 pb-1 pt-3 text-xs font-medium uppercase tracking-wide"
          :class="gruppo.key === 'late' ? 'text-ink-red-6' : 'text-ink-gray-5'"
        >
          {{ __(gruppo.label) }} · {{ gruppo.rows.length }}
        </h2>
        <div
          v-for="cosa in gruppo.rows"
          :key="cosa.name"
          class="flex items-start gap-2 border-b border-outline-gray-1 px-3 py-2.5"
        >
          <button
            v-if="!solaLettura()"
            type="button"
            class="touch-target mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border-2 border-outline-gray-3 active:bg-surface-gray-3"
            :aria-label="__('Mark done: {0}', [cosa.title])"
            @click="fatta(cosa)"
          />
          <span
            v-else
            class="mt-0.5 size-6 shrink-0 rounded-full border-2 border-outline-gray-2"
            aria-hidden="true"
          />
          <!-- the whole height of the row opens it: a task with no day nor
               person was a line of words 16px tall to hit -->
          <button
            type="button"
            class="-my-2.5 flex min-w-0 flex-1 flex-col py-2.5 text-left"
            @click="emit('apri', cosa.name)"
          >
            <span class="text-base text-ink-gray-9">{{ cosa.title }}</span>
            <span
              class="flex flex-wrap items-center gap-x-2 text-p-sm text-ink-gray-5"
            >
              <span
                v-if="cosa.due_date"
                :class="gruppo.key === 'late' && 'text-ink-red-6'"
              >
                {{ scadenzaInBreve(cosa.due_date, lingua, adesso) }}
              </span>
              <span v-if="cosa.reference_title" class="truncate">
                {{ cosa.reference_title }}
              </span>
              <span v-if="cosa.priority === 'High'" class="text-ink-amber-7">
                {{ __('High') }}
              </span>
            </span>
          </button>
          <Avatar
            v-if="di === 'tutti' && cosa.assigned_to"
            :image="getUser(cosa.assigned_to)?.user_image"
            :label="getUser(cosa.assigned_to)?.full_name || cosa.assigned_to"
            size="sm"
            class="mt-0.5 shrink-0"
          />
        </div>
      </section>

      <div
        v-if="carica.loading && !righe.length"
        class="flex justify-center py-10"
      >
        <LoaderMark />
      </div>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="
          di === 'mie' ? __('Nothing left for you') : __('Nothing left to do')
        "
        :text="
          solaLettura()
            ? ''
            : __(
                'A call to make, a document to send: add it with the + button.',
              )
        "
      />
      <p
        v-if="carica.data?.more"
        class="px-6 py-4 text-center text-p-sm text-ink-gray-5"
      >
        {{ __('More are open: the computer shows them all.') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { appLocale } from '@/utils/locale'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { useRitorno } from '@/composables/ritorno'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import { usersStore } from '@/stores/users'
import { adessoDelCentro } from '@/utils/scheduler'
import { cosePerGruppo, scadenzaInBreve } from '@/utils/sulTelefono'
import { Avatar, TabButtons, call, createResource, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const emit = defineEmits(['apri'])
const { getUser, solaLettura } = usersStore()
// the user's language, the European way (utils/locale.js)
const lingua = appLocale() || 'it-IT'

const di = ref('mie')
const opzioni = [
  { label: __('Mine', null, 'Tasks'), value: 'mie' },
  { label: __('Everybody’s'), value: 'tutti' },
]

const righe = ref([])
const carica = createResource({
  url: 'crm.api.sul_telefono.get_tasks',
  onSuccess: (dati) => {
    adesso.value = adessoDelCentro()
    righe.value = dati.rows
  },
})
// late, today, tomorrow on the centre's clock, as the Desk reads the due dates;
// taken again with the tasks
const adesso = ref(adessoDelCentro())
const gruppi = computed(() => cosePerGruppo(righe.value, adesso.value))

function ricarica() {
  return carica.submit({ mine: di.value === 'mie' ? 1 : 0 })
}
const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, ricarica)
// back from a task's page: whose tasks, the tasks and where the list was, at
// once; then brought up to date
useRitorno('cose', {
  contenitore,
  stato: () => ({ di: di.value, righe: righe.value }),
  rimetti: (salvato) => {
    di.value = salvato.di
    righe.value = salvato.righe
  },
})
watch(di, ricarica)
ricarica()

async function imposta(cosa, stato) {
  await call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: cosa.name,
    fieldname: 'status',
    value: stato,
  })
}

// done at once; the toast gives it back for a few seconds
async function fatta(cosa) {
  const prima = cosa.status
  righe.value = righe.value.filter((r) => r.name !== cosa.name)
  try {
    await imposta(cosa, 'Done')
    toast.success(__('Done: {0}', [cosa.title]), {
      action: {
        label: __('Undo'),
        onClick: async () => {
          await imposta(cosa, prima)
          ricarica()
        },
      },
    })
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not mark it done'))
    ricarica()
  }
}

defineExpose({ ricarica })
</script>
