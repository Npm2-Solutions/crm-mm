<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  The agenda (docs/progetto-ghl/56-agenda.md). A day of the centre, one column
  per professional (or per room) who works it; a week of one of them; a month.
  One bar for every view: the arrows and the date, the view, whose agenda, the
  filters, how it looks. An appointment reads its person first, in as many
  whole lines as its height holds. On a phone the day opens as a list
  (components/Mobile/AgendaDelGiorno.vue), the hours' grid and the month one
  choice away.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" label="Agenda" />
    </template>
    <template #right-header>
      <!-- making one is for who books (doc 30): an event or an appointment.
           «New» opens the panel on whatever was made last, and the panel's
           first line switches between the two. -->
      <ShortcutTooltip v-if="prenota" :label="__('New')" combo="Mod+E">
        <Button
          variant="solid"
          :label="isMobileView ? undefined : __('New')"
          :aria-label="__('New')"
          :disabled="isCreateDisabled"
          @click="nuovo()"
        >
          <template #prefix>
            <span class="lucide-plus h-4" aria-hidden="true" />
          </template>
        </Button>
      </ShortcutTooltip>
    </template>
  </LayoutHeader>

  <div class="flex h-full overflow-hidden">
    <!-- On a phone the panel takes the whole width: what it opened from steps
         aside, or its controls were drawn over the panel's title. -->
    <div
      v-show="!(isMobileView && panelOpen)"
      class="flex min-w-0 flex-1 flex-col overflow-hidden"
    >
      <!-- the bar: when, which view, whose, which, how -->
      <div
        v-if="vista !== 'elenco'"
        class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2 px-3 py-2 sm:px-5"
      >
        <div class="flex min-w-0 items-center gap-0.5">
          <Button
            variant="ghost"
            icon="lucide-chevron-left"
            :aria-label="frecce.prima"
            @click="sposta(-1)"
          />
          <Button
            :variant="mostraOggi ? 'ghost' : 'subtle'"
            :label="__('Today')"
            @click="giorno = today()"
          />
          <Button
            variant="ghost"
            icon="lucide-chevron-right"
            :aria-label="frecce.dopo"
            @click="sposta(1)"
          />
          <DatePicker
            :modelValue="giorno"
            :clearable="false"
            @update:modelValue="(valore) => setGiorno(valore)"
          >
            <template #target="{ togglePopover }">
              <Button
                variant="ghost"
                class="min-w-0 text-base-medium text-ink-gray-8"
                iconRight="chevron-down"
                @click="togglePopover"
              >
                <span class="truncate">{{ etichetta }}</span>
              </Button>
            </template>
          </DatePicker>
          <span
            v-if="countLabel"
            class="ml-1 whitespace-nowrap text-p-sm text-ink-gray-5 max-lg:hidden"
          >
            {{ countLabel }}
          </span>
        </div>
        <span class="grow max-md:hidden" />
        <!-- on a phone one row that scrolls sideways, as the filters did -->
        <div
          class="flex items-center gap-2 max-md:-mx-3 max-md:w-[calc(100%+1.5rem)] max-md:overflow-x-auto max-md:px-3 max-md:[scrollbar-width:none] max-md:[&>*]:shrink-0"
        >
          <TabButtons
            v-if="!isMobileView"
            :modelValue="vista"
            :buttons="vistePerIlComputer"
            @update:modelValue="cambiaVista"
          />
          <div v-else class="w-28 shrink-0">
            <FormControl
              type="select"
              :modelValue="vista"
              :aria-label="__('View')"
              :options="vistePerIlTelefono"
              @update:modelValue="cambiaVista"
            />
          </div>
          <ChiNellAgenda v-bind="chi" @update:modelValue="cambiaChi" />
          <FiltriAgenda
            :modelValue="filters"
            :gruppi="gruppiDeiFiltri"
            @cambia="cambiaFiltro"
            @azzera="resetFilters"
          />
          <VistaAgenda
            :colonne="prefs.colonne"
            :altezza="prefs.altezza"
            :colore="prefs.colore"
            :tutti="prefs.tutti"
            :annullati="prefs.annullati"
            :conColonne="vista !== 'mese'"
            :conAltezza="vista !== 'mese'"
            :conTutti="vista === 'giorno'"
            :impostazioni="puo('impostazioni.generali')"
            :google="puo('google_calendar.proprio')"
            @update:colonne="(valore) => cambiaPreferenza('colonne', valore)"
            @update:altezza="(valore) => cambiaPreferenza('altezza', valore)"
            @update:colore="(valore) => cambiaPreferenza('colore', valore)"
            @update:tutti="(valore) => cambiaPreferenza('tutti', valore)"
            @update:annullati="
              (valore) => cambiaPreferenza('annullati', valore)
            "
          />
        </div>
      </div>
      <!-- a phone's day as a list: whose and which above it; the list has its
           own week strip and its own switch to the grid -->
      <div
        v-else
        class="flex shrink-0 items-center gap-2 overflow-x-auto border-b border-outline-gray-2 px-3 py-2 [scrollbar-width:none] [&>*]:shrink-0"
      >
        <ChiNellAgenda v-bind="chi" @update:modelValue="cambiaChi" />
        <FiltriAgenda
          :modelValue="filters"
          :gruppi="gruppiDeiFiltri"
          @cambia="cambiaFiltro"
          @azzera="resetFilters"
        />
      </div>

      <AgendaDelGiorno
        v-if="vista === 'elenco'"
        v-model:date="giorno"
        :appointments="appuntamentiDelGiorno"
        :events="shownEvents"
        :serviceColors="serviceColors"
        :selected="selectedAppointment"
        :caricando="scheduler.loading"
        :aggiorna="ricaricaIlGiorno"
        @open="showDetails"
      >
        <template #vista>
          <div class="w-28">
            <FormControl
              type="select"
              modelValue="elenco"
              :aria-label="__('View')"
              :options="vistePerIlTelefono"
              @update:modelValue="cambiaVista"
            />
          </div>
        </template>
      </AgendaDelGiorno>
      <MeseAgenda
        v-else-if="vista === 'mese'"
        class="min-h-0 flex-1"
        :giorno="giorno"
        :cose="cosePerIlMese"
        :colorePer="prefs.colore"
        :serviceColors="serviceColors"
        :scelto="scelto"
        :compatto="isMobileView"
        @giorno="apriGiorno"
        @apri="apri"
      />
      <GrigliaAgenda
        v-else
        class="min-h-0 flex-1"
        :colonne="colonne"
        :cose="cosePerColonne"
        :pxPerMinuto="pxPerMinuto"
        :modo="prefs.colonne"
        :settimana="vista === 'settimana'"
        :passo="passo"
        :scelto="scelto"
        :modificabile="prenota"
        :colorePer="prefs.colore"
        :serviceColors="serviceColors"
        :nomeDi="nomeDi"
        :nomeStanza="nomeStanza"
        :pronto="pronto"
        @apri="apri"
        @modifica="modifica"
        @crea="creaNellaGriglia"
        @sposta="spostaNellaGriglia"
        @giorno="apriGiorno"
      >
        <template #vuoto>
          <div class="flex h-full items-center justify-center p-6">
            <EmptyState :title="vuoto.titolo" :text="vuoto.testo">
              <Button
                v-if="vuoto.azione"
                :label="vuoto.azione"
                @click="cambiaPreferenza('tutti', true)"
              />
            </EmptyState>
          </div>
        </template>
      </GrigliaAgenda>
    </div>

    <!-- One side panel, for an event or an appointment, in every view. -->
    <div
      ref="pannello"
      class="flex flex-none flex-col overflow-hidden transition-all duration-300 ease-in-out"
      :class="
        panelOpen
          ? 'w-full border-l bg-surface-base sm:w-[352px]'
          : 'w-0 border-l-0'
      "
    >
      <CalendarEventPanel
        v-if="showEventPanel"
        ref="eventPanel"
        v-model="showEventPanel"
        v-model:event="event"
        :mode="mode"
        @new="startNew"
        @save="saveEvent"
        @edit="editDetails"
        @delete="deleteEvent"
        @duplicate="duplicateEvent"
        @details="showDetails"
        @close="close"
        @sync="syncEvent"
      >
        <template #kind>
          <KindSwitch
            v-if="mode === 'new' && hasServices"
            :modelValue="'event'"
            @update:modelValue="switchKind"
          />
        </template>
      </CalendarEventPanel>
      <AppointmentPanel
        v-else-if="appointmentPanel.mode"
        :mode="appointmentPanel.mode"
        :name="appointmentPanel.name"
        :seed="appointmentPanel.seed"
        :meta="meta.data || {}"
        @mode="onAppointmentMode"
        @saved="reloadScheduler"
        @deleted="onAppointmentDeleted"
        @close="closeAppointment"
      >
        <template #kind>
          <KindSwitch
            v-if="appointmentPanel.mode === 'new'"
            :modelValue="'appointment'"
            @update:modelValue="switchKind"
          />
        </template>
      </AppointmentPanel>
    </div>
  </div>
