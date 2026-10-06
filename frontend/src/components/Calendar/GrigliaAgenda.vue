<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The agenda's hours as a grid (docs/progetto-ghl/56-agenda.md): a day's
  columns are its professionals or its rooms, a week's the days of one of
  them. Each column at least as wide as a name reads (`--col-min`), the
  columns scroll sideways under their headers and the hours stay where they
  are; a column greyed where it does not work, its hours in its header; the
  appointments as the design system's AgendaEvent (BloccoAgenda), one line
  across for now.
-->
<template>
  <div
    ref="scorre"
    class="dc-agenda relative h-full min-h-0 overflow-auto overscroll-contain"
    :class="settimana ? 'dc-agenda--settimana' : ''"
  >
    <div
      v-if="colonne.length"
      class="relative"
      :style="{ minWidth: `calc(3.5rem + ${colonne.length} * var(--col-min))` }"
    >
      <!-- the headers stay above while the hours scroll -->
      <div
        class="sticky top-0 z-20 border-b border-outline-gray-2 bg-surface-base"
      >
        <div class="flex">
          <div
            class="sticky left-0 z-10 w-14 shrink-0 border-r border-outline-gray-2 bg-surface-base"
          />
          <div
            v-for="colonna in colonne"
            :key="colonna.key"
            class="flex min-w-0 items-center gap-2 border-r border-outline-gray-2 px-2.5 py-2 last:border-r-0"
            :style="colonnaStile"
            :title="
              [colonna.titolo, colonna.sottotitolo].filter(Boolean).join(' · ')
            "
          >
            <template v-if="colonna.tipo === 'giorno'">
              <!-- a day of the week: a tap on it opens that day -->
              <button
                type="button"
                class="flex min-w-0 flex-1 items-center gap-2 rounded text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                :aria-label="__('Open {0}', [colonna.titolo])"
                @click="$emit('giorno', colonna.data)"
              >
                <span
                  class="grid size-8 shrink-0 place-items-center rounded-full text-lg-medium tabular-nums"
                  :class="
                    colonna.oggi
                      ? 'bg-[var(--brand-action)] text-[var(--on-brand-solid)]'
                      : 'text-ink-gray-8'
                  "
                >
                  {{ colonna.numero }}
                </span>
                <span class="min-w-0">
                  <span
                    class="block truncate text-p-sm-medium capitalize text-ink-gray-8"
                  >
                    {{ colonna.nome }}
                  </span>
                  <span
                    class="block min-h-4 truncate text-p-xs"
                    :class="sottotitoloColore(colonna)"
                  >
                    {{ colonna.sottotitolo }}
                  </span>
                </span>
              </button>
            </template>
            <template v-else>
              <!-- on a phone the name takes the room the face had -->
              <UserAvatar
                v-if="colonna.tipo === 'persona'"
                :user="colonna.utente"
                size="sm"
                class="shrink-0 max-md:hidden"
              />
              <span
                v-else
                class="size-2.5 shrink-0 rounded-full"
                :style="{
                  backgroundColor: colonna.colore || 'var(--ink-gray-4)',
                }"
                aria-hidden="true"
              />
              <span class="min-w-0 flex-1">
                <span class="block truncate text-p-sm-medium text-ink-gray-8">
                  {{ colonna.titolo }}
                </span>
                <span
                  class="block min-h-4 truncate text-p-xs"
                  :class="sottotitoloColore(colonna)"
                >
                  {{ colonna.sottotitolo }}
                </span>
              </span>
            </template>
            <span
              v-if="conteggi[colonna.key]"
              class="shrink-0 rounded-full bg-surface-gray-2 px-1.5 text-p-xs tabular-nums text-ink-gray-7"
              role="img"
              :aria-label="
                conteggi[colonna.key] === 1
                  ? __('1 appointment')
                  : __('{0} appointments', [conteggi[colonna.key]])
              "
            >
              {{ conteggi[colonna.key] }}
            </span>
          </div>
        </div>
        <!-- what lasts the whole day, above the hours -->
        <div v-if="conIntere" class="flex border-t border-outline-gray-1">
          <div
            class="sticky left-0 z-10 flex w-14 shrink-0 items-center justify-end border-r border-outline-gray-2 bg-surface-base pr-2 text-right text-[11px] leading-tight text-ink-gray-5"
          >
            {{ __('All day') }}
          </div>
          <div
            v-for="colonna in colonne"
            :key="colonna.key"
            class="flex min-w-0 flex-col gap-0.5 border-r border-outline-gray-2 p-1 last:border-r-0"
            :style="colonnaStile"
          >
            <button
              v-for="cosa in cose.get(colonna.key)?.intere || []"
              :key="cosa.id"
              type="button"
              class="truncate rounded px-1.5 py-0.5 text-left text-p-xs text-ink-gray-8"
              :style="{
                backgroundColor: `color-mix(in srgb, ${coloreEvento(cosa)} 18%, var(--surface-base))`,
              }"
              @click.stop="$emit('apri', cosa)"
            >
              {{ cosa.dati?.title || __('Event') }}
            </button>
          </div>
        </div>
      </div>

      <div class="flex">
        <!-- the hours, where they stay while the columns scroll sideways -->
        <div
          class="sticky left-0 z-10 w-14 shrink-0 border-r border-outline-gray-2 bg-surface-base"
          :style="{ height: altezza }"
        >
          <div
            v-for="(segno, i) in asseLeggibile"
            :key="segno.minutes"
            class="absolute right-2 text-p-xs tabular-nums text-ink-gray-5"
            :class="i === 0 ? 'translate-y-0.5' : '-translate-y-1/2'"
            :style="{ top: posizione(segno.minutes) }"
          >
            {{ segno.label }}
          </div>
          <div
            v-if="adessoMostrato"
            class="absolute inset-x-0 z-[1] flex -translate-y-1/2 items-center justify-end gap-1 bg-surface-base pr-1.5 text-p-xs-medium tabular-nums text-ink-gray-9"
            :style="{ top: posizione(adesso) }"
          >
            {{ oraAdesso }}
            <span
              class="size-1.5 rounded-full bg-[var(--brand-segno)]"
              aria-hidden="true"
            />
          </div>
        </div>

        <div
          v-for="colonna in colonne"
          :key="colonna.key"
          class="relative min-w-0 border-r border-outline-gray-2 last:border-r-0"
          :style="{ ...colonnaStile, height: altezza }"
          :data-colonna="colonna.key"
          @click="crea($event, colonna)"
          @dragover.prevent="sopra = colonna.key"
          @dragleave="sopra = sopra === colonna.key ? '' : sopra"
          @drop.prevent="lascia($event, colonna)"
        >
          <!-- where it does not work -->
          <div
            v-for="(banda, i) in chiuso(colonna)"
            :key="`chiuso-${i}`"
            class="dc-agenda-chiuso pointer-events-none absolute inset-x-0"
            :style="{
              top: posizione(banda.from),
              height: durata(banda.from, banda.to),
            }"
          />
          <!-- the hours, and the half hours where there is room to read them -->
          <div
            v-for="segno in asse"
            :key="`ora-${segno.minutes}`"
            class="pointer-events-none absolute inset-x-0 border-t border-outline-gray-1"
            :style="{ top: posizione(segno.minutes) }"
          />
          <template v-if="pxPerMinuto >= 1.6">
            <div
              v-for="segno in asse.slice(0, -1)"
              :key="`mezza-${segno.minutes}`"
              class="pointer-events-none absolute inset-x-0 border-t border-dashed border-outline-gray-1 opacity-60"
              :style="{ top: posizione(segno.minutes + 30) }"
            />
          </template>
          <!-- busy with what one may not read; a colleague's engagement -->
          <div
            v-for="banda in cose.get(colonna.key)?.bande || []"
            :key="banda.id"
            class="dc-agenda-occupato pointer-events-none absolute inset-x-1 overflow-hidden px-1.5 py-0.5 text-p-xs text-ink-gray-6"
            :style="{
              top: posizione(banda.startMinutes),
              height: durata(banda.startMinutes, banda.endMinutes),
            }"
          >
            {{ banda.tipo === 'impegno' ? __('Engaged') : __('Busy') }}
          </div>
          <!-- now, across the day -->
          <div
            v-if="adessoMostrato && colonna.oggi"
            class="pointer-events-none absolute inset-x-0 z-[3] border-t-2 border-[var(--brand-segno)]"
            :style="{ top: posizione(adesso) }"
          />
          <!-- where a dragged appointment would land -->
          <div
            v-if="sopra === colonna.key"
            class="pointer-events-none absolute inset-0 bg-[var(--brand-subtle)] opacity-40"
          />

          <BloccoAgenda
            v-for="blocco in disposti[colonna.key] || []"
            :key="blocco.id"
            :cosa="blocco"
            :righe="
              righeDelBlocco(
                blocco.endMinutes - blocco.startMinutes,
                pxPerMinuto,
              )
            "
            :modo="modo"
            :colore="coloreDi(blocco)"
            :stile="stileDi(blocco)"
            :adesso="inCorso(colonna, blocco)"
            :scelto="scelto === blocco.id"
            :trascinabile="
              modificabile && blocco.tipo === 'appuntamento' && !touch
            "
            :nomeDi="nomeDi"
            :nomeStanza="nomeStanza"
            @apri="(cosa) => $emit('apri', cosa)"
            @modifica="(cosa) => $emit('modifica', cosa)"
            @prendi="(evento, cosa) => prendi(evento, cosa, colonna)"
          />
        </div>
      </div>
    </div>
    <slot v-else name="vuoto" />
  </div>
