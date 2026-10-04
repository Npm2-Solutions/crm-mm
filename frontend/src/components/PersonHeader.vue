<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The head of a person's page, the same on the computer and on the phone: who
  they are, what comes next with them, and the five things one does with a
  person all day - call, WhatsApp, SMS, email, book - as the phone's own contact
  card has them. Calling is there whenever the person has a number: through the
  centre's telephony when it is on (the centre's number shown, the call logged),
  through the device's own dialer on a phone or where there is no telephony.
-->
<template>
  <!-- data-testata-persona, data-volto, data-prossimo: a phone held sideways
       lays the card out in one row (telefono.css) -->
  <div class="flex flex-col gap-4" data-testata-persona>
    <div class="flex items-center gap-4">
      <span class="contents" data-volto><slot name="avatar" /></span>
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <Tooltip :text="title">
          <h1
            class="truncate text-xl-semibold text-ink-gray-9 [overflow-wrap:anywhere]"
          >
            {{ title }}
          </h1>
        </Tooltip>
        <!-- every fact after its dot, the row pulled left by one dot: the dot
             of a fact that starts a line falls outside, so a line never opens
             on «·» («Paziente dal 4 ott» above «· Ultima visita») -->
        <div
          v-if="fatti.length"
          class="overflow-hidden text-p-sm text-ink-gray-6"
        >
          <div class="-ml-4 flex flex-wrap gap-y-0.5">
            <span v-for="(fatto, i) in fatti" :key="i" class="flex">
              <span aria-hidden="true" class="w-4 shrink-0 text-center">·</span>
              <span>{{ fatto }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- what comes next: one line, its day on the agenda a tap away -->
    <router-link
      v-if="prossimo"
      data-prossimo
      :to="{
        name: 'Calendar',
        query: {
          appointment: prossimo.name,
          date: String(prossimo.starts_on).slice(0, 10),
        },
      }"
      class="flex min-w-0 items-center gap-2.5 rounded-md bg-[var(--brand-subtle)] px-3 py-2 text-[var(--on-brand-subtle)] hover:bg-[var(--brand-subtle-hover)]"
    >
      <span class="lucide-calendar-clock size-4 shrink-0" aria-hidden="true" />
      <span class="flex min-w-0 flex-col">
        <span class="text-xs">{{ __('Next appointment') }}</span>
        <span class="truncate text-sm font-medium">
          {{
            [
              quandoInBreve(prossimo.starts_on, lingua),
              titoloSenzaPersona(prossimo.title, title),
            ]
              .filter(Boolean)
              .join(' · ')
          }}
        </span>
      </span>
    </router-link>

    <!-- the actions, as round keys with their word under them -->
    <div
      class="grid gap-1"
      :class="puoPrenotare ? 'grid-cols-6' : 'grid-cols-5'"
      role="toolbar"
      :aria-label="title"
    >
      <template v-if="!soloMascherati">
        <Dropdown v-if="modi.length > 1" :options="opzioniChiamata">
          <template #default>
            <button type="button" :class="tasto" :aria-label="__('Call')">
              <span :class="[tondo, primario]">
                <PhoneIcon class="size-[18px]" />
              </span>
              <span class="truncate">{{ __('Call') }}</span>
            </button>
          </template>
        </Dropdown>
        <button
          v-else
          type="button"
          :class="tasto"
          :disabled="!modi.length"
          :title="modi.length ? modi[0].numero : __('No phone number yet')"
          @click="chiama(modi[0])"
        >
          <span :class="[tondo, modi.length ? primario : spento]">
            <PhoneIcon class="size-[18px]" />
          </span>
          <span class="truncate">{{ __('Call') }}</span>
        </button>
      </template>

      <button
        v-if="whatsappEnabled && scrive"
        type="button"
        :class="tasto"
        :disabled="!numeri.length"
        @click="emit('write', 'whatsapp')"
      >
        <span :class="[tondo, numeri.length ? normale : spento]">
          <WhatsAppIcon class="size-[18px]" />
        </span>
        <span class="truncate">WhatsApp</span>
      </button>

      <button
        v-if="smsEnabled && scrive"
        type="button"
        :class="tasto"
        :disabled="!numeri.length"
        @click="emit('write', 'sms')"
      >
        <span :class="[tondo, numeri.length ? normale : spento]">
          <SMSIcon class="size-[18px]" />
        </span>
        <span class="truncate">SMS</span>
      </button>

      <button
        v-if="scrive"
        type="button"
        :class="tasto"
        :disabled="!doc.email"
        :title="doc.email || __('No email address yet')"
        @click="emit('write', 'email')"
      >
        <span :class="[tondo, doc.email ? normale : spento]">
          <Email2Icon class="size-[18px]" />
        </span>
        <span class="truncate">{{ __('Email') }}</span>
      </button>

      <button v-if="puoPrenotare" type="button" :class="tasto" @click="prenota">
        <span :class="[tondo, normale]">
          <span class="lucide-calendar-plus size-[18px]" aria-hidden="true" />
        </span>
        <span class="truncate">{{ __('Book') }}</span>
      </button>

      <Dropdown v-if="altro.length" :options="altro">
        <template #default>
          <button type="button" :class="tasto" :aria-label="__('More')">
            <span :class="[tondo, normale]">
              <span class="lucide-ellipsis size-[18px]" aria-hidden="true" />
            </span>
            <span class="truncate">{{ __('More') }}</span>
          </button>
        </template>
      </Dropdown>
    </div>
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import { callEnabled } from '@/composables/telephony'
import { whatsappEnabled } from '@/composables/whatsapp'
import { smsEnabled } from '@/composables/sms'
import { useSchedulerMeta } from '@/composables/scheduling'
import { isMobileView } from '@/composables/breakpoints'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import {
  giornoInBreve,
  indirizzoTel,
  mascherato,
  modiDiChiamare,
  numeriDi,
  prossimoAppuntamento,
  quandoInBreve,
  titoloSenzaPersona,
} from '@/utils/schedaPersona'
import { Dropdown, Tooltip, createResource } from 'frappe-ui'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doc: { type: Object, required: true },
  title: { type: String, default: '' },
  // the More menu, as the page builds it: website, attach, delete…
  more: { type: Array, default: () => [] },
})

