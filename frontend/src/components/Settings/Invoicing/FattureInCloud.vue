<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Invoicing > Fatture in Cloud (crm/invoicing/fic).

  For a centre that invoices with Fatture in Cloud: its manager connects it once,
  signing in there; then, which of its VAT rates, accounts and numerations stand
  for the ones here, who reports to the Sistema TS, and the switch that has the
  invoices born there from now on. What is the agency's - the app, the address
  Fatture in Cloud sends back to - is said to the agency only.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2
        class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
      >
        {{ __('Fatture in Cloud') }}
      </h2>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'If the centre invoices with Fatture in Cloud: the invoices made here are born there, with their number.',
          )
        }}
      </p>
    </template>
    <template #header-actions>
      <div class="flex shrink-0 items-center gap-2">
        <Dropdown v-if="aziende.length > 1" :options="aziende">
          <Button variant="ghost" iconRight="chevron-down">
            <span class="truncate">{{ dati?.company_label }}</span>
          </Button>
        </Dropdown>
        <AzioneImpostazioni
          v-if="stato === 'collegato'"
          :loading="lavoro === 'salva'"
          :disabled="!modificato"
          @click="salva"
        />
      </div>
    </template>
    <template #content>
      <div v-if="pagina.data" class="flex flex-col gap-6 pb-6">
        <!-- not set up by the agency yet: nothing to press -->
        <div
          v-if="stato === 'agenzia'"
          class="rounded-xl border border-outline-gray-2 px-4 py-4 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The agency has not set up the connection to Fatture in Cloud on this server yet.',
            )
          }}
        </div>

        <!-- what changes, before connecting -->
        <section
          v-if="stato === 'scollegato'"
          class="flex flex-col gap-4 rounded-xl border border-outline-gray-2 px-4 py-4"
        >
          <ul class="flex flex-col gap-2.5 text-p-sm text-ink-gray-7">
            <li v-for="riga in cosaCambia" :key="riga.testo" class="flex gap-2">
              <component
                :is="riga.icona"
                class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
                aria-hidden="true"
              />
              <span>{{ riga.testo }}</span>
            </li>
          </ul>
          <div class="flex flex-wrap items-center gap-3">
            <Button
              variant="solid"
              :loading="lavoro === 'collega'"
              :label="__('Connect Fatture in Cloud')"
              @click="collega"
            />
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'A window of Fatture in Cloud asks you to sign in and to allow the connection.',
                )
              }}
            </span>
          </div>
        </section>

        <!-- connected: to which company, by whom -->
        <section
          v-if="['collegato', 'da_ricollegare', 'da_scegliere'].includes(stato)"
          class="flex items-start justify-between gap-4 rounded-xl border px-4 py-4 max-md:flex-col max-md:items-stretch"
          :class="
            stato === 'da_ricollegare'
              ? 'border-outline-red-2 bg-surface-red-1'
              : 'border-outline-gray-2'
          "
        >
          <div class="flex min-w-0 flex-col gap-1">
            <span
              class="text-base-semibold text-ink-gray-8 [overflow-wrap:anywhere]"
            >
              {{
                dati.fic_company
                  ? dati.fic_company.name
                  : __('Connected to Fatture in Cloud')
              }}
            </span>
            <span
              v-if="dati.fic_company?.vat_number"
              class="text-p-sm text-ink-gray-6"
            >
              {{ __('VAT number {0}', [dati.fic_company.vat_number]) }}
            </span>
            <span v-if="dati.connected_by" class="text-p-sm text-ink-gray-6">
              {{
                __('Connected by {0} on {1}', [
                  dati.connected_by,
                  formatDate(dati.connected_on, 'D MMMM YYYY'),
                ])
              }}
            </span>
            <span
              v-if="stato === 'da_ricollegare'"
              class="text-p-sm text-ink-red-7"
            >
              {{
                dati.last_error ||
                __(
                  'Fatture in Cloud no longer recognises the access: connect it again.',
                )
              }}
            </span>
          </div>
          <div class="flex shrink-0 flex-wrap gap-2">
            <Button
              :variant="stato === 'da_ricollegare' ? 'solid' : 'subtle'"
              :loading="lavoro === 'collega'"
              :label="__('Connect again')"
              @click="collega"
            />
            <Button
              variant="ghost"
              theme="red"
              :label="__('Disconnect')"
              @click="scollega"
            />
          </div>
        </section>

        <!-- more than one company there: which one issues here -->
        <section v-if="stato === 'da_scegliere'" class="flex flex-col gap-3">
          <div class="flex flex-col gap-0.5">
            <h3 class="text-base-semibold text-ink-gray-8">
              {{ __('Which company in Fatture in Cloud') }}
            </h3>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Whoever connected it sees more than one: choose the one with the VAT number of {0}.',
                  [dati.company_label],
                )
              }}
            </p>
          </div>
          <div class="flex flex-col gap-2">
            <!-- the whole row is the target, words wrapping as they need -->
            <button
              v-for="voce in dati.to_choose"
              :key="voce.id"
              type="button"
              class="flex items-start justify-between gap-3 rounded-lg border border-outline-gray-2 px-3 py-2.5 text-left hover:bg-surface-gray-1 disabled:opacity-60"
              :disabled="Boolean(lavoro)"
              @click="scegli(voce.id)"
            >
              <span class="flex min-w-0 flex-col">
                <span
                  class="text-p-base text-ink-gray-8 [overflow-wrap:anywhere]"
                >
                  {{ voce.name }}
                </span>
                <span v-if="voce.vat_number" class="text-p-sm text-ink-gray-6">
                  {{ __('VAT number {0}', [voce.vat_number]) }}
                </span>
              </span>
              <LoadingIndicator
                v-if="lavoro === `scegli-${voce.id}`"
                class="mt-1 size-4 shrink-0"
              />
            </button>
          </div>
        </section>

        <template v-if="stato === 'collegato'">
          <!-- the switch: from now on the invoices are born there -->
          <section class="flex flex-col gap-2">
            <SettingsRow
              class="!px-0"
              :label="__('Invoices are issued in Fatture in Cloud')"
              :description="
                dati.active
                  ? __(
                      'They take their number there and leave for the SdI from there. Test invoices stay here.',
                    )
                  : __(
                      'Off: the invoices are numbered here and leave through Itala.',
                    )
              "
            >
              <Switch
                :model-value="dati.active"
                :disabled="
                  (!dati.active && !accendibile) || lavoro === 'accendi'
                "
                @update:model-value="accendi"
              />
            </SettingsRow>
            <ul
              v-if="dati.missing?.length"
              class="flex flex-col gap-1 rounded-lg bg-surface-amber-1 px-3 py-2.5 text-p-sm text-ink-amber-8"
            >
              <li v-for="riga in dati.missing" :key="riga">{{ riga }}</li>
            </ul>
          </section>

          <!-- the VAT rates: which of the company's stands for each of ours -->
          <section class="flex flex-col gap-3">
            <div class="flex items-start justify-between gap-3 max-md:flex-col">
              <div class="flex min-w-0 flex-col gap-0.5">
                <h3 class="text-base-semibold text-ink-gray-8">
                  {{ __('VAT rates') }}
                </h3>
                <p class="text-p-sm text-ink-gray-6">
                  {{
                    __(
                      'Which of the VAT rates in Fatture in Cloud stands for each of the ones here. Where only one can be meant it is chosen already.',
                    )
                  }}
                </p>
              </div>
              <Button
                class="shrink-0"
                variant="subtle"
                :loading="lavoro === 'rileggi'"
                :label="__('Read again from Fatture in Cloud')"
                @click="rileggi"
              />
            </div>
            <div class="flex flex-col divide-y divide-outline-gray-1">
              <div
                v-for="riga in dati.vat"
                :key="riga.key"
                class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-3 py-2.5 max-md:grid-cols-1 max-md:gap-1.5"
              >
                <span class="text-p-base text-ink-gray-8">{{
                  riga.label
                }}</span>
                <FormControl
                  v-if="riga.options.length"
                  v-model="form.vat[riga.key]"
                  type="select"
                  :aria-label="riga.label"
                  :options="opzioni(riga, __('Choose…'))"
                />
                <span v-else class="text-p-sm text-ink-amber-8">
                  {{
                    __(
                      'None in Fatture in Cloud: add it there, then read again.',
                    )
                  }}
                </span>
              </div>
            </div>
          </section>

          <!-- where the payments go -->
          <section class="flex flex-col gap-3">
            <div class="flex flex-col gap-0.5">
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ __('Where the payments go') }}
              </h3>
              <p class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'An invoice paid at the desk is recorded paid in Fatture in Cloud, on the account of how it was paid.',
                  )
                }}
              </p>
            </div>
            <div class="flex flex-col divide-y divide-outline-gray-1">
              <div
                v-for="riga in dati.accounts"
                :key="riga.method"
                class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-3 py-2.5 max-md:grid-cols-1 max-md:gap-1.5"
              >
                <span class="text-p-base text-ink-gray-8">{{
                  riga.label
                }}</span>
                <FormControl
                  v-model="form.accounts[riga.method]"
                  type="select"
                  :aria-label="riga.label"
                  :options="opzioni(riga, __('Choose…'))"
                />
              </div>
            </div>
            <ul
              v-if="dati.advice?.length"
              class="flex flex-col gap-1 text-p-sm text-ink-gray-6"
            >
              <li v-for="riga in dati.advice" :key="riga">{{ riga }}</li>
            </ul>
          </section>

          <!-- the numerations -->
          <section class="flex flex-col gap-3">
            <div class="flex flex-col gap-0.5">
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ __('Numbering') }}
              </h3>
              <p class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Fatture in Cloud gives the number, on the numbering chosen here.',
                  )
                }}
              </p>
            </div>
            <div class="flex flex-col divide-y divide-outline-gray-1">
              <div
                v-for="voce in numerazioni"
                :key="voce.chiave"
                class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-3 py-2.5 max-md:grid-cols-1 max-md:gap-1.5"
              >
                <span class="text-p-base text-ink-gray-8">{{
                  voce.label
                }}</span>
                <FormControl
                  v-model="form.numerations[voce.chiave]"
                  type="select"
                  :aria-label="voce.label"
                  :options="
                    opzioniDellaNumerazione(dati.numerations[voce.chiave], __)
                  "
                />
              </div>
            </div>
          </section>

          <!-- the Sistema TS: from here, or from Fatture in Cloud -->
          <section v-if="dati.healthcare" class="flex flex-col gap-3">
            <div class="flex flex-col gap-0.5">
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ __('Sistema TS') }}
              </h3>
              <p class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Who reports the healthcare expenses: one of the two, never both - the same expense twice is refused.',
                  )
                }}
              </p>
            </div>
            <div class="flex flex-col gap-2">
              <SceltaRadio
                v-for="scelta in sceltePerIlTs"
                :key="scelta.value"
                v-model="form.ts_by"
                nome="fic-ts"
                :scelta="scelta"
              />
            </div>
          </section>
        </template>

        <!-- the agency's: the address Fatture in Cloud sends back to -->
        <section
          v-if="tecnico && pagina.data.redirect_uri"
          class="flex flex-col gap-2 rounded-xl border border-outline-gray-2 px-4 py-4"
        >
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Fatture in Cloud, for the agency') }}
          </h3>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                "The address to write in the app's page on developers.fattureincloud.it, letter by letter.",
              )
            }}
          </p>
          <div class="flex items-center gap-2">
            <div
              class="min-w-0 flex-1 truncate rounded-lg bg-surface-gray-2 px-3 py-2 font-mono text-p-sm text-ink-gray-7"
            >
              {{ pagina.data.redirect_uri }}
            </div>
            <Button
              class="shrink-0"
              variant="subtle"
              :label="__('Copy')"
              @click="copia(pagina.data.redirect_uri)"
            />
          </div>
        </section>

        <ErrorMessage :message="errore" />
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { openOAuthPopup, onOAuthResult } from '@/composables/oauthPopup'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  cambiato,
  daSalvare,
  modulo,
  opzioni,
  opzioniDellaNumerazione,
  siPuoAccendere,
  statoDelCollegamento,
} from '@/utils/fattureInCloud'
import LucideFileText from '~icons/lucide/file-text'
import LucideHash from '~icons/lucide/hash'
import LucideFlaskConical from '~icons/lucide/flask-conical'
import LucideStethoscope from '~icons/lucide/stethoscope'
import {
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  call,
  createListResource,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { $dialog } = globalStore()
const tecnico = usersStore().puo('tecnico.integrazioni')

const azienda = ref('')
const lavoro = ref('')
const errore = ref('')
const form = ref(modulo(null))
const salvato = ref(modulo(null))

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'is_default'],
  orderBy: 'is_default desc, company_name asc',
  pageLength: 100,
  auto: true,
})

