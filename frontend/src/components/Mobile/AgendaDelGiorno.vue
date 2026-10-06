<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The agenda on a phone (docs/progetto-ghl/29): a grid of hours shows four of
  them at a time and a short appointment as a sliver, so a phone opens on the
  day as a list - when, who, what - in the order it happens, with a line where
  "now" falls. The week above is a tap away from any of its days; the hours'
  grid stays one switch away in the header.
-->
<template>
  <div class="flex min-h-0 min-w-0 flex-1 flex-col">
    <!-- touch-pan-y: sideways, the finger is the agenda's (it changes the
         week, the day), never the browser's back -->
    <div
      ref="striscia"
      class="flex shrink-0 touch-pan-y items-center gap-1 border-b border-outline-gray-2 px-1 py-2"
    >
      <Button
        variant="ghost"
        icon="lucide-chevron-left"
        :aria-label="__('Previous week')"
        @click="giorno = spostaGiorno(giorno, -7)"
      />
      <div class="grid flex-1 grid-cols-7 gap-0.5">
        <button
          v-for="data in settimana"
          :key="data"
          type="button"
          class="flex flex-col items-center gap-0.5 rounded-lg py-1.5"
          :class="
            data === giorno
              ? 'bg-[var(--brand-action)] text-[var(--on-brand-solid)]'
              : 'text-ink-gray-7 active:bg-surface-gray-2'
          "
          :aria-pressed="data === giorno"
          :aria-label="giornoPerEsteso(data)"
          @click="giorno = data"
        >
          <span
            class="text-xs"
            :class="data === giorno ? '' : 'text-ink-gray-5'"
          >
            {{ nomeBreve(data) }}
          </span>
          <span
            class="text-base"
            :class="[
              data === oggi ? 'font-semibold' : '',
              data === oggi && data !== giorno
                ? 'text-[var(--brand-action)]'
                : '',
            ]"
          >
            {{ numero(data) }}
          </span>
        </button>
      </div>
      <Button
        variant="ghost"
        icon="lucide-chevron-right"
        :aria-label="__('Next week')"
        @click="giorno = spostaGiorno(giorno, 7)"
      />
    </div>

    <div class="flex shrink-0 items-center justify-between gap-2 px-4 pt-3">
      <h2 class="truncate text-base-medium text-ink-gray-8">
        {{ giornoPerEsteso(giorno) }}
      </h2>
      <div class="flex shrink-0 items-center gap-1">
        <Button
          v-if="giorno !== oggi"
          variant="ghost"
          :label="__('Today')"
          @click="giorno = oggi"
        />
        <!-- the page's switch to the hours' grid -->
        <slot name="vista" />
      </div>
    </div>

    <div
      ref="contenitore"
      class="min-h-0 flex-1 touch-pan-y overflow-y-auto px-3 pb-24 pt-2"
    >
      <!-- pulled down from the top, the day reloads -->
      <TiraPerAggiornare v-bind="tira" />
      <template v-for="(riga, i) in righe" :key="riga.id">
        <div
          v-if="i === adesso"
          class="my-1.5 flex items-center gap-1.5"
          role="separator"
          :aria-label="__('Now')"
        >
          <span class="size-2 rounded-full bg-[var(--brand-segno)]" />
          <span class="flex-1 border-t border-[var(--brand-segno)]" />
        </div>
        <button
          type="button"
          class="mb-2 flex w-full items-stretch gap-3 rounded-lg border px-3 py-2.5 text-left active:bg-surface-gray-2"
          :class="
            riga.id === `appt:${selected}`
              ? 'border-outline-gray-4 bg-surface-gray-2'
              : 'border-outline-gray-2'
          "
          @click="emit('open', { id: riga.id })"
        >
          <span class="flex w-11 shrink-0 flex-col text-p-sm">
            <span v-if="riga.intero" class="text-ink-gray-7">
              {{ __('All day') }}
            </span>
            <template v-else>
              <span class="font-medium text-ink-gray-8">
                {{ ora(riga.inizio) }}
              </span>
              <span class="text-ink-gray-5">{{ ora(riga.fine) }}</span>
            </template>
          </span>
          <span
            class="w-1 shrink-0 rounded-full"
            :style="{ background: colore(riga) }"
            aria-hidden="true"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <!-- the name is read whole: the chips sit beside it while the
                 row has room, under it when it has not («Frances…» beside
                 «Completato» on a phone with its page zoomed) -->
            <span
              class="flex flex-wrap items-start justify-between gap-x-2 gap-y-1"
            >
              <span
                class="max-w-full truncate text-base-medium"
                :class="
                  annullato(riga)
                    ? 'text-ink-gray-5 line-through'
                    : 'text-ink-gray-9'
                "
              >
                {{ titolo(riga) }}
              </span>
              <!-- a first visit says so and still says how it went: a new
                   patient who did not come read only «First visit» -->
              <span
                v-if="
                  riga.dati.first_visit ||
                  statoDaDire(riga) ||
                  risposte.has(riga.id)
                "
                class="flex shrink-0 flex-wrap gap-1"
              >
                <span
                  v-if="riga.dati.first_visit"
                  class="rounded bg-[var(--brand-subtle)] px-1.5 py-0.5 text-xs text-[var(--on-brand-subtle)]"
                >
                  {{ __('First visit') }}
                </span>
                <span
                  v-if="statoDaDire(riga)"
                  class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-7"
                >
                  {{ __(riga.dati.status) }}
                </span>
                <!-- what the person answered the reminder, as the grid's block
                     says it: an icon with its words -->
                <span
                  v-if="risposte.has(riga.id)"
                  class="flex items-center gap-1 rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-7"
                >
                  <span
                    :class="[risposte.get(riga.id).icona, 'size-3 shrink-0']"
                    aria-hidden="true"
                  />
                  {{ risposte.get(riga.id).testo }}
                </span>
              </span>
            </span>
            <span v-if="sotto(riga)" class="truncate text-p-sm text-ink-gray-5">
              {{ sotto(riga) }}
            </span>
          </span>
        </button>
      </template>

      <div v-if="caricando && !righe.length" class="flex justify-center py-10">
        <LoaderMark />
      </div>
      <EmptyState
        v-else-if="!righe.length"
        :title="__('Nothing on this day')"
        :text="__('Book an appointment or add an event with the + button.')"
      />
    </div>
  </div>
