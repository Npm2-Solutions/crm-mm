<!--
  A quote as the person reads it (crm.preventivi.area): proposed, to think about;
  accepted, the services done and the ones to come, with when the next one is
  booked - a dental care plan says the tooth too. What it costs, in all and done
  so far. Proposed, it is answered here (`QuoteAnswer`): accepted and signed, or
  not.
-->
<template>
  <article class="area-card flex flex-col gap-3">
    <div class="flex items-start justify-between gap-2">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="area-row__title">{{ quote.title }}</h2>
        <p class="text-p-sm text-ink-gray-5">{{ quote.practitioner_name }}</p>
      </div>
      <!-- a care plan under way: the design system's «in progress» -->
      <InProgressBadge
        v-if="quote.status === 'Accepted'"
        class="shrink-0"
        :label="labels[quote.status]"
      />
      <Badge
        v-else
        class="shrink-0"
        variant="subtle"
        :theme="quote.status === 'Proposed' ? 'blue' : 'green'"
        :label="labels[quote.status] || __(quote.status)"
      />
    </div>
    <p
      v-if="quote.status === 'Proposed' && quote.valid_until"
      class="text-p-sm text-ink-gray-7"
    >
      {{ __('The quote is valid until {0}.', [day(quote.valid_until)]) }}
    </p>
    <ul class="flex flex-col gap-2">
      <li
        v-for="(item, index) in quote.items"
        :key="index"
        class="flex items-start gap-3"
      >
        <span
          class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-[50%_50%_50%_22%]"
          :class="
            item.status === 'Done'
              ? 'bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]'
              : 'bg-surface-gray-2'
          "
          role="img"
          :aria-label="item.status === 'Done' ? __('Done') : __('To do')"
        >
          <LucideCheck
            v-if="item.status === 'Done'"
            class="size-3.5"
            aria-hidden="true"
          />
        </span>
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="text-p-base text-ink-gray-9">
            {{ item.description }}
            <span v-if="item.detail" class="text-ink-gray-6">
              · {{ item.detail }}
            </span>
          </span>
          <span v-if="item.when" class="text-p-sm text-ink-gray-6">
            {{ __('Booked for {0}', [when(item.when)]) }}
          </span>
        </span>
        <span class="shrink-0 text-p-sm tabular-nums text-ink-gray-7">
          {{ money(item.amount) }}
        </span>
      </li>
    </ul>
    <div class="flex flex-col gap-0.5 border-t border-outline-gray-1 pt-2">
      <div class="flex justify-between text-p-base font-medium text-ink-gray-9">
        <span>{{ __('Total') }}</span>
        <span class="tabular-nums">{{ money(quote.totals.net) }}</span>
      </div>
      <div
        v-if="quote.status !== 'Proposed'"
        class="flex justify-between text-p-sm text-ink-gray-6"
      >
        <span>{{ __('Done so far') }}</span>
        <span class="tabular-nums">{{ money(quote.totals.done) }}</span>
      </div>
    </div>
    <!-- paid in instalments: each payment, what is paid, what comes next -->
    <section
      v-if="quote.payment?.rows?.length"
      class="flex flex-col gap-2 border-t border-outline-gray-1 pt-2"
    >
      <h3 class="area-row__title">{{ __('Payment plan') }}</h3>
      <p
        v-if="line"
        class="text-p-sm"
        :class="line.ritardo ? 'text-ink-amber-7' : 'text-ink-gray-7'"
      >
        {{ line.testo }}
      </p>
      <ul class="flex flex-col gap-2">
        <li
          v-for="(row, index) in shownRows"
          :key="index"
          class="flex flex-wrap items-center gap-x-3 gap-y-1"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-[50%_50%_50%_22%]"
            :class="
              row.status === 'Paid'
                ? 'bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]'
                : 'bg-surface-gray-2'
            "
            role="img"
            :aria-label="row.status === 'Paid' ? __('Paid') : __('To pay')"
          >
            <LucideCheck
              v-if="row.status === 'Paid'"
              class="size-3.5"
              aria-hidden="true"
            />
          </span>
          <span class="flex min-w-[8rem] flex-1 flex-col">
            <span class="text-p-base text-ink-gray-9">{{ rowLabel(row) }}</span>
            <span
              class="text-p-sm"
              :class="row.late ? 'text-ink-amber-7' : 'text-ink-gray-6'"
            >
              {{ rowWhen(row) }}
            </span>
          </span>
          <span class="shrink-0 text-p-sm tabular-nums text-ink-gray-7">
            {{ money(row.amount) }}
          </span>
          <Button
            v-if="row.pay_online && !anteprima"
            class="max-md:w-full"
            size="lg"
            variant="solid"
            :label="__('Pay online')"
            :loading="paying === row.invoice"
            @click="pay(row)"
          />
        </li>
      </ul>
      <Button
        v-if="quote.payment.rows.length > shownRows.length || allRows"
        class="w-fit"
        size="lg"
        variant="ghost"
        :label="
          allRows
            ? __('Show fewer')
            : __('Show all {0}', [quote.payment.rows.length])
        "
        @click="allRows = !allRows"
      />
      <ErrorMessage :message="payError" />
    </section>
    <p
      v-if="quote.patient_notes"
      class="whitespace-pre-line text-p-sm text-ink-gray-7"
    >
      {{ quote.patient_notes }}
    </p>
    <QuoteAnswer
      :quote="quote"
      :answers="answers"
      :verified="verified"
      @changed="(data) => emit('changed', data)"
      @verified="emit('verified')"
      @declined="(data) => emit('declined', data)"
    />
  </article>
