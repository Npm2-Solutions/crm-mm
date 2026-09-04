<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <div class="flex flex-col bg-surface-modal">
        <!-- header -->
        <div
          class="flex items-start justify-between gap-3 border-b border-outline-gray-2 px-5 py-4"
        >
          <div class="min-w-0">
            <h3 class="truncate text-lg-semibold text-ink-gray-9">
              {{ form.name ? __('Appointment') : __('New appointment') }}
              <span v-if="form.name" class="text-ink-gray-5"
                >· {{ form.name }}</span
              >
            </h3>
            <p class="mt-0.5 text-p-sm text-ink-gray-5">
              {{ serviceSummary }}
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <FormControl
              v-model="form.status"
              type="select"
              class="w-36"
              :options="statusOptions"
            />
            <Button variant="ghost" icon="x" @click="show = false" />
          </div>
        </div>

        <div
          class="grid max-h-[70vh] grid-cols-1 gap-5 overflow-y-auto p-5 lg:grid-cols-2"
        >
          <!-- left column: what & when -->
          <div class="flex flex-col gap-4">
            <section class="flex flex-col gap-3">
              <FormControl
                v-model="form.service"
                type="select"
                :label="__('Service')"
                :options="serviceOptions"
                @update:modelValue="onServiceChange"
              />
              <div class="grid grid-cols-3 gap-2">
                <FormControl
                  v-model="form.date"
                  type="date"
                  :label="__('Date')"
                />
                <FormControl
                  v-model="form.time"
                  type="time"
                  :label="__('Start')"
                />
                <FormControl
                  v-model.number="form.duration"
                  type="number"
                  :label="__('Minutes')"
                  min="5"
                />
              </div>
              <div class="flex items-center gap-2">
                <Button
                  :label="__('Find free slots')"
                  iconLeft="search"
                  :loading="slots.loading"
                  @click="findSlots"
                />
                <span v-if="slotHint" class="text-p-xs text-ink-gray-5">{{
                  slotHint
                }}</span>
              </div>
              <div v-if="slotList.length" class="flex flex-wrap gap-1.5">
                <Button
                  v-for="slot in slotList"
                  :key="slot.start + (slot.join_appointment || '')"
                  size="sm"
                  variant="outline"
                  :label="slotLabel(slot)"
                  @click="applySlot(slot)"
                />
              </div>
            </section>

            <!-- professionals -->
            <section class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <FormLabel :label="__('Professionals')" />
                <Button
                  size="sm"
                  variant="ghost"
                  :label="__('Auto-assign')"
                  @click="autoAssign"
                />
              </div>
              <p v-if="staffHint" class="text-p-xs text-ink-gray-5">
                {{ staffHint }}
              </p>
              <div v-if="eligibleStaff.length" class="flex flex-wrap gap-1.5">
                <Button
                  v-for="person in eligibleStaff"
                  :key="person.user"
                  size="sm"
                  :variant="isAssigned(person.user) ? 'solid' : 'outline'"
                  :label="staffLabel(person)"
                  @click="toggleStaff(person)"
                />
              </div>
              <p v-else class="text-p-sm text-ink-gray-5">
                {{ __('Pick a service to see who can deliver it.') }}
              </p>
            </section>

            <!-- rooms & equipment -->
            <section class="flex flex-col gap-2">
              <FormLabel :label="__('Rooms & equipment')" />
              <div
                v-for="(row, i) in form.resources"
                :key="i"
                class="grid grid-cols-[1fr_72px_32px] items-end gap-2"
              >
                <FormControl
                  v-model="row.resource"
                  type="select"
                  :options="resourceOptions"
                />
                <FormControl
                  v-model.number="row.quantity"
                  type="number"
                  min="1"
                />
                <Button
                  variant="ghost"
                  icon="lucide-trash-2"
                  @click="form.resources.splice(i, 1)"
                />
              </div>
              <Button
                variant="ghost"
                size="sm"
                class="self-start"
                :label="__('Add resource')"
                iconLeft="plus"
                @click="form.resources.push({ resource: '', quantity: 1 })"
              />
            </section>
          </div>

          <!-- right column: who & how much -->
          <div class="flex flex-col gap-4">
            <!-- participants -->
            <section class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <FormLabel :label="__('Participants')" />
                <span class="text-p-xs text-ink-gray-5">
                  {{ form.participants.length }}/{{ maxParticipants }}
                </span>
              </div>
              <div
                v-for="(row, i) in form.participants"
                :key="i"
                class="rounded-md border border-outline-gray-2 p-2"
              >
                <div class="grid grid-cols-[110px_1fr_32px] items-end gap-2">
                  <FormControl
                    v-model="row.party_type"
                    type="select"
                    :options="partyTypeOptions"
                  />
                  <Link
                    :doctype="row.party_type"
                    :modelValue="row.party"
                    :placeholder="__('Search…')"
                    @update:modelValue="(v) => pickParty(row, v)"
                  />
                  <Button
                    variant="ghost"
                    icon="lucide-trash-2"
                    @click="form.participants.splice(i, 1)"
                  />
                </div>
                <div class="mt-2 grid grid-cols-2 gap-2">
                  <FormControl
                    v-model="row.participant_name"
                    type="text"
                    :placeholder="__('Name')"
                  />
                  <FormControl
                    v-model="row.email"
                    type="text"
                    :placeholder="__('Email')"
                  />
                </div>
                <div class="mt-2 grid grid-cols-2 gap-2">
                  <FormControl
                    v-model="row.status"
                    type="select"
                    :options="attendanceOptions"
                  />
                  <FormControl
                    v-model.number="row.amount"
                    type="number"
                    :placeholder="__('Amount')"
                  />
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                class="self-start"
                :label="__('Add participant')"
                iconLeft="plus"
                :disabled="form.participants.length >= maxParticipants"
                @click="addParticipant"
              />
            </section>

            <!-- price -->
            <section class="flex flex-col gap-2">
              <FormLabel :label="__('Price')" />
              <FormControl
                v-model="form.price_list"
                type="select"
                :options="priceListOptions"
                @update:modelValue="refreshPrice"
              />
              <div
                class="flex items-center justify-between rounded-md bg-surface-gray-2 px-3 py-2"
              >
                <div class="min-w-0">
                  <div class="text-p-base-medium text-ink-gray-8">
                    {{ priceLabel }}
                  </div>
                  <div class="truncate text-p-xs text-ink-gray-5">
                    {{ quote.data?.source || __('Not calculated yet') }}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  icon="refresh-cw"
                  :loading="quote.loading"
                  @click="refreshPrice"
                />
              </div>
            </section>

            <FormControl
              v-model="form.location"
              type="text"
              :label="__('Location / meeting link')"
            />
            <FormControl
              v-model="form.notes"
              type="textarea"
              :rows="2"
              :label="__('Notes')"
            />

            <!-- repeat -->
            <section v-if="form.name" class="flex flex-col gap-2">
              <FormLabel :label="__('Repeat')" />
              <div class="grid grid-cols-[1fr_80px_auto] items-end gap-2">
                <FormControl
                  v-model="repeat.rule"
                  type="select"
                  :options="repeatOptions"
                />
                <FormControl
                  v-model.number="repeat.occurrences"
                  type="number"
                  min="1"
                />
                <Button
                  :label="__('Create')"
                  :loading="repeating"
                  :disabled="!repeat.rule"
                  @click="createSeries"
                />
              </div>
            </section>
          </div>
        </div>

        <!-- conflicts -->
        <div
          v-if="conflicts.length"
          class="mx-5 mb-3 rounded-md border border-outline-red-2 bg-surface-red-1 px-3 py-2"
        >
          <div class="text-p-sm-medium text-ink-red-3">
            {{ __('Scheduling conflict') }}
          </div>
          <ul class="mt-1 list-inside list-disc text-p-xs text-ink-red-3">
            <li v-for="(conflict, i) in conflicts" :key="i">{{ conflict }}</li>
          </ul>
          <label
            v-if="canOverride"
            class="mt-2 flex items-center gap-2 text-p-xs text-ink-gray-7"
          >
            <Switch v-model="form.override_conflicts" size="sm" />
            {{ __('Book anyway and record the conflict') }}
          </label>
        </div>

        <!-- actions -->
        <div
          class="flex items-center justify-between gap-2 border-t border-outline-gray-2 px-5 py-3"
        >
          <Button
            v-if="form.name"
            variant="ghost"
            theme="red"
            :label="__('Delete')"
            @click="remove"
          />
          <span v-else />
          <div class="flex items-center gap-2">
            <Button :label="__('Cancel')" @click="show = false" />
            <Button
              variant="solid"
              :label="__('Save')"
              :loading="saving"
              @click="save"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import {
  Button,
  Dialog,
  FormControl,
  FormLabel,
  Switch,
  createResource,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  /** `{ name }` to edit, or `{ date, time, staff, resource, service }` to prefill */
  seed: { type: Object, default: () => ({}) },
  meta: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue', 'saved', 'deleted'])

const { getUser } = usersStore()

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const PARTY_TYPES = ['CRM Lead', 'Contact', 'CRM Deal']
const emptyForm = () => ({
  name: null,
  service: '',
  status: 'Scheduled',
  date: dayjs().format('YYYY-MM-DD'),
  time: '09:00',
  duration: 30,
  staff: [],
  participants: [],
  resources: [],
  price_list: '',
  location: '',
  notes: '',
  override_conflicts: false,
})

const form = reactive(emptyForm())
const saving = ref(false)
const repeating = ref(false)
const conflicts = ref([])
const slotList = ref([])
const slotHint = ref('')
const repeat = reactive({ rule: '', occurrences: 4 })

const services = computed(() => props.meta?.services || [])
const service = computed(() =>
  services.value.find((s) => s.name === form.service),
)
const canOverride = computed(() => Boolean(props.meta?.settings?.can_override))

const serviceOptions = computed(() =>
  services.value.map((s) => ({ label: s.service_name, value: s.name })),
)
const resourceOptions = computed(() => [
  { label: __('Choose…'), value: '' },
  ...(props.meta?.resources || []).map((r) => ({
    label: `${r.resource_name} (${__(r.resource_type)})`,
    value: r.name,
  })),
])
const priceListOptions = computed(() => [
  { label: __('Default'), value: '' },
  ...(props.meta?.price_lists || []).map((p) => ({
    label: p.price_list_name,
    value: p.name,
  })),
])
const statusOptions = computed(() =>
  (props.meta?.statuses || []).map((s) => ({ label: __(s), value: s })),
)
const partyTypeOptions = PARTY_TYPES.map((t) => ({ label: __(t), value: t }))
const attendanceOptions = ['Booked', 'Attended', 'No Show', 'Cancelled'].map(
  (s) => ({
    label: __(s),
    value: s,
  }),
)
const repeatOptions = [
  { label: __('No repeat'), value: '' },
  { label: __('Daily'), value: 'Daily' },
  { label: __('Weekly'), value: 'Weekly' },
  { label: __('Every 2 weeks'), value: 'Biweekly' },
  { label: __('Monthly'), value: 'Monthly' },
]

const eligibleStaff = computed(() => service.value?.staff || [])
const maxParticipants = computed(() => service.value?.max_participants || 1)

const serviceSummary = computed(() => {
  if (!service.value) return __('Pick a service to start')
  const parts = [`${service.value.duration} ${__('min')}`]
  if (service.value.staff_selection === 'All required') {
    parts.push(__('all professionals attend'))
  } else if (service.value.staff_selection === 'One per role') {
    parts.push(__('one professional per role'))
  } else if (service.value.staff_count > 1) {
    parts.push(
      __('{0} professionals').replace('{0}', service.value.staff_count),
    )
  }
  if (service.value.max_participants > 1) {
    parts.push(
      __('up to {0} participants').replace(
        '{0}',
        service.value.max_participants,
      ),
    )
  }
  return parts.join(' · ')
})

const staffHint = computed(() => {
  if (!service.value) return ''
  if (service.value.staff_selection === 'All required') {
    return __('This service books every listed professional together.')
  }
  if (service.value.staff_selection === 'One per role') {
    return __('One professional per role is needed.')
  }
  return ''
})

const startsOn = computed(() =>
  dayjs(`${form.date} ${form.time}`, 'YYYY-MM-DD HH:mm').toDate(),
)
const endsOn = computed(() =>
  dayjs(startsOn.value)
    .add(form.duration || 30, 'minute')
    .toDate(),
)

// --- resources -----------------------------------------------------------

const quote = createResource({ url: 'crm.api.appointments.quote_price' })
const slots = createResource({
  url: 'crm.api.appointments.get_available_slots',
})
const conflictCheck = createResource({
  url: 'crm.api.appointments.check_conflicts',
})

const priceLabel = computed(() => {
  const data = quote.data
  if (!data) return '—'
  const total = new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: data.currency || 'EUR',
  }).format(data.total || 0)
  return data.per_participant
    ? `${total} (${__('per participant')} × ${form.participants.length || 1})`
    : total
})

