<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
    <template #right-header>
      <TabButtons
        v-model="viewMode"
        :buttons="[
          { label: __('Calendar'), value: 'calendar' },
          { label: __('Agenda'), value: 'agenda' },
        ]"
      />
      <Tooltip
        :text="
          googleConnection.data?.connected
            ? __('Google Calendar connected — busy slots block bookings')
            : __(
                'Connect your Google Calendar to block busy slots on booking pages',
              )
        "
      >
        <Button
          :variant="googleConnection.data?.connected ? 'subtle' : 'outline'"
          :label="
            googleConnection.data?.connected
              ? __('Google connected')
              : __('Connect Google Calendar')
          "
          @click="connectGoogle"
        />
      </Tooltip>
      <ShortcutTooltip :label="__('Create Event')" combo="Mod+E">
        <Button
          :label="__('Event')"
          :disabled="isCreateDisabled"
          @click="newEvent"
        >
          <template #prefix
            ><span class="lucide-plus h-4" aria-hidden="true"
          /></template>
        </Button>
      </ShortcutTooltip>
      <Button
        variant="solid"
        :label="__('Appointment')"
        @click="newAppointment()"
      >
        <template #prefix
          ><span class="lucide-plus h-4" aria-hidden="true"
        /></template>
      </Button>
    </template>
  </LayoutHeader>

  <!-- filters -->
  <div
    class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2 px-5 py-2"
  >
    <MultiSelectFilter
      v-model="filters.services"
      :label="__('Services')"
      icon="lucide-sparkles"
      :options="serviceFilterOptions"
      :emptyText="__('No services configured yet')"
      @update:modelValue="reloadScheduler"
    />
    <MultiSelectFilter
      v-model="filters.staff"
      :label="__('Professionals')"
      icon="lucide-users"
      :options="staffFilterOptions"
      @update:modelValue="reloadScheduler"
    />
    <MultiSelectFilter
      v-model="filters.resources"
      :label="__('Rooms & equipment')"
      icon="lucide-door-open"
      :options="resourceFilterOptions"
      :emptyText="__('No rooms or equipment yet')"
      @update:modelValue="reloadScheduler"
    />
    <MultiSelectFilter
      v-model="filters.statuses"
      :label="__('Status')"
      icon="lucide-circle-dot"
      :options="statusFilterOptions"
      @update:modelValue="reloadScheduler"
    />
    <span class="grow" />
    <span v-if="appointmentCount" class="text-p-sm text-ink-gray-5">
      {{ appointmentCount }} {{ __('appointments') }}
    </span>
    <Button
      v-if="hasFilters"
      variant="ghost"
      :label="__('Reset')"
      @click="resetFilters"
    />
  </div>

  <!-- agenda: one column per professional or per room -->
  <div
    v-if="viewMode === 'agenda'"
    class="flex h-full flex-col overflow-hidden"
  >
    <div class="flex flex-wrap items-center gap-2 px-5 py-2.5">
      <Button
        variant="ghost"
        icon="lucide-chevron-left"
        @click="shiftDay(-1)"
      />
      <Button
        :label="__('Today')"
        variant="ghost"
        @click="agendaDate = today()"
      />
      <Button
        variant="ghost"
        icon="lucide-chevron-right"
        @click="shiftDay(1)"
      />
      <DatePicker
        :modelValue="agendaDate"
        :clearable="false"
        @update:modelValue="(value) => setAgendaDate(value)"
      >
        <template #target="{ togglePopover }">
          <Button
            variant="ghost"
            class="text-base-medium text-ink-gray-7"
            :label="agendaLabel"
            iconRight="chevron-down"
            @click="togglePopover"
          />
        </template>
      </DatePicker>
      <span class="grow" />
      <TabButtons
        v-model="columnMode"
        :buttons="[
          { label: __('By professional'), value: 'staff' },
          { label: __('By room'), value: 'resource' },
        ]"
      />
      <FormControl
        v-model="zoom"
        type="select"
        class="w-28"
        :options="[
          { label: __('Compact'), value: 0.7 },
          { label: __('Normal'), value: 1.1 },
          { label: __('Detailed'), value: 1.8 },
        ]"
      />
    </div>
    <ResourceScheduler
      class="flex-1"
      :mode="columnMode"
      :date="agendaDate"
      :appointments="appointments"
      :columnDefs="schedulerColumns"
      :serviceColors="serviceColors"
      :selected="selectedAppointment"
      :pxPerMinute="Number(zoom)"
      @select="selectedAppointment = $event"
      @edit="(name) => openAppointment(name)"
      @create="onGridCreate"
      @move="onGridMove"
    />
  </div>

  <!-- calendar: month / week / day, appointments and events together -->
  <div v-else class="flex h-screen overflow-hidden">
    <Calendar
      ref="calendar"
      class="flex-1 overflow-hidden"
      :config="{
        defaultMode: defaultMode,
        isEditMode: true,
        eventIcons: {},
        allowCustomClickEvents: true,
        enableShortcuts: false,
        noBorder: true,
      }"
      :events="calendarItems"
      :onClick="showDetails"
      :onDblClick="editDetails"
      :onCellClick="newEvent"
      @create="(event) => createEvent(event)"
      @update="(event) => updateEvent(event, true)"
      @delete="(eventID) => deleteEvent(eventID)"
      @rangeChange="handleRangeChange"
    >
      <template
        #header="{
          currentMonthYear,
          activeView,
          selectedMonthDate,
          decrement,
          increment,
          updateActiveView,
          onMonthYearChange,
          setCalendarDate,
        }"
      >
        <div class="my-4 mx-5 flex justify-between">
          <!-- left side  -->
          <!-- Month Year -->
          <div class="flex items-center">
            <DatePicker
              :modelValue="selectedMonthDate"
              :clearable="false"
              @update:modelValue="(val) => onMonthYearChange(val)"
            >
              <template #target="{ togglePopover }">
                <Button
                  variant="ghost"
                  class="text-lg-medium text-ink-gray-7"
                  :label="currentMonthYear"
                  iconRight="chevron-down"
                  @click="togglePopover"
                />
              </template>
            </DatePicker>
          </div>
          <!-- right side -->
          <!-- actions buttons for calendar -->
          <div class="flex gap-x-1">
            <!-- Increment and Decrement Button -->

            <Button
              variant="ghost"
              icon="lucide-chevron-left"
              @click="decrement"
            />
            <Button
              :label="__('Today')"
              variant="ghost"
              @click="setCalendarDate()"
            />
            <Button
              variant="ghost"
              icon="lucide-chevron-right"
              @click="increment"
            />

            <!-- View Buttons -->
            <FormControl
              type="select"
              class="mr-1 w-24"
              :modelValue="activeView"
              :options="[
                { label: __('Day'), value: 'Day' },
                { label: __('Week'), value: 'Week' },
                { label: __('Month'), value: 'Month' },
              ]"
              :placeholder="__('Operator')"
              @update:modelValue="updateActiveView($event)"
            />

            <Link
              class="form-control"
              :value="getUser(currentUser).full_name"
              doctype="User"
              :placeholder="__('John Doe')"
              :filters="{
                name: ['in', users.data.crmUsers?.map((user) => user.name)],
                ignore_user_type: 1,
              }"
              :hideMe="true"
              @change="(option) => updateUser(option)"
            >
              <template #prefix>
                <UserAvatar class="mr-2 !h-4 !w-4" :user="currentUser" />
              </template>
              <template #item-prefix="{ option }">
                <UserAvatar class="mr-2" :user="option.value" size="sm" />
              </template>
              <template #item-label="{ option }">
                <Tooltip :text="option.value">
                  <div class="cursor-pointer text-ink-gray-9">
                    {{ getUser(option.value).full_name }}
                  </div>
                </Tooltip>
              </template>
            </Link>
          </div>
        </div>
      </template>
    </Calendar>

    <!-- Event Panel Container -->
    <div
      class="overflow-hidden flex-none transition-all duration-300 ease-in-out flex flex-col"
      :class="
        showEventPanel ? 'w-[352px] border-l bg-surface-base' : 'w-0 border-l-0'
      "
    >
      <CalendarEventPanel
        v-if="showEventPanel"
        ref="eventPanel"
        v-model="showEventPanel"
        v-model:event="event"
        :mode="mode"
        @new="newEvent"
        @save="saveEvent"
        @edit="editDetails"
        @delete="deleteEvent"
        @duplicate="duplicateEvent"
        @details="showDetails"
        @close="close"
        @sync="syncEvent"
      />
    </div>
  </div>

  <AppointmentDialog
    v-model="showAppointmentDialog"
    :seed="appointmentSeed"
    :meta="meta.data || {}"
    @saved="onAppointmentSaved"
    @deleted="onAppointmentSaved"
  />
