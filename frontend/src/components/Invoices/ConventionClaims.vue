<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The Invoices page's «Conventions» tab (crm/convenzioni, doc 61): a fund's
  pratiche of a month in direct form - to authorise, authorised, done, billed,
  paid - with what the people paid and what the fund owes. The month's statement
  leaves as one invoice to the company that pays, a line a pratica (made by the
  invoicing engine, opened in its dialog to check and issue), and as a CSV for
  the fund's portal.
-->
<template>
  <div class="flex flex-col gap-3">
    <div
      v-if="dati.data && !dati.data.conventions.length"
      class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4 text-p-sm text-ink-gray-6"
    >
      {{
        __(
          'No convention in direct form yet: a fund that pays the centre is set up in Settings > Invoicing > Conventions and funds.',
        )
      }}
    </div>

    <template v-else-if="dati.data">
      <div
        class="flex flex-wrap items-center gap-2 max-md:flex-col max-md:items-stretch"
      >
        <FormControl
          class="min-w-0 md:w-64"
          type="select"
          :aria-label="__('Convention')"
          :modelValue="dati.data.convention"
          :options="opzioni"
          @update:modelValue="(v) => carica(v, mese)"
        />
        <div class="flex items-center gap-1">
          <Button
            variant="ghost"
            icon="chevron-left"
            :aria-label="__('The month before')"
            @click="carica(dati.data.convention, meseAccanto(mese, -1))"
          />
          <span
            class="min-w-32 text-center text-p-base-medium text-ink-gray-8 first-letter:uppercase"
          >
            {{ nomeDelMese }}
          </span>
          <Button
            variant="ghost"
            icon="chevron-right"
            :aria-label="__('The month after')"
            @click="carica(dati.data.convention, meseAccanto(mese, 1))"
          />
        </div>
        <div class="flex flex-1 flex-wrap items-center gap-2 md:justify-end">
          <Button
            :label="__('Export the month')"
            icon-left="download"
            :disabled="!dati.data.claims.length"
            @click="esporta"
          />
          <Button
            v-if="dati.data.can_bill"
            variant="solid"
            :label="__('Invoice the fund')"
            :disabled="!dati.data.totals.to_bill_count"
            :loading="fatturando"
            @click="fatturaAlFondo"
          />
        </div>
      </div>

      <!-- the month in numbers: the deep block is what the fund still owes -->
      <div class="grid grid-cols-[repeat(auto-fit,minmax(8.5rem,1fr))] gap-2">
        <div
          class="min-w-0 rounded-xl border border-outline-gray-2 px-4 py-3 max-md:px-3 max-md:py-2"
        >
          <div class="text-p-sm text-ink-gray-6">{{ __('Pratiche') }}</div>
          <div class="text-xl-semibold text-ink-gray-9 max-md:text-lg-semibold">
            {{ dati.data.totals.count }}
          </div>
        </div>
        <div
          class="min-w-0 rounded-xl border border-outline-gray-2 px-4 py-3 max-md:px-3 max-md:py-2"
        >
          <div class="text-p-sm text-ink-gray-6">
            {{ __("The people's share") }}
          </div>
          <div class="text-xl-semibold text-ink-gray-9 max-md:text-lg-semibold">
            {{ soldi(dati.data.totals.patient_share) }}
          </div>
        </div>
        <div
          class="min-w-0 rounded-xl border border-outline-gray-2 px-4 py-3 max-md:px-3 max-md:py-2"
        >
          <div class="text-p-sm text-ink-gray-6">
            {{ __('To bill to the fund') }}
          </div>
          <div class="text-xl-semibold text-ink-gray-9 max-md:text-lg-semibold">
            {{ soldi(dati.data.totals.to_bill) }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __('of {0} for the month', [soldi(dati.data.totals.fund_share)])
            }}
          </div>
        </div>
      </div>
      <p v-if="dati.data.payer" class="text-p-sm text-ink-gray-6">
        {{ __('Invoiced to {0}, through the SdI.', [dati.data.payer]) }}
      </p>

      <div
        v-if="!dati.data.claims.length"
        class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4 text-p-sm text-ink-gray-5"
      >
        {{ __('No appointment in direct form this month.') }}
      </div>
      <div
        v-for="p in dati.data.claims"
        :key="p.appointment"
        class="flex flex-col gap-1.5 rounded-xl border border-outline-gray-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
      >
        <div class="flex min-w-0 flex-col gap-0.5">
          <span class="flex flex-wrap items-center gap-x-2">
            <span
              class="max-w-full truncate text-p-base-medium text-ink-gray-8"
            >
              {{ p.patient }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{ formatDate(p.date, 'D MMM, HH:mm') }}
            </span>
          </span>
          <span class="text-p-sm text-ink-gray-6 [overflow-wrap:anywhere]">
            {{
              [
                p.service,
                p.authorisation
                  ? __('Authorisation {0}', [p.authorisation])
                  : '',
                p.card_number ? __('Card {0}', [p.card_number]) : '',
              ]
                .filter(Boolean)
                .join(' · ')
            }}
          </span>
        </div>
        <div class="flex shrink-0 flex-wrap items-center gap-2">
          <span class="text-p-sm tabular-nums text-ink-gray-7">
            {{
              __('{0} the person · {1} the fund', [
                soldi(p.patient_share),
                soldi(p.fund_share),
              ])
            }}
          </span>
          <Badge
            variant="subtle"
            :theme="statoInParole(p.state, t).theme"
            :label="statoInParole(p.state, t).label"
          />
          <Button
            v-if="p.invoice_name"
            size="sm"
            variant="ghost"
            :label="p.invoice"
            @click="apriFattura(p.invoice_name, { alCambio: ricarica })"
          />
        </div>
      </div>
    </template>
    <div v-else class="flex justify-center py-10">
      <LoadingIndicator class="size-6" />
    </div>
  </div>
