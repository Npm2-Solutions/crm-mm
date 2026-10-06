<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  An appointment, or one's own event, in the agenda's grid: the design
  system's AgendaEvent (brand/design-system/espresso). The person first, then
  what and where, in as many whole lines as its height holds
  (utils/agenda.js): a half-hour that drew its time and the top half of
  «Servizio — Persona» says «09:00 Mario Rossi» and «Visita · Studio 2».
-->
<template>
  <button
    type="button"
    class="dc-evento absolute overflow-hidden text-left transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-4"
    :class="classi"
    :style="{ ...stile, '--evento': colore }"
    :draggable="trascinabile"
    :title="parole"
    :aria-label="parole"
    :data-blocco="cosa.id"
    @click.stop="$emit('apri', cosa)"
    @dblclick.stop="$emit('modifica', cosa)"
    @dragstart="$emit('prendi', $event, cosa)"
  >
    <!-- less than a line: its time and its person, small -->
    <span
      v-if="forma.forma === 'sottile' || forma.forma === 'una'"
      class="flex min-w-0 items-center gap-1"
    >
      <span
        v-if="adesso"
        class="dc-cross shrink-0"
        style="--s: 7px"
        aria-hidden="true"
      />
      <span class="dc-evento__ora shrink-0">{{ inizio }}</span>
      <span class="dc-evento__chi truncate">{{ testo.chi }}</span>
      <span
        v-if="forma.forma === 'una' && testo.dettagli"
        class="dc-evento__dettagli min-w-0 truncate"
      >
        · {{ testo.dettagli }}
      </span>
      <Segni :segni="segni" class="ml-auto" />
    </span>

    <template v-else-if="forma.forma === 'due'">
      <span class="flex min-w-0 items-center gap-1">
        <span
          v-if="adesso"
          class="dc-cross shrink-0"
          style="--s: 7px"
          aria-hidden="true"
        />
        <span class="dc-evento__ora shrink-0">{{ inizio }}</span>
        <span class="dc-evento__chi truncate">{{ testo.chi }}</span>
        <Segni :segni="segni" class="ml-auto" />
      </span>
      <span v-if="testo.dettagli" class="dc-evento__dettagli block truncate">
        {{ testo.dettagli }}
      </span>
    </template>

    <template v-else>
      <span class="flex min-w-0 items-center gap-1">
        <span
          v-if="adesso"
          class="dc-cross shrink-0"
          style="--s: 7px"
          aria-hidden="true"
        />
        <span class="dc-evento__ora truncate">
          {{ adesso ? __('Now · {0}', [orario]) : orario }}
        </span>
        <Segni :segni="segni" class="ml-auto" />
      </span>
      <span class="dc-evento__chi block truncate">{{ testo.chi }}</span>
      <template v-if="forma.forma === 'tre'">
        <span v-if="testo.dettagli" class="dc-evento__dettagli block truncate">
          {{ testo.dettagli }}
        </span>
      </template>
      <template v-else>
        <span v-if="testo.cosa" class="dc-evento__dettagli block truncate">
          {{ testo.cosa }}
        </span>
        <span v-if="testo.dove" class="dc-evento__dettagli block truncate">
          {{ testo.dove }}
        </span>
        <!-- what is left of its height reads its notes, whole lines -->
        <span
          v-if="note && forma.note"
          class="dc-evento__dettagli block overflow-hidden italic"
          :style="{
            display: '-webkit-box',
            '-webkit-box-orient': 'vertical',
            '-webkit-line-clamp': forma.note,
          }"
        >
          {{ note }}
        </span>
      </template>
    </template>
  </button>
</template>

<script setup>
import {
  formaDelBlocco,
  paroleDelBlocco,
  segniDelBlocco,
  testoDelBlocco,
} from '@/utils/agenda'
import { computed, h } from 'vue'

const props = defineProps({
  /** `{ id, tipo: 'appuntamento' | 'evento', startMinutes, endMinutes, dati }` */
  cosa: { type: Object, required: true },
  /** the lines its height holds (utils/agenda.js `righeDelBlocco`) */
  righe: { type: Number, default: 1 },
  /** what the columns are: a professional's (`staff`) or a room's (`resource`) */
  modo: { type: String, default: 'staff' },
  colore: { type: String, default: '' },
  stile: { type: Object, default: () => ({}) },
  adesso: { type: Boolean, default: false },
  scelto: { type: Boolean, default: false },
  trascinabile: { type: Boolean, default: false },
  nomeDi: { type: Function, default: (utente) => utente },
  nomeStanza: { type: Function, default: (stanza) => stanza },
})
defineEmits(['apri', 'modifica', 'prendi'])

const evento = computed(() => props.cosa.tipo === 'evento')
const dati = computed(() => props.cosa.dati || {})
const t = (testo, valori) => __(testo, valori)

const forma = computed(() => formaDelBlocco(props.righe))

// one's own event: its subject, where it is
const testo = computed(() => {
  if (evento.value) {
    const dove = dati.value.location || ''
    return {
      chi: dati.value.title || __('Event'),
      cosa: '',
      dove,
      dettagli: dove,
    }
  }
  return testoDelBlocco(dati.value, {
    modo: props.modo,
    nomeDi: props.nomeDi,
    nomeStanza: props.nomeStanza,
    t,
  })
})

const segni = computed(() =>
  evento.value ? [] : segniDelBlocco(dati.value, { t }),
)

const due = (n) => String(n).padStart(2, '0')
const hhmm = (minuti) =>
  minuti >= 24 * 60
    ? '24:00'
    : `${due(Math.floor(minuti / 60))}:${due(minuti % 60)}`
const inizio = computed(() => hhmm(props.cosa.startMinutes))
const orario = computed(
  () => `${inizio.value} – ${hhmm(props.cosa.endMinutes)}`,
)

const note = computed(() =>
  evento.value
    ? ''
    : String(dati.value.customer_notes || dati.value.notes || '').trim(),
)

const parole = computed(() => {
  if (evento.value)
    return [orario.value, testo.value.chi, testo.value.dove]
      .filter(Boolean)
      .join(', ')
  return paroleDelBlocco(dati.value, {
    modo: props.modo,
    nomeDi: props.nomeDi,
    nomeStanza: props.nomeStanza,
    t,
  })
})

const classi = computed(() => [
  forma.value.forma === 'sottile' ? 'dc-evento--sottile' : '',
  evento.value
    ? 'dc-evento--impegno'
    : dati.value.status === 'Cancelled'
      ? 'dc-evento--annullato'
      : dati.value.first_visit
        ? 'dc-evento--prima'
        : '',
  props.adesso ? 'dc-evento--adesso' : '',
  props.scelto ? 'dc-evento--scelto' : '',
  props.trascinabile ? 'cursor-grab active:cursor-grabbing' : '',
])

// the marks beside the time: an icon each, its words its name
function Segni(proprieta) {
  if (!proprieta.segni?.length) return null
  return h(
    'span',
    { class: 'flex shrink-0 items-center gap-0.5' },
    proprieta.segni.slice(0, 3).map((segno) =>
      h('span', {
        key: segno.chiave,
        class: [
          segno.icona,
          'dc-evento__segno size-3 shrink-0',
          segno.chiave === 'conflitto' ? '!text-ink-amber-7' : '',
        ],
        role: 'img',
        'aria-label': segno.testo,
        title: segno.testo,
      }),
    ),
  )
}
Segni.props = ['segni']
</script>
