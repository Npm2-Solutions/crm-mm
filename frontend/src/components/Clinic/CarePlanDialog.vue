<!--
  A dental care plan. Its dentist writes the draft: the treatments - a service,
  maybe on a tooth and its surfaces, in phases - priced from the price list, with a
  discount. Proposed, it is a quote to hand over (the PDF), which the desk records
  accepted or declined. Accepted, its treatments are done as the appointments go:
  booked from here, marked by hand when it happened otherwise.
-->
<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{
            editing
              ? plan.name
                ? __('Care plan')
                : __('New care plan')
              : plan.title
          }}
        </h3>
        <Badge
          v-if="plan.status"
          variant="subtle"
          :theme="STATO_PIANO[plan.status] || 'gray'"
          :label="__(plan.status)"
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

        <div class="overflow-x-auto">
          <div class="flex min-w-[720px] flex-col gap-2">
            <div
              class="grid grid-cols-[minmax(0,2fr)_minmax(0,2fr)_4rem_5rem_4rem_6rem_5rem_6rem_2rem] gap-2 text-p-xs text-ink-gray-5"
            >
              <span>{{ __('Service') }}</span>
              <span>{{ __('Description') }}</span>
              <span>{{ __('Tooth') }}</span>
              <span>{{ __('Surfaces') }}</span>
              <span>{{ __('Phase') }}</span>
              <span>{{ __('Price') }}</span>
              <span>{{ __('Discount %') }}</span>
              <span class="text-right">{{ __('Amount') }}</span>
              <span />
            </div>
            <div
              v-for="(item, index) in plan.items"
              :key="item.key"
              class="grid grid-cols-[minmax(0,2fr)_minmax(0,2fr)_4rem_5rem_4rem_6rem_5rem_6rem_2rem] items-center gap-2"
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
              <TextInput
                v-model="item.phase"
                type="number"
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
                :aria-label="__('Remove the treatment')"
                @click="plan.items.splice(index, 1)"
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          icon-left="plus"
          :label="__('Add a treatment')"
          @click="addItem"
        />
        <Totals :totals="liveTotals" :money="money" />
        <FormControl
          v-model="plan.patient_notes"
          type="textarea"
          :rows="2"
          :label="__('For the patient')"
          :placeholder="
            __('Printed on the quote: how the treatments go, what is included')
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
                  <span v-if="item.tooth" class="text-ink-gray-6">
                    · {{ sulDente(item) }}
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
            :label="__('Declined')"
            @click="startDeciding('decline')"
          />
          <Button
            variant="solid"
            :label="__('Accepted')"
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
import { useSchedulerMeta } from '@/composables/scheduling'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  STATO_PIANO,
  STATO_VOCE,
  importo,
  perIlServer,
  sulDente,
  totali,
} from '@/utils/cure'
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
  // the plan to open; none for a new one
  name: { type: String, default: null },
  priceLists: { type: Array, default: () => [] },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const router = useRouter()
const { $dialog } = globalStore()
const meta = useSchedulerMeta()

const plan = reactive({ items: [] })
const loading = ref(false)
const busy = ref('')
const error = ref('')
const deciding = ref('')
const decision = reactive({ reason: '', note: '' })

const editing = computed(() => !plan.name || plan.can_edit)
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
    fill({ title: __('Care plan'), status: null, items: [] })
    addItem()
    return
  }
  loading.value = true
  try {
    fill(await call('crm.clinica.cure.get_care_plan', { name: props.name }))
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not open the care plan')
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

// the treatments by phase, in their order
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
    rows.push([__('Left'), p.money(t.left)])
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
    tooth: '',
    surfaces: '',
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
    const price = await call('crm.clinica.cure.price_of', {
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

async function save(quietly = false) {
  busy.value = 'save'
  error.value = ''
  try {
    fill(
      await call('crm.clinica.cure.save_care_plan', {
        lead: props.lead,
        data: perIlServer(plan),
        name: plan.name || null,
      }),
    )
    if (!quietly) toast.success(__('Draft saved'))
    emit('changed')
    return true
  } catch (e) {
    error.value = (
      e.messages?.[0] || __('Could not save the care plan')
    ).replace(/<br>/g, ' · ')
    return false
  } finally {
    busy.value = ''
  }
}

async function propose() {
  if (!(await save(true))) return
  busy.value = 'propose'
  try {
    fill(await call('crm.clinica.cure.propose_care_plan', { name: plan.name }))
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
    message: __('The care plan was never proposed: nothing else goes with it.'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (closeDialog) => {
          closeDialog()
          try {
            await call('crm.clinica.cure.delete_care_plan_draft', {
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
      'crm.clinica.cure.accept_care_plan',
      { note: decision.note },
      __('Accepted'),
    )
  } else {
    await act(
      'decline',
      'crm.clinica.cure.decline_care_plan',
      { reason: decision.reason || null, note: decision.note },
      __('Declined'),
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
        act('mark', 'crm.clinica.cure.mark_treatment', {
          item: item.name,
          status: 'Done',
        }),
    })
  if (item.status === 'Done' || item.status === 'Cancelled')
    options.push({
      label: __('To do'),
      onClick: () =>
        act('mark', 'crm.clinica.cure.mark_treatment', {
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
        act('mark', 'crm.clinica.cure.mark_treatment', {
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
      onClick: () => act('withdraw', 'crm.clinica.cure.withdraw_care_plan'),
    })
  if (plan.can_copy)
    options.push({
      label: __('New version'),
      icon: 'copy',
      onClick: copy,
    })
  if (plan.can_close)
    options.push({
      label: __('Close the plan'),
      icon: 'lock',
      onClick: () =>
        act(
          'close',
          'crm.clinica.cure.close_care_plan',
          {},
          __('Care plan closed'),
        ),
    })
  return options
})

async function copy() {
  try {
    const data = await call('crm.clinica.cure.copy_care_plan', {
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

// on the calendar: a new appointment of the treatment's service, for the person
function book(item) {
  show.value = false
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: props.lead, service: item.service },
  })
}
</script>
