<!--
  A medical centre's invoicing in three questions.

  With the clinic on, the issuing company is a medical centre's: who issues the
  invoices, under which regime and, for a professional in their own name, which
  profession. The answers set the Sistema TS category, the regime, the fund and the
  withholding (crm.tessera_sanitaria.preimpostazione); what follows from them — the
  exemption, the expense type, which invoices go to the SdI — is worked out, never
  asked.
-->
<template>
  <div
    v-if="setup.data?.profile === 'sanitario' && company"
    class="mx-2 flex items-start justify-between gap-4 rounded-xl border px-4 py-3 max-md:flex-col"
    :class="
      setup.data.done
        ? 'border-outline-gray-2'
        : 'border-outline-amber-2 bg-surface-amber-1'
    "
  >
    <div class="flex min-w-0 flex-col gap-1">
      <span class="text-p-base-medium text-ink-gray-8">
        {{
          setup.data.done
            ? __("The centre's invoicing")
            : __("Set up the centre's invoicing")
        }}
      </span>
      <span v-if="setup.data.done" class="text-p-sm text-ink-gray-6">
        {{ riassunto }}
      </span>
      <span v-else class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Three questions: who issues the invoices, under which tax regime and, for a professional, which profession. The rest is set from the answers.',
          )
        }}
      </span>
    </div>
    <Button
      class="shrink-0"
      :variant="setup.data.done ? 'subtle' : 'solid'"
      :label="setup.data.done ? __('Change') : __('Answer them')"
      @click="apri"
    />
  </div>

  <Dialog v-model="aperto" :options="{ title: titolo, size: 'xl' }">
    <template #body-content>
      <div v-if="setup.data" class="flex flex-col gap-6">
        <fieldset class="flex flex-col gap-2">
          <legend class="mb-2 text-p-base-medium text-ink-gray-8">
            {{ __('Who issues the invoices?') }}
          </legend>
          <Scelta
            v-for="scelta in setup.data.issuers"
            :key="scelta.value"
            v-model="risposte.issuer"
            :scelta="scelta"
            nome="issuer"
          />
        </fieldset>

        <fieldset v-if="struttura" class="flex flex-col gap-2">
          <legend class="mb-1 text-p-base-medium text-ink-gray-8">
            {{ __('The codes the Region gave the facility') }}
          </legend>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'They are on the authorisation to the Sistema TS (the Codice Proprietario): the Sistema TS recognises the facility by them.',
              )
            }}
          </p>
          <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
            <FormControl
              v-model="risposte.region_code"
              :label="__('Region code')"
              maxlength="3"
            />
            <FormControl
              v-model="risposte.asl_code"
              :label="__('ASL code')"
              maxlength="3"
            />
            <FormControl
              v-model="risposte.ssa_code"
              :label="__('Facility code (SSA)')"
              maxlength="6"
            />
          </div>
        </fieldset>

        <template v-else-if="risposte.issuer">
          <fieldset class="flex flex-col gap-2">
            <legend class="mb-2 text-p-base-medium text-ink-gray-8">
              {{ __('Which profession?') }}
            </legend>
            <FormControl
              v-model="risposte.profession"
              type="select"
              :options="professioni"
              :description="cassaDellaProfessione"
            />
          </fieldset>
          <fieldset class="flex flex-col gap-2">
            <legend class="mb-2 text-p-base-medium text-ink-gray-8">
              {{ __('Under which tax regime?') }}
            </legend>
            <Scelta
              v-for="scelta in setup.data.regimes"
              :key="scelta.value"
              v-model="risposte.regime"
              :scelta="scelta"
              nome="regime"
            />
          </fieldset>
        </template>
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="aperto = false" />
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="!completa"
          :loading="salva.loading"
          @click="salva.submit()"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Scelta from '@/components/Settings/Invoicing/SceltaRadio.vue'
import {
  createResource,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  company: { type: String, default: '' },
})
const emit = defineEmits(['saved'])

const titolo = __("Set up the centre's invoicing")
const aperto = ref(false)
const errore = ref('')
const risposte = reactive({
  issuer: '',
  regime: 'RF01',
  profession: '',
  region_code: '',
  asl_code: '',
  ssa_code: '',
})

const setup = createResource({
  url: 'crm.tessera_sanitaria.preimpostazione.get_setup',
})

watch(
  () => props.company,
  (company) => company && setup.fetch({ company }),
  { immediate: true },
)

const struttura = computed(() =>
  (setup.data?.facilities || []).includes(risposte.issuer),
)

const professioni = computed(() => [
  { label: '', value: '' },
  ...((setup.data?.professions || {})[risposte.issuer] || []),
])

const cassaDellaProfessione = computed(
  () =>
    professioni.value.find((p) => p.value === risposte.profession)
      ?.description || '',
)

const completa = computed(
  () =>
    risposte.issuer &&
    (struttura.value
      ? risposte.region_code && risposte.asl_code && risposte.ssa_code
      : risposte.profession && risposte.regime),
)

// a facility invoices under the ordinary regime; a profession belongs to who issues
watch(
  () => risposte.issuer,
  () => {
    if (struttura.value) risposte.regime = 'RF01'
    if (!professioni.value.some((p) => p.value === risposte.profession)) {
      risposte.profession = ''
    }
  },
)

const riassunto = computed(() => {
  const dati = setup.data
  if (!dati?.done) return ''
  const chi = dati.issuers.find((s) => s.value === dati.values.sender_category)
  const regime = dati.regimes.find((s) => s.value === dati.values.tax_regime)
  return [chi?.label, regime?.label, dati.expense_type?.label]
    .filter(Boolean)
    .join(' · ')
})

function apri() {
  const valori = setup.data?.values || {}
  Object.assign(risposte, {
    issuer: setup.data?.issuers.some((s) => s.value === valori.sender_category)
      ? valori.sender_category
      : '',
    regime: valori.tax_regime || 'RF01',
    profession: valori.profession || '',
    region_code: valori.region_code || '',
    asl_code: valori.asl_code || '',
    ssa_code: valori.ssa_code || '',
  })
  errore.value = ''
  aperto.value = true
}

const salva = createResource({
  url: 'crm.tessera_sanitaria.preimpostazione.apply_setup',
  makeParams: () => ({ company: props.company, ...risposte }),
  onSuccess: (dati) => {
    setup.data = dati
    aperto.value = false
    toast.success(__('Saved'))
    emit('saved')
  },
  onError: (e) => {
    errore.value = e.messages?.[0] || e.message
  },
})
</script>
