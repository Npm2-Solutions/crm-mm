<!--
  Who signs the invoices.

  Everything a document needs before it can exist is on this one record: VAT
  number, registered office, tax regime, numbering, stamp duty, fund and
  withholding, and — for a practice that reports healthcare expenses — its Sistema
  TS category. A CRM can carry several of them; one is the default.
-->
<template>
  <!--
    One scroll for the whole page: the fields had a scroller of their own under
    what is still missing, and on a laptop it was a slit of 150px. The save bar
    stays at the bottom while the page scrolls.
  -->
  <div
    class="flex h-full flex-col gap-6 overflow-y-auto py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
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
          variant="solid"
          :label="__('New company')"
          iconLeft="plus"
          @click="nuova"
        />
      </div>
    </div>

    <!-- with the clinic on: a medical centre's invoicing, in three questions -->
    <HealthcareSetup
      v-if="corrente && !creando"
      :company="corrente"
      @saved="impostata"
    />

    <!-- What is still missing, and what each gap costs. A live list, not a
         document nobody opens: it gets shorter. -->
    <div
      v-if="checklist.data?.length && !creando"
      class="mx-2 flex flex-col gap-2 rounded-xl border border-outline-amber-2 bg-surface-amber-1 px-4 py-3"
    >
      <span class="text-p-base-medium text-ink-gray-8">
        {{ __('Still missing') }}
      </span>
      <div v-for="voce in checklist.data" :key="voce.title" class="text-p-sm">
        <span class="font-medium text-ink-gray-7">{{ voce.title }}</span>
        <span class="text-ink-gray-6"> — {{ voce.consequence }}</span>
      </div>
    </div>

    <div class="px-2">
      <!-- a new company starts where the DocType says: DocFields reads its defaults -->
      <DocFields
        v-if="corrente || creando"
        :key="creando ? 'nuova' : `${corrente}-${versione}`"
        doctype="CRM Invoicing Company"
        :docname="creando ? '' : corrente"
        :scroll="false"
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
import HealthcareSetup from '@/components/Settings/Invoicing/HealthcareSetup.vue'
import { createListResource, createResource, Button, Dropdown } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const corrente = ref('')
const creando = ref(false)
// the answers to the three questions change the record under the form: drawn again
const versione = ref(0)

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

function impostata() {
  versione.value += 1
  checklist.fetch({ company: corrente.value })
}

function salvata(nome) {
  creando.value = false
  corrente.value = nome
  companies.reload()
  checklist.fetch({ company: nome })
}
</script>