</template>
<script setup>
import AppointmentPanel from '@/components/Calendar/AppointmentPanel.vue'
import CalendarEventPanel from '@/components/Calendar/CalendarEventPanel.vue'
import ChiNellAgenda from '@/components/Calendar/ChiNellAgenda.vue'
import FiltriAgenda from '@/components/Calendar/FiltriAgenda.vue'
import GrigliaAgenda from '@/components/Calendar/GrigliaAgenda.vue'
import KindSwitch from '@/components/Calendar/KindSwitch.vue'
import MeseAgenda from '@/components/Calendar/MeseAgenda.vue'
import VistaAgenda from '@/components/Calendar/VistaAgenda.vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ShortcutTooltip from '@/components/ShortcutTooltip.vue'
import AgendaDelGiorno from '@/components/Mobile/AgendaDelGiorno.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { getSettings } from '@/stores/settings'
import { isMobileView } from '@/composables/breakpoints'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { useSchedulerMeta } from '@/composables/scheduling'
import {
  ALTEZZE,
  ALTEZZA_PREDEFINITA,
  colonneDelGiorno,
  cosePerColonna,
  cosePerGiorno,
  daDisegnare,
  etichettaDelPeriodo,
  giorniDellaSettimana,
  meseDi,
  orarioDelGiorno,
  periodoDi,
  spostaPeriodo,
} from '@/utils/agenda'
import { appLocale } from '@/utils/locale'
import {
  adessoDelCentro,
  dateAtMinutes,
  formatMinutes,
  oggiDelCentro,
  oraDelCentro,
} from '@/utils/scheduler'
import {
  NAMED_HEX,
  calendarColorName,
  registerCalendarColors,
} from '@/utils/calendarColors'
import {
  createListResource,
  createResource,
  dayjs,
  DatePicker,
  FormControl,
  TabButtons,
  CalendarActiveEvent as activeEvent,
  CalendarColorMap,
  call,
  toast,
} from 'frappe-ui'
import {
  onBeforeUnmount,
  onMounted,
  ref,
  reactive,
  computed,
  provide,
  nextTick,
  watch,
} from 'vue'
import { chiudeConIndietro } from '@/utils/indietro'
import { useRoute } from 'vue-router'