</template>

<script setup>
import InProgressBadge from '@/components/Espresso/InProgressBadge.vue'
import { fraseDelleRate } from '@/utils/preventivi'
import { Badge, Button, ErrorMessage, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import LucideCheck from '~icons/lucide/check'
import { anteprima } from '../anteprima'
import { day, when } from '../dates'
import { area } from '../store'
import QuoteAnswer from './QuoteAnswer.vue'

const props = defineProps({
  quote: { type: Object, required: true },
  answers: { type: Boolean, default: false },
  verified: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'verified', 'declined'])

const labels = {
  Proposed: __('To decide'),
  Accepted: __('Going on'),
  Completed: __('Completed'),
}

// the plan: the first rows, and the next ones still to pay; all on asking
const PRIMA = 4
const allRows = ref(false)
const shownRows = computed(() => {
  const righe = props.quote.payment?.rows || []
  if (allRows.value || righe.length <= PRIMA + 1) return righe
  const prossima = Math.max(
    righe.findIndex((riga) => riga.status !== 'Paid'),
    0,
  )
  const da = Math.min(prossima, righe.length - PRIMA)
  return righe.slice(da, da + PRIMA)
})

const line = computed(() =>
  fraseDelleRate(
    props.quote.payment?.summary,
    (testo, argomenti) => __(testo, argomenti),
    day,
    money,
  ),
)

function rowLabel(row) {
  if (row.kind === 'Deposit') return __('Deposit')
  return __('Instalment {0} of {1}', [row.number, props.quote.payment.count])
}

function rowWhen(row) {
  if (row.status === 'Paid') return __('Paid')
  if (!row.due_on) return __('On acceptance')
  if (row.late) return __('Was due on {0}', [day(row.due_on)])
  return __('Due on {0}', [day(row.due_on)])
}

const paying = ref('')
const payError = ref('')

// «Pay online»: the instalment's invoice on Stripe, back to the documents
async function pay(row) {
  paying.value = row.invoice
  payError.value = ''
  try {
    const link = await call('crm.area.api.pay_invoice', {
      person: area.person,
      invoice: row.invoice,
    })
    window.location.href = link.url
  } catch (e) {
    paying.value = ''
    payError.value =
      e.messages?.[0] || __('The payment could not start: try again.')
  }
}

function money(amount) {
  return new Intl.NumberFormat(document.documentElement.lang || 'it', {
    style: 'currency',
    currency: props.quote.currency || 'EUR',
  }).format(amount || 0)
}
</script>
