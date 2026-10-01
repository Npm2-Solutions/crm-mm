<!--
  A cycle of sessions: sold here, followed here. New or put right, it says the
  service, how many sessions, from when and maybe until when, the price of the
  whole cycle and how it is paid. Read, it says how far it is - each appointment
  with its number and how it went - and what comes next: book a session, invoice
  it when it is paid as a whole, close it or open it again.
-->
<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ title }}
        </h3>
        <Badge
          v-if="!editing && cycle.status"
          variant="subtle"
          :theme="TEMA_DELLO_STATO[cycle.status] || 'gray'"
          :label="__(cycle.status)"
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
            v-model="form.service"
            type="select"
            :label="__('Service')"
            :placeholder="__('Choose a service')"
            :options="serviceOptions"
            :disabled="serviceLocked"
          />
          <FormControl
            v-model="form.sessions"
            type="number"
            :label="__('Sessions')"
            :min="1"
            :max="MAX_SEDUTE"
          />
          <FormControl
            v-model="form.starts_on"
            type="date"
            :label="__('From')"
          />
          <FormControl
            v-model="form.valid_until"
            type="date"
            :label="__('Valid until')"
          />
        </div>
        <p class="-mt-1 text-p-sm text-ink-gray-6">
          {{
            __(
              'The appointments of this service join the cycle by themselves from its first day, the ones already booked too. Without a last day, it lasts until the sessions are used.',
            )
          }}
        </p>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.price"
            type="number"
            :label="__('Price of the cycle')"
            :placeholder="__('Empty: the price list')"
            :min="0"
          />
          <FormControl
            v-model="form.billing"
            type="select"
            :label="__('Invoiced')"
            :options="billingOptions"
          />
        </div>
        <p v-if="shareLine" class="-mt-1 text-p-sm text-ink-gray-6">
          {{ shareLine }}
        </p>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.practitioner"
            type="select"
            :label="__('Followed by')"
            :options="practitionerOptions"
          />
          <div class="flex items-end pb-1.5">
            <FormControl
              v-model="form.missed_count"
              type="checkbox"
              :label="__('A missed session is used')"
            />
          </div>
        </div>
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
          <div
            class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2"
            role="progressbar"
            :aria-valuenow="percentuale(cycle.counts)"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="__('Sessions used')"
          >
            <div
              class="h-full rounded-full bg-[var(--brand-segno)]"
              :style="{ width: `${percentuale(cycle.counts)}%` }"
            />
          </div>
          <p class="text-p-base text-ink-gray-8">
            {{ comeVa(cycle.counts, t) }}
          </p>
          <p class="text-p-sm text-ink-gray-6">{{ facts }}</p>
        </div>
        <p
          v-if="cycle.notes"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ cycle.notes }}
        </p>
        <ol
          v-if="cycle.appointments?.length"
          class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
        >
          <li
            v-for="appointment in cycle.appointments"
            :key="appointment.name"
            class="flex items-center gap-3 py-2"
          >
            <span
              class="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-p-xs tabular-nums text-ink-gray-7"
              :aria-label="
                appointment.number
                  ? __('Session {0}', [appointment.number])
                  : __('Not counted')
              "
            >
              {{ appointment.number || '–' }}
            </span>
            <button
              type="button"
              class="min-w-0 flex-1 truncate text-left text-p-base text-ink-gray-8 hover:underline focus-visible:underline focus-visible:outline-none"
              @click="openAppointment(appointment)"
            >
              {{ formatDate(appointment.starts_on, 'ddd D MMM YYYY, HH:mm') }}
            </button>
            <Badge
              class="shrink-0"
              variant="subtle"
              :theme="SEDUTA[appointment.state]?.theme || 'gray'"
              :label="__(SEDUTA[appointment.state]?.label || appointment.state)"
            />
          </li>
        </ol>
        <p v-else class="text-p-sm text-ink-gray-5">
          {{ __('No session booked yet.') }}
        </p>
        <ErrorMessage :message="error" />
      </div>
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-end gap-2"
      >
        <Button
          v-if="cycle.name"
          :label="__('Cancel')"
          @click="editing = false"
        />
        <Button
          variant="solid"
          :label="cycle.name ? __('Save') : __('Sell the cycle')"
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
            :loading="['close', 'reopen', 'delete'].includes(busy)"
          />
        </Dropdown>
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button
            v-if="canInvoice"
            :label="__('Invoice the cycle')"
            :loading="busy === 'invoice'"
            @click="invoice"
          />
          <Button
            v-if="cycle.status === 'Active' && cycle.counts?.left"
            variant="solid"
            :label="__('Book a session')"
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
import { useSchedulerMeta } from '@/composables/scheduling'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  INTERO,
  MAX_SEDUTE,
  PER_SEDUTA,
  SEDUTA,
  TEMA_DELLO_STATO,
  comeVa,
  daPrenotare,
  errore,
  percentuale,
  perIlServer,
  quota,
} from '@/utils/cicli'
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
  // the cycle to open; none to sell a new one
  name: { type: String, default: null },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const router = useRouter()