const { user } = sessionStore()
const { $dialog } = globalStore()
const { settings } = getSettings()
const { getUser, puo } = usersStore()
// booking, and any event in the agenda, is `agenda.prenota`'s (doc 30): who
// only reads the agenda opens what is there
const prenota = computed(() => puo('agenda.prenota'))
const route = useRoute()
const lingua = appLocale() || 'it-IT'

// grey and red, which the event panel's colours do not know by themselves
registerCalendarColors(CalendarColorMap)

// ---------------------------------------------------------------------------
// how the agenda looks to whoever reads it, kept in their browser
// ---------------------------------------------------------------------------

const VISTE_DEL_COMPUTER = ['giorno', 'settimana', 'mese']
const PREFERENZE = 'crmAgenda'
function preferenzeSalvate() {
  try {
    return JSON.parse(localStorage.getItem(PREFERENZE) || '{}') || {}
  } catch {
    return {}
  }
}
const salvate = preferenzeSalvate()
const prefs = reactive({
  vista: VISTE_DEL_COMPUTER.includes(salvate.vista) ? salvate.vista : '',
  colonne: salvate.colonne === 'resource' ? 'resource' : 'staff',
  altezza: ALTEZZE[salvate.altezza] ? salvate.altezza : ALTEZZA_PREDEFINITA,
  colore: salvate.colore === 'stato' ? 'stato' : 'servizio',
  tutti: Boolean(salvate.tutti),
  annullati: Boolean(salvate.annullati),
  // whose week, as a professional's and as a room's
  settimanaDi:
    salvate.settimanaDi && typeof salvate.settimanaDi === 'object'
      ? salvate.settimanaDi
      : {},
})
watch(
  prefs,
  () => {
    try {
      localStorage.setItem(PREFERENZE, JSON.stringify(prefs))
    } catch {
      // a private window: they are only preferences
    }
  },
  { deep: true },
)

function cambiaPreferenza(chiave, valore) {
  prefs[chiave] = valore
  if (chiave === 'colonne') reloadScheduler()
}

// ---------------------------------------------------------------------------
// the view and the day
// ---------------------------------------------------------------------------

const vistePerIlComputer = [
  { label: __('Day'), value: 'giorno' },
  { label: __('Week'), value: 'settimana' },
  { label: __('Month'), value: 'mese' },
]
// a phone has no week: seven columns of 45px read nothing, not even a name
const vistePerIlTelefono = [
  { label: __('List'), value: 'elenco' },
  { label: __('Day'), value: 'giorno' },
  { label: __('Month'), value: 'mese' },
]

// the view one left the agenda on, else the centre's (Settings > Agenda >
// Calendar & reminders), else the day: the desk's view
function vistaIniziale() {
  if (prefs.vista) return prefs.vista
  return (
    { Daily: 'giorno', Weekly: 'settimana', Monthly: 'mese' }[
      settings.value?.default_calendar_view
    ] || 'giorno'
  )
}

// an address that names a day (a notification, a person's «Book») opens on
// that day, as a day
const dataDellIndirizzo = /^\d{4}-\d{2}-\d{2}/.test(route.query.date || '')
  ? String(route.query.date).slice(0, 10)
  : ''
const vista = ref(
  isMobileView.value
    ? 'elenco'
    : dataDellIndirizzo
      ? 'giorno'
      : vistaIniziale(),
)
watch(isMobileView, (mobile) => {
  if (mobile && vista.value === 'settimana') vista.value = 'elenco'
  else if (!mobile && vista.value === 'elenco') vista.value = vistaIniziale()
})

function cambiaVista(nuova) {
  if (!nuova || nuova === vista.value) return
  // from a day with one of them ticked, the week is theirs
  if (nuova === 'settimana') {
    const scelti =
      prefs.colonne === 'resource' ? filters.resources : filters.staff
    if (scelti.length === 1)
      prefs.settimanaDi = { ...prefs.settimanaDi, [prefs.colonne]: scelti[0] }
  }
  vista.value = nuova
  if (!isMobileView.value) prefs.vista = nuova
}

// the centre's today: a phone in another time zone opened another day
function today() {
  return oggiDelCentro()
}
const giorno = ref(dataDellIndirizzo || today())

function setGiorno(valore) {
  if (valore) giorno.value = dayjs(valore).format('YYYY-MM-DD')
}

function sposta(verso) {
  giorno.value = spostaPeriodo(vista.value, giorno.value, verso)
}

// a week's day or a month's opened: that day
function apriGiorno(data) {
  giorno.value = data
  cambiaVista('giorno')
}

