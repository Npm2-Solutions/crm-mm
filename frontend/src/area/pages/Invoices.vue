<!-- Invoices, with their PDF. -->
<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Your invoices') }}
    </h1>
    <div
      v-for="invoice in invoices.data?.invoices || []"
      :key="invoice.name"
      class="flex items-center justify-between gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
    >
      <div class="flex min-w-0 flex-col">
        <span class="text-base text-ink-gray-9">
          {{ __('Invoice {0}', [invoice.number]) }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{ day(invoice.date) }} · {{ money(invoice.total) }}
        </span>
      </div>
      <a
        v-if="invoice.has_pdf"
        :href="pdf(invoice)"
        class="shrink-0 text-p-sm font-medium text-ink-gray-9 underline underline-offset-2"
      >
        PDF
      </a>
      <span v-else class="shrink-0 text-p-sm text-ink-gray-5">
        {{ __('PDF not ready') }}
      </span>
    </div>
    <p
      v-if="invoices.data && !invoices.data.invoices.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('Nothing here yet.') }}
    </p>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { day, money } from '../dates'
import { area } from '../store'

const invoices = createResource({
  url: 'crm.area.api.get_invoices',
  params: { person: area.person },
  auto: true,
})

function pdf(invoice) {
  const params = new URLSearchParams({
    person: area.person,
    invoice: invoice.name,
  })
  return `/api/method/crm.area.api.download_invoice?${params}`
}
</script>
