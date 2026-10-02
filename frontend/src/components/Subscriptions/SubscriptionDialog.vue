<!--
  A subscription: sold here, followed here. Sold, it is a type from a day - maybe
  at another price or paid otherwise - with who follows it. Read, it says until
  when it lasts, how this week's or month's entries stand, each appointment that
  used one, the instalments and their invoices, the suspensions; and what comes
  next: book, suspend, renew, close or open it again.
-->
<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ title }}
        </h3>
        <Badge
          v-if="!editing && sub.status"
          variant="subtle"
          :theme="TEMA_DELLO_STATO[sub.status] || 'gray'"
          :label="__(sub.status)"
        />
      </div>
    </template>
    <template #body-content>
      <div v-if="loading" class="py-10 text-center text-p-sm text-ink-gray-5">
        {{ __('Loading…') }}
      </div>

      <!-- selling it, or putting it right -->
      <div v-else-if="editing" class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.subscription_type"
            type="select"
            :label="__('Type')"
            :placeholder="__('Choose a type')"
            :options="typeOptions"
            :disabled="Boolean(sub.name)"
          />
          <FormControl
            v-model="form.starts_on"
            type="date"
            :label="__('From')"
          />
        </div>
        <p v-if="chosen" class="-mt-1 text-p-sm text-ink-gray-6">
          {{ chosenLine }}
        </p>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.price"
            type="number"
            :label="__('Price')"
            :placeholder="
              chosen ? money(chosen.price, chosen.currency) : __('The type’s')
            "
            :min="0"
          />
          <FormControl
            v-model="form.payment"
            type="select"
            :label="__('Paid')"
            :options="paymentOptions"
          />
        </div>
        <p v-if="planLine" class="-mt-1 text-p-sm text-ink-gray-6">
          {{ planLine }}
        </p>
        <FormControl
          v-model="form.practitioner"
          type="select"
          :label="__('Followed by')"
          :options="practitionerOptions"
        />
        <FormControl
          v-model="form.notes"
          type="textarea"
          :rows="2"
          :label="__('Notes')"
        />
        <ErrorMessage :message="error" />
      </div>

      <!-- following it -->
      <div v-else class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <template v-if="sub.entries !== ILLIMITATI && sub.used !== null">
            <div
              class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2"
              role="progressbar"
              :aria-valuenow="percentuale(sub)"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-label="__('Entries used')"
            >
              <div
                class="h-full rounded-full bg-[var(--brand-segno)]"
                :style="{ width: `${percentuale(sub)}%` }"
              />
            </div>
            <p class="text-p-base text-ink-gray-8">
              {{ questoPeriodo(sub, t) }}
            </p>
          </template>
          <p class="text-p-sm text-ink-gray-6">{{ facts }}</p>
          <p v-if="sub.suspended_until" class="text-p-sm text-ink-amber-7">
            {{
              __('Suspended until {0}', [
                formatDate(sub.suspended_until, 'D MMM YYYY'),
              ])
            }}
          </p>
        </div>
        <p
          v-if="sub.notes"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ sub.notes }}
        </p>

        <!-- suspending it -->
        <div
          v-if="suspending"
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
            <FormControl
              v-model="pause.from_date"
              type="date"
              :label="__('From')"
            />
            <FormControl
              v-model="pause.to_date"
              type="date"
              :label="__('To')"
            />
          </div>
          <FormControl
            v-model="pause.reason"
            :label="__('Why')"
            :placeholder="__('An injury, a holiday…')"
          />
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'The end moves by those days; the appointments booked in them stop using an entry.',
              )
            }}
          </p>
          <div class="flex flex-wrap justify-end gap-2">
            <Button :label="__('Cancel')" @click="suspending = false" />
            <Button
              variant="solid"
              :label="__('Suspend')"
              :loading="busy === 'suspend'"
              @click="suspend"
            />
          </div>
        </div>

        <section class="flex flex-col gap-1.5">
          <h4 class="text-p-sm-medium text-ink-gray-7">
            {{ __('Entries') }}
          </h4>
          <ol
            v-if="sub.appointments?.length"
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <li
              v-for="appointment in sub.appointments"
              :key="appointment.name"
              class="flex items-center gap-3 py-2"
            >
              <button
                type="button"
                class="min-w-0 flex-1 truncate text-left text-p-base text-ink-gray-8 hover:underline focus-visible:underline focus-visible:outline-none max-md:whitespace-normal"
                @click="openAppointment(appointment)"
              >
                {{ formatDate(appointment.starts_on, 'ddd D MMM YYYY, HH:mm') }}
                · {{ serviceName(appointment.service) }}
              </button>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="SEDUTA[appointment.state]?.theme || 'gray'"
                :label="
                  __(SEDUTA[appointment.state]?.label || appointment.state)
                "
              />
            </li>
          </ol>
          <p v-else class="text-p-sm text-ink-gray-5">
            {{ __('No appointment has used an entry yet.') }}
          </p>
        </section>

        <section class="flex flex-col gap-1.5">
          <h4 class="text-p-sm-medium text-ink-gray-7">
            {{ __('Instalments') }}
          </h4>
          <ul
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <li
              v-for="row in sub.instalments || []"
              :key="row.name"
              class="flex flex-wrap items-center gap-x-3 gap-y-1 py-2"
            >
              <span class="min-w-0 flex-1 text-p-base text-ink-gray-8">
                {{ formatDate(row.due_on, 'D MMM YYYY') }} ·
                {{ money(row.amount, sub.currency) }}
              </span>
              <span
                class="text-p-sm"
                :class="row.problem ? 'text-ink-red-4' : 'text-ink-gray-6'"
              >
                {{ instalmentLine(row) }}
              </span>
              <Button
                v-if="canInvoiceRow(row)"
                size="sm"
                class="shrink-0"
                :label="__('Invoice')"
                :loading="busy === `invoice-${row.name}`"
                @click="invoice(row)"
              />
            </li>
          </ul>
        </section>

        <section v-if="sub.suspensions?.length" class="flex flex-col gap-1.5">
          <h4 class="text-p-sm-medium text-ink-gray-7">
            {{ __('Suspensions') }}
          </h4>
          <ul
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <li
              v-for="row in sub.suspensions"
              :key="row.name"
              class="flex items-center gap-3 py-2"
            >
              <span class="min-w-0 flex-1 text-p-base text-ink-gray-8">
                {{
                  __('{0} to {1}', [
                    formatDate(row.from_date, 'D MMM YYYY'),
                    formatDate(row.to_date, 'D MMM YYYY'),
                  ])
                }}
                <span v-if="row.reason" class="text-ink-gray-5">
                  · {{ row.reason }}
                </span>
              </span>
              <Button
                v-if="sub.can_manage && sub.status !== 'Closed'"
                variant="ghost"
                class="touch-target shrink-0"
                icon="x"
                :aria-label="__('Take the suspension away')"
                :title="__('Take the suspension away')"
                :loading="busy === `pause-${row.name}`"
                @click="unpause(row)"
              />
            </li>
          </ul>
        </section>
        <ErrorMessage :message="error" />
      </div>
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-end gap-2"
      >
        <Button
          v-if="sub.name"
          :label="__('Cancel')"
          @click="editing = false"
        />
        <Button
          variant="solid"
          :label="sub.name ? __('Save') : __('Sell the subscription')"
          :loading="busy === 'save'"
          @click="save"
        />
      </div>
      <div
        v-else-if="!loading"
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Dropdown v-if="moreOptions.length" :options="moreOptions">
          <Button
            :label="__('More')"
            icon-right="chevron-down"
            :loading="['close', 'reopen', 'delete', 'renew'].includes(busy)"
          />
        </Dropdown>
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button
            v-if="['Active', 'Suspended'].includes(sub.status)"
            variant="solid"
            :label="__('Book')"
            @click="book"
          />
          <Button
            v-else
            variant="solid"
            :label="__('Done')"
            @click="show = false"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { useFattura } from '@/composables/fattura'
