<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A quote (crm.preventivi). Its author writes the draft: services from the price
  list, in phases, with a discount - and what a module adds to a row, where the
  server offers it: the clinic's tooth and surfaces, to a dentist. Proposed, it is
  a PDF to hand over, which the desk records accepted or declined - or sends to
  the person, who accepts and signs it in their area (crm.preventivi.firma): the
  signed copy is kept with it. Accepted, its
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
        <!-- the deal it belongs to, a step away; on a phone it goes under
             the title, its words in line with it -->
        <Button
          v-if="plan.deal && puo('trattative.vedi')"
          class="max-md:-ml-2"
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
            :format="dateFormat()"
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

        <!-- how it is paid: at once, or a deposit and instalments - the centre's
             own plan, no interest nor fees (crm.preventivi.rate) -->
        <section
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
        >
          <h4 class="text-p-base font-medium text-ink-gray-8">
            {{ __('Payment') }}
          </h4>
          <div
            role="radiogroup"
            :aria-label="__('Payment')"
            class="grid grid-cols-2 gap-2"
          >
            <button
              v-for="via in paymentOptions"
              :key="via.value"
              type="button"
              role="radio"
              :aria-checked="plan.payment === via.value"
              class="flex min-h-10 items-center justify-center rounded-md border px-3 py-2 text-center text-p-base"
              :class="
                plan.payment === via.value
                  ? 'dc-scelto border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="choosePayment(via.value)"
            >
              {{ via.label }}
            </button>
          </div>
          <template v-if="plan.payment === A_RATE">
            <div class="grid grid-cols-3 gap-3 max-md:grid-cols-2">
              <FormControl
                v-model="plan.deposit_type"
                type="select"
                :label="__('Deposit as')"
                :options="depositTypeOptions"
              />
              <FormControl
                v-model="plan.deposit_value"
                type="number"
                :label="
                  plan.deposit_type === 'Percent'
                    ? __('Deposit, %')
                    : __('Deposit, {0}', [currencySymbol])
                "
                :min="0"
                placeholder="0"
              />
              <FormControl
                v-model="plan.instalments_count"
                type="number"
                inputmode="numeric"
                :label="__('Instalments')"
                :min="MIN_RATE"
                :max="MAX_RATE"
                :placeholder="__('2 to 36')"
              />
              <FormControl
                v-model="plan.every_months"
                type="select"
                :label="__('How often', null, 'Instalments')"
                :options="everyOptions"
              />
              <FormControl
                v-model="plan.first_due_on"
                class="max-md:col-span-2"
                type="date"
                :format="dateFormat()"
                :label="__('First instalment on')"
              />
            </div>
            <p
              v-if="planProblems.length"
              class="text-p-sm text-ink-amber-7"
              role="status"
            >
              {{ planProblems.join(' · ') }}
            </p>
            <p v-else-if="planWords" class="text-p-sm text-ink-gray-7">
              {{ planWords }}
            </p>
          </template>
        </section>

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

        <!-- paid in instalments: the plan, and how it goes -->
        <section
          v-if="plan.payment === A_RATE && plan.instalments?.length"
          class="flex flex-col gap-2"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h4 class="text-p-sm font-medium text-ink-gray-7">
              {{ __('Payment plan') }}
            </h4>
            <Button
              v-if="plan.can_settle"
              size="sm"
              :label="__('Pay off the rest, {0}', [money(plan.rest)])"
              :loading="busy === 'settle'"
              @click="settle"
            />
          </div>
          <InstalmentsLine
            v-if="plan.instalments_summary"
            :summary="plan.instalments_summary"
            :currency="plan.currency || 'EUR'"
          />
          <div
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <div
              v-for="row in plan.instalments"
              :key="row.name"
              class="flex flex-wrap items-center gap-x-3 gap-y-1 py-2"
            >
              <span class="flex min-w-[10rem] flex-1 flex-col">
                <span
                  class="text-p-base"
                  :class="
                    row.status === 'Cancelled'
                      ? 'text-ink-gray-5 line-through'
                      : 'text-ink-gray-8'
                  "
                >
                  {{ rowLabel(row) }}
                </span>
                <span
                  class="text-p-xs"
                  :class="row.late ? 'text-ink-amber-7' : 'text-ink-gray-5'"
                >
                  {{ rowWhen(row) }}
                </span>
                <span v-if="row.problem" class="text-p-xs text-ink-amber-7">
                  {{ row.problem }}
                </span>
              </span>
              <Button
                v-if="row.invoice"
                size="sm"
                variant="ghost"
                class="shrink-0"
                icon-left="file-text"
                :label="
                  row.invoice_draft
                    ? __('Draft invoice')
                    : row.invoice_number || __('Invoice')
                "
                @click="openInvoice(row.invoice)"
              />
              <span class="shrink-0 text-p-base tabular-nums text-ink-gray-8">
                {{ money(row.amount) }}
              </span>
              <Dropdown
                v-if="rowOptions(row).length"
                :options="rowOptions(row)"
              >
                <Button
                  size="sm"
                  variant="subtle"
                  :theme="STATO_RATA[row.status] || 'gray'"
                  :label="__(row.status, null, 'Instalment')"
                  icon-right="chevron-down"
                  class="shrink-0"
                />
              </Dropdown>
              <Badge
                v-else
                class="shrink-0"
                variant="subtle"
                :theme="STATO_RATA[row.status] || 'gray'"
                :label="__(row.status, null, 'Instalment')"
              />
            </div>
          </div>
          <p v-if="isGoing" class="text-p-sm text-ink-gray-6">
            {{
              plan.instalments_invoiced
                ? __(
                    'Each payment is invoiced by itself when it falls due; the appointments of these services are not invoiced again.',
                  )
                : __(
                    'The centre invoices these payments by itself: mark each one paid here.',
                  )
            }}
          </p>
        </section>
        <p
          v-if="plan.patient_notes"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ plan.patient_notes }}
        </p>

        <!-- the desk records what the person said, or sends it to sign -->
        <div
          v-if="deciding"
          class="flex flex-col gap-3 rounded-md border border-outline-gray-2 p-3"
        >
          <template v-if="deciding === 'send'">
            <p class="text-p-sm text-ink-gray-7">
              {{
                __(
                  'The person reads it in their area and accepts and signs it there, or says no. The message says only that there is a quote to read.',
                )
              }}
            </p>
            <p v-if="!sendOptions" class="text-p-sm text-ink-gray-5">…</p>
            <p v-else-if="sendOptions.demo" class="text-p-sm text-ink-gray-7">
              {{
                __('This is a person of the demo data: nothing is sent to them')
              }}
            </p>
            <div v-else role="radiogroup" class="flex flex-col gap-1.5">
              <button
                v-for="via in sendOptions.channels"
                :key="via.channel"
                type="button"
                role="radio"
                :aria-checked="sending === via.channel"
                :disabled="!via.to"
                class="flex min-h-10 items-start gap-2 rounded-md border px-3 py-2 text-left disabled:cursor-not-allowed disabled:opacity-60"
                :class="
                  sending === via.channel
                    ? 'border-outline-gray-4 bg-surface-gray-2'
                    : 'border-outline-gray-2'
                "
                @click="sending = via.channel"
              >
                <span class="min-w-0 flex-1">
                  <span class="block text-p-base text-ink-gray-9">
                    {{ __(via.channel) }}
                  </span>
                  <span class="block text-p-sm text-ink-gray-6">
                    {{ via.to || via.reason }}
                  </span>
                </span>
              </button>
            </div>
          </template>
          <template v-else-if="deciding === 'accept'">
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
              :theme="deciding === 'decline' ? 'red' : 'gray'"
              :label="
                deciding === 'send'
                  ? __('Send')
                  : deciding === 'accept'
                    ? __('Record accepted')
                    : __('Record declined')
              "
              :disabled="deciding === 'send' && (!sending || sendOptions?.demo)"
              :loading="busy === deciding"
              @click="deciding === 'send' ? sendToSign() : decide()"
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
          <!-- on a phone the row is one: these go under «More» -->
          <Button
            v-if="plan.signed_pdf && !isMobileView"
            icon-left="file-text"
            :label="__('Signed copy (PDF)')"
            @click="openSigned"
          />
          <Button
            v-if="plan.can_send_to_sign && !deciding && !isMobileView"
            icon-left="send"
            :label="__('Send to sign')"
            @click="startSending"
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
          :label="__('Done', null, 'Closes a dialog')"
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
import { dateFormat, formatDate } from '@/utils'
import {
  A_RATE,
  MAX_RATE,
  MIN_RATE,
  STATO,
  STATO_RATA,
  STATO_VOCE,
  UNICA,
  acconto,
  importo,
  perIlServer,
  pianoDelleRate,
  problemiDelleRate,
  totali,
} from '@/utils/preventivi'
import { useFattura } from '@/composables/fattura'
import { oggiDelCentro } from '@/utils/scheduler'
import { simboloDellaValuta } from '@/utils/valute'
import InstalmentsLine from './InstalmentsLine.vue'
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
// where the quote may go to sign, and the way chosen
const sendOptions = ref(null)
const sending = ref('')

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
    payment: data.payment || UNICA,
    deposit_type: data.deposit_type || 'Amount',
    deposit_value: data.deposit_value || '',
    instalments_count: data.instalments_count || '',
    every_months: String(data.every_months || 1),
    first_due_on: data.first_due_on || '',
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
  if (plan.status === 'Proposed' && plan.sent_to_sign_on)
    parts.push(
      __('sent to sign on {0}', [
        formatDate(plan.sent_to_sign_on, 'D MMM YYYY'),
      ]),
    )
  if (plan.signed_on)
    parts.push(
      __('signed in the client area by {0} on {1}', [
        plan.signer_name,
        formatDate(plan.signed_on, 'D MMM YYYY, HH:mm'),
      ]),
    )
  else if (plan.accepted_on)
    parts.push(
      __('accepted on {0}', [formatDate(plan.accepted_on, 'D MMM YYYY')]) +
        (plan.acceptance_note ? ` (${plan.acceptance_note})` : ''),
    )
  if (plan.declined_on)
    parts.push(
      (plan.answered_in === 'In the client area'
        ? __('declined in the client area on {0}', [
            formatDate(plan.declined_on, 'D MMM YYYY'),
          ])
        : __('declined on {0}', [formatDate(plan.declined_on, 'D MMM YYYY')])) +
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
        // on the right on a desk; on a phone as wide as the rows above
        'ml-auto grid w-full max-w-xs grid-cols-[1fr_auto] gap-x-4 gap-y-0.5 text-p-sm max-md:max-w-none',
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

async function startSending() {
  error.value = ''
  sendOptions.value = null
  sending.value = ''
  deciding.value = 'send'
  try {
    sendOptions.value = await call('crm.preventivi.firma.sign_options', {
      name: plan.name,
    })
    sending.value =
      sendOptions.value.channels.find((via) => via.to)?.channel || ''
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not change it')
    deciding.value = ''
  }
}

async function sendToSign() {
  await act(
    'send',
    'crm.preventivi.firma.send_to_sign',
    { channel: sending.value },
    __('Sent: the person reads it in their area'),
  )
  if (!error.value) deciding.value = ''
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
  if (isMobileView.value && plan.signed_pdf)
    options.push({
      label: __('Signed copy (PDF)'),
      icon: 'file-text',
      onClick: openSigned,
    })
  if (isMobileView.value && plan.can_send_to_sign && !deciding.value)
    options.push({
      label: __('Send to sign'),
      icon: 'send',
      onClick: startSending,
    })
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
      onClick: closeQuote,
    })
  return options
})