</template>
<script setup>
import AppointmentDialog from '@/components/Calendar/AppointmentDialog.vue'
import CalendarEventPanel from '@/components/Calendar/CalendarEventPanel.vue'
import MultiSelectFilter from '@/components/Calendar/MultiSelectFilter.vue'
import ResourceScheduler from '@/components/Calendar/ResourceScheduler.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ShortcutTooltip from '@/components/ShortcutTooltip.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { getSettings } from '@/stores/settings'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { appointmentColor, formatMinutes } from '@/utils/scheduler'
import {
  Calendar,
  createListResource,
  createResource,
  dayjs,
  DatePicker,
  TabButtons,
  Tooltip,
  CalendarActiveEvent as activeEvent,
  call,
  toast,
} from 'frappe-ui'
import {
  onMounted,
  ref,
  reactive,
  computed,
  provide,
  nextTick,
  watch,
} from 'vue'
import { useRoute } from 'vue-router'

const { user } = sessionStore()
const { $dialog } = globalStore()

const googleConnection = createResource({
  url: 'crm.api.booking.google_calendar_connection',
  cache: 'google-calendar-connection',
  auto: true,
})

function connectGoogle() {
  if (googleConnection.data?.connected) {
    toast.success(__('Google Calendar is already connected'))
    return
  }
  createResource({
    url: 'crm.api.booking.setup_google_calendar',
    auto: true,
    onSuccess: (data) => {
      window.location.href = data.authorize_url
    },
    onError: (e) => {
      toast.error(e.messages?.[0] || __('Failed to start Google authorization'))
    },
  })
}
const { settings } = getSettings()
const { users, getUser } = usersStore()
const route = useRoute()

