<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A quote (crm.preventivi). Its author writes the draft: services from the price
  list, in phases, with a discount - and what a module adds to a row, where the
  server offers it: the clinic's tooth and surfaces, to a dentist. Proposed, it is
  a PDF to hand over, which the desk records accepted or declined. Accepted, its
  services are done as the appointments go: booked from here, marked by hand when
  it happened otherwise.
-->
<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{
            editing ? (plan.name ? __('Quote') : __('New quote')) : plan.title
          }}
        </h3>
        <Badge
          v-if="plan.status"
          variant="subtle"
          :theme="STATO[plan.status] || 'gray'"
          :label="__(plan.status, null, 'Quote')"
        />
        <!-- the deal it belongs to, a step away -->
        <Button
          v-if="plan.deal && puo('trattative.vedi')"
          variant="ghost"
          size="sm"
          :label="
            plan.deal_label
              ? __('Deal: {0}', [plan.deal_label])
              : __('Open the deal')
          "
          @click="apriTrattativa"
        />
      </div>
    </template>
    <template #body-content>
      <div v-if="loading" class="py-10 text-center text-p-sm text-ink-gray-5">
        {{ __('Loading…') }}
      </div>

      <!-- writing the draft -->
      <div v-else-if="editing" class="flex flex-col gap-4">
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <FormControl v-model="plan.title" :label="__('Title')" />
          <FormControl
            v-model="plan.price_list"
            type="select"
            :label="__('Price list')"
            :options="priceListOptions"
          />
          <FormControl
            v-model="plan.valid_until"
            type="date"
            :label="__('Quote valid until')"
          />
        </div>

        <!-- on a phone a row is a card: the service and its words as wide as
             the screen, the numbers side by side, its amount; the table's
             seven columns ran off the edge -->
        <div v-if="isMobileView" class="flex flex-col gap-3">
          <div
            v-for="(item, index) in plan.items"
            :key="item.key"
            class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-3"
          >
            <div class="flex items-center gap-2">
              <FormControl
                class="min-w-0 flex-1"
                :modelValue="item.service"
                type="select"
                :options="serviceOptions"
                :placeholder="__('Service')"
                :aria-label="__('Service')"
                @update:modelValue="(value) => pickService(item, value)"
              />
              <Button
                variant="ghost"
                icon="x"
                class="shrink-0 touch-target"
                :aria-label="__('Remove the service')"
                @click="plan.items.splice(index, 1)"
              />
            </div>
            <TextInput
              v-model="item.description"
              :placeholder="__('Description')"
              :aria-label="__('Description')"
            />
            <div v-if="teeth" class="grid grid-cols-2 gap-2">
              <FormControl
                v-model="item.tooth"
                :label="__('Tooth')"
                :placeholder="'36'"
              />
              <FormControl
                v-model="item.surfaces"
                :label="__('Surfaces')"
                :placeholder="'MOD'"
                :disabled="!item.tooth"
              />
            </div>
            <div class="grid grid-cols-3 gap-2">
              <FormControl
                v-model="item.phase"
                type="number"
                inputmode="numeric"
                :label="__('Phase')"
              />
              <FormControl
                v-model="item.rate"
                type="number"
                :label="__('Price')"
              />
              <FormControl
                v-model="item.discount"
                type="number"
                :label="__('Discount %')"
              />
            </div>
            <div class="flex items-baseline justify-between gap-3">
              <span class="text-p-sm text-ink-gray-6">{{ __('Amount') }}</span>
              <span class="text-p-base tabular-nums text-ink-gray-8">
                {{ money(importo(item.qty, item.rate, item.discount)) }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="overflow-x-auto">
          <div
            class="flex flex-col gap-2"
            :class="teeth ? 'min-w-[720px]' : 'min-w-[600px]'"
          >
            <div class="grid gap-2 text-p-xs text-ink-gray-5" :class="columns">
              <span>{{ __('Service') }}</span>
              <span>{{ __('Description') }}</span>
              <template v-if="teeth">
                <span>{{ __('Tooth') }}</span>
                <span>{{ __('Surfaces') }}</span>
              </template>
              <span>{{ __('Phase') }}</span>
              <span>{{ __('Price') }}</span>
              <span>{{ __('Discount %') }}</span>
              <span class="text-right">{{ __('Amount') }}</span>
              <span />
            </div>
            <div
              v-for="(item, index) in plan.items"
              :key="item.key"
              class="grid items-center gap-2"
              :class="columns"
            >
              <FormControl
                :modelValue="item.service"
                type="select"
                :options="serviceOptions"
                :placeholder="__('Service')"
                :aria-label="__('Service')"
                @update:modelValue="(value) => pickService(item, value)"
              />
              <TextInput
                v-model="item.description"
                :aria-label="__('Description')"
              />
              <template v-if="teeth">
                <TextInput
                  v-model="item.tooth"
                  :placeholder="'36'"
                  :aria-label="__('Tooth')"
                />
                <TextInput
                  v-model="item.surfaces"
                  :placeholder="'MOD'"
                  :disabled="!item.tooth"
                  :aria-label="__('Surfaces')"
                />
              </template>
              <TextInput
                v-model="item.phase"
                type="number"
                inputmode="numeric"
                :aria-label="__('Phase')"
              />
              <TextInput
                v-model="item.rate"
                type="number"
                :aria-label="__('Price')"
              />
              <TextInput
                v-model="item.discount"
                type="number"
                :aria-label="__('Discount %')"
              />
              <span class="text-right text-p-base tabular-nums text-ink-gray-8">
                {{ money(importo(item.qty, item.rate, item.discount)) }}
              </span>
              <Button
                variant="ghost"
                icon="x"
                class="touch-target"
                :aria-label="__('Remove the service')"
                @click="plan.items.splice(index, 1)"
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          icon-left="plus"
          :label="__('Add a service')"
          @click="addItem"
        />
        <Totals :totals="liveTotals" :money="money" />
        <FormControl
          v-model="plan.patient_notes"
          type="textarea"
          :rows="2"
          :label="__('For the person')"
          :placeholder="
            __('Printed on the quote: how the services go, what is included')
          "
        />
        <ErrorMessage :message="error" />
      </div>

      <!-- reading it -->
      <div v-else class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">{{ facts }}</p>
        <section
          v-for="[phase, items] in phases"
          :key="phase"
          class="flex flex-col gap-1"
        >
          <h4
            v-if="phases.length > 1"
            class="text-p-sm font-medium text-ink-gray-7"
          >
            {{ __('Phase {0}', [phase]) }}
          </h4>
          <div
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <div
              v-for="item in items"
              :key="item.name"
              class="flex flex-wrap items-center gap-x-3 gap-y-1 py-2"
            >
              <span class="min-w-0 flex-1">
                <span
                  class="block text-p-base"
                  :class="
                    item.status === 'Cancelled'
                      ? 'text-ink-gray-5 line-through'
                      : 'text-ink-gray-8'
                  "
                >
                  {{ item.description }}
                  <span v-if="item.detail" class="text-ink-gray-6">
                    · {{ item.detail }}
                  </span>
                </span>
                <span
                  v-if="item.done_on || item.discount"
                  class="block text-p-xs text-ink-gray-5"
                >
                  {{ itemLine(item) }}
                </span>
              </span>
              <span class="shrink-0 text-p-base tabular-nums text-ink-gray-8">
                {{ money(item.amount) }}
              </span>
              <Dropdown
                v-if="plan.can_mark && markOptions(item).length"
                :options="markOptions(item)"
              >
                <Button
                  size="sm"
                  variant="subtle"
                  :theme="STATO_VOCE[item.status] || 'gray'"
                  :label="__(item.status)"
                  icon-right="chevron-down"
                  class="shrink-0"
                />
              </Dropdown>
              <Badge
                v-else
                class="shrink-0"
                variant="subtle"
                :theme="STATO_VOCE[item.status] || 'gray'"
                :label="__(item.status)"
              />
            </div>
          </div>
        </section>
        <Totals :totals="plan.totals" :money="money" :done="isGoing" />
        <p
          v-if="plan.patient_notes"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ plan.patient_notes }}
        </p>

        <!-- the desk records what the person said -->
        <div
          v-if="deciding"
          class="flex flex-col gap-3 rounded-md border border-outline-gray-2 p-3"
        >
          <template v-if="deciding === 'accept'">
            <FormControl
              v-model="decision.note"
              :label="__('How it was accepted')"
              :placeholder="__('Signed at the desk, by email…')"
            />
          </template>
          <template v-else>
            <FormControl
              v-model="decision.reason"
              type="select"
              :label="__('Why')"
              :options="reasonOptions"
            />
            <FormControl
              v-model="decision.note"
              :label="__('In their words')"
              :placeholder="__('Wants to think about it, too expensive…')"
            />
          </template>
          <div class="flex flex-wrap justify-end gap-2">
            <Button :label="__('Cancel')" @click="deciding = ''" />
            <Button
              variant="solid"
              :theme="deciding === 'accept' ? 'gray' : 'red'"
              :label="
                deciding === 'accept'
                  ? __('Record accepted')
                  : __('Record declined')
              "
              :loading="busy === deciding"
              @click="decide"
            />
          </div>
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          v-if="plan.name"
          variant="ghost"
          theme="red"
          :label="__('Delete the draft')"
          @click="removeDraft"
        />
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button
            :label="__('Save the draft')"
            :loading="busy === 'save'"
            @click="save()"
          />
          <Button
            variant="solid"
            :label="__('Propose as a quote')"
            :loading="busy === 'propose'"
            @click="propose"
          />
        </div>
      </div>
      <div
        v-else-if="!loading"
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <div class="flex flex-wrap gap-2">
          <Button
            v-if="plan.quote_pdf"
            icon-left="file-text"
            :label="__('Quote (PDF)')"
            @click="openQuote"
          />
          <Dropdown v-if="moreOptions.length" :options="moreOptions">
            <Button :label="__('More')" icon-right="chevron-down" />
          </Dropdown>
        </div>
        <div v-if="plan.can_decide && !deciding" class="flex flex-wrap gap-2">
          <Button
            theme="red"
            :label="__('Declined', null, 'Quote')"
            @click="startDeciding('decline')"
          />
          <Button
            variant="solid"
            :label="__('Accepted', null, 'Quote')"
            @click="startDeciding('accept')"
          />
        </div>
        <Button
          v-else-if="!deciding"
          :label="__('Done')"
          @click="show = false"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { isMobileView } from '@/composables/breakpoints'