const { $dialog } = globalStore()
const meta = useSchedulerMeta()
const t = (text, args) => __(text, args)

const cycle = reactive({})
const form = reactive({})
const editing = ref(false)
const loading = ref(false)
const busy = ref('')
const error = ref('')

function empty() {
  return {
    service: '',
    sessions: 10,
    starts_on: dayjs().format('YYYY-MM-DD'),
    valid_until: '',
    price: '',
    billing: PER_SEDUTA,
    missed_count: true,
    practitioner: '',
    notes: '',
  }
}

function fill(data) {
  for (const key of Object.keys(cycle)) delete cycle[key]
  Object.assign(cycle, data)
}

function edit() {
  Object.assign(form, empty(), {
    service: cycle.service,
    sessions: cycle.sessions,
    starts_on: cycle.starts_on || '',
    valid_until: cycle.valid_until || '',
    price: cycle.price || '',
    billing: cycle.billing || PER_SEDUTA,
    missed_count: Boolean(cycle.missed_count),
    practitioner: cycle.practitioner || '',
    notes: cycle.notes || '',
  })
  error.value = ''
  editing.value = true
}

watch(show, async (open) => {
  if (!open) return
  error.value = ''
  busy.value = ''
  if (!props.name) {
    fill({})
    Object.assign(form, empty())
    const services = meta.data?.services || []
    if (services.length === 1) form.service = services[0].name
    editing.value = true
    return
  }
  editing.value = false
  loading.value = true
  try {
    fill(await call('crm.scheduling.cicli.get_cycle', { name: props.name }))
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not open the cycle')
  } finally {
    loading.value = false
  }
})

// --- words --------------------------------------------------------------------

function serviceName(name) {
  const service = (meta.data?.services || []).find((one) => one.name === name)
  return service?.service_name || name || ''
}

const title = computed(() => {
  if (editing.value)
    return cycle.name ? __('Change the cycle') : __('New cycle')
  return serviceName(cycle.service)
})

function money(amount, currency) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount || 0)
}

const serviceOptions = computed(() =>
  (meta.data?.services || []).map((service) => ({
    label: service.service_name,
    value: service.name,
  })),
)

// the service stays once a session is booked: the server says it too
const serviceLocked = computed(
  () =>
    Boolean(cycle.name) &&
    (cycle.counts?.used || 0) + (cycle.counts?.booked || 0) > 0,
)

const billingOptions = [
  { label: __('Session by session'), value: PER_SEDUTA },
  { label: __('The whole cycle, in one invoice'), value: INTERO },
]

const practitionerOptions = computed(() => {
  const service = (meta.data?.services || []).find(
    (one) => one.name === form.service,
  )
  const theirs = new Set((service?.staff || []).map((row) => row.user))
  const staff = (meta.data?.staff || []).filter(
    (user) => !theirs.size || theirs.has(user.name),
  )
  return [
    { label: __('Nobody in particular'), value: '' },
    ...staff.map((user) => ({ label: user.full_name, value: user.name })),
  ]
})