</template>

<script setup>
import { appLocale } from '@/utils/locale'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { useScorriGiorni } from '@/composables/scorriGiorni'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { NAMED_HEX } from '@/utils/calendarColors'
import { chiLoFa } from '@/utils/oggi'
import { rispostaDellAppuntamento } from '@/utils/promemoriaAppuntamenti'
import { adessoDelCentro, appointmentColor } from '@/utils/scheduler'
import {
  chiDellAppuntamentoDelGiorno,
  doveAdesso,
  elencoDelGiorno,
  settimanaDi,
  spostaGiorno,
} from '@/utils/sulTelefono'
import { Button } from 'frappe-ui'
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  appointments: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
  serviceColors: { type: Object, default: () => ({}) },
  // the appointment open in the panel beside, if any
  selected: { type: String, default: '' },
  caricando: { type: Boolean, default: false },
  // what reloads the day when it is pulled down from the top
  aggiorna: { type: Function, default: () => {} },
})
// the day shown, YYYY-MM-DD: the page's own, so the grid opens on it too
const giorno = defineModel('date', { type: String, required: true })
const emit = defineEmits(['open'])
const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, () => props.aggiorna())
// swiped sideways: the day's list moves a day, the week's strip a week
const striscia = ref(null)
useScorriGiorni(
  contenitore,
  (verso) => (giorno.value = spostaGiorno(giorno.value, verso)),
  { segue: true },
)
useScorriGiorni(
  striscia,
  (verso) => (giorno.value = spostaGiorno(giorno.value, 7 * verso)),
)

const { getUser } = usersStore()
// whoever reads, as the store gives it: the user's name, not a ref
const { user } = sessionStore()
// the user's language, the European way (utils/locale.js)
const lingua = appLocale() || 'it-IT'

// "now" moves on its own while the page stays open, on the centre's clock as
// the day's times are
const adessoOra = ref(adessoDelCentro())
const orologio = setInterval(() => (adessoOra.value = adessoDelCentro()), 60000)
onBeforeUnmount(() => clearInterval(orologio))

const oggi = computed(() => locale(adessoOra.value))
const settimana = computed(() => settimanaDi(giorno.value))
const righe = computed(() =>
  elencoDelGiorno(props.appointments, props.events, giorno.value),
)
// what the person of each appointment answered its reminder, by row
const risposte = computed(() => {
  const mappa = new Map()
  for (const riga of righe.value) {
    if (riga.tipo !== 'appointment') continue
    const segno = rispostaDellAppuntamento(riga.dati, __)
    if (segno) mappa.set(riga.id, segno)
  }
  return mappa
})
const adesso = computed(() =>
  doveAdesso(righe.value, giorno.value, adessoOra.value),
)

function locale(data) {
  const due = (n) => String(n).padStart(2, '0')
  return `${data.getFullYear()}-${due(data.getMonth() + 1)}-${due(data.getDate())}`
}

function comeData(giornoScritto) {
  const [a, m, g] = giornoScritto.split('-').map(Number)
  return new Date(a, m - 1, g)
}

function nomeBreve(giornoScritto) {
  return new Intl.DateTimeFormat(lingua, { weekday: 'short' })
    .format(comeData(giornoScritto))
    .replace('.', '')
}

function numero(giornoScritto) {
  return comeData(giornoScritto).getDate()
}

function giornoPerEsteso(giornoScritto) {
  const testo = new Intl.DateTimeFormat(lingua, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(comeData(giornoScritto))
  return testo.charAt(0).toUpperCase() + testo.slice(1)
}

function ora(data) {
  return new Intl.DateTimeFormat(lingua, {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(data)
}

function annullato(riga) {
  return riga.tipo === 'appointment' && riga.dati.status === 'Cancelled'
}

function colore(riga) {
  if (annullato(riga)) return 'var(--outline-gray-3)'
  if (riga.tipo === 'appointment')
    return appointmentColor(riga.dati, props.serviceColors)
  return NAMED_HEX[riga.dati.color] || 'var(--outline-gray-4)'
}

// who comes, as the desk says it (a class by its service); an event by its
// subject
function titolo(riga) {
  if (riga.tipo === 'event') return riga.dati.title || __('Event')
  return chiDellAppuntamentoDelGiorno(riga.dati).titolo
}

// what and with whom: the service and the professionals - a class says how
// many come - or where an event is
function sotto(riga) {
  if (riga.tipo === 'event') return riga.dati.location || ''
  const professionisti = chiLoFa(riga.dati.staff, user)
    .map((s) => getUser(s.user)?.full_name || s.user)
    .filter(Boolean)
  const { persone } = chiDellAppuntamentoDelGiorno(riga.dati)
  const cosa =
    persone > 1 ? __('{0} people', [persone]) : riga.dati.service || ''
  return [cosa, ...professionisti].filter(Boolean).join(' · ')
}

// booked is what an appointment is: the other states are worth a word
function statoDaDire(riga) {
  return (
    riga.tipo === 'appointment' &&
    riga.dati.status &&
    riga.dati.status !== 'Scheduled'
  )
}
</script>
