<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Invoicing > Test and go live (doc 49).

  A centre tries its invoicing before the first real invoice: every company starts
  in test, where an invoice is made and issued as it will be, numbered PROVA, and
  reaches nobody. Going live is one button, once nothing stops it: the test
  invoices go away and the real numbering starts at one.

  How invoices leave is not a choice here: electronic invoices through Itala, on
  the agency's account. What the agency keeps - the account, the company's
  registration at Itala, back to test, a company's own webhook - sits in its own
  block, for the agency only.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Test and go live') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Try invoicing before the first real invoice: in test the invoices are numbered PROVA and reach nobody.',
            )
          }}
        </p>
      </div>
      <Dropdown v-if="opzioni.length > 1" class="shrink-0" :options="opzioni">
        <Button variant="ghost" iconRight="chevron-down">
          <span class="truncate">{{ etichettaCorrente }}</span>
        </Button>
      </Dropdown>
    </div>

    <div
      v-if="stato.data?.company"
      class="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto px-2 pb-2"
    >
      <!-- where the company is: the one thing this page is for -->
      <div
        class="flex items-start justify-between gap-4 rounded-xl border px-4 py-4 max-md:flex-col max-md:items-start"
        :class="
          dalVivo
            ? 'border-outline-green-2 bg-surface-green-1'
            : 'border-outline-amber-2 bg-surface-amber-1'
        "
      >
        <div class="flex min-w-0 flex-col gap-1">
          <span class="text-base-semibold text-ink-gray-8">
            {{ dalVivo ? __('Live') : __('In test') }}
          </span>
          <span class="text-p-sm text-ink-gray-7">
            {{
              dalVivo
                ? stato.data.live_since
                  ? __('Since {0}: every invoice is real.', [
                      formatDate(stato.data.live_since, 'D MMMM YYYY'),
                    ])
                  : __('Every invoice is real.')
                : __(
                    'The invoices issued now are test invoices: numbered PROVA, with a band on the PDF, and they reach nobody.',
                  )
            }}
          </span>
          <span
            v-if="!dalVivo && stato.data.test_invoices"
            class="text-p-sm text-ink-gray-6"
          >
            {{
              stato.data.test_invoices === 1
                ? __('One test invoice issued so far.')
                : __('{0} test invoices issued so far.', [
                    stato.data.test_invoices,
                  ])
            }}
          </span>
        </div>
        <Button
          v-if="stato.data.can.go_live"
          class="shrink-0"
          variant="solid"
          :disabled="!stato.data.ready"
          :loading="lavoro === 'live'"
          :label="__('Go live')"
          @click="passaAlVivo"
        />
        <Button
          v-else-if="stato.data.can.back_to_test"
          class="shrink-0"
          variant="subtle"
          :loading="lavoro === 'test'"
          :label="__('Back to test')"
          @click="tornaInProva"
        />
      </div>

      <!-- what is missing: what stops going live first, then what is advised -->
      <section v-if="stato.data.missing.length" class="flex flex-col gap-3">
        <div class="flex flex-col gap-0.5">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ dalVivo ? __('Still missing') : __('Before going live') }}
          </h3>
          <p v-if="!dalVivo" class="text-p-sm text-ink-gray-5">
            {{
              stato.data.ready
                ? __('Nothing stops going live. These are worth doing too.')
                : __('What is marked with the cross is needed to go live.')
            }}
          </p>
        </div>
        <div class="flex flex-col divide-y divide-outline-gray-1">
          <!-- each gap a click from the page that fills it -->
          <div
            v-for="voce in mancanti"
            :key="voce.title"
            class="flex items-start justify-between gap-4 py-2.5"
          >
            <div class="flex min-w-0 flex-col gap-0.5">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ voce.title }}
                <!-- the brand's mark for what must be filled -->
                <span
                  v-if="voce.blocking && !dalVivo"
                  class="segno-obbligatorio text-ink-red-6"
                  :title="__('Needed to go live')"
                />
              </span>
              <span class="text-p-sm text-ink-gray-6">{{
                voce.consequence
              }}</span>
            </div>
            <Button
              v-if="paginaDellaMancanza(voce)"
              class="shrink-0"
              variant="subtle"
              :label="__('Set up')"
              @click="activeSettingsPage = paginaDellaMancanza(voce)"
            />
          </div>
        </div>
      </section>

      <!-- how invoices leave: said, not chosen -->
      <section class="flex flex-col gap-3">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __('How invoices leave') }}
        </h3>
        <div class="flex flex-col gap-2 text-p-sm text-ink-gray-7">
          <!-- a centre that reports no healthcare expense: every invoice is electronic -->
          <div v-if="!stato.data.healthcare" class="flex items-start gap-2">
            <LucideSend class="mt-0.5 size-4 shrink-0 text-ink-gray-5" />
            <span>
              {{
                stato.data.itala
                  ? __(
                      'Every invoice reaches the SdI through Itala, an intermediary accredited by the Agenzia delle Entrate, and the client gets it as a PDF too. Connected.',
                    )
                  : __(
                      'Every invoice reaches the SdI through Itala, an intermediary accredited by the Agenzia delle Entrate, and the client gets it as a PDF too. {brand} connects it.',
                    )
              }}
            </span>
          </div>
          <div v-else class="flex items-start gap-2">
            <LucideSend class="mt-0.5 size-4 shrink-0 text-ink-gray-5" />
            <span>
              {{
                stato.data.itala
                  ? __(
                      'Electronic invoices, to companies and public bodies: through Itala, an intermediary accredited by the Agenzia delle Entrate. Connected.',
                    )
                  : __(
                      'Electronic invoices, to companies and public bodies: through Itala, an intermediary accredited by the Agenzia delle Entrate. {brand} connects it.',
                    )
              }}
            </span>
          </div>
          <div v-if="stato.data.healthcare" class="flex items-start gap-2">
            <LucideFileText class="mt-0.5 size-4 shrink-0 text-ink-gray-5" />
            <span>
              {{
                __(
                  'Invoices to patients: a PDF to the patient, and the expense to the Sistema TS in the centre’s name, with its credentials.',
                )
              }}
            </span>
          </div>
        </div>
      </section>

      <!-- the agency's: the account, the registration, a company's own webhook -->
      <section
        v-if="stato.data.agency"
        class="flex flex-col gap-4 rounded-xl border border-outline-gray-2 px-4 py-4"
      >
        <div class="flex flex-col gap-0.5">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Itala, for the agency') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Only the agency sees this block: the account every centre sends with, and where this company stands at Itala.',
              )
            }}
          </p>
        </div>

        <div
          class="grid grid-cols-2 gap-x-6 gap-y-3 text-p-sm max-md:grid-cols-1"
        >
          <div class="flex flex-col gap-0.5">
            <span class="text-ink-gray-5">{{ __('Itala account') }}</span>
            <span class="text-ink-gray-8">{{ account }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-ink-gray-5">{{ __('Channel') }}</span>
            <span class="text-ink-gray-8">{{ canale }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-ink-gray-5">{{
              __('Registered at Itala, test')
            }}</span>
            <span class="text-ink-gray-8">{{
              stato.data.agency.registered.test || __('Not yet')
            }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-ink-gray-5">{{
              __('Registered at Itala, production')
            }}</span>
            <span class="text-ink-gray-8">{{
              stato.data.agency.registered.production || __('Not yet')
            }}</span>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            v-if="
              stato.data.agency.mode === 'provider' &&
              !stato.data.agency.own_account &&
              stato.data.itala &&
              !registrataQui
            "
            :loading="lavoro === 'registra'"
            :label="__('Register at Itala now')"
            @click="registra"
          />
          <!-- a centre that leaves: it stops sending and receiving through the
               agency's account -->
          <Button
            v-if="
              !stato.data.agency.own_account &&
              stato.data.agency.registered.production
            "
            theme="red"
            :loading="lavoro === 'togli'"
            :label="__('Remove from Itala')"
            @click="togliDaItala"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The account is entered in Invoicing > Options, or once for the whole server; the company is registered by itself with its first electronic invoice.',
              )
            }}
          </span>
        </div>

        <!-- a company with an account of its own: Itala pushes its updates here -->
        <div
          v-if="stato.data.agency.own_account"
          class="flex flex-col gap-3 border-t border-outline-gray-2 pt-4"
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
              class="min-w-0 flex-1 truncate rounded-lg bg-surface-gray-2 px-3 py-2 font-mono text-p-sm text-ink-gray-7"
            >
              {{ endpoint.data?.url || '—' }}
            </div>
            <Button
              class="shrink-0"
              variant="subtle"
              :label="__('Copy')"
              :disabled="!endpoint.data?.url"
              @click="copia(endpoint.data.url)"
            />
          </div>
          <div
            class="flex items-center justify-between gap-3 max-md:flex-col max-md:items-start"
          >
            <span
              class="text-p-sm"
              :class="armato ? 'text-ink-green-8' : 'text-ink-amber-8'"
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
              class="shrink-0"
              variant="solid"
              :loading="lavoro === 'segreto'"
              :label="armato ? __('Rotate secret') : __('Generate secret')"
              @click="generaSegreto"
            />
          </div>
          <!-- shown once: a secret that can be read back out of a screen is one
               that can be read out of a screenshot -->
          <div
            v-if="segreto"
            class="flex flex-col gap-2 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-3 py-3"
          >
            <span class="text-p-sm-medium text-ink-gray-8">{{ avviso }}</span>
            <div class="flex items-center gap-2">
              <div
                class="min-w-0 flex-1 select-all break-all rounded bg-surface-elevation-2 px-2 py-1 font-mono text-p-sm text-ink-gray-9"
              >
                {{ segreto }}
              </div>
              <Button
                class="shrink-0"
                variant="subtle"
                :label="__('Copy')"
                @click="copia(segreto)"
              />
            </div>
          </div>
        </div>
      </section>
    </div>

    <div
      v-else-if="!stato.loading && !companies.loading"
      class="px-2 text-p-base text-ink-gray-5"
    >
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
import { activeSettingsPage } from '@/composables/settings'
import { inOrdine, paginaDellaMancanza } from '@/utils/mancanze'
import LucideFileText from '~icons/lucide/file-text'
import LucideSend from '~icons/lucide/send'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import { computed, ref, watch } from 'vue'