const pagina = createResource({
  url: 'crm.invoicing.fic.collegamento.get_fic',
  auto: true,
  onSuccess: riempi,
})

function riempi(data) {
  form.value = modulo(data)
  salvato.value = modulo(data)
}

const dati = computed(() => pagina.data)
const stato = computed(() => statoDelCollegamento(pagina.data))
const modificato = computed(() => cambiato(form.value, salvato.value))
const accendibile = computed(() => siPuoAccendere(pagina.data))

const aziende = computed(() =>
  (companies.data || []).map((riga) => ({
    label: riga.company_name || riga.name,
    onClick: () => {
      azienda.value = riga.name
    },
  })),
)

watch(azienda, (nome) => {
  if (nome) pagina.fetch({ company: nome })
})

// what connecting changes, said before anybody connects
const cosaCambia = computed(() => [
  {
    icona: LucideHash,
    testo: __(
      'The invoices take their number in Fatture in Cloud, and the electronic ones leave for the SdI from there.',
    ),
  },
  {
    icona: LucideFileText,
    testo: __(
      'People, appointments, payments and the PDF given to the client stay here as they are.',
    ),
  },
  {
    icona: LucideStethoscope,
    testo: __(
      'The Sistema TS: reported by {brand} or by Fatture in Cloud, as you choose.',
    ),
  },
  {
    icona: LucideFlaskConical,
    testo: __(
      'Test invoices stay here: Fatture in Cloud receives only the real ones.',
    ),
  },
])

