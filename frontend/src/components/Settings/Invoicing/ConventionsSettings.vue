<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Invoicing > Conventions and funds (crm/convenzioni, doc 61): the
  health funds, insurances and companies the centre has a convention with. Each
  says who pays (a company with its billing details: in direct form it gets the
  month's invoice), the forms the person may use it in, its prices (a price list
  of the agenda, a discount, the centre's own), the person's share in direct
  form, whether the fund authorises each visit first, and whether /prenota
  offers it.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Conventions and funds') }}
      </h2>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Health funds, insurances and companies: their prices, the share the person pays, who is billed.',
          )
        }}
      </p>
    </template>
    <template #header-actions>
      <AzioneImpostazioni
        icon-left="plus"
        :label="__('New convention')"
        @click="apri(null)"
      />
    </template>
    <template #content>
      <div v-if="elenco.data" class="flex flex-col gap-4 pb-6">
        <div
          v-if="elenco.data.conventions.length"
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <button
            v-for="c in elenco.data.conventions"
            :key="c.name"
            type="button"
            class="flex w-full flex-col gap-1 px-3 py-2.5 text-left hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1 focus-visible:outline-none"
            @click="apri(c)"
          >
            <span class="flex flex-wrap items-center justify-between gap-2">
              <span
                class="min-w-0 max-w-full truncate text-p-base-medium text-ink-gray-8"
              >
                {{ c.convention_name }}
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="c.enabled ? 'green' : 'gray'"
                :label="
                  c.enabled ? __('Active', null, 'Convention') : __('Off')
                "
              />
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ rigaDellaConvenzione(c, t, soldi) }}
            </span>
            <span
              v-if="c.organization_name || c.covers"
              class="text-p-sm text-ink-gray-5"
            >
              {{
                [
                  c.organization_name
                    ? __('Paid by {0}', [c.organization_name])
                    : '',
                  c.covers === 1
                    ? __('1 person covered')
                    : c.covers
                      ? __('{0} people covered', [c.covers])
                      : '',
                ]
                  .filter(Boolean)
                  .join(' · ')
              }}
            </span>
          </button>
        </div>
        <EmptyState
          v-else
          :title="__('No convention yet')"
          :text="
            __(
              'A health fund in direct form, an insurer, a company whose employees get a discount.',
            )
          "
        />
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>

  <Dialog v-model="editor.show" :options="{ size: 'xl' }">
    <template #body-title>
      <h3 class="text-2xl font-semibold text-ink-gray-9">
        {{ editor.name ? form.convention_name : __('New convention') }}
      </h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.convention_name"
            :label="__('Name')"
            :placeholder="__('UniSalute, Fasi, Dipendenti Rossi S.p.A.…')"
            :disabled="Boolean(editor.name)"
          />
          <FormControl
            v-model="form.kind"
            type="select"
            :label="__('Kind')"
            :options="tipi"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <Link
            class="w-full"
            doctype="CRM Organization"
            variant="outline"
            :label="__('Who pays')"
            :placeholder="__('Search a company')"
            :modelValue="form.organization"
            @update:modelValue="(v) => (form.organization = v)"
          />
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                "The fund, the insurer or the company, with its billing details on its page: in direct form it gets the month's invoice.",
              )
            }}
          </p>
        </div>

        <fieldset class="flex flex-col gap-2">
          <legend class="mb-1 text-p-sm font-medium text-ink-gray-7">
            {{ __('How the person pays') }}
          </legend>
          <FormControl
            v-model="form.direct"
            type="checkbox"
            :label="
              __(
                'Direct form: the fund pays the centre, the person their share',
              )
            "
          />
          <div v-if="form.direct" class="pl-6">
            <FormControl
              v-model="form.requires_authorisation"
              type="checkbox"
              :label="__('The fund authorises each appointment first')"
            />
          </div>
          <FormControl
            v-model="form.indirect"
            type="checkbox"
            :label="
              __(
                'Indirect form: the person pays everything and asks the fund for it back',
              )
            "
          />
          <FormControl
            v-model="form.show_online"
            type="checkbox"
            :label="
              __(
                'Offered on the booking page: the booking then waits for the centre’s yes',
              )
            "
          />
        </fieldset>

        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.price_mode"
            type="select"
            :label="__('Prices')"
            :options="modiDiPrezzo"
          />
          <FormControl
            v-if="form.price_mode === LISTINO"
            v-model="form.price_list"
            type="select"
            :label="__('Price list')"
            :options="listini"
          />
          <FormControl
            v-else-if="form.price_mode === SCONTO"
            v-model="form.discount_percent"
            type="number"
            inputmode="decimal"
            :min="0"
            :max="100"
            :label="__('Discount (%)')"
          />
        </div>

        <template v-if="form.direct">
          <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
            <FormControl
              v-model="form.share_mode"
              type="select"
              :label="__('Share paid by the person')"
              :options="modiDiQuota"
            />
            <FormControl
              v-if="form.share_mode === FISSA"
              v-model="form.share_amount"
              type="number"
              :min="0"
              :label="__('Fixed share (franchigia)')"
            />
            <FormControl
              v-else-if="form.share_mode === PERCENTUALE"
              v-model="form.share_percent"
              type="number"
              inputmode="decimal"
              :min="0"
              :max="100"
              :label="__('Share in percent (scoperto)')"
            />
          </div>
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between gap-2">
              <span class="text-p-sm font-medium text-ink-gray-7">
                {{ __('Share by service') }}
              </span>
              <Button
                class="touch-target"
                variant="ghost"
                icon-left="plus"
                :label="__('Add a service')"
                @click="form.shares.push({ service: '', patient_share: 0 })"
              />
            </div>
            <p v-if="!form.shares.length" class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'A service with a share of its own, when the fund says so: it wins over the one above.',
                )
              }}
            </p>
            <div
              v-for="(riga, i) in form.shares"
              :key="i"
              class="flex items-end gap-2"
            >
              <FormControl
                v-model="riga.service"
                class="min-w-0 flex-1"
                type="select"
                :label="i === 0 ? __('Service') : ''"
                :aria-label="__('Service')"
                :options="servizi"
              />
              <FormControl
                v-model="riga.patient_share"
                class="w-28 shrink-0"
                type="number"
                :min="0"
                :label="i === 0 ? __('Share') : ''"
                :aria-label="__('Share paid by the person')"
              />
              <Button
                class="shrink-0"
                variant="ghost"
                icon="lucide-trash-2"
                :aria-label="__('Remove')"
                @click="form.shares.splice(i, 1)"
              />
            </div>
          </div>
          <p
            class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
          >
            {{ esempio }}
          </p>
        </template>

        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.valid_from"
            type="date"
            :label="__('Valid from')"
          />
          <FormControl
            v-model="form.valid_upto"
            type="date"
            :label="__('Valid until')"
          />
        </div>
        <FormControl
          v-model="form.notes"
          type="textarea"
          :rows="2"
          :label="__('Notes')"
          :placeholder="
            __('How to ask for the authorisation, the portal, the deadlines…')
          "
        />
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          v-if="editor.name && !editor.used"
          theme="red"
          :label="__('Delete')"
          :loading="busy === 'delete'"
          @click="togli"
        />
        <FormControl
          v-else-if="editor.name"
          v-model="form.enabled"
          type="checkbox"
          :label="__('Active', null, 'Convention')"
        />
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button :label="__('Cancel')" @click="editor.show = false" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="busy === 'save'"
            @click="salva"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import Link from '@/components/Controls/Link.vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { useSchedulerMeta } from '@/composables/scheduling'
