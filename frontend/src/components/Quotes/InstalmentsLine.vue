<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  How a quote paid in instalments goes (crm.preventivi.rate), in one line: «Rate:
  3 di 10 pagate · prossima 1 novembre 2026, 250,00 €»; the late ones in the
  warning colour, with its mark, never the colour alone.
-->
<template>
  <span
    v-if="frase"
    class="inline-flex items-start gap-1 break-words text-p-sm"
    :class="frase.ritardo ? 'text-ink-amber-7' : 'text-ink-gray-6'"
  >
    <LucideAlertTriangle
      v-if="frase.ritardo"
      class="mt-0.5 size-3.5 shrink-0"
      aria-hidden="true"
    />
    <span class="min-w-0">{{ frase.testo }}</span>
  </span>
</template>

<script setup>
import { formatDate } from '@/utils'
import { appLocale } from '@/utils/locale'
import { fraseDelleRate } from '@/utils/preventivi'
import { prezzo } from '@/utils/valute'
import { computed } from 'vue'
import LucideAlertTriangle from '~icons/lucide/triangle-alert'

const props = defineProps({
  // the server's summary of the plan (`rate.riassunto`)
  summary: { type: Object, default: null },
  currency: { type: String, default: 'EUR' },
})

const frase = computed(() =>
  fraseDelleRate(
    props.summary,
    (testo, argomenti) => __(testo, argomenti),
    (giorno) => formatDate(giorno, 'D MMMM YYYY'),
    (soldi) => prezzo(soldi, props.currency, appLocale()),
  ),
)
</script>
