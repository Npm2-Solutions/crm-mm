<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The Invoices page's «Received» tab: the invoices the centre's suppliers sent,
  through Itala (crm/invoicing/ricevute.py). Found by a word or by what is left to
  do with them; one opens in its dialog; the month's files leave for the
  accountant as one ZIP, the issued ones with them.
-->
<template>
  <div class="flex flex-col gap-3">
    <div
      class="flex flex-wrap items-center gap-2 max-md:flex-col max-md:items-stretch"
    >
      <div class="flex flex-wrap gap-1">
        <Button
          v-for="filtro in filtri"
          :key="filtro.value"
          :variant="stato === filtro.value ? 'subtle' : 'ghost'"
          :label="filtro.label"
          @click="stato = filtro.value"
        />
      </div>
      <div class="flex min-w-0 flex-1 items-center gap-2 md:justify-end">
        <FormControl
          v-model="cerca"
          class="min-w-0 flex-1 md:max-w-64"
          type="text"
          v-bind="tastiera('cerca')"
          :placeholder="__('Supplier, number, VAT number')"
          :aria-label="__('Search the received invoices')"
        />
        <Dropdown v-if="puo('fatture.esporta')" :options="mesi">
          <Button
            class="shrink-0"
            iconLeft="download"
            :label="__('For the accountant')"
          />
        </Dropdown>
      </div>
    </div>

    <div v-if="elenco.data?.rows?.length" class="text-p-sm text-ink-gray-6">
      {{
        elenco.data.rows.length === 1
          ? __('One invoice, {0}', [formatEuro(elenco.data.total)])
          : __('{0} invoices, {1}', [
              elenco.data.rows.length,
              formatEuro(elenco.data.total),
            ])
      }}
    </div>

    <div
      v-for="riga in elenco.data?.rows || []"
      :key="riga.name"
      role="button"
      tabindex="0"
      class="flex cursor-pointer flex-col gap-2 rounded-xl border border-outline-gray-2 px-4 py-3 hover:bg-surface-gray-1 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
      @click="apri(riga.name)"
      @keydown.enter.self="apri(riga.name)"
    >
      <div class="flex min-w-0 flex-col">
        <span class="truncate text-p-base-medium text-ink-gray-8">
          {{ riga.supplier_name || riga.supplier_tax_id || __('A supplier') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{
            [
              riga.document_number,
              riga.document_date &&
                dayjs(riga.document_date).format('DD/MM/YYYY'),
              formatEuro(riga.total_amount),
            ]
              .filter(Boolean)
              .join(' · ')
          }}
        </span>
      </div>
      <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
        <Badge
          v-if="scadenza(riga)"
          :theme="scadenza(riga).theme"
          :label="scadenza(riga).label"
        />
        <Badge
          :theme="statoRicevuta(riga.status, __).theme"
          :label="statoRicevuta(riga.status, __).label"
        />
      </div>
    </div>

    <EmptyState
      v-if="elenco.fetched && !elenco.loading && !elenco.data?.rows?.length"
      :title="
        cerca || stato ? __('Nothing found') : __('No supplier invoices yet')
      "
      :text="
        cerca || stato
          ? __('Try another word, or another filter.')
          : __(
              'They arrive here through Itala once the centre has registered its recipient code at the Agenzia.',
            )
      "
    />

    <ReceivedInvoiceDialog
      v-model="aperta"
      :invoice="scelta"
      @changed="elenco.reload()"
    />
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import ReceivedInvoiceDialog from '@/components/Invoices/ReceivedInvoiceDialog.vue'
import { usersStore } from '@/stores/users'
import { formatEuro } from '@/utils/invoicing'
import {
  filtriRicevute,
  mesiDaEsportare,
  scadenzaRicevuta,
  statoRicevuta,
} from '@/utils/ricevute'
import { oggiDelCentro } from '@/utils/scheduler'
import { tastiera } from '@/utils/tastiera'
import { appLocale } from '@/utils/locale'
import { useDebounceFn } from '@vueuse/core'
import {
  createResource,
  Badge,
  Button,
  Dropdown,
  FormControl,
  dayjs,
} from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  company: { type: String, default: '' },
})

const { puo } = usersStore()
const route = useRoute()

const stato = ref('')
const cerca = ref('')
const aperta = ref(false)
const scelta = ref('')
const oggi = oggiDelCentro()

const filtri = computed(() => filtriRicevute(__))

const elenco = createResource({
  url: 'crm.invoicing.ricevute.get_received',
  makeParams: () => ({
    company: props.company,
    status: stato.value,
    search: cerca.value,
  }),
})

const cercaPiuTardi = useDebounceFn(() => elenco.reload(), 300)
watch([() => props.company, stato], () => elenco.reload(), { immediate: true })
watch(cerca, cercaPiuTardi)

function scadenza(riga) {
  return scadenzaRicevuta(riga, oggi, __)
}

function apri(nome) {
  scelta.value = nome
  aperta.value = true
}

// a notification about one opens it (`?ricevuta=`)
onMounted(() => {
  if (route.query.ricevuta) apri(String(route.query.ricevuta))
})

const nomeDelMese = (mese) =>
  new Intl.DateTimeFormat(appLocale(), { month: 'long' }).format(
    new Date(2026, mese - 1, 1),
  )

const mesi = computed(() =>
  mesiDaEsportare(oggi, nomeDelMese).map((mese) => ({
    label: mese.label,
    onClick: () =>
      window.open(
        `/api/method/crm.invoicing.ricevute.export_month?${new URLSearchParams({
          company: props.company,
          year: mese.year,
          month: mese.month,
        })}`,
        '_blank',
      ),
  })),
)
</script>