function payload() {
  return {
    service: form.service,
    status: form.status,
    starts_on: startsOn.value.toISOString(),
    ends_on: endsOn.value.toISOString(),
    staff: form.staff.map((user) => ({ user, required: 1 })),
    participants: form.participants.map((row) => ({ ...row })),
    resources: form.resources.filter((row) => row.resource),
    price_list: form.price_list || null,
    location: form.location,
    notes: form.notes,
    override_conflicts: form.override_conflicts ? 1 : 0,
  }
}

function refreshPrice() {
  if (!form.service) return
  quote.submit({
    service: form.service,
    when: startsOn.value.toISOString(),
    price_list: form.price_list || null,
    staff: form.staff,
    resources: form.resources.map((row) => row.resource).filter(Boolean),
    participants: form.participants.length || 1,
  })
}

function refreshConflicts() {
  if (!form.service || !form.staff.length) {
    conflicts.value = []
    return
  }
  conflictCheck.submit(
    { appointment: { ...payload(), name: form.name } },
    { onSuccess: (data) => (conflicts.value = data || []) },
  )
}

function findSlots() {
  if (!form.service) {
    toast.error(__('Pick a service first'))
    return
  }
  slotHint.value = ''
  slots.submit(
    {
      service: form.service,
      start_date: form.date,
      end_date: dayjs(form.date).add(6, 'day').format('YYYY-MM-DD'),
      staff: form.staff,
      resources: form.resources.map((row) => row.resource).filter(Boolean),
      participants: Math.max(form.participants.length, 1),
      exclude_appointment: form.name || null,
    },
    {
      onSuccess: (data) => {
        slotList.value = (data || []).slice(0, 24)
        slotHint.value = slotList.value.length
          ? __('{0} free slots in the next 7 days').replace('{0}', data.length)
          : __('No free slot in the next 7 days')
      },
      onError: (e) =>
        toast.error(e.messages?.[0] || __('Could not load slots')),
    },
  )
}