const modeMap = {
  Daily: 'Day',
  Weekly: 'Week',
  Monthly: 'Month',
}

const defaultMode = computed(() => {
  return modeMap[settings.value?.default_calendar_view] || 'Week'
})

const calendar = ref(null)
const activeRangeKey = ref('')
const currentUser = ref(user)

// ---------------------------------------------------------------------------
// appointments (services, professionals, rooms, equipment)
// ---------------------------------------------------------------------------

const APPOINTMENT_PREFIX = 'appt:'
const isAppointmentId = (id) => String(id || '').startsWith(APPOINTMENT_PREFIX)
const appointmentName = (id) => String(id).slice(APPOINTMENT_PREFIX.length)

const viewMode = ref('calendar')
const columnMode = ref('staff')
const zoom = ref(1.1)
const agendaDate = ref(today())
const selectedAppointment = ref('')
const showAppointmentDialog = ref(false)
const appointmentSeed = ref({})

const filters = reactive({
  services: [],
  staff: [],
  resources: [],
  statuses: [],
})

const meta = createResource({
  url: 'crm.api.appointments.get_scheduler_meta',
  cache: 'crm-scheduler-meta',
  auto: true,
})

const scheduler = createResource({
  url: 'crm.api.appointments.get_calendar',
  auto: false,
})

const appointments = computed(() => scheduler.data?.appointments || [])
const appointmentCount = computed(() => appointments.value.length)

