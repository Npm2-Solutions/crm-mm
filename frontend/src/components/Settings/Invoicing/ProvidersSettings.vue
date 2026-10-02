<!--
  Whoever performs the service.

  The qualification is not a registry detail: it decides the expense type and the
  VAT regime. In a shared calendar a wrong assignment produces no error — it
  produces rejected rows in January.
-->
<template>
  <RecordList
    doctype="CRM Service Provider"
    :title="__('Providers')"
    :subtitle="
      __(
        'Who performs the service. Their qualification decides the expense type and the VAT regime, so it is confirmed on every line.',
      )
    "
    :add-label="__('New provider')"
    :empty-text="
      __('No providers yet. A line without one has no VAT regime to follow.')
    "
    title-field="provider_name"
    :list-fields="[
      'name',
      'provider_name',
      'qualification',
      'user',
      'professional_register',
      'register_number',
      'enabled',
    ]"
    order-by="provider_name asc"
    :defaults="{ enabled: 1 }"
    :describe="descrivi"
    :badges="etichette"
  />
</template>

<script setup>
import RecordList from '@/components/Settings/Invoicing/RecordList.vue'
import { useVocabolarioFatturazione } from '@/composables/vocabolarioFatturazione'
import { nomeDi } from '@/utils/scelte'

const { nomi } = useVocabolarioFatturazione()

function descrivi(row) {
  // the qualification by its name: "Fisioterapista", not `fisioterapista`
  const parti = [nomeDi(nomi.value, 'qualifica', row.qualification)]
  if (row.professional_register) {
    parti.push(
      [row.professional_register, row.register_number]
        .filter(Boolean)
        .join(' '),
    )
  }
  return parti.filter(Boolean).join(' · ')
}

function etichette(row) {
  return row.enabled ? [] : [{ label: __('Off'), theme: 'gray' }]
}
</script>