</template>

<script setup>
import BloccoAgenda from '@/components/Calendar/BloccoAgenda.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  chiusure,
  coloreDelBlocco,
  finestraDellaGiornata,
  righeDelBlocco,
} from '@/utils/agenda'
import { NAMED_HEX } from '@/utils/calendarColors'
import {
  adessoDelCentro,
  buildTimeAxis,
  formatMinutes,
  layoutLanes,
  minutesFromMidnight,
} from '@/utils/scheduler'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  /**
   * `[{ key, tipo: 'persona' | 'stanza' | 'giorno', titolo, sottotitolo,
   * utente, colore, data, oggi, aperto, nome, numero }]`: `aperto` the open
   * windows of its day in minutes, `[]` off duty, null or undefined unknown
   */
  colonne: { type: Array, default: () => [] },
  /** what each column draws (utils/agenda.js `cosePerColonna`) */
  cose: { type: Map, default: () => new Map() },
  pxPerMinuto: { type: Number, default: 1.6 },
  /** what a day's columns are: professionals (`staff`) or rooms (`resource`) */
  modo: { type: String, default: 'staff' },
  /** the columns are the days of one of them */
  settimana: { type: Boolean, default: false },
  /** minutes a click or a drop snaps to */
  passo: { type: Number, default: 15 },
  /** the block open in the panel */
  scelto: { type: String, default: '' },
  /** false for who reads the agenda only: a click on a free time makes nothing, a block does not move */
  modificabile: { type: Boolean, default: true },
  colorePer: { type: String, default: 'servizio' },
  serviceColors: { type: Object, default: () => ({}) },
  nomeDi: { type: Function, default: (utente) => utente },
  nomeStanza: { type: Function, default: (stanza) => stanza },
  /** what the columns draw has come for these days: the hours open where they matter */
  pronto: { type: Boolean, default: true },
})