const serviceColors = computed(() =>
  Object.fromEntries(
    (meta.data?.services || []).map((service) => [service.name, service.color]),
  ),
)

const serviceFilterOptions = computed(() =>
  (meta.data?.services || []).map((service) => ({
    label: service.service_name,
    value: service.name,
    color: service.color,
  })),
)
const staffFilterOptions = computed(() =>
  (meta.data?.staff || []).map((person) => ({
    label: person.full_name || person.name,
    value: person.name,
  })),
)
const resourceFilterOptions = computed(() =>
  (meta.data?.resources || []).map((resource) => ({
    label: `${resource.resource_name} · ${__(resource.resource_type)}`,
    value: resource.name,
    color: resource.color,
  })),
)
const statusFilterOptions = computed(() =>
  (meta.data?.statuses || []).map((status) => ({
    label: __(status),
    value: status,
  })),
)

const hasFilters = computed(() =>
  Object.values(filters).some((value) => value.length),
)

function resetFilters() {
  filters.services = []
  filters.staff = []
  filters.resources = []
  filters.statuses = []
  reloadScheduler()
}

/** Columns of the agenda grid: professionals, or rooms and equipment. */
const schedulerColumns = computed(() => {
  if (columnMode.value === 'resource') {
    const wanted = filters.resources
    return (meta.data?.resources || [])
      .filter((resource) => !wanted.length || wanted.includes(resource.name))
      .map((resource) => ({
        key: resource.name,
        label: resource.resource_name,
        caption: [
          __(resource.resource_type),
          resource.capacity > 1
            ? __('{0} at a time').replace('{0}', resource.capacity)
            : '',
          resource.seats ? __('{0} seats').replace('{0}', resource.seats) : '',
        ]
          .filter(Boolean)
          .join(' · '),
        color: resource.color,
        closed: [],
      }))
  }
  const wanted = filters.staff
  return (meta.data?.staff || [])
    .filter((person) => !wanted.length || wanted.includes(person.name))
    .map((person) => ({
      key: person.name,
      label: person.full_name || person.name,
      caption: person.name,
      closed: [],
    }))
})

const agendaLabel = computed(() =>
  dayjs(agendaDate.value).format('dddd D MMMM YYYY'),
)

function today() {
  return dayjs().format('YYYY-MM-DD')
}

function shiftDay(days) {
  agendaDate.value = dayjs(agendaDate.value)
    .add(days, 'day')
    .format('YYYY-MM-DD')
}

function setAgendaDate(value) {
  if (value) agendaDate.value = dayjs(value).format('YYYY-MM-DD')
}

/** Window the appointment feed should cover for the current view. */
function schedulerRange() {
  if (viewMode.value === 'agenda') {
    return { start: agendaDate.value, end: agendaDate.value }
  }
  const range = lastRange.value
  if (range?.startDate && range?.endDate) {
    return {
      start: dayjs(range.startDate).format('YYYY-MM-DD'),
      end: dayjs(range.endDate).format('YYYY-MM-DD'),
    }
  }
  return {
    start: dayjs().startOf('month').format('YYYY-MM-DD'),
    end: dayjs().endOf('month').format('YYYY-MM-DD'),
  }
}

function reloadScheduler() {
  const range = schedulerRange()
  scheduler.submit({
    start: range.start,
    end: range.end,
    services: filters.services,
    staff: filters.staff,
    resources: filters.resources,
    statuses: filters.statuses,
    include_events: false,
  })
}

/** Appointments rendered as calendar events, alongside the plain ones. */
const appointmentItems = computed(() =>
  appointments.value.map((appointment) => ({
    id: `${APPOINTMENT_PREFIX}${appointment.name}`,
    title: appointment.title || appointment.service,
    description: appointment.notes || '',
    status: appointment.status,
    fromDate: dayjs(appointment.starts_on).format('YYYY-MM-DD'),
    toDate: dayjs(appointment.ends_on).format('YYYY-MM-DD'),
    fromTime: dayjs(appointment.starts_on).format('HH:mm'),
    toTime: dayjs(appointment.ends_on).format('HH:mm'),
    isFullDay: false,
    location: appointment.location,
    color: appointmentColor(appointment, serviceColors.value),
    attending: 'Yes',
  })),
)