import { useSchedulerMeta } from '@/composables/scheduling'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  ILLIMITATI,
  MENSILE,
  SUBITO,
  TEMA_DELLO_STATO,
  cosaDa,
  errore,
  fine,
  percentuale,
  questoPeriodo,
  rate,
} from '@/utils/abbonamenti'
import { SEDUTA } from '@/utils/cicli'
import { appLocale } from '@/utils/locale'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  call,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: String, required: true },
  // the subscription to open; none to sell a new one
  name: { type: String, default: null },
  // the types on sale, from the person's section
  types: { type: Array, default: () => [] },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })
const { apriFattura } = useFattura()

const router = useRouter()
const { $dialog } = globalStore()
const meta = useSchedulerMeta()
const t = (text, args) => __(text, args)

const sub = reactive({})
const form = reactive({})
const pause = reactive({ from_date: '', to_date: '', reason: '' })
const editing = ref(false)
const suspending = ref(false)
const loading = ref(false)
const busy = ref('')
const error = ref('')

function empty() {
  return {
    subscription_type: '',
    starts_on: dayjs().format('YYYY-MM-DD'),
    price: '',
    payment: '',
    practitioner: '',
    notes: '',
  }
}

function fill(data) {
  for (const key of Object.keys(sub)) delete sub[key]
  Object.assign(sub, data)
}

