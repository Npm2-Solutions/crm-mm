<!--
  The connection to the accredited provider, and the door it pushes notices back
  through.

  Everything else about a channel is a field on the company and is rendered from
  the DocType's own layout. Two things here cannot be: the webhook URL, which is
  built rather than stored, and the secret, which is shown exactly once and then
  never again.

  The environment sits at the top and not in a fieldset, because it is the one
  setting whose wrong value is invisible: a practice on sandbox issues documents
  all day and reaches nobody.
-->
<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-start justify-between gap-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Provider connection') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'How documents leave, and how the outcome finds its way back. Without the return path nobody learns whether an invoice was accepted.',
            )
          }}
        </p>
      </div>
      <Dropdown v-if="opzioni.length > 1" :options="opzioni">
        <Button variant="ghost" iconRight="chevron-down">
          <span class="truncate">{{ etichettaCorrente }}</span>
        </Button>
      </Dropdown>
    </div>

    <div
      v-if="azienda"
      class="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto"
    >
      <!-- The environment. Loud on purpose: it is the only switch whose wrong
           value produces no error anywhere. -->
      <div
        class="flex items-start justify-between gap-4 rounded-xl border px-4 py-3"
        :class="
          inProduzione
            ? 'border-outline-green-2 bg-surface-green-1'
            : 'border-outline-amber-2 bg-surface-amber-1'
        "
      >
        <div class="flex flex-col gap-1">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ inProduzione ? __('Production') : __('Sandbox') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              inProduzione
                ? __('Documents sent from here are real and reach the SdI.')
                : __(
                    'Documents sent from here reach nobody. Nothing is issued until this says production.',
                  )
            }}
          </span>
        </div>
        <Button
          variant="subtle"
          :loading="cambiando"
          :label="inProduzione ? __('Back to sandbox') : __('Go to production')"
          @click="cambiaAmbiente"
        />
      </div>

      <!-- The return path. -->
      <div
        class="flex flex-col gap-3 rounded-xl border border-outline-gray-2 px-4 py-4"
      >
        <div class="flex flex-col gap-1">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('Notice webhook') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ endpoint.data?.hint || __('Loading…') }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <div
            class="flex-1 truncate rounded-lg bg-surface-gray-2 px-3 py-2 font-mono text-p-sm text-ink-gray-7"
          >
            {{ endpoint.data?.url || '—' }}
          </div>
          <Button
            variant="subtle"
            :label="__('Copy')"
            :disabled="!endpoint.data?.url"
            @click="copia(endpoint.data.url)"
          />
        </div>

        <div class="flex items-center justify-between gap-3">
          <span
            class="text-p-sm"
            :class="armato ? 'text-ink-green-3' : 'text-ink-amber-3'"
          >
            {{
              armato
                ? __(
                    'A secret is configured. The door only opens for the provider.',
                  )
                : __(
                    'No secret yet: the door stays shut and notices cannot arrive.',
                  )
            }}
          </span>
          <Button
            variant="solid"
            :loading="generando"
            :label="armato ? __('Rotate secret') : __('Generate secret')"
            @click="generaSegreto"
          />
        </div>

        <!-- Shown once. Storing it anywhere it could be read back would defeat
             the point of encrypting it. -->
        <div
          v-if="segreto"
          class="flex flex-col gap-2 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-3 py-3"
        >
          <span class="text-p-sm-medium text-ink-gray-8">{{ avviso }}</span>
          <div class="flex items-center gap-2">
            <div
              class="flex-1 select-all break-all rounded bg-surface-white px-2 py-1 font-mono text-p-sm"
            >
              {{ segreto }}
            </div>
            <Button
              variant="subtle"
              :label="__('Copy')"
              @click="copia(segreto)"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!companies.loading" class="text-p-base text-ink-gray-5">
      {{ __('Create an issuing company first.') }}
    </div>
  </div>
</template>

<script setup>
import {
  createListResource,
  createResource,
  call,
  Button,
  Dropdown,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const azienda = ref('')
const segreto = ref('')
const avviso = ref('')
const generando = ref(false)
const cambiando = ref(false)

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'provider_environment', 'is_default'],
  orderBy: 'is_default desc, company_name asc',
  pageLength: 100,
  auto: true,
  onSuccess: (rows) => {
    if (!azienda.value && rows.length) azienda.value = rows[0].name
  },
})

const endpoint = createResource({ url: 'crm.invoicing.api.webhook_endpoint' })

const corrente = computed(() =>
  (companies.data || []).find((r) => r.name === azienda.value),
)
const etichettaCorrente = computed(
  () => corrente.value?.company_name || __('Companies'),
)
const inProduzione = computed(
  () => corrente.value?.provider_environment === 'production',
)
const armato = computed(() => !!endpoint.data?.configured)

const opzioni = computed(() =>
  (companies.data || []).map((row) => ({
    label: row.company_name,
    onClick: () => {
      azienda.value = row.name
    },
  })),
)

watch(azienda, (nome) => {
  // A secret belongs to the company it was minted for: showing one while another
  // is selected is how it ends up pasted into the wrong dashboard.
  segreto.value = ''
  if (nome) endpoint.fetch({ company: nome })
})

async function generaSegreto() {
  generando.value = true
  try {
    const esito = await call('crm.invoicing.api.generate_webhook_secret', {
      company: azienda.value,
    })
    segreto.value = esito.secret
    avviso.value = esito.warning
    endpoint.fetch({ company: azienda.value })
  } catch (errore) {
    toast.error(errore.messages?.[0] || __('Could not generate the secret'))
  } finally {
    generando.value = false
  }
}

async function cambiaAmbiente() {
  cambiando.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Invoicing Company',
      name: azienda.value,
      fieldname: 'provider_environment',
      value: inProduzione.value ? 'sandbox' : 'production',
    })
    companies.reload()
  } catch (errore) {
    toast.error(errore.messages?.[0] || __('Could not change the environment'))
  } finally {
    cambiando.value = false
  }
}

function copia(testo) {
  navigator.clipboard.writeText(testo)
  toast.success(__('Copied'))
}
</script>