function slotLabel(slot) {
  const when = dayjs(slot.start).format('ddd D MMM HH:mm')
  return slot.join_appointment
    ? `${when} · ${__('join')} (${slot.seats_left})`
    : when
}

function applySlot(slot) {
  form.date = dayjs(slot.start).format('YYYY-MM-DD')
  form.time = dayjs(slot.start).format('HH:mm')
  form.duration = dayjs(slot.end).diff(dayjs(slot.start), 'minute')
  form.staff = [...(slot.staff || [])]
  if (slot.resources?.length) {
    form.resources = slot.resources.map((row) => ({ ...row }))
  }
  slotList.value = []
  refreshPrice()
  refreshConflicts()
}

// --- staff ---------------------------------------------------------------

function staffLabel(person) {
  const name = getUser(person.user)?.full_name || person.user
  return person.role ? `${name} · ${person.role}` : name
}

function isAssigned(user) {
  return form.staff.includes(user)
}

function toggleStaff(person) {
  const i = form.staff.indexOf(person.user)
  if (i === -1) form.staff.push(person.user)
  else form.staff.splice(i, 1)
  refreshConflicts()
  refreshPrice()
}

function autoAssign() {
  if (!form.service) return
  slots.submit(
    {
      service: form.service,
      start_date: form.date,
      end_date: form.date,
      participants: Math.max(form.participants.length, 1),
      exclude_appointment: form.name || null,
    },
    {
      onSuccess: (data) => {
        const wanted = dayjs(startsOn.value).toISOString()
        const match =
          (data || []).find((slot) => dayjs(slot.start).isSame(wanted)) ||
          (data || [])[0]
        if (!match) {
          toast.error(__('Nobody is free that day'))
          return
        }
        form.staff = [...(match.staff || [])]
        if (
          match.resources?.length &&
          !form.resources.some((r) => r.resource)
        ) {
          form.resources = match.resources.map((row) => ({ ...row }))
        }
        refreshConflicts()
        refreshPrice()
      },
    },
  )
}

