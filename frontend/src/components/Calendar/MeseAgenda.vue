<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The agenda's month (docs/crm/56-agenda.md): each day how many
  appointments it holds and the first of them by their time and their person;
  a day opens on a tap, an appointment on its own. On a phone a day says its
  number and how many it holds.
-->
<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="grid shrink-0 grid-cols-7 border-b border-outline-gray-2 bg-surface-base"
    >
      <span
        v-for="nome in nomiDeiGiorni"
        :key="nome"
        class="truncate px-2 py-1.5 text-p-xs-medium capitalize text-ink-gray-5 max-md:text-center"
      >
        {{ nome }}
      </span>
    </div>
    <div
      class="grid min-h-0 flex-1 grid-cols-7 overflow-y-auto"
      :style="{
        gridTemplateRows: `repeat(${settimane.length}, minmax(${compatto ? '3.5rem' : '6.75rem'}, 1fr))`,
      }"
    >
      <template v-for="settimana in settimane" :key="settimana[0]">
        <div
          v-for="data in settimana"
          :key="data"
          class="relative flex min-w-0 flex-col gap-0.5 border-b border-r border-outline-gray-2 p-1.5 [&:nth-child(7n)]:border-r-0"
          :class="delMese(data) ? '' : 'bg-surface-gray-1'"
        >
          <!-- the whole day opens it -->
          <button
            type="button"
            class="absolute inset-0 rounded-none focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-outline-gray-4 active:bg-surface-gray-2"
            :aria-label="parolaDelGiorno(data)"
            @click="$emit('giorno', data)"
          />
          <span
            class="pointer-events-none relative flex items-center justify-between gap-1 max-md:flex-col"
          >
            <span
              class="grid size-6 place-items-center rounded-full text-p-sm tabular-nums"
              :class="
                data === oggi
                  ? 'bg-[var(--brand-action)] font-semibold text-[var(--on-brand-solid)]'
                  : delMese(data)
                    ? 'text-ink-gray-8'
                    : 'text-ink-gray-5'
              "
            >
              {{ numero(data) }}
            </span>
            <!-- how many: a small tag beside the day on a desk, under it on a
                 phone. A bare grey number beside the day's read as another
                 date («28  21») on the desk too -->
            <span
              v-if="giorni[data].totale"
              class="rounded-full bg-surface-gray-2 px-1.5 tabular-nums text-ink-gray-6"
              :class="
                compatto ? 'text-[11px] leading-4' : 'text-p-xs leading-5'
              "
              aria-hidden="true"
            >
              {{ giorni[data].totale }}
            </span>
          </span>
          <template v-if="!compatto">
            <button
              v-for="cosa in giorni[data].primi"
              :key="cosa.id"
              type="button"
              class="relative flex min-w-0 items-center gap-1 rounded px-1 text-left text-p-xs leading-5 hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              :class="scelto === cosa.id ? 'bg-surface-gray-2' : ''"
              @click.stop="$emit('apri', cosa)"
            >
              <span
                class="h-3 w-0.5 shrink-0 rounded"
                :style="{ background: coloreDi(cosa) }"
                aria-hidden="true"
              />
              <span class="shrink-0 tabular-nums text-ink-gray-6">
                {{ inizio(cosa) }}
              </span>
              <span
                class="truncate"
                :class="
                  cosa.dati?.status === 'Cancelled'
                    ? 'text-ink-gray-5 line-through'
                    : 'text-ink-gray-8'
                "
              >
                {{ chi(cosa) }}
              </span>
            </button>
            <span
              v-if="giorni[data].altri"
              class="pointer-events-none relative px-1 text-p-xs text-ink-gray-5"
            >
              {{ __('{0} more', [giorni[data].altri]) }}
            </span>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import {
  coloreDelBlocco,
  giornoDelMese,
  meseDi,
  testoDelBlocco,
} from '@/utils/agenda'
import { NAMED_HEX } from '@/utils/calendarColors'
import { appLocale } from '@/utils/locale'
import { formatMinutes, oggiDelCentro } from '@/utils/scheduler'
import { computed } from 'vue'

const props = defineProps({
  /** any day of the month shown, YYYY-MM-DD */
  giorno: { type: String, required: true },
  /** each day's rows, by date: `{ id, tipo, startMinutes, dati }` */
  cose: { type: Map, default: () => new Map() },
  colorePer: { type: String, default: 'servizio' },
  serviceColors: { type: Object, default: () => ({}) },
  scelto: { type: String, default: '' },
  /** a phone's: a day says its number and dots, no names */
  compatto: { type: Boolean, default: false },
})
defineEmits(['giorno', 'apri'])

const lingua = appLocale() || 'it-IT'
const oggi = oggiDelCentro()

const settimane = computed(() => meseDi(props.giorno))
const mese = computed(() => props.giorno.slice(0, 7))
const delMese = (data) => data.slice(0, 7) === mese.value

const giorni = computed(() =>
  Object.fromEntries(
    settimane.value
      .flat()
      .map((data) => [data, giornoDelMese(props.cose.get(data) || [], 3)]),
  ),
)

const comeData = (data) => {
  const [a, m, g] = data.split('-').map(Number)
  return new Date(a, m - 1, g)
}
const numero = (data) => comeData(data).getDate()

// Monday to Sunday, in the reader's language
const nomiDeiGiorni = computed(() => {
  const formato = new Intl.DateTimeFormat(lingua, {
    weekday: props.compatto ? 'narrow' : 'short',
  })
  return (settimane.value[0] || []).map((data) =>
    formato.format(comeData(data)).replace('.', ''),
  )
})

function parolaDelGiorno(data) {
  const giorno = new Intl.DateTimeFormat(lingua, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(comeData(data))
  const totale = giorni.value[data].totale
  if (!totale) return giorno
  return totale === 1
    ? `${giorno}, ${__('1 appointment')}`
    : `${giorno}, ${__('{0} appointments', [totale])}`
}

const inizio = (cosa) => formatMinutes(cosa.startMinutes)

function chi(cosa) {
  if (cosa.tipo === 'evento') return cosa.dati?.title || __('Event')
  return testoDelBlocco(cosa.dati, { t: (testo, valori) => __(testo, valori) })
    .chi
}

function coloreDi(cosa) {
  if (cosa.tipo === 'evento')
    return NAMED_HEX[cosa.dati?.color] || 'var(--ink-gray-5)'
  return coloreDelBlocco(cosa.dati, {
    per: props.colorePer,
    serviceColors: props.serviceColors,
  })
}
</script>