function edit() {
  Object.assign(form, empty(), {
    subscription_type: sub.subscription_type,
    starts_on: sub.starts_on || '',
    price: sub.price ?? '',
    payment: sub.payment || SUBITO,
    practitioner: sub.practitioner || '',
    notes: sub.notes || '',
  })
  error.value = ''
  editing.value = true
}

watch(
  show,
  async (open) => {
    if (!open) return
    error.value = ''
    busy.value = ''
    suspending.value = false
    if (!props.name) {
      fill({})
      Object.assign(form, empty())
      if (props.types.length === 1) form.subscription_type = props.types[0].name
      editing.value = true
      return
    }
    editing.value = false
    loading.value = true
    try {
      fill(
        await call('crm.scheduling.abbonamenti.get_subscription', {
          name: props.name,
        }),
      )
    } catch (e) {
      error.value = e.messages?.[0] || __('Could not open the subscription')
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

// a type chosen: its payment, unless one was chosen already
watch(
  () => form.subscription_type,
  (name) => {
    const type = props.types.find((one) => one.name === name)
    if (type && !sub.name) form.payment = type.payment || SUBITO
  },
)

// --- words --------------------------------------------------------------------

function serviceName(name) {
  const service = (meta.data?.services || []).find((one) => one.name === name)
  return service?.service_name || name || ''
}

function money(amount, currency) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount || 0)
}

const title = computed(() => {
  if (editing.value)
    return sub.name ? __('Change the subscription') : __('New subscription')
  return sub.subscription_type || ''
})

const typeOptions = computed(() =>
  props.types.map((type) => ({ label: type.name, value: type.name })),
)

const chosen = computed(() =>
  props.types.find((one) => one.name === form.subscription_type),
)

const chosenLine = computed(() => {
  const type = chosen.value
  if (!type) return ''
  const parts = [cosaDa(type, t)]
  if (type.services?.length)
    parts.push(type.services.map(serviceName).join(', '))
  if (form.starts_on)
    parts.push(
      __('until {0}', [
        formatDate(fine(form.starts_on, type.months), 'D MMM YYYY'),
      ]),
    )
  return parts.join(' · ')
})

const paymentOptions = [
  { label: __('All at once'), value: SUBITO },
  { label: __('By the month'), value: MENSILE },
]

// the instalments the sale will make, as the server makes them
const planLine = computed(() => {
  const type = chosen.value
  if (!type || !form.starts_on) return ''
  const price = form.price === '' ? type.price : Number(form.price)
  const rows = rate(form.starts_on, type.months, price, form.payment)
  if (rows.length <= 1) return ''
  return __('{0} instalments of {1}, the first on {2}', [
    rows.length,
    money(rows[0].amount, type.currency),
    formatDate(rows[0].due_on, 'D MMM'),
  ])
})

const practitionerOptions = computed(() => [
  { label: __('Nobody in particular'), value: '' },
  ...(meta.data?.staff || []).map((user) => ({
    label: user.full_name,
    value: user.name,
  })),
])

const facts = computed(() => {
  const parts = [
    __('{0} to {1}', [
      formatDate(sub.starts_on, 'D MMM YYYY'),
      formatDate(sub.ends_on, 'D MMM YYYY'),
    ]),
    cosaDa(sub, t),
  ]
  if (sub.price)
    parts.push(
      sub.payment === MENSILE && sub.instalments?.length > 1
        ? __('{0} in {1} instalments', [
            money(sub.price, sub.currency),
            sub.instalments.length,
          ])
        : money(sub.price, sub.currency),
    )
  if (sub.auto_renew) parts.push(__('renews by itself'))
  if (sub.renewed_by) parts.push(__('renewed'))
  if (sub.practitioner_name) parts.push(sub.practitioner_name)
  return parts.filter(Boolean).join(' · ')
})

function instalmentLine(row) {
  if (row.problem) return row.problem
  if (row.invoice)
    return row.issued
      ? __('Invoiced {0}', [row.number || ''])
      : __('Invoice to issue')
  if (!sub.billable) return ''
  return row.due_on <= dayjs().format('YYYY-MM-DD')
    ? __('To invoice')
    : __('Invoiced on its day')
}

function canInvoiceRow(row) {
  return (
    sub.can_invoice && sub.billable && !row.invoice && sub.status !== 'Closed'
  )
}

// --- what can be done -----------------------------------------------------------

const moreOptions = computed(() => {
  if (!sub.can_manage) return []
  const options = []
  if (sub.status !== 'Closed') {
    options.push({ label: __('Change'), icon: 'edit-2', onClick: edit })
    if (sub.can_suspend)
      options.push({
        label: __('Suspend'),
        icon: 'pause',
        onClick: () => {
          Object.assign(pause, {
            from_date: dayjs().format('YYYY-MM-DD'),
            to_date: '',
            reason: '',
          })
          suspending.value = true
        },
      })
    if (!sub.renewed_by)
      options.push({ label: __('Renew'), icon: 'repeat', onClick: renew })
    options.push({
      label: __('Close the subscription'),
      icon: 'lock',
      onClick: close,
    })
  } else {
    options.push({
      label: __('Open it again'),
      icon: 'unlock',
      onClick: () =>
        act('reopen', 'crm.scheduling.abbonamenti.reopen_subscription'),
    })
  }
  const used = (sub.appointments || []).some((one) =>
    ['done', 'missed'].includes(one.state),
  )
  if (!used && !(sub.instalments || []).some((row) => row.invoice))
    options.push({ label: __('Delete'), icon: 'trash-2', onClick: remove })
  return options
})

async function act(what, url, extra = {}) {
  busy.value = what
  error.value = ''
  try {
    fill(await call(url, { name: sub.name, ...extra }))
    emit('changed')
    return true
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not change it')
    return false
  } finally {
    busy.value = ''
  }
}

async function suspend() {
  if (
    await act('suspend', 'crm.scheduling.abbonamenti.suspend_subscription', {
      ...pause,
    })
  )
    suspending.value = false
}

function unpause(row) {
  act(`pause-${row.name}`, 'crm.scheduling.abbonamenti.remove_suspension', {
    row: row.name,
  })
}

function renew() {
  $dialog({
    title: __('Renew the subscription?'),
    message: __(
      'The next one starts the day after this one ends, at the type’s price of today.',
    ),
    actions: [
      {
        label: __('Renew'),
        variant: 'solid',
        onClick: async (closeDialog) => {
          closeDialog()
          if (
            await act('renew', 'crm.scheduling.abbonamenti.renew_subscription')
          )
            toast.success(__('Subscription renewed'))
        },
      },
    ],
  })
}

function close() {
  $dialog({
    title: __('Close the subscription?'),
    message: __(
      'What is booked keeps its entry; no new appointment uses one. It can be opened again.',
    ),
    actions: [
      {
        label: __('Close it'),
        variant: 'solid',
        onClick: (closeDialog) => {
          closeDialog()
          act('close', 'crm.scheduling.abbonamenti.close_subscription')
        },
      },
    ],
  })
}

function remove() {
  $dialog({
    title: __('Delete the subscription?'),
    message: __(
      'For a subscription sold by mistake: its booked appointments stay in the agenda, at the price list’s price.',
    ),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (closeDialog) => {
          closeDialog()
          busy.value = 'delete'
          try {
            await call('crm.scheduling.abbonamenti.delete_subscription', {
              name: sub.name,
            })
            toast.success(__('Subscription deleted'))
            emit('changed')
            show.value = false
          } catch (e) {
            error.value = e.messages?.[0] || __('Could not delete it')
          } finally {
            busy.value = ''
          }
        },
      },
    ],
  })
}