const numerazioni = computed(() => [
  { chiave: 'sdi', label: __('Electronic invoices') },
  { chiave: 'paper', label: __('Paper invoices') },
  { chiave: 'credit', label: __('Credit notes') },
])

const sceltePerIlTs = computed(() => [
  {
    value: 'dottorcloud',
    label: __('Reported by {brand}'),
    description: __(
      'Expense by expense, with the centre’s credentials, as with every invoice: in Fatture in Cloud leave the Sistema TS off.',
    ),
  },
  {
    value: 'fatture_in_cloud',
    label: __('Reported by Fatture in Cloud'),
    description: dati.value?.fic_sends_ts
      ? __(
          'It is on in Fatture in Cloud already. One kind of expense per invoice, the whole invoice reported.',
        )
      : __(
          'Switch it on in Fatture in Cloud too. One kind of expense per invoice, the whole invoice reported.',
        ),
  },
])

function messaggio(e) {
  return e?.messages?.join(' ') || e?.message || String(e || '')
}

async function chiama(cosa, metodo, argomenti, riuscito) {
  lavoro.value = cosa
  errore.value = ''
  try {
    const risposta = await call(metodo, {
      company: azienda.value || dati.value?.company,
      ...argomenti,
    })
    if (risposta && 'configured' in risposta) {
      pagina.data = risposta
      riempi(risposta)
    }
    if (riuscito) toast.success(riuscito)
    return risposta
  } catch (e) {
    errore.value = messaggio(e)
    toast.error(errore.value)
    return null
  } finally {
    lavoro.value = ''
  }
}