const calendarItems = computed(() => [
  ...(Array.isArray(events.data) ? events.data : []),
  ...appointmentItems.value,
])

function newAppointment(seed = {}) {
  appointmentSeed.value = { ...seed }
  showAppointmentDialog.value = true
}

function openAppointment(name) {
  appointmentSeed.value = { name }
  showAppointmentDialog.value = true
}

function onGridCreate({ date, minutes, mode, key }) {
  newAppointment({
    date,
    time: formatMinutes(minutes),
    staff: mode === 'staff' ? key : undefined,
    resource: mode === 'resource' ? key : undefined,
  })
}

function onGridMove({ name, startsOn, endsOn, mode, from, to }) {
  const target = appointments.value.find((a) => a.name === name)
  if (!target) return
  const sameColumn = from === to
  const reassign =
    !sameColumn && mode === 'staff'
      ? (target.staff || []).map((row) =>
          row.user === from ? { ...row, user: to } : row,
        )
      : !sameColumn && mode === 'resource'
        ? (target.resources || []).map((row) =>
            row.resource === from ? { ...row, resource: to } : row,
          )
        : null

  if (!reassign) {
    createResource({
      url: 'crm.api.appointments.move_appointment',
      params: {
        name,
        starts_on: startsOn.toISOString(),
        ends_on: endsOn.toISOString(),
      },
      auto: true,
      onSuccess: () => {
        toast.success(__('Appointment moved'))
        reloadScheduler()
      },
      onError: (e) => toast.error(e.messages?.[0] || __('Could not move it')),
    })
    return
  }

  // dropped on a different column: move it *and* swap the professional or room
  createResource({
    url: 'crm.api.appointments.save_appointment',
    params: {
      name,
      appointment: {
        service: target.service,
        status: target.status,
        starts_on: startsOn.toISOString(),
        ends_on: endsOn.toISOString(),
        staff: mode === 'staff' ? reassign : target.staff,
        resources: mode === 'resource' ? reassign : target.resources,
        participants: target.participants,
        location: target.location,
        notes: target.notes,
      },
    },
    auto: true,
    onSuccess: () => {
      toast.success(__('Appointment reassigned'))
      reloadScheduler()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Could not reassign it')),
  })
}

function onAppointmentSaved() {
  reloadScheduler()
}

watch([viewMode, agendaDate], reloadScheduler)

// ---------------------------------------------------------------------------
// events (the classic calendar)
// ---------------------------------------------------------------------------

async function updateUser(u) {
  currentUser.value = u
  events.update({
    orFilters: buildEventOrFilters(),
  })
  await events.reload()
}

function buildEventFilters(range) {
  const filters = [['status', '=', 'Open']]
  if (range?.startDate && range?.endDate) {
    const start = dayjs(range.startDate)
      .startOf('day')
      .format('YYYY-MM-DD HH:mm:ss')
    const end = dayjs(range.endDate).endOf('day').format('YYYY-MM-DD HH:mm:ss')
    filters.push(['starts_on', '<=', end])
    filters.push(['ends_on', '>=', start])
  }
  return filters
}

function buildEventOrFilters() {
  return [
    ['owner', '=', currentUser.value],
    ['Event Participants', 'email', '=', currentUser.value],
  ]
}

const events = createListResource({
  doctype: 'Event',
  fields: [
    'name',
    'status',
    'subject',
    'description',
    'location',
    'starts_on',
    'ends_on',
    'all_day',
    'event_type',
    'color',
    'attending',
    'reference_doctype',
    'reference_docname',
  ],
  filters: buildEventFilters(),
  orFilters: buildEventOrFilters(),
  pageLength: 9999,
  auto: true,
  transform: (data) =>
    data
      // appointments are mirrored into Event for Google sync; showing both would
      // draw every appointment twice
      .filter((ev) => ev.reference_doctype !== 'CRM Appointment')
      .map((ev) => ({
        id: ev.name,
        title: ev.subject,
        description: ev.description,
        status: ev.status,
        fromDate: dayjs(ev.starts_on).format('YYYY-MM-DD'),
        toDate: dayjs(ev.ends_on).format('YYYY-MM-DD'),
        fromTime: dayjs(ev.starts_on).format('HH:mm'),
        toTime: dayjs(ev.ends_on).format('HH:mm'),
        isFullDay: ev.all_day,
        eventType: ev.event_type,
        location: ev.location,
        color: ev.color,
        attending: ev.attending,
        referenceDoctype: ev.reference_doctype,
        referenceDocname: ev.reference_docname,
      }))
      .filter(
        (ev, index, self) => index === self.findIndex((e) => e.id === ev.id),
      ),
})

provide('events', events)

const eventPanel = ref(null)
const showEventPanel = ref(false)
const event = ref({})
const mode = ref('')
const lastRange = ref(null)

const isCreateDisabled = computed(() =>
  ['edit', 'new', 'duplicate'].includes(mode.value),
)

// Temp event helpers
const TEMP_EVENT_IDS = new Set(['new-event', 'duplicate-event'])
const isTempEvent = (id) => TEMP_EVENT_IDS.has(id)
function removeTempEvents() {
  if (!Array.isArray(events.data)) return
  events.data = events.data.filter((ev) => !isTempEvent(ev.id))
}

function openEvent(e, nextMode, reloadEvent = false) {
  const _e = e?.calendarEvent || e
  if (!_e?.id || isTempEvent(_e.id)) return
  removeTempEvents()
  showEventPanel.value = true
  event.value = { id: _e.id, reloadEvent }
  activeEvent.value = _e.id
  mode.value = nextMode
}

function saveEvent(_event) {
  if (!_event?.id || isTempEvent(_event.id)) return createEvent(_event)
  updateEvent(_event)
}

function buildEventPayload(_event) {
  return {
    subject: _event.title,
    description: _event.description,
    starts_on: `${_event.fromDate} ${_event.fromTime}`,
    ends_on: `${_event.toDate} ${_event.toTime}`,
    all_day: _event.isFullDay || false,
    event_type: _event.eventType,
    location: _event.location,
    color: _event.color,
    attending: _event.attending,
    reference_doctype: _event.referenceDoctype,
    reference_docname: _event.referenceDocname,
    event_participants: _event.event_participants,
    notifications: _event.notifications,
  }
}

function createEvent(_event) {
  if (!_event?.title) return
  events.insert.submit(buildEventPayload(_event), {
    onSuccess: async (e) => {
      await updateUser(user)
      toast.success(__('Event created successfully'))
      showDetails({ id: e.name })
    },
    onError: (err) => {
      toast.error(err.messages[0])
      console.error('Failed creating event', err)
    },
  })
}

async function updateEvent(_event, afterDrag = false) {
  if (!_event.id) return

  // an appointment dragged on the classic calendar reschedules through the
  // scheduling engine, so conflicts and buffers still apply
  if (isAppointmentId(_event.id)) {
    const start = dayjs(
      `${_event.fromDate} ${_event.fromTime}`,
      'YYYY-MM-DD HH:mm',
    )
    const end = dayjs(`${_event.toDate} ${_event.toTime}`, 'YYYY-MM-DD HH:mm')
    createResource({
      url: 'crm.api.appointments.move_appointment',
      params: {
        name: appointmentName(_event.id),
        starts_on: start.toDate().toISOString(),
        ends_on: end.toDate().toISOString(),
      },
      auto: true,
      onSuccess: () => {
        toast.success(__('Appointment moved'))
        reloadScheduler()
      },
      onError: (e) => {
        toast.error(e.messages?.[0] || __('Could not move it'))
        reloadScheduler()
      },
    })
    return
  }

  _event.fromTime = dayjs(_event.fromTime, 'HH:mm').format('HH:mm')
  _event.toTime = dayjs(_event.toTime, 'HH:mm').format('HH:mm')

  if (
    ['duplicate', 'new'].includes(mode.value) &&
    !['duplicate-event', 'new-event'].includes(_event.id) &&
    afterDrag
  ) {
    event.value = { id: _event.id }
    activeEvent.value = _event.id
    mode.value = 'details'
  }

  if (mode.value == 'edit' && afterDrag) {
    eventPanel.value.updateEvent({
      fromDate: _event.fromDate,
      toDate: _event.toDate,
      fromTime: _event.fromTime,
      toTime: _event.toTime,
    })
    return
  }

  if (!mode.value || mode.value == 'edit' || mode.value === 'details') {
    // Ensure Contacts exist for participants referencing a new/unknown Contact, if not create them
    if (
      Array.isArray(_event.event_participants) &&
      _event.event_participants.length
    ) {
      _event.event_participants = await ensureParticipantContacts(
        _event.event_participants,
      )
    }

    events.setValue.submit(
      { name: _event.id, ...buildEventPayload(_event) },
      {
        onSuccess: async (e) => {
          await events.reload()
          if (showEventPanel.value) showDetails({ id: e.name }, true)
        },
        onError: (err) => {
          toast.error(err.messages[0])
          console.error('Failed updating event', err)
        },
      },
    )
  } else {
    event.value = { ..._event }
  }
}

function deleteEvent(eventID) {
  if (!eventID) return

  if (isAppointmentId(eventID)) {
    openAppointment(appointmentName(eventID))
    return
  }

  $dialog({
    title: __('Delete'),
    message: __('Are you sure you want to delete this event?'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          events.delete.submit(eventID, {
            onSuccess: () => {
              toast.success(__('Event deleted successfully'))
              events.reload()
            },
            onError: (err) => {
              toast.error(err.messages[0])
              console.error('Failed deleting event', err)
            },
          })
          showEventPanel.value = false
          event.value = {}
          activeEvent.value = ''
          mode.value = ''
          close()
        },
      },
    ],
  })
}

