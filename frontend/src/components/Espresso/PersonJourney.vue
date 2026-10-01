<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The person's journey at the head of their page (the design system's
  PatientJourney): arrives, books, comes in, after, at home. Done steps in the
  brand's solid with the tick, the one under way mint with the cross, the next
  ones numbered. Read from the centre's data (crm/clienti/percorso.py).
-->
<template>
  <ol v-if="tappe.length" class="dc-journey" :aria-label="__('Journey')">
    <li
      v-for="(tappa, i) in tappe"
      :key="tappa.key"
      :class="{
        'is-done': tappa.state === 'done',
        'is-current': tappa.state === 'current',
      }"
      :aria-current="tappa.state === 'current' ? 'step' : undefined"
    >
      <span class="dc-journey__dot" aria-hidden="true">
        <span v-if="tappa.state === 'done'" class="lucide-check size-3" />
        <span v-else-if="tappa.state === 'current'" class="dc-cross" />
        <template v-else>{{ i + 1 }}</template>
      </span>
      <span class="dc-journey__label truncate">{{ __(NOMI[tappa.key]) }}</span>
      <span class="dc-journey__meta truncate" :title="sotto(tappa)">
        {{ sotto(tappa) || '\u00a0' }}
      </span>
    </li>
  </ol>
</template>

<script setup>
import { formatDate } from '@/utils'
import { NOMI, sottotitolo } from '@/utils/percorso'
import { createResource } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const percorso = createResource({
  url: 'crm.clienti.percorso.get_journey',
  makeParams: () => ({ lead: props.lead }),
  auto: true,
})
watch(
  () => props.lead,
  () => percorso.reload(),
)

const tappe = computed(() => percorso.data?.steps || [])

const oggi = formatDate(new Date(), 'YYYY-MM-DD')

function sotto(tappa) {
  return sottotitolo(tappa, {
    oggi,
    giorno: (data) => formatDate(data, 'D MMM'),
    t: (testo, args) => __(testo, args),
  })
}

defineExpose({ reload: () => percorso.reload() })
</script>