const emit = defineEmits(['write'])

const router = useRouter()
const { makeCall } = globalStore()
const { puo } = usersStore()
const scheduling = useSchedulerMeta()

const lingua = window.navigator?.language || 'it-IT'

// a round key and its word: what the phone's own contact card looks like
const tasto =
  'touch-target group flex min-w-0 flex-col items-center gap-1.5 rounded-md px-0.5 py-1 text-xs font-medium text-ink-gray-7 outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 disabled:cursor-not-allowed'
const tondo =
  'grid size-10 place-items-center rounded-full transition-colors [border-bottom-left-radius:6px]'
const primario =
  'bg-[var(--brand-action)] text-[var(--on-brand-solid)] group-hover:bg-[var(--brand-action-hover)]'
const normale =
  'bg-surface-gray-2 text-ink-gray-8 group-hover:bg-surface-gray-3'
const spento = 'bg-surface-gray-1 text-ink-gray-5'

// writing to somebody is the composer's, and the level's (doc 30)
const scrive = computed(() => puo('conversazioni.usa'))

const numeri = computed(() => numeriDi(props.doc))

// a number reaches whoever sees people masked (Marketing) as «+39XXXXXX»: it is
// no number to call, and «No phone number yet» would not be true either, so
// there is no key at all
const soloMascherati = computed(
  () =>
    !numeri.value.length &&
    ['mobile_no', 'phone'].some((campo) => mascherato(props.doc?.[campo])),
)

// the centre's telephony, for whoever may call with it
const telefonia = computed(() => callEnabled.value && puo('telefono.chiama'))

const modi = computed(() =>
  modiDiChiamare(numeri.value, {
    telefonia: telefonia.value,
    telefono: isMobileView.value,
  }),
)

function chiama(modo) {
  if (!modo) return
  if (modo.via === 'centro') makeCall(modo.numero)
  else window.location.href = indirizzoTel(modo.numero)
}

const opzioniChiamata = computed(() =>
  modi.value.map((modo) => ({
    label:
      modo.via === 'centro'
        ? __('{0} · with {brand}', [modo.numero])
        : __('{0} · from your phone', [modo.numero]),
    icon: modo.via === 'centro' ? 'phone' : 'smartphone',
    onClick: () => chiama(modo),
  })),
)

// booking starts from the person as often as from the agenda: the agenda
// opens with a new appointment for them, where the free times are
const puoPrenotare = computed(
  () => puo('agenda.prenota') && (scheduling.data?.services || []).length > 0,
)

function prenota() {
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: props.doc.name },
  })
}

const appuntamenti = createResource({
  url: 'crm.api.appointments.get_person_appointments',
  params: { doctype: 'CRM Lead', name: props.doc.name },
  cache: ['person-appointments', props.doc.name],
  auto: puo('agenda.vedi'),
})

const prossimo = computed(() => prossimoAppuntamento(appuntamenti.data))

// who they are to the centre, in a few words: client since, last visit
const fatti = computed(() => {
  const fatti = []
  if (props.doc.client_since)
    fatti.push(
      __('Client since {0}', [giornoInBreve(props.doc.client_since, lingua)]),
    )
  if (props.doc.last_visit)
    fatti.push(
      __('Last visit {0}', [giornoInBreve(props.doc.last_visit, lingua)]),
    )
  return fatti
})

const altro = computed(() => props.more.filter(Boolean))

defineExpose({ reload: () => appuntamenti.reload() })
</script>