async function closeQuote() {
  busy.value = 'close'
  error.value = ''
  try {
    const data = await call('crm.preventivi.api.close_quote', {
      name: plan.name,
    })
    fill(data)
    const n = data.cancelled_instalments || 0
    toast.success(
      n === 1
        ? __('Quote closed: the 1 instalment not invoiced yet is cancelled')
        : n
          ? __(
              'Quote closed: the {0} instalments not invoiced yet are cancelled',
              [n],
            )
          : __('Quote closed'),
    )
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not change it')
  } finally {
    busy.value = ''
  }
}

// --- the payment -------------------------------------------------------------------

const paymentOptions = computed(() => [
  { label: __('At once'), value: UNICA },
  { label: __('In instalments'), value: A_RATE },
])
const depositTypeOptions = computed(() => [
  { label: __('An amount'), value: 'Amount' },
  { label: __('A share of the total'), value: 'Percent' },
])
const everyOptions = computed(() => [
  { label: __('Every month'), value: '1' },
  { label: __('Every two months'), value: '2' },
])
const currencySymbol = computed(() =>
  simboloDellaValuta(plan.currency || 'EUR', appLocale()),
)

function choosePayment(value) {
  plan.payment = value
  if (value !== A_RATE) return
  // a start a desk would choose: ten a month, from the first of next month
  if (!plan.instalments_count) plan.instalments_count = 10
  if (!plan.first_due_on) {
    const [anno, mese] = oggiDelCentro().split('-').map(Number)
    const dopo = mese === 12 ? [anno + 1, 1] : [anno, mese + 1]
    plan.first_due_on = `${dopo[0]}-${String(dopo[1]).padStart(2, '0')}-01`
  }
}

