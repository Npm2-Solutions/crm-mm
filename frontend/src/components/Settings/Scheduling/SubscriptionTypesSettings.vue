<!--
  The types of subscription the desk sells: how many months, the price and
  whether it is paid at once or by the month, the services it comprises and how
  many entries, whether it can be suspended, the reminder of the end, renewing
  by itself, the fiscal card of its invoices. A subscription sold keeps the
  terms of its day: a type changed later changes nothing sold.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Subscriptions') }}
      </h2>
    </template>
    <template #header-actions>
      <Button
        variant="solid"
        icon-left="plus"
        :label="__('New type')"
        @click="open(null)"
      />
    </template>
    <template #content>
      <div v-if="types.data" class="flex flex-col gap-4 pb-6">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'A type is what the desk sells from the person’s page: the appointments of the services it comprises use its entries by themselves and cost nothing. A subscription sold keeps the terms of its day.',
            )
          }}
        </p>
        <div
          v-if="types.data.length"
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <button
            v-for="type in types.data"
            :key="type.name"
            type="button"
            class="flex w-full flex-col gap-1 px-3 py-2.5 text-left hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1 focus-visible:outline-none"
            @click="open(type)"
          >
            <span class="flex items-center justify-between gap-2">
              <span class="min-w-0 truncate text-p-base-medium text-ink-gray-8">
                {{ type.type_name }}
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="type.enabled ? 'green' : 'gray'"
                :label="type.enabled ? __('On sale') : __('Off')"
              />
            </span>
            <span class="text-p-sm text-ink-gray-6">{{ line(type) }}</span>
          </button>
        </div>
        <p v-else class="px-1 text-p-sm text-ink-gray-5">
          {{
            __(
              'No type yet: a month of the gym, three months of pilates twice a week, a year of treatments…',
            )
          }}
        </p>
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>

  <Dialog v-model="editor.show" :options="{ size: 'xl' }">
    <template #body-title>
      <h3 class="text-2xl font-semibold text-ink-gray-9">
        {{ editor.name ? __('Change the type') : __('New type') }}
      </h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.type_name"
            :label="__('Name')"
            :placeholder="__('Open, Twice a week…')"
            :disabled="Boolean(editor.name)"
          />
          <FormControl
            v-model.number="form.months"
            type="number"
            inputmode="numeric"
            :min="1"
            :max="MAX_MESI"
            :label="__('Months')"
          />
          <FormControl
            v-model="form.price"
            type="number"
            :min="0"
            :label="__('Price')"
          />
          <FormControl
            v-model="form.payment"
            type="select"
            :label="__('Paid')"
            :options="paymentOptions"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <span class="text-xs text-ink-gray-5">{{ __('Services') }}</span>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="service in serviceOptions"
              :key="service.value"
              class="touch-target"
              :variant="
                form.services.includes(service.value) ? 'solid' : 'subtle'
              "
              :aria-pressed="form.services.includes(service.value)"
              :label="service.label"
              @click="toggle(service.value)"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.entries"
            type="select"
            :label="__('Entries')"
            :options="entryOptions"
          />
          <FormControl
            v-if="form.entries !== ILLIMITATI"
            v-model.number="form.entries_count"
            type="number"
            inputmode="numeric"
            :min="1"
            :label="__('How many')"
          />
        </div>
        <p class="-mt-1 text-p-sm text-ink-gray-6">{{ preview }}</p>

        <div class="flex flex-col gap-2">
          <FormControl
            v-model="form.missed_count"
            type="checkbox"
            :label="__('A missed entry is used')"
          />
          <FormControl
            v-model="form.can_suspend"
            type="checkbox"
            :label="__('Can be suspended')"
          />
          <FormControl
            v-if="form.can_suspend"
            v-model.number="form.max_suspension_days"
            class="max-w-xs"
            type="number"
            inputmode="numeric"
            :min="0"
            :label="__('Days of suspension at most')"
            :placeholder="__('Empty: as many as needed')"
          />
          <FormControl
            v-model="form.auto_renew"
            type="checkbox"
            :label="__('Renews by itself the day after the last one')"
          />
        </div>

        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model.number="form.remind_days"
            type="number"
            inputmode="numeric"
            :min="0"
            :label="__('Remind days before the end')"
          />
          <FormControl
            v-model="form.billable_service"
            type="select"
            :label="__('Fiscal card')"
            :options="cardOptions"
          />
        </div>
        <FormControl
          v-if="form.billable_service"
          v-model="form.issue_invoices"
          type="checkbox"
          :label="__('Issue the invoices by themselves')"
        />
        <p class="-mt-1 text-p-sm text-ink-gray-6">
          {{
            form.billable_service
              ? form.issue_invoices
                ? __(
                    'On each instalment’s day its invoice is issued; one that cannot be stays a draft and says why.',
                  )
                : __(
                    'On each instalment’s day a draft invoice waits for the desk.',
                  )
              : __('Without a fiscal card the instalments are only a schedule.')
          }}
        </p>
        <FormControl
          v-model="form.description"
          type="textarea"
          :rows="2"
          :label="__('What the person reads')"
          :placeholder="__('In their area, with the subscription')"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          v-if="editor.name && !editor.sold"
          theme="red"
          :label="__('Delete')"
          :loading="busy === 'delete'"
          @click="remove"
        />
        <FormControl
          v-else-if="editor.name"
          v-model="form.enabled"
          type="checkbox"
          :label="__('On sale')"
        />
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button :label="__('Cancel')" @click="editor.show = false" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="busy === 'save'"
            @click="save"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { useSchedulerMeta } from '@/composables/scheduling'