function collega() {
  lavoro.value = 'collega'
  call('crm.invoicing.fic.collegamento.connect', {
    company: azienda.value || dati.value?.company,
  })
    .then(({ url }) => openOAuthPopup(url, 'crm-fic-oauth'))
    .catch((e) => {
      lavoro.value = ''
      toast.error(messaggio(e))
    })
}

onOAuthResult('fic', ({ error }) => {
  lavoro.value = ''
  if (error) toast.error(error)
  else toast.success(__('Fatture in Cloud connected'))
  pagina.fetch({ company: azienda.value || dati.value?.company })
})

function scegli(id) {
  chiama(
    `scegli-${id}`,
    'crm.invoicing.fic.collegamento.choose_fic_company',
    { fic_company: id },
    __('Saved'),
  )
}

function rileggi() {
  chiama(
    'rileggi',
    'crm.invoicing.fic.collegamento.refresh_fic',
    {},
    __('Up to date with Fatture in Cloud'),
  )
}

function salva() {
  chiama(
    'salva',
    'crm.invoicing.fic.collegamento.save_fic',
    { settings: daSalvare(form.value) },
    __('Saved'),
  )
}

function accendi(acceso) {
  const fai = () =>
    chiama(
      'accendi',
      'crm.invoicing.fic.collegamento.save_fic',
      { settings: { ...daSalvare(form.value), active: acceso } },
      acceso
        ? __('From now on the invoices are issued in Fatture in Cloud.')
        : __('From now on the invoices are numbered here again.'),
    )
  if (!acceso) return fai()
  $dialog({
    title: __('Issue in Fatture in Cloud?'),
    message: __(
      'From the next invoice, every real invoice takes its number in Fatture in Cloud and is kept there. The ones issued so far stay as they are.',
    ),
    actions: [
      {
        label: __('Issue in Fatture in Cloud'),
        variant: 'solid',
        onClick: (chiudi) => {
          chiudi()
          fai()
        },
      },
    ],
  })
}

function scollega() {
  $dialog({
    title: __('Disconnect Fatture in Cloud?'),
    message: __(
      'The invoices issued there stay there and here; the next ones are numbered here again. The states of the ones on their way to the SdI are no longer read.',
    ),
    actions: [
      {
        label: __('Disconnect'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          chiama(
            'scollega',
            'crm.invoicing.fic.collegamento.disconnect_fic',
            {},
            __('Fatture in Cloud disconnected'),
          )
        },
      },
    ],
  })
}

function copia(testo) {
  navigator.clipboard
    ?.writeText(testo)
    .then(() => toast.success(__('Copied')))
    .catch(() => toast.error(__('Could not copy')))
}
</script>