const { $dialog } = globalStore()

const azienda = ref('')
const segreto = ref('')
const avviso = ref('')
const lavoro = ref('')

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'is_default'],
  orderBy: 'is_default desc, company_name asc',
  pageLength: 100,
  auto: true,
  onSuccess: (rows) => {
    if (!azienda.value && rows.length) azienda.value = rows[0].name
  },
})

const stato = createResource({ url: 'crm.invoicing.prova.get_status' })
const endpoint = createResource({ url: 'crm.invoicing.api.webhook_endpoint' })

const dalVivo = computed(() => !!stato.data?.live)
const etichettaCorrente = computed(
  () =>
    (companies.data || []).find((r) => r.name === azienda.value)
      ?.company_name || __('Companies'),
)
const opzioni = computed(() =>
  (companies.data || []).map((row) => ({
    label: row.company_name,
    onClick: () => {
      azienda.value = row.name
    },
  })),
)
// what stops going live first, then the rest
const mancanti = computed(() => inOrdine(stato.data?.missing))
const registrataQui = computed(() => {
  const registrata = stato.data?.agency?.registered || {}
  return dalVivo.value ? !!registrata.production : !!registrata.test
})
const account = computed(() => {
  const agenzia = stato.data?.agency
  if (!agenzia) return ''
  if (agenzia.own_account) return __('The company’s own')
  if (agenzia.account === 'site') return __('The agency’s, on this site')
  if (agenzia.account === 'server')
    return __('The agency’s, for the whole server')
  return __('Not entered yet')
})
const canale = computed(() => {
  const modo = stato.data?.agency?.mode
  if (modo === 'pec') return __('The centre’s PEC mailbox')
  if (modo === 'export') return __('Download and upload it yourself')
  return __('Itala, automatic')
})
const armato = computed(() => !!endpoint.data?.configured)