function syncEvent(eventID, _event) {
  if (!eventID || !Array.isArray(events.data)) return
  const target = events.data.find((event) => event.id === eventID)
  if (!target) return
  Object.assign(target, _event)
}

async function handleRangeChange(range) {
  if (!range?.startDate || !range?.endDate) return
  lastRange.value = range
  const key = `${range.view}-${range.startDate}-${range.endDate}`
  if (key === activeRangeKey.value) {
    if (events.list?.loading || events.list?.fetched) return
  }
  activeRangeKey.value = key
  events.update({
    filters: buildEventFilters(range),
    orFilters: buildEventOrFilters(),
  })
  await events.reload()
  reloadScheduler()
}

onMounted(async () => {
  activeEvent.value = ''
  mode.value = ''
  showEventPanel.value = false
  reloadScheduler()

  const { eventId, date, appointment } = route.query
  if (appointment) {
    openAppointment(appointment)
  }
  if (eventId && date) {
    await events.promise
    await nextTick()

    // Set calendar date to the event's date
    if (calendar.value.onMonthYearChange) {
      calendar.value.onMonthYearChange(dayjs(date).toDate())
    }

    showDetails({ id: eventId })
  }
})

// Global shortcut: Cmd/Ctrl + E -> new event (when not already creating/editing)
useKeyboardShortcuts({
  shortcuts: [
    {
      match: (e) =>
        (e.metaKey || e.ctrlKey) &&
        !e.shiftKey &&
        !e.altKey &&
        e.key.toLowerCase() === 'e',
      guard: () => !isCreateDisabled.value,
      action: () =>
        newEvent({
          date: dayjs().format('YYYY-MM-DD'),
          time: dayjs().format('HH:mm'),
          isFullDay: false,
        }),
    },
  ],
})

