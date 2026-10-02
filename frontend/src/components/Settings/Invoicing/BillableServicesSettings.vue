<!--
  The fiscal card of a service.

  A service without a card is not billable, and that is the point: the exemption is
  a configured property somebody signs off, never something read out of the service
  name.
-->
<template>
  <RecordList
    doctype="CRM Billable Service"
    :title="__('Billable services')"
    :subtitle="
      __(
        'What each service is, fiscally. A service without a card cannot be invoiced — the exemption is confirmed, never inferred.',
      )
    "
    :add-label="__('New service')"
    :empty-text="__('Nothing can be invoiced yet: add the first service card.')"
    title-field="service_name"
    :list-fields="[
      'name',
      'service_name',
      'is_healthcare',
      'vat_exempt',
      'vat_rate',
      'vat_nature',
      'ts_expense_type',
      'default_rate',
      'verified_by_accountant',
      'enabled',
    ]"
    order-by="service_name asc"
    :defaults="{ enabled: 1, subject_to_stamp_duty: 1, vat_rate: 22 }"
    :describe="descrivi"
    :badges="etichette"
  />
</template>

<script setup>
import RecordList from '@/components/Settings/Invoicing/RecordList.vue'
import { useVocabolarioFatturazione } from '@/composables/vocabolarioFatturazione'
import { formatEuro } from '@/utils/invoicing'
import { nomeDi } from '@/utils/scelte'

const { nomi } = useVocabolarioFatturazione()

// what the card says, in words: "Exempt (art. 10) · Health professional's
// services · 70,00 €", never a natura or an expense type code
function descrivi(row) {
  const parti = []
  if (row.vat_exempt) parti.push(nomeDi(nomi.value, 'natura', 'N4'))
  else if (row.vat_nature)
    parti.push(nomeDi(nomi.value, 'natura', row.vat_nature))
  else parti.push(`${__('VAT')} ${row.vat_rate || 0}%`)
  if (row.ts_expense_type)
    parti.push(nomeDi(nomi.value, 'tipo_spesa', row.ts_expense_type))
  if (row.default_rate) parti.push(formatEuro(row.default_rate))
  return parti.join(' · ')
}

function etichette(row) {
  const badge = []
  if (!row.enabled) badge.push({ label: __('Off'), theme: 'gray' })
  if (row.is_healthcare) badge.push({ label: __('Healthcare'), theme: 'blue' })
  if (!row.verified_by_accountant)
    badge.push({ label: __('Unverified'), theme: 'orange' })
  return badge
}
</script>
