<!--
  The person's papers, in one place as on the brand's phone: what the centre gave
  online - until when, and a download after a code verified in the last minutes -
  and the invoices, with their PDF, what is left to pay of each and how to pay.
-->
<template>
  <div class="flex flex-col gap-5">
    <h1 class="area-title">{{ __('Documents') }}</h1>
    <section v-if="section('documents')" class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Documents online') }}</h2>
      <p class="text-p-sm text-ink-gray-6">
        {{ __('Documents the centre gave you, online until the date shown.') }}
      </p>
      <template v-for="doc in documents.data?.documents || []" :key="doc.name">
        <HiddenCard
          v-if="doc.hidden"
          :when="__('Online until {0}', [day(doc.expires_on)])"
        />
        <div v-else class="area-card area-row">
          <AreaChip colore="blue" icona="file-text" />
          <div class="min-w-0 flex-1">
            <span class="area-row__title">{{ doc.title }}</span>
            <span class="area-row__sub">
              {{ __(doc.document_type) }} ·
              {{ __('Online until {0}', [day(doc.expires_on)]) }}
            </span>
          </div>
          <!-- the centre's preview downloads nothing -->
          <Button
            v-if="!anteprima"
            class="shrink-0"
            size="lg"
            :variant="doc.downloaded ? 'subtle' : 'solid'"
            :label="__('Download')"
            @click="download(doc)"
          />
        </div>
      </template>
      <p
        v-if="documents.data && !documents.data.documents.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('Nothing here yet.') }}
      </p>
    </section>
    <section class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Invoices') }}</h2>
      <!-- what is left to pay of them, and how the centre is paid -->
      <div v-if="invoices.data?.to_pay" class="area-card flex flex-col gap-1.5">
        <div class="flex flex-wrap items-baseline justify-between gap-x-3">
          <span class="area-row__title">{{ __('To pay') }}</span>
          <span class="text-xl font-semibold tabular-nums text-ink-gray-9">
            {{ money(invoices.data.to_pay) }}
          </span>
        </div>
        <template v-if="invoices.data.how_to_pay">
          <span class="area-row__sub">{{ __('How to pay') }}</span>
          <p
            class="whitespace-pre-line text-p-base text-ink-gray-8 [overflow-wrap:anywhere]"
          >
            {{ invoices.data.how_to_pay }}
          </p>
        </template>
      </div>
      <template
        v-for="invoice in invoices.data?.invoices || []"
        :key="invoice.name"
      >
        <HiddenCard v-if="invoice.hidden" />
        <div v-else class="area-card area-row">
          <AreaChip icona="receipt" />
          <div class="min-w-0 flex-1">
            <span class="area-row__title">
              {{ __('Invoice {0}', [invoice.number]) }}
            </span>
            <span class="area-row__sub tabular-nums">
              {{ day(invoice.date) }} · {{ money(invoice.total) }}
            </span>
            <span
              v-if="invoice.to_pay"
              class="area-row__sub tabular-nums font-semibold text-ink-amber-8"
            >
              {{ __('To pay: {0}', [money(invoice.to_pay)]) }}
            </span>
            <!-- under the words, not beside them: at 320 the row has no room -->
            <span v-if="!invoice.has_pdf" class="area-row__sub">
              {{ __('PDF not ready') }}
            </span>
          </div>
          <!-- the centre's preview downloads nothing -->
          <Button
            v-if="invoice.has_pdf && !anteprima"
            class="shrink-0"
            size="lg"
            variant="subtle"
            label="PDF"
            :link="pdf(invoice)"
          />
        </div>
      </template>
      <p
        v-if="invoices.data && !invoices.data.invoices.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('Nothing here yet.') }}
      </p>
    </section>
    <CodeDialog v-model="asking" @verified="afterCode" />
  </div>
</template>

<script setup>
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { anteprima } from '../anteprima'
import AreaChip from '../components/AreaChip.vue'
import CodeDialog from '../components/CodeDialog.vue'
import HiddenCard from '../components/HiddenCard.vue'
import { day, money } from '../dates'
import { area, section } from '../store'

const documents = createResource({
  url: 'crm.documenti.area.get_documents',
  params: { person: area.person },
  auto: section('documents'),
})
const invoices = createResource({
  url: 'crm.area.api.get_invoices',
  params: { person: area.person },
  auto: true,
})

const asking = ref(false)
const waiting = ref(null)

function download(doc) {
  if (!documents.data?.verified) {
    waiting.value = doc
    asking.value = true
    return
  }
  go(doc)
}

function afterCode() {
  documents.data.verified = true
  if (waiting.value) go(waiting.value)
  waiting.value = null
}

function go(doc) {
  const params = new URLSearchParams({
    person: area.person,
    delivery: doc.name,
  })
  window.location.href = `/api/method/crm.documenti.area.download_document?${params}`
  doc.downloaded = true
}

function pdf(invoice) {
  const params = new URLSearchParams({
    person: area.person,
    invoice: invoice.name,
  })
  return `/api/method/crm.area.api.download_invoice?${params}`
}
</script>