// --- participants --------------------------------------------------------

function addParticipant() {
  form.participants.push({
    party_type: 'CRM Lead',
    party: '',
    participant_name: '',
    email: '',
    phone: '',
    status: 'Booked',
    amount: 0,
  })
}

const partyDetails = createResource({ url: 'frappe.client.get_value' })

function pickParty(row, value) {
  row.party = value
  if (!value) return
  const fieldsByType = {
    'CRM Lead': ['lead_name', 'email', 'mobile_no'],
    Contact: ['name', 'email_id', 'mobile_no'],
    'CRM Deal': ['organization', 'email', 'mobile_no'],
  }
  partyDetails.submit(
    {
      doctype: row.party_type,
      filters: { name: value },
      fieldname: fieldsByType[row.party_type],
    },
    {
      onSuccess: (data) => {
        if (!data) return
        row.participant_name =
          data.lead_name ||
          data.organization ||
          data.name ||
          row.participant_name ||
          value
        row.email = data.email || data.email_id || row.email
        row.phone = data.mobile_no || row.phone
        refreshPrice()
      },
      onError: () => {
        row.participant_name = row.participant_name || value
      },
    },
  )
}

// --- load / save ---------------------------------------------------------

const appointment = createResource({
  url: 'crm.api.appointments.get_appointment',
})