const planProblems = computed(() =>
  plan.payment === A_RATE
    ? problemiDelleRate(
        liveTotals.value.net,
        plan.deposit_type,
        plan.deposit_value,
        plan.instalments_count,
        plan.every_months,
        plan.first_due_on || null,
      ).map((problema) => __(problema, [MIN_RATE, MAX_RATE]))
    : [],
)

// the plan in a sentence: «Acconto 400,00 € alla firma · 10 rate da 360,00 €
// ogni mese, dal 1 novembre 2026 al 1 agosto 2027»
const planWords = computed(() => {
  if (plan.payment !== A_RATE || planProblems.value.length) return ''
  const totale = liveTotals.value.net
  const anticipo = acconto(totale, plan.deposit_type, plan.deposit_value)
  const righe = pianoDelleRate(
    totale,
    anticipo,
    plan.instalments_count,
    plan.every_months,
    plan.first_due_on,
  ).filter((riga) => riga.kind !== 'Deposit')
  if (!righe.length) return ''
  const giorno = (d) => formatDate(d, 'D MMMM YYYY')
  const parti = []
  if (anticipo > 0)
    parti.push(__('Deposit of {0} on acceptance', [money(anticipo)]))
  const prima = righe[0]
  const ultima = righe.at(-1)
  parti.push(
    prima.amount === ultima.amount
      ? __('{0} instalments of {1}', [righe.length, money(prima.amount)])
      : __('{0} instalments of {1}, the last {2}', [
          righe.length,
          money(prima.amount),
          money(ultima.amount),
        ]),
  )
  parti.push(
    __('from {0} to {1}', [giorno(prima.due_on), giorno(ultima.due_on)]),
  )
  return parti.join(' · ')
})

