<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Somebody on a waiting list. New or put right, it says the service, with whom,
  the days and parts of the day, until when, how the offers reach them. Read, it
  says what they wait for and how the offers went; the desk looks for a free
  place, offers it (the same message and link as the ones that leave by
  themselves) or books it straight away.
-->
<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ title }}
        </h3>
        <Badge
          v-if="!editing && entry.status"
          variant="subtle"
          :theme="STATO[entry.status]?.theme || 'gray'"
          :label="__(STATO[entry.status]?.label || entry.status)"
        />
        <Badge
          v-if="!editing && entry.urgent && aperta"
          variant="subtle"
          theme="red"
          :label="__('Urgent')"
        />
      </div>
    </template>
    <template #body-content>
      <div v-if="loading" class="py-10 text-center text-p-sm text-ink-gray-5">
        {{ __('Loading…') }}
      </div>

      <!-- putting somebody on the list, or putting the entry right -->
      <div v-else-if="editing" class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.service"
            type="select"
            :label="__('Service')"
            :placeholder="__('Choose a service')"
            :options="serviceOptions"
            :disabled="Boolean(entry.name)"
          />
          <FormControl
            v-model="form.staff"
            type="select"
            :label="__('With')"
            :options="staffOptions"
          />
        </div>
        <div v-if="isClass" class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.class_session"
            type="select"
            :label="__('A place in')"
            :options="classOptions"
            :disabled="Boolean(entry.name)"
          />
          <FormControl
            v-model="form.seats"
            type="number"
            inputmode="numeric"
            :label="__('Places')"
            :min="1"
            :max="MASSIMO_POSTI"
          />
        </div>
        <template v-if="!form.class_session">
          <div class="flex flex-col gap-1.5">
            <span class="text-xs text-ink-gray-5">{{ __('Days') }}</span>
            <div class="flex flex-wrap gap-1.5">
              <Button
                v-for="giorno in GIORNI"
                :key="giorno"
                size="sm"
                class="touch-target"
                :variant="form.weekdays.includes(giorno) ? 'solid' : 'subtle'"
                :aria-pressed="form.weekdays.includes(giorno)"
                :label="giornoBreve(giorno, locale)"
                @click="form.weekdays = scegli(form.weekdays, giorno, GIORNI)"
              />
            </div>
          </div>
          <div class="flex flex-col gap-1.5">
            <span class="text-xs text-ink-gray-5">
              {{ __('Parts of the day') }}
            </span>
            <div class="flex flex-wrap gap-1.5">
              <Button
                v-for="parte in PARTI"
                :key="parte"
                size="sm"
                class="touch-target"
                :variant="form.parts.includes(parte) ? 'solid' : 'subtle'"
                :aria-pressed="form.parts.includes(parte)"
                :label="__(NOMI_DELLE_PARTI[parte])"
                @click="form.parts = scegli(form.parts, parte, PARTI)"
              />
            </div>
            <p class="text-p-sm text-ink-gray-5">
              {{
                form.weekdays.length || form.parts.length
                  ? __('A place is offered only when it falls in these.')
                  : __('Nothing chosen: any time the centre is open.')
              }}
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
            <FormControl
              v-model="form.from_date"
              type="date"
              :label="__('Not before')"
            />
            <FormControl
              v-model="form.until"
              type="date"
              :label="__('Until')"
            />
          </div>
        </template>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.channel"
            type="select"
            :label="__('Offers by')"
            :options="channelOptions"
          />
          <div class="flex items-end pb-1.5">
            <FormControl
              v-model="form.urgent"
              type="checkbox"
              :label="__('Urgent: ahead of the others')"
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

      <!-- what they wait for, and what was offered -->
      <div v-else class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <p class="text-p-base text-ink-gray-8">{{ waitsFor }}</p>
          <p class="text-p-sm text-ink-gray-6">{{ facts }}</p>
        </div>
        <p
          v-if="entry.notes"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ entry.notes }}
        </p>

        <div
          v-if="entry.offer"
          class="flex flex-col gap-1 rounded-lg border border-outline-gray-2 px-3 py-2"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="min-w-0 text-p-base font-medium text-ink-gray-9">
              {{ placeLabel(entry.offer) }}
            </span>
            <Badge
              class="shrink-0"
              variant="subtle"
              :theme="entry.offer.channel ? 'blue' : 'red'"
              :label="
                comeStaLOfferta(entry.offer, t, (value) =>
                  formatDate(value, 'ddd D MMM, HH:mm'),
                )
              "
            />
          </div>
          <span class="text-p-sm text-ink-gray-6">
            {{ offerFacts(entry.offer) }}
          </span>
        </div>

        <div v-if="entry.booked_appointment" class="flex flex-wrap gap-2">
          <Button
            :label="__('Open the appointment')"
            icon-left="calendar"
            @click="openAppointment(entry)"
          />
        </div>

        <!-- the free places, when the desk looks -->
        <div v-if="places" class="flex flex-col gap-2">
          <h4 class="text-base font-semibold text-ink-gray-8">
            {{ __('Free places') }}
          </h4>
          <ol
            v-if="places.places.length"
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-3"
          >
            <li
              v-for="place in places.places"
              :key="place.start + (place.class_session || '')"
              class="flex flex-wrap items-center gap-2 py-2"
            >
              <div class="flex min-w-0 flex-1 flex-col">
                <span
                  class="text-p-base text-ink-gray-9 first-letter:uppercase"
                >
                  {{ formatDate(place.starts_on, 'dddd D MMM, HH:mm') }}
                </span>
                <span class="text-p-sm text-ink-gray-6">
                  {{ placeFacts(place) }}
                </span>
              </div>
              <div class="flex shrink-0 gap-2">
                <Button
                  v-if="entry.status === 'Waiting'"
                  :label="__('Offer')"
                  :disabled="!place.can_offer"
                  :title="
                    place.can_offer
                      ? ''
                      : __('It starts too soon to wait for an answer')
                  "
                  :loading="busy === 'offer:' + place.start"
                  @click="offer(place)"
                />
                <Button
                  v-if="entry.can_book"
                  variant="solid"
                  :label="__('Book')"
                  :loading="busy === 'book:' + place.start"
                  @click="book(place)"
                />
              </div>
            </li>
          </ol>
          <p v-else class="text-p-sm text-ink-gray-5">
            {{
              __('No free place that suits them in the next {0} days.', [
                places.days_ahead,
              ])
            }}
          </p>
        </div>

        <details v-if="pastOffers.length" class="text-p-sm">
          <summary class="cursor-pointer text-ink-gray-6">
            {{ __('Offers made ({0})', [pastOffers.length]) }}
          </summary>
          <ul class="mt-2 flex flex-col gap-1.5">
            <li
              v-for="past in pastOffers"
              :key="past.name"
              class="flex flex-wrap items-center justify-between gap-2"
            >
              <span class="min-w-0 text-ink-gray-7">
                {{ placeLabel(past) }}
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="OFFERTA[past.status]?.theme || 'gray'"
                :label="__(OFFERTA[past.status]?.label || past.status)"
              />
            </li>
          </ul>
        </details>
        <ErrorMessage :message="error" />
      </div>
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-end gap-2"
      >
        <Button
          v-if="entry.name"
          :label="__('Cancel')"
          @click="editing = false"
        />
        <Button
          variant="solid"
          :label="entry.name ? __('Save') : __('Put on the list')"
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
            :loading="busy === 'remove'"
          />
        </Dropdown>
        <span v-else />
        <div class="flex flex-wrap gap-2">
          <Button
            v-if="aperta && entry.can_manage"
            variant="solid"
            :label="places ? __('Look again') : __('Find a place')"
            :loading="busy === 'places'"
            @click="findPlaces"
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
  APERTE,
  GIORNI,
  MASSIMO_POSTI,
  NOMI_DELLE_PARTI,
  OFFERTA,
  PARTI,
  STATO,
  comeStaLOfferta,
  errore,
  giornoBreve,
  perIlServer,
  quandoPuo,
  scegli,
} from '@/utils/attese'
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
  // the entry to open; none to put the person on a list
  name: { type: String, default: null },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const router = useRouter()