import {
  AL_MESE,
  A_SETTIMANA,
  ILLIMITATI,
  MAX_MESI,
  MENSILE,
  SUBITO,
  cosaDa,
  erroreDelTipo,
} from '@/utils/abbonamenti'
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

const meta = useSchedulerMeta()
const t = (text, args) => __(text, args)

const types = createResource({
  url: 'crm.scheduling.abbonamenti.get_types',
  auto: true,
})
const cards = createResource({
  url: 'crm.scheduling.abbonamenti.get_fiscal_cards',
  auto: true,
})

const editor = reactive({ show: false, name: null, sold: 0 })
const form = reactive({})
const busy = ref('')
const error = ref('')

function money(amount, currency) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount || 0)
}

function line(type) {
  const parts = [cosaDa(type, t)]
  if (type.price)
    parts.push(
      type.payment === MENSILE && type.months > 1
        ? __('{0} by the month', [money(type.price, type.currency)])
        : money(type.price, type.currency),
    )
  parts.push(type.sold === 1 ? __('1 sold') : __('{0} sold', [type.sold || 0]))
  return parts.join(' · ')
}

const paymentOptions = [
  { label: __('All at once'), value: SUBITO },
  { label: __('By the month'), value: MENSILE },
]

const entryOptions = [
  { label: __('As many as one likes'), value: ILLIMITATI },
  { label: __('So many a week'), value: A_SETTIMANA },
  { label: __('So many a month'), value: AL_MESE },
]

const serviceOptions = computed(() =>
  (meta.data?.services || []).map((service) => ({
    label: service.service_name,
    value: service.name,
  })),
)

const cardOptions = computed(() => [
  { label: __('None: no invoices'), value: '' },
  ...(cards.data || []),
])

const preview = computed(() => cosaDa(form, t))

function toggle(service) {
  form.services = form.services.includes(service)
    ? form.services.filter((one) => one !== service)
    : [...form.services, service]
}

function open(type) {
  Object.assign(form, {
    type_name: type?.type_name || '',
    enabled: type ? Boolean(type.enabled) : true,
    description: type?.description || '',
    months: type?.months || 1,
    payment: type?.payment || SUBITO,
    price: type?.price ?? '',
    currency: type?.currency || '',
    billable_service: type?.billable_service || '',
    issue_invoices: Boolean(type?.issue_invoices),
    services: [...(type?.services || [])],
    entries: type?.entries || ILLIMITATI,
    entries_count: type?.entries_count || '',
    missed_count: type ? Boolean(type.missed_count) : true,
    can_suspend: Boolean(type?.can_suspend),
    max_suspension_days: type?.max_suspension_days || '',
    remind_days: type?.remind_days ?? 7,
    auto_renew: Boolean(type?.auto_renew),
  })
  Object.assign(editor, {
    show: true,
    name: type?.name || null,
    sold: type?.sold || 0,
  })
  error.value = ''
}

async function save() {
  error.value = erroreDelTipo(form, t)
  if (error.value) return
  busy.value = 'save'
  try {
    await call('crm.scheduling.abbonamenti.save_type', {
      data: JSON.stringify({
        ...form,
        enabled: form.enabled ? 1 : 0,
        issue_invoices: form.issue_invoices ? 1 : 0,
        missed_count: form.missed_count ? 1 : 0,
        can_suspend: form.can_suspend ? 1 : 0,
        auto_renew: form.auto_renew ? 1 : 0,
        price: Number(form.price) || 0,
        remind_days: Number(form.remind_days) || 0,
      }),
      name: editor.name,
    })
    toast.success(__('Saved'))
    editor.show = false
    types.reload()
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function remove() {
  busy.value = 'delete'
  try {
    await call('crm.scheduling.abbonamenti.delete_type', { name: editor.name })
    toast.success(__('Deleted'))
    editor.show = false
    types.reload()
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}
</script>