import { useSchedulerMeta } from '@/composables/scheduling'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  STATO,
  STATO_VOCE,
  importo,
  perIlServer,
  totali,
} from '@/utils/preventivi'
import { appLocale } from '@/utils/locale'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  TextInput,
  call,
  toast,
} from 'frappe-ui'
import { computed, h, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: String, required: true },
  // made from a deal's page: a new quote is that deal's
  deal: { type: String, default: null },
  // the quote to open; none for a new one
  name: { type: String, default: null },
  priceLists: { type: Array, default: () => [] },
  // what a module offers on the rows, for a new quote: { teeth: true }
  offers: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const router = useRouter()
const { $dialog } = globalStore()
const { puo } = usersStore()
const meta = useSchedulerMeta()

const plan = reactive({ items: [] })
const loading = ref(false)
const busy = ref('')
const error = ref('')
const deciding = ref('')
const decision = reactive({ reason: '', note: '' })

const editing = computed(() => !plan.name || plan.can_edit)
// a dentist writes the tooth and its surfaces on a row: the clinic offers them
const teeth = computed(() => Boolean((plan.offers || props.offers)?.teeth))
const campi = computed(() => (teeth.value ? ['tooth', 'surfaces'] : []))
const columns = computed(() =>
  teeth.value
    ? 'grid-cols-[minmax(0,2fr)_minmax(0,2fr)_4rem_5rem_4rem_6rem_5rem_6rem_2rem]'
    : 'grid-cols-[minmax(0,2fr)_minmax(0,2fr)_4rem_6rem_5rem_6rem_2rem]',
)
const isGoing = computed(() =>
  ['Accepted', 'Completed', 'Closed'].includes(plan.status),
)

