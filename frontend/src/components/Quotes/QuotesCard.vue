<!--
  A person's quotes (crm.preventivi): in draft for their author, proposed for who
  reads the person's quotes and for the desk that records the answer, then done
  service by service. With the clinic, a dentist's quote is a care plan: its rows
  may be on a tooth. On the page of a deal of the quotes pipeline, the deal's quotes:
  a new one is the deal's. On any other deal's page, the person's.
-->
<template>
  <section
    v-if="quotes.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Quotes') }}
        <span
          v-if="quotes.data.quotes.length"
          class="text-ink-gray-5 tabular-nums"
        >
          {{ quotes.data.quotes.length }}
        </span>
      </h3>
      <Button
        v-if="quotes.data.can_write"
        class="shrink-0"
        icon-left="plus"
        :label="__('New quote')"
        @click="openQuote(null)"
      />
    </div>

    <p v-if="!quotes.data.quotes.length" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'No quote yet. A quote is the services from the price list, with their discount: proposed, it is a PDF to hand over; accepted, the appointments do it.',
        )
      }}
    </p>
    <div v-else class="flex flex-col">
      <button
        v-for="quote in quotes.data.quotes"
        :key="quote.name"
        type="button"
        class="flex items-center justify-between gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
        @click="openQuote(quote.name)"
      >
        <span class="flex min-w-0 flex-col">
          <span class="truncate text-base text-ink-gray-8">
            {{ quote.title }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ money(quote.total_net, quote.currency) }} ·
            {{ __('{0} of {1} done', [quote.done, quote.services]) }} ·
            {{ quote.practitioner_name }}
          </span>
        </span>
        <span class="flex shrink-0 items-center gap-2">
          <!-- read like the clinical record: the dossier's rules, the access log -->
          <Badge
            v-if="quote.clinical"
            size="sm"
            theme="gray"
            :label="__('Health data')"
          />
          <Badge
            variant="subtle"
            :theme="STATO[quote.status] || 'gray'"
            :label="__(quote.status, null, 'Quote')"
          />
        </span>
      </button>
    </div>

    <QuoteDialog
      v-model="dialog.show"
      :lead="lead"
      :deal="quotes.data.deal"
      :name="dialog.name"
      :price-lists="quotes.data.price_lists"
      :offers="quotes.data.offers"
      @changed="quotes.reload()"
    />
  </section>
</template>

<script setup>
import QuoteDialog from '@/components/Quotes/QuoteDialog.vue'
import { appLocale } from '@/utils/locale'
import { STATO } from '@/utils/preventivi'
import { Badge, Button, createResource } from 'frappe-ui'
import { reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
  // the deal whose page this is: the server says whether quotes may be its
  deal: { type: String, default: null },
})

const quotes = createResource({
  url: 'crm.preventivi.api.get_quotes',
  makeParams: () => ({ lead: props.lead, deal: props.deal }),
  onError: () => quotes.setData(null),
})

watch(
  () => [props.lead, props.deal],
  ([lead]) => lead && quotes.reload(),
  { immediate: true },
)

function money(amount, currency) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount || 0)
}

const dialog = reactive({ show: false, name: null })

function openQuote(name) {
  Object.assign(dialog, { show: true, name })
}

defineExpose({ reload: () => quotes.reload() })
</script>
