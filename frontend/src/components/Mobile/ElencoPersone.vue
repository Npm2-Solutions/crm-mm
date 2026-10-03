<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The people on a phone (docs/progetto-ghl/34): found by typing a name, a number
  written any way, or an email; one line each - who, how to reach them, when
  they come next - and the call a thumb away. The list grows as it scrolls.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        type="search"
        size="md"
        :placeholder="__('Name, number or email')"
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
    </div>

    <div
      ref="contenitore"
      class="min-h-0 flex-1 overflow-y-auto pb-20"
      @scroll.passive="forseAltre"
    >
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
            <span class="truncate text-base-medium text-ink-gray-9">
              {{ nomeDi(persona) }}
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

      <div v-if="carica.loading" class="flex justify-center py-6">
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
          __(
            'Whoever writes, calls or books is here: add one with the + button.',
          )
        "
      />
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { indirizzoTel } from '@/utils/schedaPersona'
import { contattoDi, quandoTorna } from '@/utils/sulTelefono'
import {
  Avatar,
  LoadingIndicator,
  TextInput,
  createResource,
  debounce,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const lingua = window.navigator?.language || 'it-IT'

const testo = ref('')
const righe = ref([])
const altre = ref(false)
const contenitore = ref(null)

const carica = createResource({
  url: 'crm.api.sul_telefono.get_people',
  onSuccess(dati) {
    righe.value = dati.start ? [...righe.value, ...dati.rows] : dati.rows
    altre.value = dati.more
  },
})

function cerca() {
  carica.submit({ text: testo.value.trim(), start: 0 })
}

const cercaPocoDopo = debounce(cerca, 300)
watch(testo, cercaPocoDopo)
cerca()

// near the bottom: the next page, once
function forseAltre() {
  const el = contenitore.value
  if (!el || !altre.value || carica.loading) return
  if (el.scrollTop + el.clientHeight < el.scrollHeight - 300) return
  carica.submit({ text: testo.value.trim(), start: righe.value.length })
}

function nomeDi(persona) {
  return persona.lead_name || persona.first_name || persona.name
}

function numeroDi(persona) {
  return persona.mobile_no || persona.phone || ''
}

function torna(persona) {
  const quando = quandoTorna(persona.next_appointment, lingua)
  if (!quando) return ''
  if (quando.quando === 'today') return __('Today {0}', [quando.ora])
  if (quando.quando === 'tomorrow') return __('Tomorrow {0}', [quando.ora])
  return quando.giorno
}

defineExpose({ ricarica: cerca })
</script>
