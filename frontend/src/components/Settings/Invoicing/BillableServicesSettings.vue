<!--
  The fiscal card of a service.

  A service without a card is not billable, and that is the point: the exemption is
  a configured property somebody signs off, never something read out of the service
  name.
-->
<template>
  <RecordList
    ref="elenco"
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
    :defaults="predefiniti"
    :describe="descrivi"
    :badges="etichette"
  >
    <template #banner>
      <!-- with the clinic on: the agenda's services become cards in one click,
           healthcare and exempt, for the accountant to confirm -->
      <div
        v-if="sanitario && senzaScheda"
        class="mx-2 flex items-start justify-between gap-4 rounded-xl border border-outline-gray-2 px-4 py-3 max-md:flex-col"
      >
        <div class="flex min-w-0 flex-col gap-1">
          <span class="text-p-base-medium text-ink-gray-8">
            {{
              senzaScheda === 1
                ? __('One service of the agenda has no card')
                : __('{0} services of the agenda have no card', [senzaScheda])
            }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Each becomes a healthcare service, exempt, with the expense type of whoever issues and the agenda's price; one only somebody who is not exempt performs (an osteopath, a kinesiologist) is taxed at their rate. The accountant confirms them; one that is not a healthcare service (a course, a product) is corrected on its card.",
              )
            }}
          </span>
        </div>
        <Button
          class="shrink-0"
          variant="solid"
          :label="__('Create the cards')"
          :loading="crea.loading"
          @click="crea.submit()"
        />
      </div>
    </template>
  </RecordList>
</template>

<script setup>
import RecordList from '@/components/Settings/Invoicing/RecordList.vue'
import { useVocabolarioFatturazione } from '@/composables/vocabolarioFatturazione'
import { formatEuro } from '@/utils/invoicing'
import { nomeDi } from '@/utils/scelte'
import { createResource, toast, Button } from 'frappe-ui'
import { computed, ref } from 'vue'

const { nomi } = useVocabolarioFatturazione()
const elenco = ref(null)

// a medical centre's: what a new card starts as, and the services still without one
const setup = createResource({
  url: 'crm.tessera_sanitaria.preimpostazione.get_setup',
  auto: true,
})
const sanitario = computed(() => setup.data?.profile === 'sanitario')
const senzaScheda = computed(() => setup.data?.services_without_card || 0)
const predefiniti = computed(() =>
  sanitario.value && setup.data?.card_defaults
    ? setup.data.card_defaults
    : { enabled: 1, subject_to_stamp_duty: 1, vat_rate: 22 },
)

const crea = createResource({
  url: 'crm.tessera_sanitaria.preimpostazione.cards_from_services',
  onSuccess: (esito) => {
    const fatte = esito.created.length + esito.linked.length
    toast.success(
      fatte === 1 ? __('One card ready') : __('{0} cards ready', [fatte]),
    )
    setup.reload()
    elenco.value?.reload()
  },
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

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