const periodo = computed(() =>
  periodoDi(vista.value === 'elenco' ? 'giorno' : vista.value, giorno.value),
)

const etichetta = computed(() =>
  etichettaDelPeriodo(vista.value, giorno.value, lingua),
)

const frecce = computed(
  () =>
    ({
      settimana: { prima: __('The week before'), dopo: __('The week after') },
      mese: { prima: __('The month before'), dopo: __('The month after') },
    })[vista.value] || {
      prima: __('Previous day'),
      dopo: __('Next day'),
    },
)

// «Today» is a way back: quiet where today is already shown
const mostraOggi = computed(() => {
  const { start, end } = periodo.value
  const adesso = today()
  return start <= adesso && adesso <= end
})

// ---------------------------------------------------------------------------
// appointments (services, professionals, rooms, equipment)
// ---------------------------------------------------------------------------

const APPOINTMENT_PREFIX = 'appt:'
const isAppointmentId = (id) => String(id || '').startsWith(APPOINTMENT_PREFIX)
const appointmentName = (id) => String(id).slice(APPOINTMENT_PREFIX.length)

const selectedAppointment = ref('')

const filters = reactive({
  services: [],
  staff: [],
  resources: [],
  statuses: [],
  sources: [],
})

const meta = useSchedulerMeta()

const scheduler = createResource({
  url: 'crm.api.appointments.get_calendar',
  auto: false,
})

// the period the data that came are of: the grid opens its hours on them
const caricatoPer = ref('')
const pronto = computed(
  () =>
    caricatoPer.value === `${periodo.value.start}|${periodo.value.end}` &&
    !scheduler.loading,
)

// what the grid and the month draw: a cancelled appointment leaves its place
// free, unless asked for
const appuntamenti = computed(() =>
  daDisegnare(scheduler.data?.appointments || [], {
    annullati: prefs.annullati,
    stati: filters.statuses,
  }),
)
// the phone's list says how every one went, a cancelled one too
const appuntamentiDelGiorno = computed(() => scheduler.data?.appointments || [])
// the rest of the agenda, for who sees only part of it: when, not who or why
const busy = computed(() => scheduler.data?.busy || [])
const ore = computed(() => scheduler.data?.hours || {})

const serviceColors = computed(() =>
  Object.fromEntries(
    (meta.data?.services || []).map((service) => [service.name, service.color]),
  ),
)

const professionisti = computed(() => meta.data?.staff || [])
const stanze = computed(() => meta.data?.resources || [])

function nomeDi(utente) {
  const persona = professionisti.value.find((p) => p.name === utente)
  return persona?.full_name || getUser(utente)?.full_name || utente
}
function nomeStanza(stanza) {
  return (
    stanze.value.find((s) => s.name === stanza)?.resource_name || stanza || ''
  )
}

const hasFilters = computed(() =>
  Object.values(filters).some((value) => value.length),
)

function resetFilters() {
  filters.services = []
  filters.staff = []
  filters.resources = []
  filters.statuses = []
  filters.sources = []
  reloadScheduler()
}

function cambiaFiltro(chiave, valori) {
  filters[chiave] = valori
  reloadScheduler()
}

// the other filters, by what the columns are not
const gruppiDeiFiltri = computed(() => [
  {
    chiave: 'services',
    titolo: __('Services'),
    vuoto: __('No services configured yet'),
    opzioni: (meta.data?.services || []).map((service) => ({
      label: service.service_name,
      value: service.name,
      colore: service.color,
    })),
  },
  perStanza.value
    ? {
        chiave: 'staff',
        titolo: __('Professionals'),
        opzioni: professionisti.value.map((persona) => ({
          label: persona.full_name || persona.name,
          value: persona.name,
        })),
      }
    : {
        chiave: 'resources',
        titolo: __('Rooms & equipment'),
        vuoto: __('No rooms or equipment yet'),
        opzioni: stanze.value.map((stanza) => ({
          label: stanza.resource_name,
          value: stanza.name,
          colore: stanza.color,
        })),
      },
  {
    chiave: 'statuses',
    titolo: __('Status'),
    opzioni: (meta.data?.statuses || []).map((status) => ({
      label: __(status),
      value: status,
    })),
  },
  {
    chiave: 'sources',
    titolo: __('Source'),
    opzioni: [
      { label: __('Created in {brand}'), value: 'Internal' },
      { label: __('Online booking page'), value: 'Online' },
      ...(meta.data?.platforms || []).map((platform) => ({
        label: platform,
        value: platform,
      })),
    ],
  },
])

// ---------------------------------------------------------------------------
// whose agenda: the columns of a day, the one a week is of
// ---------------------------------------------------------------------------

const perStanza = computed(() => prefs.colonne === 'resource')

// a week is of one of them: the one chosen, else oneself, else the first
const chiDellaSettimana = computed(() => {
  const chiavi = perStanza.value
    ? stanze.value.map((s) => s.name)
    : professionisti.value.map((p) => p.name)
  const scelto = prefs.settimanaDi[prefs.colonne]
  if (chiavi.includes(scelto)) return scelto
  if (!perStanza.value && chiavi.includes(user)) return user
  return chiavi[0] || ''
})