let chiave = 0
function key() {
  chiave += 1
  return `n${chiave}`
}

function fill(data) {
  for (const k of Object.keys(plan)) delete plan[k]
  Object.assign(plan, data, {
    price_list: data.price_list || '',
    items: (data.items || []).map((item) => ({
      ...item,
      key: item.name || key(),
    })),
  })
}

watch(show, async (open) => {
  if (!open) return
  error.value = ''
  busy.value = ''
  deciding.value = ''
  if (!props.name) {
    fill({ title: __('Quote'), status: null, items: [] })
    addItem()
    return
  }
  loading.value = true
  try {
    fill(await call('crm.preventivi.api.get_quote', { name: props.name }))
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not open the quote')
  } finally {
    loading.value = false
  }
})

// --- words ---------------------------------------------------------------------

function money(amount) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: plan.currency || 'EUR',
  }).format(amount || 0)
}

const serviceOptions = computed(() =>
  (meta.data?.services || []).map((service) => ({
    label: service.service_name,
    value: service.name,
  })),
)

const priceListOptions = computed(() => [
  { label: __('The default one'), value: '' },
  ...props.priceLists.map((list) => ({
    label: list.price_list_name,
    value: list.name,
  })),
])

const reasonOptions = computed(() => [
  { label: __('Not said'), value: '' },
  ...(plan.lost_reasons || []).map((reason) => ({
    label: __(reason),
    value: reason,
  })),
])