watch(azienda, (nome) => {
  // a secret belongs to the company it was minted for
  segreto.value = ''
  if (nome) stato.fetch({ company: nome })
})

watch(
  () => stato.data?.agency?.own_account,
  (proprio) => {
    if (proprio && azienda.value) endpoint.fetch({ company: azienda.value })
  },
)

function passaAlVivo() {
  const prova = stato.data?.test_invoices || 0
  $dialog({
    title: __('Go live?'),
    message:
      prova === 0
        ? __('From now on every invoice is real, numbered from one.')
        : prova === 1
          ? __(
              'From now on every invoice is real, numbered from one. The test invoice is removed.',
            )
          : __(
              'From now on every invoice is real, numbered from one. The {0} test invoices are removed.',
              [prova],
            ),
    actions: [
      {
        label: __('Go live'),
        variant: 'solid',
        onClick: async (chiudi) => {
          chiudi()
          lavoro.value = 'live'
          try {
            const esito = await call('crm.invoicing.prova.go_live', {
              company: azienda.value,
            })
            stato.data = esito.status
            toast.success(__('Invoicing is live'))
            if (esito.note) toast.warning(esito.note)
          } catch (e) {
            toast.error(e.messages?.[0] || __('Could not go live'))
          } finally {
            lavoro.value = ''
          }
        },
      },
    ],
  })
}