function orariDi(chiave) {
  return perStanza.value
    ? ore.value.resources?.[chiave]
    : ore.value.staff?.[chiave]
}

// a column's line under its name: its hours that day, why it is off, or that
// it is off
function sottotitolo(orari, data) {
  const delGiorno = orari?.[data]
  if (!delGiorno) return ''
  if (delGiorno.note) return delGiorno.note
  if (!delGiorno.open?.length)
    return perStanza.value ? __('Closed') : __('Not working')
  return orarioDelGiorno(delGiorno.open)
}

const opzioniDiChi = computed(() =>
  perStanza.value
    ? stanze.value.map((stanza) => ({
        value: stanza.name,
        label: stanza.resource_name,
        colore: stanza.color,
        nota: __(stanza.resource_type),
      }))
    : professionisti.value.map((persona) => ({
        value: persona.name,
        label: persona.full_name || persona.name,
        utente: persona.name,
        nota:
          vista.value === 'giorno'
            ? sottotitolo(ore.value.staff?.[persona.name], giorno.value)
            : '',
      })),
)

const chi = computed(() => ({
  modelValue:
    vista.value === 'settimana'
      ? chiDellaSettimana.value
      : perStanza.value
        ? filters.resources
        : filters.staff,
  singolo: vista.value === 'settimana',
  opzioni: opzioniDiChi.value,
  titolo: perStanza.value ? __('Rooms & equipment') : __('Professionals'),
  tutti: perStanza.value ? __('All rooms') : __('All professionals'),
  quanti: perStanza.value
    ? (n) => __('{0} rooms', [n])
    : (n) => __('{0} professionals', [n]),
  vuoto: perStanza.value
    ? __('No rooms or equipment yet')
    : __('No professionals to show — add them to a service first'),
  icona: perStanza.value ? 'lucide-door-open' : 'lucide-users',
}))

function cambiaChi(valore) {
  if (vista.value === 'settimana')
    prefs.settimanaDi = { ...prefs.settimanaDi, [prefs.colonne]: valore }
  else if (perStanza.value) filters.resources = valore
  else filters.staff = valore
  reloadScheduler()
}

// ---------------------------------------------------------------------------
// what the views draw
// ---------------------------------------------------------------------------

// one's own events: there are none in a list filtered by what only
// appointments have (a service, a professional, a room, a state)
const shownEvents = computed(() =>
  hasFilters.value ? [] : Array.isArray(events.data) ? events.data : [],
)

const oggi = computed(() => today())

// whose rows are these: the professionals', or the rooms'
const diChi = (riga) =>
  perStanza.value
    ? (riga.resources || []).map((r) => r.resource)
    : (riga.staff || []).map((s) => s.user)

// who has something drawn on the day: they show, working or not
const occupatiNelGiorno = computed(() => {
  const chiavi = new Set()
  for (const riga of [...appuntamenti.value, ...busy.value]) {
    if (String(riga.starts_on).slice(0, 10) > giorno.value) continue
    if (String(riga.ends_on).slice(0, 10) < giorno.value) continue
    diChi(riga).forEach((chiave) => chiavi.add(chiave))
  }
  return chiavi
})

const mieiEventiDelGiorno = computed(() =>
  shownEvents.value.some(
    (evento) =>
      evento.fromDate <= giorno.value &&
      (evento.toDate || evento.fromDate) >= giorno.value,
  ),
)

const nomeDelGiorno = new Intl.DateTimeFormat(lingua, { weekday: 'short' })
const giornoPerEsteso = new Intl.DateTimeFormat(lingua, {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})
const comeData = (data) => {
  const [a, m, g] = data.split('-').map(Number)
  return new Date(a, m - 1, g)
}

// a column's open hours on its day: unknown (undefined), never set (null), or
// its windows - none when it does not work
function apertoDi(orari, data) {
  if (orari === null) return null
  return orari ? orari[data]?.open ?? [] : undefined
}

const colonne = computed(() => {
  if (vista.value === 'settimana') {
    const chiave = chiDellaSettimana.value
    const orari = orariDi(chiave)
    const occupati = new Set()
    for (const riga of [...appuntamenti.value, ...busy.value])
      if (diChi(riga).includes(chiave))
        occupati.add(String(riga.starts_on).slice(0, 10))
    if (!perStanza.value && chiave === user)
      shownEvents.value.forEach((evento) => occupati.add(evento.fromDate))
    return giorniDellaSettimana(giorno.value, { orari, occupati }).map(
      (data) => ({
        key: data,
        tipo: 'giorno',
        data,
        oggi: data === oggi.value,
        nome: nomeDelGiorno.format(comeData(data)).replace('.', ''),
        numero: comeData(data).getDate(),
        titolo: giornoPerEsteso.format(comeData(data)),
        aperto: apertoDi(orari, data),
        sottotitolo: sottotitolo(orari, data),
      }),
    )
  }

  const tutti = perStanza.value
    ? stanze.value.map((s) => s.name)
    : professionisti.value.map((p) => p.name)
  let chiavi = colonneDelGiorno(tutti, {
    giorno: giorno.value,
    orari: (perStanza.value ? ore.value.resources : ore.value.staff) || {},
    occupati: occupatiNelGiorno.value,
    scelti: perStanza.value ? filters.resources : filters.staff,
    mostraTutti: prefs.tutti,
  })
  // one's own events need a column: one's own, first
  if (
    !perStanza.value &&
    !filters.staff.length &&
    mieiEventiDelGiorno.value &&
    !chiavi.includes(user)
  )
    chiavi = [user, ...chiavi]
  return chiavi.map((chiave) => {
    const orari = orariDi(chiave)
    const stanza = perStanza.value
      ? stanze.value.find((s) => s.name === chiave)
      : null
    const professionista = professionisti.value.some((p) => p.name === chiave)
    return {
      key: chiave,
      tipo: perStanza.value ? 'stanza' : 'persona',
      data: giorno.value,
      oggi: giorno.value === oggi.value,
      titolo: perStanza.value
        ? stanza?.resource_name || chiave
        : nomeDi(chiave),
      utente: perStanza.value ? '' : chiave,
      colore: stanza?.color || '',
      aperto: apertoDi(orari, giorno.value),
      sottotitolo:
        !perStanza.value && !professionista
          ? __('Your events')
          : sottotitolo(orari, giorno.value),
    }
  })
})

