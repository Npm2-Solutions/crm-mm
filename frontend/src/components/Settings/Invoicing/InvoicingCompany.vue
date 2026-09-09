<!--
  Who signs the invoices.

  Everything a document needs before it can exist is on this one record: VAT
  number, registered office, tax regime, numbering, stamp duty, fund and
  withholding, and — for a practice that reports healthcare expenses — its Sistema
  TS category. A CRM can carry several of them; one is the default.
-->
<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-start justify-between gap-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Issuing company') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The party whose VAT number goes on the invoice. Nothing can be issued until this exists.',
            )
          }}
        </p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Dropdown v-if="companies.data?.length > 1" :options="opzioni">
          <Button variant="ghost" iconRight="chevron-down">
            <span class="truncate">{{ etichettaCorrente }}</span>
          </Button>
        </Dropdown>
        <Button
          variant="subtle"
          :label="__('New company')"
          iconLeft="plus"
          @click="nuova"
        />
      </div>
    </div>

    <!-- What is still missing, and what each gap costs. A live list, not a
         document nobody opens: it gets shorter. -->
    <div
      v-if="checklist.data?.length"
      class="flex flex-col gap-2 rounded-xl border border-outline-amber-2 bg-surface-amber-1 px-4 py-3"
    >
      <span class="text-p-base-medium text-ink-gray-8">
        {{ __('Still missing') }}
      </span>
      <div v-for="voce in checklist.data" :key="voce.title" class="text-p-sm">
        <span class="font-medium text-ink-gray-7">{{ voce.title }}</span>
        <span class="text-ink-gray-6"> — {{ voce.consequence }}</span>
      </div>
    </div>

    <div class="min-h-0 flex-1">
      <DocFields
        v-if="corrente || creando"
        :key="corrente || 'nuova'"
        doctype="CRM Invoicing Company"
        :docname="creando ? '' : corrente"
        :defaults="creando ? predefiniti : {}"
        @saved="salvata"
      />
      <div v-else-if="!companies.loading" class="text-p-base text-ink-gray-5">
        {{ __('No company yet. Create the first one.') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import DocFields from '@/components/Settings/Invoicing/DocFields.vue'
import { createListResource, createResource, Button, Dropdown } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const corrente = ref('')
const creando = ref(false)

const predefiniti = {
  tax_regime: 'RF01',
  country: 'IT',
  series_electronic: 'E',
  series_healthcare: 'S',
  number_format: '{anno}/{serie}/{numero}',
  stamp_duty_mode: 'su_originale',
  sender_category: 'non_sanitario',
  ts_mode: 'export',
  sdi_mode: 'export',
  enabled: 1,
}

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'is_default'],
  orderBy: 'is_default desc, company_name asc',
  pageLength: 100,
  auto: true,
  onSuccess: (rows) => {
    if (!corrente.value && rows.length) corrente.value = rows[0].name
  },
})

const checklist = createResource({
  url: 'crm.invoicing.api.onboarding_checklist',
})

watch(corrente, (nome) => {
  if (nome) checklist.fetch({ company: nome })
})

const etichettaCorrente = computed(
  () =>
    (companies.data || []).find((r) => r.name === corrente.value)
      ?.company_name || __('Companies'),
)

const opzioni = computed(() =>
  (companies.data || []).map((row) => ({
    label: row.company_name,
    onClick: () => {
      creando.value = false
      corrente.value = row.name
    },
  })),
)

function nuova() {
  creando.value = true
}

function salvata(nome) {
  creando.value = false
  corrente.value = nome
  companies.reload()
  checklist.fetch({ company: nome })
}
</script>