async function tornaInProva() {
  lavoro.value = 'test'
  try {
    stato.data = await call('crm.invoicing.prova.back_to_test', {
      company: azienda.value,
    })
    toast.success(__('Invoicing is back in test'))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not go back to test'))
  } finally {
    lavoro.value = ''
  }
}

async function registra() {
  lavoro.value = 'registra'
  try {
    const esito = await call('crm.invoicing.prova.register_at_itala', {
      company: azienda.value,
    })
    stato.data = esito.status
    toast.success(__('Registered at Itala'))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not register at Itala'))
  } finally {
    lavoro.value = ''
  }
}

function togliDaItala() {
  $dialog({
    title: __('Remove the company from Itala?'),
    message: __(
      'Only for a centre that leaves: its invoices stop leaving through the agency’s account, and the ones its suppliers send stop arriving here.',
    ),
    actions: [
      {
        label: __('Remove from Itala'),
        variant: 'solid',
        theme: 'red',
        onClick: async (chiudi) => {
          chiudi()
          lavoro.value = 'togli'
          try {
            const esito = await call('crm.invoicing.prova.remove_from_itala', {
              company: azienda.value,
            })
            stato.data = esito.status
            toast.success(__('Removed from Itala'))
          } catch (e) {
            toast.error(e.messages?.[0] || __('Could not remove it from Itala'))
          } finally {
            lavoro.value = ''
          }
        },
      },
    ],
  })
}

async function generaSegreto() {
  lavoro.value = 'segreto'
  try {
    const esito = await call('crm.invoicing.api.generate_webhook_secret', {
      company: azienda.value,
    })
    segreto.value = esito.secret
    avviso.value = esito.warning
    endpoint.fetch({ company: azienda.value })
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not generate the secret'))
  } finally {
    lavoro.value = ''
  }
}

function copia(testo) {
  navigator.clipboard.writeText(testo)
  toast.success(__('Copied'))
}
</script>