const cosePerColonne = computed(() =>
  cosePerColonna(colonne.value, {
    modo: prefs.colonne,
    settimana: vista.value === 'settimana',
    chi: chiDellaSettimana.value,
    io: user,
    appuntamenti: appuntamenti.value,
    eventi: shownEvents.value,
    occupato: busy.value,
    impegni: scheduler.data?.engaged || [],
  }),
)

const cosePerIlMese = computed(() =>
  cosePerGiorno(meseDi(giorno.value).flat(), {
    appuntamenti: appuntamenti.value,
    eventi: shownEvents.value,
  }),
)

// nothing to draw on the day: why, and what would show more
const vuoto = computed(() => {
  if (perStanza.value && !stanze.value.length)
    return { titolo: __('No rooms or equipment yet'), testo: '', azione: '' }
  if (!perStanza.value && !professionisti.value.length)
    return {
      titolo: __('No professionals to show — add them to a service first'),
      testo: '',
      azione: '',
    }
  const quando = giornoPerEsteso.format(comeData(giorno.value))
  return {
    titolo: perStanza.value
      ? __('Every room is closed on {0}', [quando])
      : __('Nobody works on {0}', [quando]),
    testo: __('Nothing is booked on this day.'),
    azione: prefs.tutti ? '' : __('Show everybody'),
  }
})

const pxPerMinuto = computed(
  () => ALTEZZE[prefs.altezza] || ALTEZZE[ALTEZZA_PREDEFINITA],
)
// how far a click or a drop snaps, as the centre set it
const passo = computed(() => Number(settings.value?.calendar_grid_step) || 15)

const scelto = computed(() =>
  selectedAppointment.value
    ? `${APPOINTMENT_PREFIX}${selectedAppointment.value}`
    : showEventPanel.value
      ? event.value?.id || ''
      : '',
)

const countLabel = computed(() => {
  const booked = appuntamenti.value.filter(
    (appuntamento) => appuntamento.status !== 'Cancelled',
  ).length
  const planned = shownEvents.value.filter((ev) => !isTempEvent(ev.id)).length
  const parts = []
  if (booked)
    parts.push(
      booked === 1 ? __('1 appointment') : __('{0} appointments', [booked]),
    )
  if (planned)
    parts.push(planned === 1 ? __('1 event') : __('{0} events', [planned]))
  return parts.join(' · ')
})

// the day pulled down on a phone: its appointments and its events
function ricaricaIlGiorno() {
  return Promise.all([reloadScheduler(), events.reload()])
}

function reloadScheduler() {
  const { start, end } = periodo.value
  // a week is of one of them: only theirs come
  const suoi =
    vista.value === 'settimana' && chiDellaSettimana.value
      ? [chiDellaSettimana.value]
      : null
  const chiave = `${start}|${end}`
  return scheduler.submit(
    {
      start,
      end,
      services: filters.services,
      staff: !perStanza.value && suoi ? suoi : filters.staff,
      resources: perStanza.value && suoi ? suoi : filters.resources,
      statuses: filters.statuses,
      sources: filters.sources,
      include_events: false,
      with_hours: ['giorno', 'settimana'].includes(vista.value),
    },
    {
      onSuccess: () => {
        caricatoPer.value = chiave
      },
    },
  )
}

// ---------------------------------------------------------------------------
// the side panel: an event, or an appointment
// ---------------------------------------------------------------------------

// `mode` is details, edit or new; '' when no appointment is open
const appointmentPanel = reactive({ mode: '', name: '', seed: {} })

const panelOpen = computed(
  () => showEventPanel.value || Boolean(appointmentPanel.mode),
)

const hasServices = computed(() => (meta.data?.services || []).length > 0)

// What «New» makes: what was made last, remembered in this browser. On a
// calendar without services there is nothing to book, only events.
const KIND_KEY = 'crmCalendarNewKind'
function rememberedKind() {
  try {
    return localStorage.getItem(KIND_KEY) === 'event' ? 'event' : 'appointment'
  } catch {
    return 'appointment'
  }
}
const newKind = ref(rememberedKind())
watch(newKind, (kind) => {
  try {
    localStorage.setItem(KIND_KEY, kind)
  } catch {
    // private window: it is only a preference
  }
})