function showDetails(e, reloadEvent = false) {
  const id = (e?.calendarEvent || e)?.id
  if (isAppointmentId(id)) {
    selectedAppointment.value = appointmentName(id)
    openAppointment(appointmentName(id))
    return
  }
  openEvent(e, 'details', reloadEvent)
}

function editDetails(e) {
  const id = (e?.calendarEvent || e)?.id
  if (isAppointmentId(id)) {
    openAppointment(appointmentName(id))
    return
  }
  openEvent(e, 'edit')
}

function buildTempEvent(e = {}, duplicate = false) {
  const id = duplicate ? 'duplicate-event' : 'new-event'

  return {
    id,
    title: e.title,
    description: e.description || '',
    date: e.fromDate,
    fromDate: e.fromDate,
    toDate: e.toDate,
    fromTime: e.fromTime,
    toTime: e.toTime,
    location: e.location || '',
    isFullDay: e.isFullDay || false,
    eventType: e.eventType || 'Private',
    color: e.color || 'green',
    attending: e.attending || 'Yes',
    event_participants: e.event_participants || [],
    notifications: e.notifications || [],
  }
}

function newEvent(e = {}, duplicate = false) {
  removeTempEvents()

  let base = { ...e }
  if (!duplicate) {
    const [fromTime, toTime] = getFromToTime(e.time)
    const fromDate = dayjs(e.date).format('YYYY-MM-DD')
    base = {
      ...base,
      fromDate,
      toDate: fromDate,
      fromTime,
      toTime,
      isFullDay: e.isFullDay,
    }
  }

  event.value = buildTempEvent(base, duplicate)
  if (!Array.isArray(events.data)) {
    events.data = []
  }
  events.data.push(event.value)
  showEventPanel.value = true
  activeEvent.value = event.value.id
  mode.value = duplicate ? 'duplicate' : 'new'
}

