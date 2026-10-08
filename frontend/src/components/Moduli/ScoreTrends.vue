<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A person's questionnaires followed over time: each score's total, form after
  form, on its bands (`crm.moduli.andamenti`). On the Forms tab, and in the
  clinic's summary where the clinic is on, with the visits on its sheets.
  What the session does not read is not here: the server leaves it out.
-->
<template>
  <section
    v-if="series.length"
    class="andamenti flex flex-col gap-4 rounded-lg border border-outline-gray-2 p-4"
  >
    <h3 class="text-base-semibold text-ink-gray-8">
      {{ __('Questionnaires over time') }}
    </h3>
    <div
      v-for="serie in series"
      :key="`${serie.template}-${serie.field}`"
      class="flex flex-col gap-2"
    >
      <div
        class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1"
      >
        <span class="min-w-0 text-base text-ink-gray-8">
          {{ serie.title }}
          <span v-if="serie.label" class="text-ink-gray-5">
            · {{ serie.label }}
          </span>
        </span>
        <span class="flex shrink-0 items-center gap-2">
          <span class="text-lg font-semibold text-ink-gray-9">
            {{ ultimo(serie).value }}
          </span>
          <Badge
            v-if="ultimo(serie).band"
            :label="ultimo(serie).band"
            theme="blue"
            variant="subtle"
          />
        </span>
      </div>
      <p v-if="variazione(serie)" class="text-sm text-ink-gray-6">
        {{ comeCambia(serie) }}
      </p>
      <svg
        viewBox="0 0 320 140"
        class="w-full max-w-md"
        role="img"
        :aria-label="descrizione(serie)"
      >
        <template v-for="g in [grafico(serie)]" :key="g.linea">
          <g v-for="fascia in g.fasce" :key="fascia.etichetta">
            <rect
              :x="g.area.sinistra"
              :y="fascia.y"
              :width="g.area.destra - g.area.sinistra"
              :height="fascia.altezza"
              :style="{
                fill: fascia.pari
                  ? 'var(--surface-gray-2)'
                  : 'var(--surface-gray-1)',
              }"
            />
            <!-- the band's name beside its stripe, never under a point -->
            <text
              :x="g.area.destra + 6"
              :y="fascia.y + Math.min(fascia.altezza / 2, 12) + 3"
              font-size="9"
              :style="{ fill: 'var(--ink-gray-6)' }"
            >
              {{ fascia.etichetta }}
            </text>
          </g>
          <text
            v-for="tacca in g.tacche"
            :key="tacca.y"
            :x="g.area.sinistra - 6"
            :y="tacca.y + 3"
            text-anchor="end"
            font-size="9"
            :style="{ fill: 'var(--ink-gray-6)' }"
          >
            {{ tacca.valore }}
          </text>
          <path
            :d="g.linea"
            fill="none"
            stroke-width="2"
            stroke-linejoin="round"
            :style="{ stroke: 'var(--brand-segno, var(--ink-gray-7))' }"
          />
          <circle
            v-for="punto in g.punti"
            :key="punto.name"
            :cx="punto.x"
            :cy="punto.y"
            r="3.5"
            stroke-width="2"
            :style="{
              fill: 'var(--surface-white, #fff)',
              stroke: 'var(--brand-segno, var(--ink-gray-7))',
            }"
          />
          <!-- the first and the last day, under their points -->
          <text
            v-for="(punto, i) in estremi(g.punti)"
            :key="`d${i}`"
            :x="punto.x"
            :y="g.area.sotto + 15"
            :text-anchor="
              estremi(g.punti).length === 1
                ? 'middle'
                : i === 0
                  ? 'start'
                  : 'end'
            "
            font-size="9"
            :style="{ fill: 'var(--ink-gray-6)' }"
          >
            {{ data(punto.date) }}
          </text>
        </template>
      </svg>
      <!-- every total in words: what the line says, for whoever does not see it -->
      <details class="text-sm text-ink-gray-7">
        <summary class="touch-target w-fit cursor-pointer text-ink-gray-6">
          {{
            serie.points.length === 1
              ? __('1 time')
              : __('{0} times', [serie.points.length])
          }}
        </summary>
        <ul class="mt-1 flex flex-col gap-0.5">
          <li
            v-for="punto in [...serie.points].reverse()"
            :key="punto.name"
            class="flex flex-wrap gap-x-2"
          >
            <span class="text-ink-gray-5">{{ data(punto.date) }}</span>
            <span class="font-medium text-ink-gray-8">{{ punto.value }}</span>
            <span v-if="punto.band">{{ punto.band }}</span>
          </li>
        </ul>
      </details>
    </div>
  </section>
</template>

<script setup>
import { formatDate } from '@/utils'
import { graficoDellAndamento, variazione } from '@/utils/andamenti'
import { Badge, createResource } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const trends = createResource({
  url: 'crm.moduli.andamenti.get_trends',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && trends.reload(),
  { immediate: true },
)

const series = computed(() =>
  (trends.data || []).filter((serie) => serie.points?.length),
)

const grafici = new WeakMap()
function grafico(serie) {
  if (!grafici.has(serie)) grafici.set(serie, graficoDellAndamento(serie))
  return grafici.get(serie)
}

const ultimo = (serie) => serie.points[serie.points.length - 1]
const estremi = (punti) =>
  punti.length > 1 ? [punti[0], punti[punti.length - 1]] : punti
const data = (quando) => formatDate(quando, 'D MMM YYYY')

function comeCambia(serie) {
  const { differenza, da } = variazione(serie)
  if (!differenza) return __('The same as on {0}', [data(da)])
  // a minus as the page writes one, not a hyphen
  const segno = differenza > 0 ? `+${differenza}` : `−${-differenza}`
  return __('{0} compared with {1}', [segno, data(da)])
}

function descrizione(serie) {
  return __('{0}: {1}', [
    serie.label || serie.title,
    serie.points
      .map((punto) => `${data(punto.date)} ${punto.value}`)
      .join(', '),
  ])
}

defineExpose({ reload: () => trends.reload() })
</script>