// where the last «New» was asked for, for switching kinds without losing it
let newAt = {}

// «New» from the header: on the day shown, when it is not today
function nuovo() {
  if (giorno.value !== today() && vista.value !== 'mese')
    return startNew({ date: giorno.value })
  startNew()
}

/**
 * Something new, from «New», Mod+E, or a click on a free time. `at` is the
 * slot: a date, a time, all day or not, and whose column it was in. A click on
 * the all-day row is an event: an appointment has hours.
 */
function startNew(at = {}) {
  if (!prenota.value) return
  const fromTime = at.time ? getFromToTime(at.time)[0] : nextQuarter()
  newAt = {
    date: at.date ? dayjs(at.date).format('YYYY-MM-DD') : today(),
    time: fromTime,
    isFullDay: Boolean(at.isFullDay),
    staff: at.staff,
    resource: at.resource,
  }
  const kind = hasServices.value && !newAt.isFullDay ? newKind.value : 'event'
  if (kind === 'appointment') openNewAppointment(newAt)
  else {
    closeAppointment()
    newEvent(newAt)
  }
}

// With no slot clicked, the next quarter of an hour on the centre's clock:
// rounding down, as the slot picker does, proposed a time already gone.
function nextQuarter() {
  const now = dayjs(adessoDelCentro())
  return formatMinutes(Math.ceil((now.hour() * 60 + now.minute()) / 15) * 15)
}

// The first line of a new one switched: the same day and time, the other kind.
function switchKind(kind) {
  newKind.value = kind
  if (kind === 'appointment') {
    close()
    openNewAppointment(newAt)
  } else {
    closeAppointment()
    newEvent(newAt)
  }
}

function openNewAppointment(seed = {}) {
  close()
  newAt = { ...newAt, ...seed }
  appointmentPanel.seed = { ...seed }
  appointmentPanel.name = ''
  appointmentPanel.mode = 'new'
}

function openAppointment(name, mode = 'details') {
  close()
  selectedAppointment.value = name
  appointmentPanel.name = name
  appointmentPanel.mode = mode
}

function closeAppointment() {
  appointmentPanel.mode = ''
  appointmentPanel.name = ''
  selectedAppointment.value = ''
}

function onAppointmentMode(mode, name) {
  if (name) {
    appointmentPanel.name = name
    selectedAppointment.value = name
  }
  appointmentPanel.mode = mode
}

function onAppointmentDeleted() {
  closeAppointment()
  reloadScheduler()
}

// a block of the grid or a line of the month, opened or edited
function apri(cosa) {
  if (cosa.tipo === 'appuntamento') openAppointment(cosa.dati.name)
  else showDetails({ id: cosa.id })
}

function modifica(cosa) {
  if (cosa.tipo === 'appuntamento') openAppointment(cosa.dati.name, 'edit')
  else editDetails({ id: cosa.id })
}

// a free time of a column: something new there, for its professional or room
function creaNellaGriglia({ colonna, minuti }) {
  if (!prenota.value) return
  const suo =
    vista.value === 'settimana' ? chiDellaSettimana.value : colonna.key
  const professionista = professionisti.value.some((p) => p.name === suo)
  startNew({
    date: colonna.data,
    time: formatMinutes(minuti),
    staff: !perStanza.value && professionista ? suo : undefined,
    resource: perStanza.value ? suo : undefined,
  })
}

// an appointment dropped: another time, another day of the week, another
// professional's or room's column
function spostaNellaGriglia({ cosa, da, a, minuti, durata }) {
  if (cosa.tipo !== 'appuntamento') return
  const settimana = vista.value === 'settimana'
  onGridMove({
    name: cosa.dati.name,
    startsOn: dateAtMinutes(a.data, minuti),
    endsOn: dateAtMinutes(a.data, minuti + durata),
    mode: prefs.colonne,
    from: settimana ? chiDellaSettimana.value : da,
    to: settimana ? chiDellaSettimana.value : a.key,
  })
}

function onGridMove({ name, startsOn, endsOn, mode, from, to }) {
  const target = appuntamenti.value.find((a) => a.name === name)
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
        starts_on: oraDelCentro(startsOn),
        ends_on: oraDelCentro(endsOn),
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
        starts_on: oraDelCentro(startsOn),
        ends_on: oraDelCentro(endsOn),
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

// whose week changed: theirs
watch(chiDellaSettimana, () => {
  if (vista.value === 'settimana') reloadScheduler()
})

// ---------------------------------------------------------------------------
// events (one's own calendar)
// ---------------------------------------------------------------------------

function buildEventFilters(range) {
  const filters = [['status', '=', 'Open']]
  if (range?.start && range?.end) {
    const start = dayjs(range.start)
      .startOf('day')
      .format('YYYY-MM-DD HH:mm:ss')
    const end = dayjs(range.end).endOf('day').format('YYYY-MM-DD HH:mm:ss')
    filters.push(['starts_on', '<=', end])
    filters.push(['ends_on', '>=', start])
  }
  return filters
}

function buildEventOrFilters() {
  return [
    ['owner', '=', user],
    ['Event Participants', 'email', '=', user],
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
  // asked by what shows them, for its period (`eventiDelPeriodo`): asked by
  // itself as well, it brought every open event of the centre, to 9,999
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
        // stored as a hex, a design-system variable or a name: one name of
        // the palette, as the panel's colours have them
        color: calendarColorName(ev.color),
        attending: ev.attending,
        referenceDoctype: ev.reference_doctype,
        referenceDocname: ev.reference_docname,
      }))
      .filter(
        (ev, index, self) => index === self.findIndex((e) => e.id === ev.id),
      ),
})