const liveTotals = computed(() => totali(plan.items))

// the services by phase, in their order
const phases = computed(() => {
  const groups = new Map()
  for (const item of plan.items || []) {
    const phase = Math.max(Number(item.phase) || 1, 1)
    if (!groups.has(phase)) groups.set(phase, [])
    groups.get(phase).push(item)
  }
  return [...groups.entries()].sort(([a], [b]) => a - b)
})

const facts = computed(() => {
  const parts = [plan.practitioner_name]
  if (plan.proposed_on)
    parts.push(
      __('proposed on {0}', [formatDate(plan.proposed_on, 'D MMM YYYY')]),
    )
  if (plan.valid_until && plan.status === 'Proposed')
    parts.push(
      __('valid until {0}', [formatDate(plan.valid_until, 'D MMM YYYY')]),
    )
  if (plan.accepted_on)
    parts.push(
      __('accepted on {0}', [formatDate(plan.accepted_on, 'D MMM YYYY')]) +
        (plan.acceptance_note ? ` (${plan.acceptance_note})` : ''),
    )
  if (plan.declined_on)
    parts.push(
      __('declined on {0}', [formatDate(plan.declined_on, 'D MMM YYYY')]) +
        (plan.decline_reason ? ` (${plan.decline_reason})` : ''),
    )
  if (plan.closed_on)
    parts.push(__('closed on {0}', [formatDate(plan.closed_on, 'D MMM YYYY')]))
  return parts.filter(Boolean).join(' · ')
})

function itemLine(item) {
  const parts = []
  if (item.discount)
    parts.push(
      __('{0} less {1}%', [money(item.rate * item.qty), item.discount]),
    )
  if (item.done_on)
    parts.push(
      __('done on {0}', [formatDate(item.done_on, 'D MMM YYYY')]) +
        (item.done_by_name ? ` · ${item.done_by_name}` : ''),
    )
  return parts.join(' · ')
}

// --- the totals, as one small table ------------------------------------------------

const Totals = (p) => {
  const t = p.totals || {}
  const rows = []
  if (t.discount) {
    rows.push([__('Before discount'), p.money(t.gross)])
    rows.push([__('Discount'), `− ${p.money(t.discount)}`])
  }
  rows.push([__('Total'), p.money(t.net), true])
  if (p.done) {
    rows.push([__('Done'), p.money(t.done)])
    rows.push([__('Left', null, 'Quote amount still to do'), p.money(t.left)])
  }
  return h(
    'dl',
    {
      class:
        'ml-auto grid w-full max-w-xs grid-cols-[1fr_auto] gap-x-4 gap-y-0.5 text-p-sm',
    },
    rows.flatMap(([label, value, strong]) => [
      h(
        'dt',
        { class: strong ? 'font-medium text-ink-gray-8' : 'text-ink-gray-6' },
        label,
      ),
      h(
        'dd',
        {
          class: `text-right tabular-nums ${strong ? 'font-medium text-ink-gray-8' : 'text-ink-gray-7'}`,
        },
        value,
      ),
    ]),
  )
}
Totals.props = ['totals', 'money', 'done']

// --- writing the draft ------------------------------------------------------------

function addItem() {
  plan.items.push({
    key: key(),
    service: '',
    description: '',
    ...(teeth.value ? { tooth: '', surfaces: '' } : {}),
    phase: plan.items.at(-1)?.phase || 1,
    qty: 1,
    rate: 0,
    discount: 0,
  })
}

async function pickService(item, service) {
  const before = (meta.data?.services || []).find(
    (one) => one.name === item.service,
  )?.service_name
  item.service = service
  try {
    const price = await call('crm.preventivi.api.price_of', {
      service,
      price_list: plan.price_list || null,
    })
    item.rate = price.rate
    if (!item.description || item.description === before)
      item.description = price.description
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not read the price')
  }
}

function apriTrattativa() {
  show.value = false
  router.push({ name: 'Deal', params: { dealId: plan.deal } })
}

