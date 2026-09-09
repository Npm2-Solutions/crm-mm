<!--
  The switches that apply to every document, and the two buttons that only make
  sense here.

  Probing the Entratel mandate sends one real document and reads the answer, and
  reading the PEC mailbox applies the notices sitting in it. Both belong next to
  the configuration they depend on, not on an invoice.
-->
<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Invoicing') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'What applies to every document: what gets attached, how long a link stays open, and when silence becomes an alert.',
          )
        }}
      </p>
    </div>

    <div class="min-h-0 flex-1">
      <DocFields
        doctype="CRM Invoicing Settings"
        docname="CRM Invoicing Settings"
      />
    </div>

    <div class="flex flex-col gap-3 border-t border-outline-gray-2 pt-4">
      <div class="text-p-base-medium text-ink-gray-7">
        {{ __('Maintenance') }}
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <Button
          :loading="scansione"
          :label="__('Read the SdI mailbox')"
          iconLeft="mail"
          @click="scansiona"
        />
        <Dropdown v-if="companies.data?.length" :options="opzioniSonda">
          <Button :loading="sondaggio" iconRight="chevron-down">
            {{ __('Probe the Entratel mandate') }}
          </Button>
        </Dropdown>
      </div>
      <p class="text-p-sm text-ink-gray-5">
        {{
          __(
            'The mandate is not asked for, it is probed: one real document goes out in the practice’s own name and the rejection code answers. 105 means there is no mandate, 106 means there is one.',
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import DocFields from '@/components/Settings/Invoicing/DocFields.vue'
import { createListResource, Button, Dropdown, call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const scansione = ref(false)
const sondaggio = ref(false)

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'ts_mode'],
  filters: { enabled: 1 },
  pageLength: 100,
  auto: true,
})

const opzioniSonda = computed(() =>
  (companies.data || [])
    .filter((row) => row.ts_mode !== 'export')
    .map((row) => ({
      label: row.company_name,
      onClick: () => sonda(row.name),
    })),
)

async function scansiona() {
  scansione.value = true
  try {
    const esiti = await call('crm.invoicing.api.scan_sdi_mailbox', { days: 30 })
    toast.success(__('{0} notices applied', [esiti.length]))
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  } finally {
    scansione.value = false
  }
}

async function sonda(company) {
  sondaggio.value = true
  try {
    const esito = await call('crm.invoicing.api.probe_delegation', { company })
    // Not probed is an answer too: it needs one document waiting to send.
    if (esito.probed) toast.success(esito.summary)
    else toast.info(esito.reason)
    companies.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  } finally {
    sondaggio.value = false
  }
}
</script>
