<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The price lists and, beside the one chosen, its rules; where the page is
  narrow (a phone, a tablet held upright) the rules come under the lists, and
  the page scrolls as one.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5 impostazioni-strette:h-auto"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Price Lists') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'A price is a rule, not a number: it can depend on the professional, the room, the day, the hour and how many people attend.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('New price list')"
        iconLeft="plus"
        @click="openListEditor()"
      />
    </div>

    <div
      class="flex flex-1 gap-4 overflow-hidden px-2 impostazioni-strette:flex-col"
    >
      <!-- price lists -->
      <div class="w-64 shrink-0 overflow-y-auto impostazioni-strette:w-full">
        <!-- an empty bordered list drew a stray hairline over the empty state -->
        <div
          v-if="priceLists.data?.length"
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="list in priceLists.data || []"
            :key="list.name"
            class="flex cursor-pointer items-center gap-2 px-3 py-2.5"
            :class="
              selected === list.name
                ? 'bg-surface-gray-2'
                : 'hover:bg-surface-gray-1'
            "
            @click="select(list.name)"
          >
            <div class="min-w-0 flex-1">
              <div class="truncate text-p-base-medium text-ink-gray-8">
                {{ list.price_list_name }}
              </div>
              <div class="truncate text-p-sm text-ink-gray-5">
                {{ nomeDellaValuta(list.currency, appLocale()) }} ·
                {{
                  list.rule_count === 1
                    ? __('1 rule')
                    : __('{0} rules', [list.rule_count])
                }}
              </div>
            </div>
            <Badge
              v-if="list.is_default"
              :label="__('Default')"
              theme="blue"
              size="sm"
            />
            <Button
              :aria-label="__('Edit')"
              variant="ghost"
              icon="lucide-pencil"
              @click.stop="openListEditor(list)"
            />
          </div>
        </div>
        <EmptyState
          v-if="!priceLists.data?.length && !priceLists.loading"
          :title="__('No price lists yet')"
          :text="
            __('Services keep their own price until a list says otherwise.')
          "
        />
      </div>

      <!-- rules -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <div
          v-if="selected"
          class="mb-2 flex flex-wrap items-center justify-between gap-2"
        >
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('Rules of {0}', [selected]) }}
          </span>
          <div class="flex items-center gap-2">
            <Button
              variant="ghost"
              theme="red"
              :label="__('Delete list')"
              @click="removeList"
            />
            <Button
              :label="__('New rule')"
              iconLeft="plus"
              @click="openRuleEditor()"
            />
          </div>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div
            v-if="prices.data?.length"
            class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="rule in prices.data"
              :key="rule.name"
              class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
              @click="openRuleEditor(rule)"
            >
              <div class="min-w-0 flex-1">
                <div class="truncate text-p-base-medium text-ink-gray-8">
                  {{ serviceName(rule.service) }}
                  <span v-if="rule.label" class="text-ink-gray-5"
                    >· {{ rule.label }}</span
                  >
                </div>
                <div class="truncate text-p-sm text-ink-gray-5">
                  {{ conditionsOf(rule) }}
                </div>
              </div>
              <span class="shrink-0 text-p-base-medium text-ink-gray-8">
                {{ money(rule.price, rule.currency || listCurrency) }}
                <span
                  v-if="rule.per_participant"
                  class="text-p-xs text-ink-gray-5"
                >
                  /{{ __('person') }}
                </span>
              </span>
              <Badge
                v-if="rule.priority"
                :label="__('priority {0}', [rule.priority])"
                :title="__('Higher priority wins when more rules match')"
                theme="gray"
                size="sm"
              />
              <Button
                :aria-label="__('Delete')"
                variant="ghost"
                icon="lucide-trash-2"
                @click.stop="removeRule(rule)"
              />
            </div>
          </div>
          <div
            v-else-if="selected && !prices.loading"
            class="rounded-lg border border-dashed border-outline-gray-2 px-3 py-6 text-center text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'No rule yet — services fall back to their own base price on this list.',
              )
            }}
          </div>
          <div
            v-else-if="!selected && priceLists.data?.length"
            class="px-1 text-p-sm text-ink-gray-5"
          >
            <span class="impostazioni-strette:hidden">{{
              __('Pick a price list on the left.')
            }}</span>
            <span class="hidden impostazioni-strette:inline">{{
              __('Pick a price list above.')
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- price list editor -->
  <Dialog v-model="showListEditor" :options="{ title: listTitle, size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="listForm.price_list_name"
          type="text"
          :label="__('Name')"
          required
        />
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <CampoValuta v-model="listForm.currency" :label="__('Currency')" />
          <FormControl
            v-model="listForm.valid_from"
            type="date"
            :format="dateFormat()"
            :label="__('Valid from')"
          />
          <FormControl
            v-model="listForm.valid_upto"
            type="date"
            :format="dateFormat()"
            :label="__('Valid upto')"
          />
        </div>
        <div class="flex gap-4">
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="listForm.enabled" size="sm" /> {{ __('Enabled') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="listForm.is_default" size="sm" />
            {{ __('Default list') }}
          </label>
        </div>
        <FormControl
          v-model="listForm.description"
          type="textarea"
          :rows="2"
          :label="__('Notes')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="savingList"
        @click="saveList"
      />
    </template>
  </Dialog>

  <!-- rule editor -->
  <Dialog v-model="showRuleEditor" :options="{ title: ruleTitle, size: '2xl' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="ruleForm.service"
            type="select"
            :label="__('Service')"
            :options="serviceOptions"
          />
          <FormControl
            v-model="ruleForm.label"
            type="text"
            :label="__('Rule name')"
            :placeholder="__('Evening rate')"
          />
        </div>
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model.number="ruleForm.price"
            type="number"
            :label="__('Price')"
          />
          <CampoValuta
            v-model="ruleForm.currency"
            :label="__('Currency')"
            :vuota="
              __('As the price list ({0})', [
                nomeDellaValuta(listCurrency, appLocale()),
              ])
            "
          />
          <FormControl
            v-model.number="ruleForm.priority"
            type="number"
            inputmode="numeric"
            :label="__('Priority')"
            :description="__('Highest wins')"
          />
        </div>

        <div class="rounded-lg border border-outline-gray-2 p-3">
          <div class="mb-2 text-p-base-medium text-ink-gray-8">
            {{ __('Applies when') }}
          </div>
          <p class="mb-3 text-p-xs text-ink-gray-5">
            {{ __('Leave a condition empty to mean "any".') }}
          </p>
          <div class="grid grid-cols-2 gap-3">
            <Link
              doctype="User"
              :modelValue="ruleForm.staff"
              :label="__('Professional')"
              :placeholder="__('Any')"
              @update:modelValue="(v) => (ruleForm.staff = v)"
            />
            <FormControl
              v-model="ruleForm.resource"
              type="select"
              :label="__('Room / equipment')"
              :options="resourceOptions"
            />
          </div>
          <div class="mt-3 grid grid-cols-3 gap-3 max-md:grid-cols-1">
            <FormControl
              v-model="ruleForm.weekday"
              type="select"
              :label="__('Weekday')"
              :options="weekdayOptions"
            />
            <FormControl
              v-model="ruleForm.start_time"
              type="time"
              :label="__('From')"
            />
            <FormControl
              v-model="ruleForm.end_time"
              type="time"
              :label="__('To')"
            />
          </div>
          <div class="mt-3 grid grid-cols-4 gap-3 max-md:grid-cols-2">
            <FormControl
              v-model.number="ruleForm.min_participants"
              type="number"
              inputmode="numeric"
              min="0"
              :label="__('From N people')"
            />
            <FormControl
              v-model.number="ruleForm.max_participants"
              type="number"
              inputmode="numeric"
              min="0"
              :label="__('Up to N people')"
            />
            <FormControl
              v-model="ruleForm.valid_from"
              type="date"
              :format="dateFormat()"
              :label="__('Valid from')"
            />
            <FormControl
              v-model="ruleForm.valid_upto"
              type="date"
              :format="dateFormat()"
              :label="__('Valid upto')"
            />
          </div>
        </div>

        <div class="flex gap-4">
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="ruleForm.enabled" size="sm" /> {{ __('Enabled') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="ruleForm.per_participant" size="sm" />
            {{ __('Price is per participant') }}
          </label>
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="savingRule"
        @click="saveRule"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { chiedi } from '@/utils/chiedi'
import Link from '@/components/Controls/Link.vue'
import CampoValuta from '@/components/Controls/CampoValuta.vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'
import { hhmm } from '@/utils/scheduler'
import { appLocale } from '@/utils/locale'
import { nomeDellaValuta, prezzo } from '@/utils/valute'
import { globalStore } from '@/stores/global'
import { dateFormat } from '@/utils'

const { $dialog } = globalStore()

const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const priceLists = createResource({
  url: 'crm.api.appointments.list_price_lists',
  cache: 'crm-price-lists',
  auto: true,
})

function serviceName(name) {
  return (
    (services.data || []).find((s) => s.name === name)?.service_name || name
  )
}

const services = createResource({
  url: 'crm.api.appointments.list_services',
  cache: 'crm-services-admin',
  auto: true,
})

const resources = createResource({
  url: 'crm.api.appointments.list_resources',
  cache: 'crm-resources-admin',
  auto: true,
})

const prices = createResource({ url: 'crm.api.appointments.list_prices' })

const selected = ref('')

function select(name) {
  selected.value = name
  prices.submit({ price_list: name }).catch(() => {})
}

// The first list is opened once the lists are here. Not in `onSuccess`: the
// resource is kept (`cache`) and keeps the callback of the page that made it,
// so opening these settings a second time selected nothing.
watch(
  () => priceLists.data,
  (data) => {
    if (!selected.value && data?.length) select(data[0].name)
  },
  { immediate: true },
)

const serviceOptions = computed(() =>
  (services.data || []).map((s) => ({ label: s.service_name, value: s.name })),
)
const resourceOptions = computed(() => [
  { label: __('Any'), value: '' },
  ...(resources.data || []).map((r) => ({
    label: r.resource_name,
    value: r.name,
  })),
])
const weekdayOptions = [
  { label: __('Any day'), value: '' },
  ...WEEKDAYS.map((d) => ({ label: __(d), value: d })),
]

function conditionsOf(rule) {
  const parts = []
  if (rule.staff) parts.push(rule.staff)
  if (rule.resource) parts.push(rule.resource)
  if (rule.weekday) parts.push(__(rule.weekday))
  if (rule.start_time || rule.end_time) {
    parts.push(
      `${hhmm(rule.start_time) || '00:00'}–${hhmm(rule.end_time) || '24:00'}`,
    )
  }
  if (rule.min_participants) {
    parts.push(__('{0}+ people', [rule.min_participants]))
  }
  if (rule.max_participants) {
    parts.push(__('up to {0}', [rule.max_participants]))
  }
  if (rule.valid_from || rule.valid_upto) {
    parts.push(`${rule.valid_from || '…'} → ${rule.valid_upto || '…'}`)
  }
  return parts.length ? parts.join(' · ') : __('Always')
}

// a price as the rest of DottorCloud writes it, «65,00 €», never «65 EUR»; a
// rule without a currency of its own counts in its list's
const listCurrency = computed(
  () => priceLists.data?.find((list) => list.name === selected.value)?.currency,
)

function money(amount, currency) {
  return prezzo(
    amount,
    currency || window.sysdefaults?.currency || 'EUR',
    appLocale(),
  )
}

// --- price list editor ---------------------------------------------------

const showListEditor = ref(false)
const savingList = ref(false)
const editingList = ref(null)

const emptyList = () => ({
  price_list_name: '',
  currency: 'EUR',
  enabled: true,
  is_default: false,
  valid_from: '',
  valid_upto: '',
  description: '',
})
const listForm = reactive(emptyList())
const listTitle = computed(() =>
  editingList.value ? __('Edit price list') : __('New price list'),
)

function openListEditor(list = null) {
  editingList.value = list?.name || null
  Object.assign(
    listForm,
    emptyList(),
    list
      ? {
          price_list_name: list.price_list_name,
          currency: list.currency,
          enabled: Boolean(list.enabled),
          is_default: Boolean(list.is_default),
          valid_from: list.valid_from || '',
          valid_upto: list.valid_upto || '',
        }
      : {},
  )
  showListEditor.value = true
}

function saveList() {
  savingList.value = true
  chiedi({
    url: 'crm.api.appointments.save_price_list',
    params: { name: editingList.value, price_list: { ...listForm } },
    onSuccess: (doc) => {
      savingList.value = false
      showListEditor.value = false
      toast.success(__('Price list saved'))
      priceLists.reload()
      select(doc.name)
    },
    onError: (e) => {
      savingList.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

// a list goes with all its rules: asked first, as a service is - one tap beside
// «New rule» took it away
function removeList() {
  const name = selected.value
  const list = priceLists.data?.find((l) => l.name === name)
  $dialog({
    title: __('Delete {0}?', [list?.price_list_name || name]),
    message: __(
      'Its rules go with it, and the services go back to their own prices. This cannot be undone.',
    ),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        onClick: (close) => {
          close()
          chiedi({
            url: 'crm.api.appointments.delete_price_list',
            params: { name },
            onSuccess: () => {
              selected.value = ''
              priceLists.reload()
            },
            onError: (e) =>
              toast.error(e.messages?.[0] || __('Failed to delete')),
          })
        },
      },
    ],
  })
}

// --- rule editor ---------------------------------------------------------

const showRuleEditor = ref(false)
const savingRule = ref(false)
const editingRule = ref(null)

const emptyRule = () => ({
  service: services.data?.[0]?.name || '',
  label: '',
  price: 0,
  currency: '',
  priority: 0,
  enabled: true,
  per_participant: false,
  staff: '',
  resource: '',
  weekday: '',
  start_time: '',
  end_time: '',
  min_participants: 0,
  max_participants: 0,
  valid_from: '',
  valid_upto: '',
})
const ruleForm = reactive(emptyRule())
const ruleTitle = computed(() =>
  editingRule.value ? __('Edit rule') : __('New price rule'),
)

function openRuleEditor(rule = null) {
  editingRule.value = rule?.name || null
  Object.assign(
    ruleForm,
    emptyRule(),
    rule
      ? {
          ...rule,
          enabled: Boolean(rule.enabled),
          per_participant: Boolean(rule.per_participant),
          staff: rule.staff || '',
          resource: rule.resource || '',
          weekday: rule.weekday || '',
          start_time: hhmm(rule.start_time),
          end_time: hhmm(rule.end_time),
          valid_from: rule.valid_from || '',
          valid_upto: rule.valid_upto || '',
        }
      : {},
  )
  showRuleEditor.value = true
}

function saveRule() {
  savingRule.value = true
  chiedi({
    url: 'crm.api.appointments.save_price',
    params: {
      name: editingRule.value,
      price: { ...ruleForm, price_list: selected.value },
    },
    onSuccess: () => {
      savingRule.value = false
      showRuleEditor.value = false
      toast.success(__('Rule saved'))
      prices.submit({ price_list: selected.value }).catch(() => {})
      priceLists.reload()
    },
    onError: (e) => {
      savingRule.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function removeRule(rule) {
  $dialog({
    title: __('Delete this rule?'),
    message: __(
      '{0} goes back to the price the service or the list’s other rules give it. This cannot be undone.',
      [serviceName(rule.service)],
    ),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        onClick: (close) => {
          close()
          chiedi({
            url: 'crm.api.appointments.delete_price',
            params: { name: rule.name },
            onSuccess: () => {
              prices.submit({ price_list: selected.value }).catch(() => {})
              priceLists.reload()
            },
            onError: (e) =>
              toast.error(e.messages?.[0] || __('Failed to delete')),
          })
        },
      },
    ],
  })
}
</script>