async function save(quietly = false) {
  busy.value = 'save'
  error.value = ''
  try {
    fill(
      await call('crm.preventivi.api.save_quote', {
        lead: props.lead,
        data: perIlServer(plan, campi.value),
        name: plan.name || null,
        deal: plan.name ? null : props.deal,
      }),
    )
    if (!quietly) toast.success(__('Draft saved'))
    emit('changed')
    return true
  } catch (e) {
    error.value = (e.messages?.[0] || __('Could not save the quote')).replace(
      /<br>/g,
      ' · ',
    )
    return false
  } finally {
    busy.value = ''
  }
}

async function propose() {
  if (!(await save(true))) return
  busy.value = 'propose'
  try {
    fill(await call('crm.preventivi.api.propose_quote', { name: plan.name }))
    toast.success(__('Proposed: the quote is ready to hand over'))
    emit('changed')
  } catch (e) {
    error.value = (e.messages?.[0] || __('Could not propose it')).replace(
      /<br>/g,
      ' · ',
    )
  } finally {
    busy.value = ''
  }
}

function removeDraft() {
  $dialog({
    title: __('Delete the draft?'),
    message: __('The quote was never proposed: nothing else goes with it.'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (closeDialog) => {
          closeDialog()
          try {
            await call('crm.preventivi.api.delete_quote_draft', {
              name: plan.name,
            })
            emit('changed')
            show.value = false
          } catch (e) {
            error.value = e.messages?.[0] || __('Could not delete it')
          }
        },
      },
    ],
  })
}

// --- after it is proposed ----------------------------------------------------------

function startDeciding(what) {
  Object.assign(decision, { reason: '', note: '' })
  deciding.value = what
}

async function act(what, url, params = {}, done) {
  busy.value = what
  error.value = ''
  try {
    fill(await call(url, { name: plan.name, ...params }))
    if (done) toast.success(done)
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not change it')
  } finally {
    busy.value = ''
  }
}

async function decide() {
  if (deciding.value === 'accept') {
    await act(
      'accept',
      'crm.preventivi.api.accept_quote',
      { note: decision.note },
      __('Accepted', null, 'Quote'),
    )
  } else {
    await act(
      'decline',
      'crm.preventivi.api.decline_quote',
      { reason: decision.reason || null, note: decision.note },
      __('Declined', null, 'Quote'),
    )
  }
  if (!error.value) deciding.value = ''
}

function markOptions(item) {
  const options = []
  if (item.status !== 'Done')
    options.push({
      label: __('Done'),
      onClick: () =>
        act('mark', 'crm.preventivi.api.mark_item', {
          item: item.name,
          status: 'Done',
        }),
    })
  if (item.status === 'Done' || item.status === 'Cancelled')
    options.push({
      label: __('To do'),
      onClick: () =>
        act('mark', 'crm.preventivi.api.mark_item', {
          item: item.name,
          status: 'To do',
        }),
    })
  if (item.status === 'To do')
    options.push({
      label: __('Book it'),
      onClick: () => book(item),
    })
  if (item.status !== 'Cancelled' && item.status !== 'Done')
    options.push({
      label: __('Cancelled'),
      onClick: () =>
        act('mark', 'crm.preventivi.api.mark_item', {
          item: item.name,
          status: 'Cancelled',
        }),
    })
  return options
}

const moreOptions = computed(() => {
  const options = []
  if (plan.can_withdraw)
    options.push({
      label: __('Take it back to change it'),
      icon: 'edit-2',
      onClick: () => act('withdraw', 'crm.preventivi.api.withdraw_quote'),
    })
  if (plan.can_copy)
    options.push({
      label: __('New version'),
      icon: 'copy',
      onClick: copy,
    })
  if (plan.can_close)
    options.push({
      label: __('Close the quote'),
      icon: 'lock',
      onClick: () =>
        act('close', 'crm.preventivi.api.close_quote', {}, __('Quote closed')),
    })
  return options
})

async function copy() {
  try {
    const data = await call('crm.preventivi.api.copy_quote', {
      name: plan.name,
    })
    fill(data)
    toast.success(__('A new version, as a draft'))
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not copy it')
  }
}

function openQuote() {
  window.open(plan.quote_pdf, '_blank')
}

// on the calendar: a new appointment of the row's service, for the person
function book(item) {
  show.value = false
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: props.lead, service: item.service },
  })
}
</script>