</template>

<script setup>
import { useFattura } from '@/composables/fattura'
import { formatDate } from '@/utils'
import { meseAccanto, statoInParole } from '@/utils/convenzioni'
import { appLocale } from '@/utils/locale'
import { oggiDelCentro } from '@/utils/scheduler'
import {
  Badge,
  Button,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const t = (text, args, context) => __(text, args, context)
const { apriFattura } = useFattura()

const mese = ref(oggiDelCentro().slice(0, 7))
const fatturando = ref(false)

const dati = createResource({
  url: 'crm.convenzioni.api.get_claims',
  makeParams: () => ({ month: mese.value }),
  auto: true,
})

function carica(convenzione, nuovoMese) {
  mese.value = nuovoMese
  dati.submit({ convention: convenzione, month: nuovoMese }).catch(() => {})
}

function ricarica() {
  carica(dati.data?.convention, mese.value)
}

const opzioni = computed(() =>
  (dati.data?.conventions || []).map((c) => ({
    label: c.enabled
      ? c.convention_name
      : `${c.convention_name} (${__('Off')})`,
    value: c.name,
  })),
)

const nomeDelMese = computed(() =>
  new Intl.DateTimeFormat(appLocale(), {
    month: 'long',
    year: 'numeric',
  }).format(new Date(`${mese.value}-15T12:00:00`)),
)

function soldi(importo) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: 'EUR',
  }).format(Number(importo) || 0)
}

async function fatturaAlFondo() {
  fatturando.value = true
  try {
    const nome = await call('crm.convenzioni.api.bill_fund', {
      convention: dati.data.convention,
      month: mese.value,
    })
    toast.success(__('Draft to the fund ready: check it and issue it'))
    ricarica()
    apriFattura(nome, { alCambio: ricarica })
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not make the invoice'))
  } finally {
    fatturando.value = false
  }
}

async function esporta() {
  try {
    const file = await call('crm.convenzioni.api.export_month', {
      convention: dati.data.convention,
      month: mese.value,
    })
    // a BOM, so that Excel reads the accents
    const blob = new Blob(['﻿' + file.content], {
      type: 'text/csv;charset=utf-8',
    })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = file.filename
    link.click()
    setTimeout(() => URL.revokeObjectURL(link.href), 1000)
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not export'))
  }
}
</script>