import {
  FISSA,
  LISTINO,
  NIENTE,
  PERCENTUALE,
  PREZZI_DEL_CENTRO,
  SCONTO,
  TIPI,
  DIRETTA,
  nomeDelTipo,
  problemaDellaConvenzione,
  quote,
  rigaDellaConvenzione,
} from '@/utils/convenzioni'
import { appLocale } from '@/utils/locale'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const t = (text, args, context) => __(text, args, context)
const meta = useSchedulerMeta()

const elenco = createResource({
  url: 'crm.convenzioni.api.list_conventions',
  auto: true,
})

function soldi(importo) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: 'EUR',
  }).format(Number(importo) || 0)
}

const tipi = TIPI.map((tipo) => ({ label: nomeDelTipo(tipo, t), value: tipo }))
const modiDiPrezzo = [
  { label: __("The centre's prices"), value: PREZZI_DEL_CENTRO },
  { label: __('A price list of the agenda'), value: LISTINO },
  { label: __("A discount on the centre's prices"), value: SCONTO },
]
const modiDiQuota = [
  { label: __('Nothing: the fund pays it all'), value: NIENTE },
  { label: __('A fixed amount'), value: FISSA },
  { label: __('A percentage'), value: PERCENTUALE },
]
const listini = computed(() => [
  { label: __('Choose…'), value: '' },
  ...(elenco.data?.price_lists || []).map((l) => ({
    label: l.price_list_name,
    value: l.name,
  })),
])
const servizi = computed(() => [
  { label: __('Choose…'), value: '' },
  ...(meta.data?.services || []).map((s) => ({
    label: s.service_name,
    value: s.name,
  })),
])