const { $dialog } = globalStore()
const meta = useSchedulerMeta()
const t = (text, args) => __(text, args)
const locale = appLocale()

const entry = reactive({})
const form = reactive({})
const editing = ref(false)
const loading = ref(false)
const busy = ref('')
const error = ref('')
const places = ref(null)
const fullClasses = ref([])

const aperta = computed(() => APERTE.includes(entry.status))

function empty() {
  return {
    service: '',
    staff: '',
    class_session: '',
    seats: 1,
    weekdays: [],
    parts: [],
    from_date: '',
    until: dayjs().add(30, 'day').format('YYYY-MM-DD'),
    channel: entry.channels?.[0] || 'Email',
    urgent: false,
    notes: '',
  }
}

function fill(data) {
  for (const key of Object.keys(entry)) delete entry[key]
  Object.assign(entry, data)
}

function edit() {
  Object.assign(form, empty(), {
    service: entry.service,
    staff: entry.staff || '',
    class_session: entry.class_session || '',
    seats: entry.seats || 1,
    weekdays: entry.choice ? [...entry.choice.days] : [],
    parts: entry.choice ? [...entry.choice.parts] : [],
    from_date: entry.from_date || '',
    until: entry.until || '',
    channel: entry.channel,
    urgent: Boolean(entry.urgent),
    notes: entry.notes || '',
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
    places.value = null
    if (!props.name) {
      fill({})
      loading.value = true
      try {
        // the channels this centre offers, for the choice below
        const entries = await call('crm.scheduling.attese.get_entries', {
          lead: props.lead,
        })
        entry.channels = entries.channels
      } catch {
        entry.channels = ['Email']
      } finally {
        loading.value = false
      }
      Object.assign(form, empty())
      const services = meta.data?.services || []
      if (services.length === 1) form.service = services[0].name
      editing.value = true
      return
    }
    editing.value = false
    loading.value = true
    try {
      fill(await call('crm.scheduling.attese.get_entry', { name: props.name }))
    } catch (e) {
      error.value = e.messages?.[0] || __('Could not open the entry')
    } finally {
      loading.value = false
    }
    // the list page mounts it open: it loads the first time too
  },
  { immediate: true },
)

// --- words --------------------------------------------------------------------

function service(name) {
  return (meta.data?.services || []).find((one) => one.name === name)
}

function staffName(user) {
  return (
    (meta.data?.staff || []).find((one) => one.name === user)?.full_name || user
  )
}

const title = computed(() => {
  if (editing.value)
    return entry.name ? __('Change the entry') : __('On the waiting list')
  return entry.service_name || ''
})

const serviceOptions = computed(() =>
  (meta.data?.services || []).map((one) => ({
    label: one.service_name,
    value: one.name,
  })),
)

const staffOptions = computed(() => [
  { label: __('Anybody who does it'), value: '' },
  ...(service(form.service)?.staff || []).map((row) => ({
    label: staffName(row.user),
    value: row.user,
  })),
])

const isClass = computed(
  () => (service(form.service)?.max_participants || 1) > 1,
)

const classOptions = computed(() => [
  { label: __('Any class of the service'), value: '' },
  ...fullClasses.value.map((lesson) => ({
    label: __('Full: {0}', [formatDate(lesson.starts_on, 'ddd D MMM, HH:mm')]),
    value: lesson.name,
  })),
])

watch(
  () => [form.service, editing.value],
  async ([name, isEditing]) => {
    fullClasses.value = []
    if (!isEditing || !name || !isClass.value) return
    try {
      fullClasses.value = await call('crm.scheduling.attese.get_full_classes', {
        service: name,
      })
    } catch {
      fullClasses.value = []
    }
  },
)

const channelOptions = computed(() =>
  (entry.channels || ['Email']).map((channel) => ({
    label: __(channel),
    value: channel,
  })),
)

const waitsFor = computed(() => {
  if (entry.class_session)
    return __('A seat in the class of {0}', [
      formatDate(entry.class_starts_on, 'dddd D MMM, HH:mm'),
    ])
  return quandoPuo(entry, t, locale)
})

const facts = computed(() => {
  const parts = []
  if (entry.staff_name) parts.push(__('with {0}', [entry.staff_name]))
  if (entry.seats > 1) parts.push(__('{0} places', [entry.seats]))
  if (entry.from_date)
    parts.push(__('not before {0}', [formatDate(entry.from_date, 'D MMM')]))
  parts.push(
    entry.until
      ? __('until {0}', [formatDate(entry.until, 'D MMM YYYY')])
      : __('with no last day'),
  )
  parts.push(__('offers by {0}', [__(entry.channel)]))
  // where they go, when the person gave them joining
  const to =
    entry.channel === 'Email' ? entry.email : entry.phone || entry.email
  if (to) parts.push(__('to {0}', [to]))
  if (entry.contact_name)
    parts.push(__('messages to {0}', [entry.contact_name]))
  parts.push(
    entry.source === 'Desk'
      ? __('added {0}', [formatDate(entry.since, 'D MMM')])
      : __('joined {0} ({1})', [
          formatDate(entry.since, 'D MMM'),
          __(entry.source),
        ]),
  )
  return parts.join(' · ')
})

function placeLabel(offer) {
  const when = formatDate(offer.starts_on, 'ddd D MMM, HH:mm')
  return offer.staff_name ? `${when} · ${offer.staff_name}` : when
}

function offerFacts(offer) {
  const parts = []
  if (offer.channel) parts.push(__('sent by {0}', [__(offer.channel)]))
  // why it did not leave, kept in the words of whoever offered it (a job
  // writes English): read in the reader's language
  else if (offer.not_sent) parts.push(__(offer.not_sent))
  if (offer.offered_by) parts.push(__('offered by {0}', [offer.offered_by]))
  if (offer.sent_on) parts.push(formatDate(offer.sent_on, 'D MMM, HH:mm'))
  return parts.join(' · ')
}

function placeFacts(place) {
  const parts = [place.staff_name]
  if (place.class_session) parts.push(__('{0} seats left', [place.seats_left]))
  if (place.offered) parts.push(__('offered to {0} already', [place.offered]))
  return parts.filter(Boolean).join(' · ')
}

const pastOffers = computed(() =>
  (entry.offers || []).filter((offer) => offer.status !== 'Sent'),
)

// --- what can be done -----------------------------------------------------------

const moreOptions = computed(() => {
  if (!entry.can_manage || !aperta.value) return []
  return [
    { label: __('Change'), icon: 'edit-2', onClick: edit },
    { label: __('Take off the list'), icon: 'x', onClick: remove },
  ]
})

async function save() {
  error.value = errore(form, t)
  if (error.value) return
  busy.value = 'save'
  const nuova = !entry.name
  try {
    const channels = entry.channels
    fill(
      await call('crm.scheduling.attese.save_entry', {
        lead: props.lead,
        data: perIlServer(form),
        name: entry.name || null,
      }),
    )
    entry.channels = entry.channels || channels
    toast.success(nuova ? __('On the waiting list') : __('Entry saved'))
    editing.value = false
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not save the entry')
  } finally {
    busy.value = ''
  }
}

async function findPlaces() {
  busy.value = 'places'
  error.value = ''
  try {
    places.value = await call('crm.scheduling.attese.find_places', {
      name: entry.name,
    })
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not look for places')
  } finally {
    busy.value = ''
  }
}

async function offer(place) {
  busy.value = 'offer:' + place.start
  error.value = ''
  try {
    const fatto = await call('crm.scheduling.attese.offer_place', {
      name: entry.name,
      start: place.start,
      staff: place.class_session ? null : place.staff[0] || null,
      class_session: place.class_session || null,
    })
    fill(fatto)
    places.value = null
    if (fatto.sent?.channel)
      toast.success(__('Offered by {0}', [__(fatto.sent.channel)]))
    else toast.warning(__('Offered, but nothing could be sent: call them'))
    emit('changed')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not offer the place')
  } finally {
    busy.value = ''
  }
}

function book(place) {
  $dialog({
    title: __('Book this place?'),
    message: __('{0}, {1}: the entry leaves the list.', [
      entry.service_name,
      formatDate(place.starts_on, 'dddd D MMM, HH:mm'),
    ]),
    actions: [
      {
        label: __('Book'),
        variant: 'solid',
        onClick: async (closeDialog) => {
          closeDialog()
          busy.value = 'book:' + place.start
          error.value = ''
          try {
            fill(
              await call('crm.scheduling.attese.book_place', {
                name: entry.name,
                start: place.start,
                staff: place.class_session ? null : place.staff[0] || null,
                class_session: place.class_session || null,
              }),
            )
            places.value = null
            toast.success(__('Booked'))
            emit('changed')
          } catch (e) {
            error.value = e.messages?.[0] || __('Could not book the place')
          } finally {
            busy.value = ''
          }
        },
      },
    ],
  })
}

function remove() {
  $dialog({
    title: __('Take off the waiting list?'),
    message: __(
      'They no longer wait: an offer still waiting for their answer goes to the next ones.',
    ),
    actions: [
      {
        label: __('Take off'),
        variant: 'solid',
        theme: 'red',
        onClick: async (closeDialog) => {
          closeDialog()
          busy.value = 'remove'
          try {
            fill(
              await call('crm.scheduling.attese.remove_entry', {
                name: entry.name,
              }),
            )
            emit('changed')
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

function openAppointment(voce) {
  show.value = false
  router.push({
    name: 'Calendar',
    query: {
      appointment: voce.booked_appointment,
      date: dayjs(voce.booked_starts_on).format('YYYY-MM-DD'),
    },
  })
}
</script>
