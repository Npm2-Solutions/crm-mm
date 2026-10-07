<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The people on a phone (docs/crm/29): found by typing a name, a number
  written any way, or an email; one line each - who, how to reach them, when
  they come next - and the call a thumb away. The list grows as it scrolls.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        v-bind="tastiera('cerca')"
        size="md"
        :placeholder="
          mascherati ? __('Name or company') : __('Name, number or email')
        "
        :aria-label="__('Search people')"
        autocomplete="off"
      >
        <template #prefix>
          <span
            class="lucide-search size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </TextInput>
      <!-- everybody, or one step: the leads, the clients, the patients - one
           list of people (docs/crm/54) -->
      <div
        v-if="viste.length > 2"
        class="-mx-3 mt-2 overflow-x-auto px-3 [&::-webkit-scrollbar]:h-0"
      >
        <TabButtons
          v-model="rapporto"
          class="w-max"
          :options="viste"
          :aria-label="__('Relationship')"
        />
      </div>
    </div>

    <div
      ref="contenitore"
      class="min-h-0 flex-1 overflow-y-auto pb-20"
      @scroll.passive="forseAltre"
    >
      <!-- pulled down from the top, the list reloads -->
      <TiraPerAggiornare v-bind="tira" />
      <div
        v-for="persona in righe"
        :key="persona.name"
        class="flex items-center border-b border-outline-gray-1"
      >
        <router-link
          :to="{ name: 'Lead', params: { leadId: persona.name } }"
          class="flex min-w-0 flex-1 items-center gap-3 py-2.5 pl-3 active:bg-surface-gray-2"
        >
          <Avatar
            :image="persona.image"
            :label="nomeDi(persona)"
            size="xl"
            class="shrink-0"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <!-- a client or a patient says so beside the name, and wraps
                 under it on a page zoomed (utils/rapporto.js) -->
            <span class="flex min-w-0 flex-wrap items-center gap-x-1.5">
              <span
                class="max-w-full truncate text-base-medium text-ink-gray-9"
              >
                {{ nomeDi(persona) }}
              </span>
              <CategoryTag
                v-if="tonoDel(rapportoDi(persona))"
                class="shrink-0"
                :color="tonoDel(rapportoDi(persona))"
                :label="__(rapportoDi(persona), null, CONTESTO)"
              />
            </span>
            <span
              v-if="contattoDi(persona)"
              class="truncate text-p-sm text-ink-gray-5"
            >
              {{ contattoDi(persona) }}
            </span>
          </span>
          <span
            v-if="torna(persona)"
            class="shrink-0 rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-7"
          >
            {{ torna(persona) }}
          </span>
        </router-link>
        <a
          v-if="numeroDi(persona)"
          :href="indirizzoTel(numeroDi(persona))"
          class="touch-target ml-1 mr-2 flex size-9 shrink-0 items-center justify-center rounded-full text-ink-gray-6 active:bg-surface-gray-3"
          :aria-label="__('Call {0}', [nomeDi(persona)])"
        >
          <span class="lucide-phone size-4" aria-hidden="true" />
        </a>
        <span v-else class="mr-2 size-9 shrink-0" />
      </div>

      <!-- the list's first load is the brand's cross (the design system's
           Progress); more rows coming under the ones there, a spinner -->
      <div
        v-if="carica.loading && !righe.length"
        class="flex justify-center py-10"
      >
        <LoaderMark />
      </div>
      <div v-else-if="carica.loading" class="flex justify-center py-6">
        <LoadingIndicator class="size-5" />
      </div>
      <p
        v-else-if="!righe.length && testo.trim()"
        class="px-6 py-12 text-center text-p-base text-ink-gray-5"
      >
        {{ __('Nobody found for «{0}».', [testo.trim()]) }}
      </p>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="__('No people yet')"
        :text="
          puo('persone.scrivi')
            ? __(
                'Whoever writes, calls or books is here: add one with the + button.',
              )
            : ''
        "
      />
    </div>
  </div>
</template>

<script setup>
import { appLocale } from '@/utils/locale'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useElencoDelTelefono } from '@/composables/elencoDelTelefono'
import { tastiera } from '@/utils/tastiera'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import CategoryTag from '@/components/Espresso/CategoryTag.vue'
import {
  CONTESTO,
  rapportoDi,
  tonoDel,
  vistePerRapporto,
} from '@/utils/rapporto'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { indirizzoTel, mascherato } from '@/utils/schedaPersona'
import { adessoDelCentro } from '@/utils/scheduler'
import { contattoDi, quandoTorna } from '@/utils/sulTelefono'
import { Avatar, LoadingIndicator, TabButtons, TextInput } from 'frappe-ui'
import { computed } from 'vue'

const { puo, ambito } = usersStore()
// whoever reads people masked finds them by name only (the server says so too)
const mascherati = computed(() => ambito('persone.vedi') === 'mascherato')
// the user's language, the European way (utils/locale.js)
const lingua = appLocale() || 'it-IT'

const { testo, filtri, righe, contenitore, carica, cerca, forseAltre, tira } =
  useElencoDelTelefono('crm.api.sul_telefono.get_people', 'persone')

// the steps a person may be at here, as the field has them (the clinic adds
// its patients)
const { doctypeMeta } = getMeta('CRM Lead')
const viste = computed(() =>
  vistePerRapporto(
    (
      doctypeMeta.value?.fields?.find((f) => f.fieldname === 'relationship')
        ?.options || ''
    ).split('\n'),
  ).map((vista) => ({
    label: __(vista.etichetta, null, vista.contesto),
    value: vista.valore,
  })),
)
const rapporto = computed({
  get: () => filtri.value.relationship || '',
  set: (valore) => (filtri.value = valore ? { relationship: valore } : {}),
})

function nomeDi(persona) {
  return persona.lead_name || persona.first_name || persona.name
}

// a masked number (Marketing's) is none to call
function numeroDi(persona) {
  return (
    [persona.mobile_no, persona.phone].find((n) => n && !mascherato(n)) || ''
  )
}

function torna(persona) {
  // today or tomorrow on the centre's clock, as the agenda keeps it
  const quando = quandoTorna(
    persona.next_appointment,
    lingua,
    adessoDelCentro(),
  )
  if (!quando) return ''
  if (quando.quando === 'today') return __('Today {0}', [quando.ora])
  if (quando.quando === 'tomorrow') return __('Tomorrow {0}', [quando.ora])
  return quando.giorno
}

defineExpose({ ricarica: cerca })
</script>