function loadInto(doc) {
  Object.assign(form, emptyForm(), {
    name: doc.name,
    service: doc.service,
    status: doc.status,
    date: dayjs(doc.starts_on).format('YYYY-MM-DD'),
    time: dayjs(doc.starts_on).format('HH:mm'),
    duration: dayjs(doc.ends_on).diff(dayjs(doc.starts_on), 'minute'),
    staff: (doc.staff || []).map((row) => row.user),
    participants: (doc.participants || []).map((row) => ({
      party_type: row.party_type || 'CRM Lead',
      party: row.party || '',
      participant_name: row.participant_name || '',
      email: row.email || '',
      phone: row.phone || '',
      status: row.status || 'Booked',
      amount: row.amount || 0,
    })),
    resources: (doc.resources || []).map((row) => ({
      resource: row.resource,
      quantity: row.quantity || 1,
    })),
    price_list: doc.price_list || '',
    location: doc.location || '',
    notes: doc.notes || '',
    override_conflicts: Boolean(doc.override_conflicts),
  })
  refreshPrice()
  refreshConflicts()
}

function seedForm() {
  conflicts.value = []
  slotList.value = []
  slotHint.value = ''
  repeat.rule = ''
  const seed = props.seed || {}
  if (seed.name) {
    appointment.submit({ name: seed.name }, { onSuccess: loadInto })
    return
  }
  Object.assign(form, emptyForm(), {
    date: seed.date || dayjs().format('YYYY-MM-DD'),
    time: seed.time || dayjs().format('HH:mm'),
    price_list: props.meta?.settings?.default_price_list || '',
  })
  const preferred = seed.service || services.value[0]?.name || ''
  if (preferred) onServiceChange(preferred)
  if (seed.staff) form.staff = [seed.staff]
  if (seed.resource) form.resources = [{ resource: seed.resource, quantity: 1 }]
  addParticipant()
  refreshPrice()
}

function onServiceChange(value) {
  form.service = value
  const picked = services.value.find((s) => s.name === value)
  if (!picked) return
  form.duration = picked.duration || 30
  // a collective service books everyone; a round-robin one waits for the pick
  form.staff =
    picked.staff_selection === 'All required'
      ? (picked.staff || []).map((row) => row.user)
      : form.staff.filter((user) =>
          (picked.staff || []).some((row) => row.user === user),
        )
  if (!form.resources.length && picked.resources?.length) {
    form.resources = picked.resources
      .filter((row) => row.resource)
      .map((row) => ({ resource: row.resource, quantity: row.quantity || 1 }))
  }
  refreshPrice()
  refreshConflicts()
}

function save() {
  if (!form.service) {
    toast.error(__('Pick a service'))
    return
  }
  if (!form.staff.length) {
    toast.error(__('Assign at least one professional'))
    return
  }
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_appointment',
    params: { appointment: payload(), name: form.name || null },
    auto: true,
    onSuccess: (doc) => {
      saving.value = false
      show.value = false
      toast.success(
        form.name ? __('Appointment updated') : __('Appointment created'),
      )
      emit('saved', doc)
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Could not save the appointment'))
      refreshConflicts()
    },
  })
}

function remove() {
  createResource({
    url: 'crm.api.appointments.delete_appointment',
    params: { name: form.name },
    auto: true,
    onSuccess: () => {
      show.value = false
      toast.success(__('Appointment deleted'))
      emit('deleted', form.name)
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Could not delete')),
  })
}

function createSeries() {
  repeating.value = true
  createResource({
    url: 'crm.api.appointments.create_series',
    params: {
      name: form.name,
      repeat: repeat.rule,
      occurrences: repeat.occurrences,
    },
    auto: true,
    onSuccess: (data) => {
      repeating.value = false
      const created = data.created?.length || 0
      const skipped = data.skipped?.length || 0
      toast.success(
        skipped
          ? __('{0} appointments created, {1} skipped for conflicts')
              .replace('{0}', created)
              .replace('{1}', skipped)
          : __('{0} appointments created').replace('{0}', created),
      )
      emit('saved', null)
    },
    onError: (e) => {
      repeating.value = false
      toast.error(e.messages?.[0] || __('Could not create the series'))
    },
  })
}

watch(
  () => [props.modelValue, props.seed],
  ([open]) => {
    if (open) seedForm()
  },
  { immediate: true },
)

watch(
  () => [form.date, form.time, form.duration],
  () => {
    refreshConflicts()
    refreshPrice()
  },
)
</script>