provide('events', events)

// one's events of the period shown
function eventiDelPeriodo() {
  events.update({
    filters: buildEventFilters(periodo.value),
    orFilters: buildEventOrFilters(),
  })
  return events.reload()
}

// a period, a view: its appointments, and one's events in it - the first
// as the page is made
watch(
  () => [vista.value, periodo.value.start, periodo.value.end],
  () => {
    reloadScheduler()
    eventiDelPeriodo()
  },
  { immediate: true },
)

const eventPanel = ref(null)
const showEventPanel = ref(false)

// A panel that opens takes focus to its heading, so a screen reader reads it
// from the top (on a phone it covers the agenda); closed, focus goes back to
// whatever opened it, or to the page's heading when that was drawn anew
const pannello = ref(null)
let primaDelPannello = null
watch(panelOpen, async (aperto) => {
  if (aperto) {
    primaDelPannello = document.activeElement
    await nextTick()
    pannello.value
      ?.querySelector('[data-titolo-pannello]')
      ?.focus({ preventScroll: true })
    return
  }
  // only when focus was in the panel (its close button) or lost, never taken
  // from somewhere else
  const qui = document.activeElement
  const prima = primaDelPannello
  primaDelPannello = null
  if (qui && qui !== document.body && !pannello.value?.contains(qui)) return
  await nextTick()
  const dove = prima?.isConnected
    ? prima
    : document.getElementById('titolo-pagina')
  dove?.focus({ preventScroll: true })
})

// on a phone the panel covers the agenda: a back closes it, not the page.
// After `showEventPanel`: the watch reads it at once
let togliDaIndietro = null
watch(
  () => panelOpen.value && isMobileView.value,
  (sopra) => {
    togliDaIndietro?.()
    togliDaIndietro = sopra
      ? chiudeConIndietro(() =>
          showEventPanel.value ? close() : closeAppointment(),
        )
      : null
  },
  // the panel may open while the page is made (?new=appointment)
  { immediate: true },
)
onBeforeUnmount(() => togliDaIndietro?.())
const event = ref({})
const mode = ref('')

const isCreateDisabled = computed(
  () =>
    !prenota.value ||
    ['edit', 'new', 'duplicate'].includes(mode.value) ||
    ['edit', 'new'].includes(appointmentPanel.mode),
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
  closeAppointment()
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
      await eventiDelPeriodo()
      toast.success(__('Event created successfully'))
      showDetails({ id: e.name })
    },
    onError: (err) => {
      toast.error(err.messages[0])
      console.error('Failed creating event', err)
    },
  })
}

async function updateEvent(_event) {
  if (!_event.id) return

  _event.fromTime = dayjs(_event.fromTime, 'HH:mm').format('HH:mm')
  _event.toTime = dayjs(_event.toTime, 'HH:mm').format('HH:mm')

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
  // the panel's own copy is the same object for a new event: its colour stays
  // what it will be saved as, and the grid resolves it
  if (target === _event) return
  Object.assign(target, _event, { color: calendarColorName(_event.color) })
}

onMounted(async () => {
  activeEvent.value = ''
  mode.value = ''
  showEventPanel.value = false

  const { eventId, date, appointment } = route.query
  // an appointment the address names, on its day
  if (appointment) openAppointment(appointment)
  // «Book an appointment» on a person: a new appointment, for them - of the
  // cycle's service, from a cycle of sessions. The query stays in the address —
  // the page is keyed on it, and taking it away rebuilds the page without the
  // panel it had just opened.
  if (route.query.new === 'appointment' && prenota.value) {
    openNewAppointment({
      date: date || today(),
      time: nextQuarter(),
      party: route.query.party || undefined,
      service: route.query.service || undefined,
    })
  }
  if (eventId && date) {
    await events.promise
    await nextTick()
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
      action: () => startNew(),
    },
  ],
})

function showDetails(e, reloadEvent = false) {
  const id = (e?.calendarEvent || e)?.id
  if (isAppointmentId(id)) {
    openAppointment(appointmentName(id))
    return
  }
  openEvent(e, 'details', reloadEvent)
}

function editDetails(e) {
  const id = (e?.calendarEvent || e)?.id
  if (isAppointmentId(id)) {
    openAppointment(appointmentName(id), 'edit')
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
    // as the panel saves it: the hex
    color: e.color || NAMED_HEX.green,
    attending: e.attending || 'Yes',
    event_participants: e.event_participants || [],
    notifications: e.notifications || [],
  }
}

function newEvent(e = {}, duplicate = false) {
  closeAppointment()
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
  let now = dayjs(adessoDelCentro())
  let h = now.hour()
  let m = Math.floor(now.minute() / 15) * 15
  let fromHour = h
  let fromMinute = m
  if (time && /^\d{1,2}:?\d{0,2}$/.test(time)) {
    const [hh, mm = '00'] = time.split(':')
    fromHour = parseInt(hh)
    fromMinute = parseInt(mm) || 0
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