const emit = defineEmits(['apri', 'modifica', 'crea', 'sposta', 'giorno'])

const scorre = ref(null)
const sopra = ref('')
// a finger drags nothing here: an appointment's hours change in its panel
const touch =
  typeof window !== 'undefined' &&
  window.matchMedia?.('(pointer: coarse)')?.matches

const colonnaStile = { flex: '1 1 0', minWidth: 'var(--col-min)' }

// "now" moves on its own while the page stays open, on the centre's clock
const ora = ref(adessoDelCentro())
const orologio = setInterval(() => (ora.value = adessoDelCentro()), 60000)
onBeforeUnmount(() => clearInterval(orologio))
const adesso = computed(() => minutesFromMidnight(ora.value))
const oraAdesso = computed(() => formatMinutes(adesso.value))

const finestra = computed(() =>
  finestraDellaGiornata(
    props.colonne.flatMap((colonna) => {
      const suo = props.cose.get(colonna.key) || {}
      return [...(suo.blocchi || []), ...(suo.bande || [])]
    }),
    props.colonne.map((colonna) => colonna.aperto),
  ),
)
const asse = computed(() =>
  buildTimeAxis(
    Math.floor(finestra.value.startMinutes / 60),
    Math.floor(finestra.value.endMinutes / 60),
  ),
)
// the hours' labels, but where now is written: one over the other read neither
const asseLeggibile = computed(() =>
  asse.value.filter(
    (segno) =>
      !adessoMostrato.value ||
      Math.abs(segno.minutes - adesso.value) * props.pxPerMinuto >= 18,
  ),
)
const altezza = computed(
  () =>
    `${(finestra.value.endMinutes - finestra.value.startMinutes) * props.pxPerMinuto}px`,
)
const adessoMostrato = computed(
  () =>
    props.colonne.some((colonna) => colonna.oggi) &&
    adesso.value >= finestra.value.startMinutes &&
    adesso.value <= finestra.value.endMinutes,
)

function posizione(minuti) {
  return `${(minuti - finestra.value.startMinutes) * props.pxPerMinuto}px`
}

function durata(da, a) {
  return `${Math.max(a - da, 0) * props.pxPerMinuto}px`
}

function chiuso(colonna) {
  return chiusure(colonna.aperto, finestra.value)
}

// side by side where two overlap, each its lane
const disposti = computed(() =>
  Object.fromEntries(
    props.colonne.map((colonna) => [
      colonna.key,
      layoutLanes(props.cose.get(colonna.key)?.blocchi || []),
    ]),
  ),
)