const { apriFattura } = useFattura()

function openInvoice(name) {
  apriFattura(name, { alCambio: reload })
}

async function reload() {
  if (!plan.name) return
  try {
    fill(await call('crm.preventivi.api.get_quote', { name: plan.name }))
    emit('changed')
  } catch {
    // the quote stays as it was read
  }
}

function rowLabel(row) {
  if (row.kind === 'Deposit') return __('Deposit')
  const quante = plan.instalments.filter(
    (riga) => riga.kind !== 'Deposit' && riga.status !== 'Cancelled',
  ).length
  return __('Instalment {0} of {1}', [row.number, quante || row.number])
}

function rowWhen(row) {
  if (!row.due_on) return __('On acceptance')
  const giorno = formatDate(row.due_on, 'D MMMM YYYY')
  if (row.status === 'Paid' && row.paid_on)
    return __('due {0} · paid {1}', [
      giorno,
      formatDate(row.paid_on, 'D MMMM YYYY'),
    ])
  return row.late ? __('due {0} · late', [giorno]) : __('due {0}', [giorno])
}

function rowOptions(row) {
  const options = []
  if (plan.can_invoice_instalment && row.status === 'To pay')
    options.push({
      label: __('Invoice it now'),
      onClick: () => invoiceRow(row),
    })
  if (plan.can_mark_instalment && row.status === 'To pay')
    options.push({
      label: __('Mark it paid'),
      onClick: () =>
        act('mark', 'crm.preventivi.rate.mark_instalment', {
          row: row.name,
          paid: 1,
        }),
    })
  if (plan.can_mark_instalment && row.status === 'Paid' && !row.invoice)
    options.push({
      label: __('Back to pay'),
      onClick: () =>
        act('mark', 'crm.preventivi.rate.mark_instalment', {
          row: row.name,
          paid: 0,
        }),
    })
  return options
}

async function invoiceRow(row) {
  busy.value = 'invoice'
  error.value = ''
  try {
    const data = await call('crm.preventivi.rate.invoice_instalment', {
      name: plan.name,
      row: row.name,
    })
    fill(data)
    emit('changed')
    openInvoice(data.invoice)
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not invoice it')
  } finally {
    busy.value = ''
  }
}

function settle() {
  $dialog({
    title: __('Pay off the rest?'),
    message: plan.instalments_invoiced
      ? __(
          'One invoice of {0} takes the place of the instalments still to invoice: it opens as a draft.',
          [money(plan.rest)],
        )
      : __('The instalments still to pay are marked paid today.'),
    actions: [
      {
        label: __('Pay off the rest'),
        variant: 'solid',
        onClick: async (closeDialog) => {
          closeDialog()
          busy.value = 'settle'
          error.value = ''
          try {
            const data = await call('crm.preventivi.rate.settle_quote', {
              name: plan.name,
            })
            fill(data)
            emit('changed')
            if (data.invoice) openInvoice(data.invoice)
          } catch (e) {
            error.value = e.messages?.[0] || __('Could not change it')
          } finally {
            busy.value = ''
          }
        },
      },
    ],
  })
}

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

function openSigned() {
  window.open(plan.signed_pdf, '_blank')
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