const editor = reactive({ show: false, name: null, used: 0 })
const form = reactive({ shares: [] })
const busy = ref('')
const errore = ref('')

// what a visit of 100 means for the person and the fund, as it is set now
const esempio = computed(() => {
  const [persona, fondo] = quote(form, DIRETTA, 100)
  return __(
    'In direct form, of a visit of {0} the person pays {1} and the fund {2}.',
    [soldi(100), soldi(persona), soldi(fondo)],
  )
})

function apri(c) {
  Object.assign(form, {
    convention_name: c?.convention_name || '',
    kind: c?.kind || TIPI[0],
    enabled: c ? Boolean(c.enabled) : true,
    organization: c?.organization || '',
    valid_from: c?.valid_from || '',
    valid_upto: c?.valid_upto || '',
    direct: c ? Boolean(c.direct) : true,
    indirect: c ? Boolean(c.indirect) : false,
    requires_authorisation: c ? Boolean(c.requires_authorisation) : true,
    show_online: Boolean(c?.show_online),
    price_mode: c?.price_mode || PREZZI_DEL_CENTRO,
    price_list: c?.price_list || '',
    discount_percent: c?.discount_percent ?? '',
    share_mode: c?.share_mode || NIENTE,
    share_amount: c?.share_amount ?? '',
    share_percent: c?.share_percent ?? '',
    shares: (c?.shares || []).map((r) => ({ ...r })),
    notes: c?.notes || '',
  })
  Object.assign(editor, { show: true, name: c?.name || null, used: c?.used })
  errore.value = ''
}

async function salva() {
  form.shares = form.shares.filter((r) => r.service)
  errore.value = problemaDellaConvenzione(form, t)
  if (errore.value) return
  busy.value = 'save'
  try {
    await call('crm.convenzioni.api.save_convention', {
      data: JSON.stringify({
        ...form,
        enabled: form.enabled ? 1 : 0,
        direct: form.direct ? 1 : 0,
        indirect: form.indirect ? 1 : 0,
        requires_authorisation: form.requires_authorisation ? 1 : 0,
        show_online: form.show_online ? 1 : 0,
        discount_percent: Number(form.discount_percent) || 0,
        share_amount: Number(form.share_amount) || 0,
        share_percent: Number(form.share_percent) || 0,
      }),
      name: editor.name,
    })
    toast.success(__('Saved'))
    editor.show = false
    elenco.reload()
  } catch (e) {
    errore.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function togli() {
  busy.value = 'delete'
  try {
    await call('crm.convenzioni.api.delete_convention', { name: editor.name })
    toast.success(__('Convention deleted'))
    editor.show = false
    elenco.reload()
  } catch (e) {
    errore.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}
</script>
