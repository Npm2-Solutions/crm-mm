<template>
  <!-- The codice fiscale and the address, written once for every invoice.
       Only for who may see billing details at all: marketing sees the person,
       not their codice fiscale. -->
  <div v-if="profile.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Billing details')"
        :opened="opened"
      >
        <div class="flex flex-col gap-1.5 pb-1">
          <template v-for="field in fields" :key="field.name">
            <div class="flex items-center gap-2 px-3 leading-5 first:mt-3">
              <div
                class="line-clamp-2 w-[35%] min-w-20 shrink-0 break-words text-sm text-ink-gray-5"
              >
                {{ field.label }}
              </div>
              <div class="grid min-h-[28px] min-w-0 flex-1 items-center">
                <TextInput
                  :key="field.name + resets"
                  class="form-control"
                  type="text"
                  variant="ghost"
                  :modelValue="values[field.name]"
                  :placeholder="__('Add {0}...', [field.label])"
                  :disabled="!profile.data.can_write || saving === field.name"
                  @change.stop="save(field.name, $event.target.value)"
                />
              </div>
            </div>
            <!-- what the codice fiscale says, right under it: the date of
                 birth and sex are read from it, never typed, and a code that
                 contradicts the person is said here, not refused -->
            <template v-if="field.name === 'fiscal_code'">
              <div
                v-if="bornOn"
                class="-mt-1 flex gap-2 px-3 text-p-sm leading-5 text-ink-gray-5"
              >
                <span class="w-[35%] min-w-20 shrink-0" />
                <span class="min-w-0 px-2">{{ bornOn }}</span>
              </div>
              <div
                v-for="warning in profile.data.warnings"
                :key="warning"
                class="mx-3 flex items-start gap-1.5 rounded bg-surface-amber-1 px-2 py-1.5 text-p-sm text-ink-amber-8"
              >
                <span
                  class="lucide-triangle-alert mt-0.5 size-3.5 shrink-0"
                  aria-hidden="true"
                />
                <span class="min-w-0">{{ warning }}</span>
              </div>
            </template>
          </template>
        </div>
      </CollapsibleSection>
    </div>
  </div>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { TextInput, createResource, call, toast } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  partyType: { type: String, default: 'CRM Lead' },
  party: { type: String, required: true },
})

const { puo } = usersStore()

const profile = createResource({
  url: 'crm.invoicing.anagrafica.get_billing_profile',
  makeParams: () => ({ party_type: props.partyType, party: props.party }),
  // a person the user sees but whose billing details they may not: nothing
  // to show, and nothing to say about it either
  onError: () => profile.setData(null),
})

watch(
  () => props.party,
  (party) => party && puo('persone.dati_fiscali') && profile.reload(),
  { immediate: true },
)

const values = computed(() => profile.data?.values || {})

// open when there is something in it, closed on a person with nothing yet: the
// panel above is what most people come for
const opened = computed(() =>
  Object.entries(values.value).some(([k, v]) => v && k !== 'country'),
)

const fields = computed(() => {
  const list = [
    { name: 'fiscal_code', label: __('Codice fiscale') },
    { name: 'tax_id', label: __('VAT number') },
    { name: 'recipient_code', label: __('Codice destinatario') },
    { name: 'pec', label: __('PEC') },
    { name: 'address_line', label: __('Address') },
    { name: 'civic_number', label: __('Number') },
    { name: 'postal_code', label: __('Postal code') },
    { name: 'city', label: __('City') },
    { name: 'province', label: __('Province') },
    { name: 'country', label: __('Country') },
  ]
  // a company's registered name can differ from the one the CRM knows it by;
  // a person's invoice carries their first name and surname
  if (props.partyType === 'CRM Organization') {
    list.unshift({ name: 'billing_name', label: __('Name on the invoice') })
  }
  return list
})

const bornOn = computed(() => {
  const data = profile.data
  if (!data?.birth_date) return ''
  const born = formatDate(data.birth_date, '', true)
  const sex = { M: __('male'), F: __('female') }[data.sex]
  return sex ? __('Born on {0}, {1}', [born, sex]) : __('Born on {0}', [born])
})

const saving = ref('')
// bumped to put the saved values back in the inputs after a refused change
const resets = ref(0)

async function save(fieldname, value) {
  if ((value || '') === (values.value[fieldname] || '')) return
  saving.value = fieldname
  try {
    const data = await call('crm.invoicing.anagrafica.save_billing_profile', {
      party_type: props.partyType,
      party: props.party,
      values: { [fieldname]: value },
    })
    profile.setData(data)
  } catch (err) {
    // the value goes back to what is saved: a codice fiscale that fails its
    // check is exactly the one that must not look accepted
    resets.value++
    toast.error(err.messages?.[0] || __('Could not save the billing details'))
  } finally {
    saving.value = ''
  }
}
</script>

<style scoped>
:deep(.form-control input) {
  border-color: transparent;
}

:deep(.form-control input::placeholder) {
  color: var(--ink-gray-4);
}
</style>