async function save() {
  error.value = errore(form, t)
  if (error.value) return
  busy.value = 'save'
  const sold = !sub.name
  const data = {
    subscription_type: form.subscription_type,
    starts_on: form.starts_on,
    price: form.price === '' ? null : Number(form.price),
    payment: form.payment || null,
    practitioner: form.practitioner || null,
    notes: (form.notes || '').trim() || null,
  }
  try {
    fill(
      sold
        ? await call('crm.scheduling.abbonamenti.sell_subscription', {
            lead: props.lead,
            data,
          })
        : await call('crm.scheduling.abbonamenti.save_subscription', {
            name: sub.name,
            data,
          }),
    )
    toast.success(sold ? __('Subscription sold') : __('Subscription saved'))
    editing.value = false
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not save the subscription')
  } finally {
    busy.value = ''
  }
}

async function invoice(row) {
  busy.value = `invoice-${row.name}`
  error.value = ''
  try {
    const done = await call('crm.scheduling.abbonamenti.invoice_instalment', {
      name: sub.name,
      row: row.name,
    })
    fill(done)
    emit('changed')
    // the instalment's draft, to check and issue: one dialog at a time
    show.value = false
    apriFattura(done.invoice)
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not open the invoice')
  } finally {
    busy.value = ''
  }
}

// on the calendar: a new appointment for the person, of the first service
function book() {
  show.value = false
  router.push({
    name: 'Calendar',
    query: {
      new: 'appointment',
      party: props.lead,
      service: sub.services?.[0] || undefined,
    },
  })
}

function openAppointment(appointment) {
  show.value = false
  router.push({
    name: 'Calendar',
    query: {
      appointment: appointment.name,
      date: dayjs(appointment.starts_on).format('YYYY-MM-DD'),
    },
  })
}
</script>