const shareLine = computed(() => {
  const each = quota(form.price, form.sessions)
  if (each) {
    const currency = (meta.data?.services || []).find(
      (one) => one.name === form.service,
    )?.currency
    return __('Each session costs {0}', [money(each, currency)])
  }
  return ''
})

const facts = computed(() => {
  const parts = [daPrenotare(cycle.counts, t)]
  if (cycle.next)
    parts.push(__('next {0}', [formatDate(cycle.next, 'ddd D MMM, HH:mm')]))
  if (cycle.valid_until)
    parts.push(
      __('valid until {0}', [formatDate(cycle.valid_until, 'D MMM YYYY')]),
    )
  if (cycle.price) {
    parts.push(
      cycle.billing === INTERO
        ? __('{0} in one invoice', [money(cycle.price, cycle.currency)])
        : __('{0}, a session {1}', [
            money(cycle.price, cycle.currency),
            money(quota(cycle.price, cycle.sessions), cycle.currency),
          ]),
    )
  }
  if (cycle.invoice) parts.push(__('invoiced'))
  if (cycle.practitioner_name) parts.push(cycle.practitioner_name)
  return parts.filter(Boolean).join(' · ')
})

// --- what can be done -----------------------------------------------------------

const canInvoice = computed(
  () =>
    cycle.can_invoice &&
    cycle.billing === INTERO &&
    cycle.price &&
    !cycle.invoice &&
    cycle.status !== 'Closed',
)

const moreOptions = computed(() => {
  if (!cycle.can_manage) return []
  const options = []
  if (cycle.status !== 'Closed') {
    options.push({ label: __('Change'), icon: 'edit-2', onClick: edit })
    options.push({ label: __('Close the cycle'), icon: 'lock', onClick: close })
  } else {
    options.push({
      label: __('Open it again'),
      icon: 'unlock',
      onClick: () => act('reopen', 'crm.scheduling.cicli.reopen_cycle'),
    })
  }
  if (!cycle.counts?.used && !cycle.invoice)
    options.push({ label: __('Delete'), icon: 'trash-2', onClick: remove })
  return options
})

async function act(what, url) {
  busy.value = what
  error.value = ''
  try {
    fill(await call(url, { name: cycle.name }))
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not change it')
  } finally {
    busy.value = ''
  }
}

function close() {
  $dialog({
    title: __('Close the cycle?'),
    message: __(
      'The sessions booked stay booked; no new appointment joins it. It can be opened again.',
    ),
    actions: [
      {
        label: __('Close it'),
        variant: 'solid',
        onClick: (closeDialog) => {
          closeDialog()
          act('close', 'crm.scheduling.cicli.close_cycle')
        },
      },
    ],
  })
}

function remove() {
  $dialog({
    title: __('Delete the cycle?'),
    message: __(
      'For a cycle sold by mistake: its booked appointments stay in the agenda, at the price list’s price.',
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
            await call('crm.scheduling.cicli.delete_cycle', {
              name: cycle.name,
            })
            toast.success(__('Cycle deleted'))
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
  const sold = !cycle.name
  try {
    fill(
      await call('crm.scheduling.cicli.save_cycle', {
        lead: props.lead,
        data: perIlServer(form),
        name: cycle.name || null,
      }),
    )
    toast.success(sold ? __('Cycle sold') : __('Cycle saved'))
    editing.value = false
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not save the cycle')
  } finally {
    busy.value = ''
  }
}

async function invoice() {
  busy.value = 'invoice'
  error.value = ''
  try {
    const name = await call('crm.invoicing.api.issue_from_cycle', {
      cycle: cycle.name,
    })
    fill(await call('crm.scheduling.cicli.get_cycle', { name: cycle.name }))
    window.open(`/app/crm-invoice/${name}`, '_blank')
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not open the invoice')
  } finally {
    busy.value = ''
  }
}

// on the calendar: a new appointment of the cycle's service, for the person
function book() {
  show.value = false
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: props.lead, service: cycle.service },
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
