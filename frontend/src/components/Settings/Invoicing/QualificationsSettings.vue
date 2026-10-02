<!--
  The register: what each qualification means for VAT, for the Sistema TS and for
  the SdI.

  It ships seeded and it is **yours** from then on. The file the entries came from
  is where the research lives; these records are what the practice runs on, and a
  correction made here is never overwritten by a migration.
-->
<template>
  <RecordList
    doctype="CRM Professional Qualification"
    :title="__('Qualification register')"
    :subtitle="
      __(
        'What a qualification means for VAT, for the Sistema TS and for the SdI. Seeded once, then yours: a correction here survives every update.',
      )
    "
    :add-label="__('New qualification')"
    :empty-text="
      __('The register is empty — reinstall or add the first entry.')
    "
    title-field="qualification_name"
    :list-fields="[
      'name',
      'qualification_name',
      'category',
      'vat_exempt',
      'sdi_rule',
      'ts_required',
      'verified',
      'needs_verification',
      'enabled',
    ]"
    order-by="category asc, qualification_name asc"
    :describe="descrivi"
    :badges="etichette"
    :visibile="visibile"
  >
    <template #banner>
      <!-- with the clinic on, the register a medical centre reads: the health
           professions, and any other one somebody already performs with -->
      <div
        v-if="sanitario && nascoste"
        class="mx-2 flex items-center justify-between gap-4 text-p-sm text-ink-gray-6 max-md:flex-col max-md:items-start"
      >
        <span class="min-w-0">
          {{
            tutte
              ? __('Every qualification, the other professions too.')
              : __('The health professions, and the ones in use.')
          }}
        </span>
        <Button
          class="shrink-0"
          variant="ghost"
          :label="
            tutte
              ? __('Only the health professions')
              : __('Show the other professions ({0})', [nascoste])
          "
          @click="tutte = !tutte"
        />
      </div>
      <!-- The exemption test is joint and the catalogue never infers, so the
           entries that still need an accountant's word say so until somebody
           gives it. -->
      <div
        v-if="daVerificare.length"
        class="mx-2 flex flex-col gap-1 rounded-xl border border-outline-amber-2 bg-surface-amber-1 px-4 py-3"
      >
        <span class="text-p-base-medium text-ink-gray-8">
          {{
            __('{0} entries still need the accountant', [daVerificare.length])
          }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            __(
              'They can be invoiced today. What is not confirmed is the exemption on them, and that is not something the system can decide.',
            )
          }}
        </span>
      </div>
    </template>
  </RecordList>
</template>

<script setup>
import RecordList from '@/components/Settings/Invoicing/RecordList.vue'
import { useVocabolarioFatturazione } from '@/composables/vocabolarioFatturazione'
import { createListResource, Button } from 'frappe-ui'
import { computed, ref } from 'vue'

const { profilo } = useVocabolarioFatturazione()
const sanitario = computed(() => profilo.value === 'sanitario')
const tutte = ref(false)

// the qualifications somebody performs with stay in sight, whatever they are
const inUso = createListResource({
  doctype: 'CRM Service Provider',
  fields: ['qualification'],
  pageLength: 500,
  auto: true,
})
const usate = computed(
  () => new Set((inUso.data || []).map((riga) => riga.qualification)),
)
const tutteLeQualifiche = createListResource({
  doctype: 'CRM Professional Qualification',
  fields: ['name', 'category'],
  pageLength: 500,
  auto: true,
})

function sanitariaOUsata(row) {
  return row.category === 'sanitaria' || usate.value.has(row.name)
}

function visibile(row) {
  return !sanitario.value || tutte.value || sanitariaOUsata(row)
}

const nascoste = computed(
  () =>
    (tutteLeQualifiche.data || []).filter((row) => !sanitariaOUsata(row))
      .length,
)

const daVerificareRes = createListResource({
  doctype: 'CRM Professional Qualification',
  fields: ['name', 'qualification_name'],
  filters: { enabled: 1, verified: 0, needs_verification: ['is', 'set'] },
  pageLength: 100,
  auto: true,
})
const daVerificare = computed(() => daVerificareRes.data || [])

const REGOLA = {
  vietato: 'SdI forbidden',
  obbligatorio: 'SdI mandatory',
  ammesso: 'SdI allowed',
}

function descrivi(row) {
  const parti = [
    row.vat_exempt ? __('Exempt') : __('Taxable'),
    __(REGOLA[row.sdi_rule]),
  ]
  if (row.ts_required) parti.push(__('Sistema TS'))
  return parti.join(' · ')
}

function etichette(row) {
  const badge = []
  if (!row.enabled) badge.push({ label: __('Off'), theme: 'gray' })
  if (row.needs_verification && !row.verified)
    badge.push({ label: __('To verify'), theme: 'orange' })
  if (row.sdi_rule === 'vietato')
    badge.push({ label: __('No SdI'), theme: 'red' })
  return badge
}
</script>