const conteggi = computed(() =>
  Object.fromEntries(
    props.colonne.map((colonna) => [
      colonna.key,
      (props.cose.get(colonna.key)?.blocchi || []).filter(
        (blocco) =>
          blocco.tipo === 'appuntamento' && blocco.dati?.status !== 'Cancelled',
      ).length,
    ]),
  ),
)

const conIntere = computed(() =>
  props.colonne.some((colonna) => props.cose.get(colonna.key)?.intere?.length),
)

// a block's box: its hours, its lane, a hair of space around it
function stileDi(blocco) {
  const corsie = blocco.lanes || 1
  const alto = (blocco.endMinutes - blocco.startMinutes) * props.pxPerMinuto
  return {
    top: posizione(blocco.startMinutes),
    height: `${Math.max(alto - 1, 14)}px`,
    left: `calc(${((blocco.lane || 0) / corsie) * 100}% + 2px)`,
    width: `calc(${100 / corsie}% - 4px)`,
  }
}

function coloreEvento(cosa) {
  return NAMED_HEX[cosa.dati?.color] || cosa.dati?.color || 'var(--ink-gray-5)'
}

function coloreDi(blocco) {
  if (blocco.tipo === 'evento') return coloreEvento(blocco)
  return coloreDelBlocco(blocco.dati, {
    per: props.colorePer,
    serviceColors: props.serviceColors,
  })
}

function inCorso(colonna, blocco) {
  return (
    colonna.oggi &&
    blocco.tipo === 'appuntamento' &&
    blocco.dati?.status !== 'Cancelled' &&
    blocco.startMinutes <= adesso.value &&
    adesso.value < blocco.endMinutes
  )
}

function sottotitoloColore(colonna) {
  return Array.isArray(colonna.aperto) && !colonna.aperto.length
    ? 'text-ink-amber-7'
    : 'text-ink-gray-5'
}

/** The minute of the day the pointer is on, inside a column, snapped down. */
function minutoA(evento, sotto = 0) {
  const box = evento.currentTarget.getBoundingClientRect()
  const minuti =
    finestra.value.startMinutes +
    (evento.clientY - box.top) / props.pxPerMinuto -
    sotto
  const passo = Math.max(props.passo, 1)
  return Math.min(
    Math.max(Math.floor(minuti / passo) * passo, finestra.value.startMinutes),
    finestra.value.endMinutes - passo,
  )
}

function crea(evento, colonna) {
  if (!props.modificabile) return
  emit('crea', { colonna, minuti: minutoA(evento) })
}

function prendi(evento, cosa, colonna) {
  if (!evento.dataTransfer) return
  const box = evento.currentTarget.getBoundingClientRect()
  evento.dataTransfer.effectAllowed = 'move'
  evento.dataTransfer.setData(
    'text/plain',
    JSON.stringify({
      id: cosa.id,
      da: colonna.key,
      // where in the block it was taken: it lands the same way under the pointer
      presa: (evento.clientY - box.top) / props.pxPerMinuto,
      durata: cosa.endMinutes - cosa.startMinutes,
    }),
  )
}

function lascia(evento, colonna) {
  sopra.value = ''
  if (!props.modificabile) return
  let preso
  try {
    preso = JSON.parse(evento.dataTransfer.getData('text/plain'))
  } catch {
    return
  }
  if (!preso?.id) return
  const blocco = (props.cose.get(preso.da)?.blocchi || []).find(
    (b) => b.id === preso.id,
  )
  if (!blocco) return
  emit('sposta', {
    cosa: blocco,
    da: preso.da,
    a: colonna,
    minuti: minutoA(evento, preso.presa || 0),
    durata: preso.durata || 30,
  })
}

/**
 * Where the hours open: now on today, a little above it; else the day's first
 * appointment; else the first hour shown.
 */
async function alPunto() {
  await nextTick()
  const box = scorre.value
  if (!box) return
  const blocchi = props.colonne.flatMap(
    (colonna) => props.cose.get(colonna.key)?.blocchi || [],
  )
  const primo = blocchi.length
    ? Math.min(...blocchi.map((b) => b.startMinutes))
    : finestra.value.startMinutes
  const dove = adessoMostrato.value ? adesso.value - 90 : primo - 30
  box.scrollTop = Math.max(
    0,
    (dove - finestra.value.startMinutes) * props.pxPerMinuto,
  )
}

// a new day, a new week: once what it holds has come, the hours open where
// they matter - and stay where they were left while it reloads
let giaAperto = ''
watch(
  () => [props.colonne.map((c) => c.data).join('|'), props.pronto],
  ([giorni, pronto]) => {
    if (!pronto || !giorni || giorni === giaAperto) return
    giaAperto = giorni
    alPunto()
  },
  { immediate: true },
)

defineExpose({ scorre, alPunto })
</script>