function duplicateEvent(e) {
  newEvent(e, true)
}

function close() {
  showEventPanel.value = false
  event.value = {}
  activeEvent.value = ''
  mode.value = ''

  removeTempEvents()
}

// utils
function getFromToTime(time) {
  const pad = (v) => String(v).padStart(2, '0')
  let now = dayjs()
  let h = now.hour()
  let m = Math.floor(now.minute() / 15) * 15
  let fromHour = h
  let fromMinute = m
  if (time) {
    if (/am|pm/i.test(time)) {
      const raw = time.trim().replace(' ', '')
      const ampm = raw.slice(-2).toLowerCase()
      let hour = parseInt(raw.slice(0, -2))
      if (ampm === 'pm' && hour < 12) hour += 12
      if (ampm === 'am' && hour === 12) hour = 0
      fromHour = hour
      fromMinute = 0
    } else if (/^\d{1,2}:?\d{0,2}$/.test(time)) {
      const [hh, mm = '00'] = time.split(':')
      fromHour = parseInt(hh)
      fromMinute = parseInt(mm) || 0
    }
  }
  const toHour = (fromHour + 1) % 24
  return [
    `${pad(fromHour)}:${pad(fromMinute)}`,
    `${pad(toHour)}:${pad(fromMinute)}`,
  ]
}

async function ensureParticipantContacts(participants) {
  if (!Array.isArray(participants) || !participants.length) return participants
  const updated = []
  for (const part of participants) {
    const p = { ...part }
    try {
      if (
        p.reference_doctype === 'Contact' &&
        (!p.reference_docname || p.reference_docname === 'new') &&
        p.email
      ) {
        const firstName = p.email.split('@')[0] || p.email
        const contactDoc = await call('frappe.client.insert', {
          doc: {
            doctype: 'Contact',
            first_name: firstName,
            email_ids: [{ email_id: p.email, is_primary: 1 }],
          },
        })
        if (contactDoc?.name) p.reference_docname = contactDoc.name
      }
    } catch (e) {
      console.error('Failed creating contact for participant', p.email, e)
    }
    updated.push(p)
  }
  return updated
}
</script>
