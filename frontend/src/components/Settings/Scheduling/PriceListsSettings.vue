<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
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

    <div class="flex flex-1 gap-4 overflow-hidden px-2">
      <!-- price lists -->
      <div class="w-64 shrink-0 overflow-y-auto">
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
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
                {{ list.currency }} · {{ list.rule_count }} {{ __('rules') }}
              </div>
            </div>
            <Badge
              v-if="list.is_default"
              :label="__('Default')"
              theme="blue"
              size="sm"
            />
            <Button
              variant="ghost"
              icon="lucide-pencil"
              @click.stop="openListEditor(list)"
            />
          </div>
        </div>
        <div
          v-if="!priceLists.data?.length && !priceLists.loading"
          class="px-2 pt-3 text-p-sm text-ink-gray-5"
        >
          {{ __('Create a price list to start.') }}
        </div>
      </div>

      <!-- rules -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <div v-if="selected" class="mb-2 flex items-center justify-between">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('Rules of {0}').replace('{0}', selected) }}
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
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="rule in prices.data"
              :key="rule.name"
              class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
              @click="openRuleEditor(rule)"
            >
              <div class="min-w-0 flex-1">
                <div class="truncate text-p-base-medium text-ink-gray-8">
                  {{ rule.service }}
                  <span v-if="rule.label" class="text-ink-gray-5"
                    >· {{ rule.label }}</span
                  >
                </div>
                <div class="truncate text-p-sm text-ink-gray-5">
                  {{ conditionsOf(rule) }}
                </div>
              </div>
              <span class="shrink-0 text-p-base-medium text-ink-gray-8">
                {{ rule.price }} {{ rule.currency || '' }}
                <span
                  v-if="rule.per_participant"
                  class="text-p-xs text-ink-gray-5"
                >
                  /{{ __('person') }}
                </span>
              </span>
              <Badge
                v-if="rule.priority"
                :label="`P${rule.priority}`"
                theme="orange"
                size="sm"
              />
              <Button
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
          <div v-else-if="!selected" class="px-1 text-p-sm text-ink-gray-5">
            {{ __('Pick a price list on the left.') }}
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
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model="listForm.currency"
            type="text"
            :label="__('Currency')"
          />
          <FormControl
            v-model="listForm.valid_from"
            type="date"
            :label="__('Valid from')"
          />
          <FormControl
            v-model="listForm.valid_upto"
            type="date"
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
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model.number="ruleForm.price"
            type="number"
            :label="__('Price')"
          />
          <FormControl
            v-model="ruleForm.currency"
            type="text"
            :label="__('Currency')"
          />
          <FormControl
            v-model.number="ruleForm.priority"
            type="number"
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
          <div class="mt-3 grid grid-cols-3 gap-3">
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
          <div class="mt-3 grid grid-cols-4 gap-3">
            <FormControl
              v-model.number="ruleForm.min_participants"
              type="number"
              min="0"
              :label="__('From N people')"
            />
            <FormControl
              v-model.number="ruleForm.max_participants"
              type="number"
              min="0"
              :label="__('Up to N people')"
            />
            <FormControl
              v-model="ruleForm.valid_from"
              type="date"
              :label="__('Valid from')"
            />
            <FormControl
              v-model="ruleForm.valid_upto"
              type="date"
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
import Link from '@/components/Controls/Link.vue'
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

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
  onSuccess: (data) => {
    if (!selected.value && data?.length) select(data[0].name)
  },
})

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
  prices.submit({ price_list: name })
}

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
      `${String(rule.start_time || '00:00').slice(0, 5)}–${String(
        rule.end_time || '24:00',
      ).slice(0, 5)}`,
    )
  }
  if (rule.min_participants) {
    parts.push(__('{0}+ people').replace('{0}', rule.min_participants))
  }
  if (rule.max_participants) {
    parts.push(__('up to {0}').replace('{0}', rule.max_participants))
  }
  if (rule.valid_from || rule.valid_upto) {
    parts.push(`${rule.valid_from || '…'} → ${rule.valid_upto || '…'}`)
  }
  return parts.length ? parts.join(' · ') : __('Always')
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
  createResource({
    url: 'crm.api.appointments.save_price_list',
    params: { name: editingList.value, price_list: { ...listForm } },
    auto: true,
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

function removeList() {
  createResource({
    url: 'crm.api.appointments.delete_price_list',
    params: { name: selected.value },
    auto: true,
    onSuccess: () => {
      selected.value = ''
      priceLists.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
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
          start_time: String(rule.start_time || '').slice(0, 5),
          end_time: String(rule.end_time || '').slice(0, 5),
          valid_from: rule.valid_from || '',
          valid_upto: rule.valid_upto || '',
        }
      : {},
  )
  showRuleEditor.value = true
}

function saveRule() {
  savingRule.value = true
  createResource({
    url: 'crm.api.appointments.save_price',
    params: {
      name: editingRule.value,
      price: { ...ruleForm, price_list: selected.value },
    },
    auto: true,
    onSuccess: () => {
      savingRule.value = false
      showRuleEditor.value = false
      toast.success(__('Rule saved'))
      prices.submit({ price_list: selected.value })
      priceLists.reload()
    },
    onError: (e) => {
      savingRule.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function removeRule(rule) {
  createResource({
    url: 'crm.api.appointments.delete_price',
    params: { name: rule.name },
    auto: true,
    onSuccess: () => {
      prices.submit({ price_list: selected.value })
      priceLists.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
