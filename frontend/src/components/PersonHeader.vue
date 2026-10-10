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
              <!-- the first says who they are to the centre: it is read first -->
              <span :class="i === 0 && 'font-medium text-ink-gray-8'">{{
                fatto
              }}</span>
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
        <!-- on two lines when it must: at 360px the service was
             «Massaggio decontrattura…» -->
        <span class="break-words text-sm font-medium">
          {{
            [
              quandoInBreve(prossimo.starts_on, lingua),
              nomeDellAppuntamento(prossimo, title),
            ]
              .filter(Boolean)
              .join(' · ')
          }}
        </span>
      </span>
    </router-link>

    <!-- the actions, as round keys with their word under them: a column for
         each key drawn. Six columns for five keys (no SMS) left each word
         a column narrower than itself, «Chiama» touching «WhatsApp». The
         columns are equal while each word fits; a word that would not
         («WhatsA…» at 320 points, a page zoomed, or six keys on an iPhone
         SE) takes the few points it needs from the others -->
    <div
      class="grid gap-0.5"
      :style="{
        gridTemplateColumns: `repeat(${tasti}, minmax(min-content, 1fr))`,
      }"
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
              <span class="max-w-full truncate">{{ __('Call') }}</span>
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
          <span class="max-w-full truncate">{{ __('Call') }}</span>
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
        <span class="max-w-full truncate">WhatsApp</span>
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
        <span class="max-w-full truncate">SMS</span>
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
        <span class="max-w-full truncate">{{ __('Email') }}</span>
      </button>

      <button v-if="puoPrenotare" type="button" :class="tasto" @click="prenota">
        <span :class="[tondo, normale]">
          <span class="lucide-calendar-plus size-[18px]" aria-hidden="true" />
        </span>
        <span class="max-w-full truncate">{{ __('Book') }}</span>
      </button>

      <Dropdown v-if="altro.length" :options="altro">
        <template #default>
          <button type="button" :class="tasto" :aria-label="__('More')">
            <span :class="[tondo, normale]">
              <span class="lucide-ellipsis size-[18px]" aria-hidden="true" />
            </span>
            <span class="max-w-full truncate">{{ __('More') }}</span>
          </button>
        </template>
      </Dropdown>
    </div>
  </div>
</template>

<script setup>
import { appLocale } from '@/utils/locale'
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
  etaENascita,
  modiDiChiamare,
  nomeDellAppuntamento,
  numeriDi,
  prossimoAppuntamento,
  quandoInBreve,
} from '@/utils/schedaPersona'
import { adessoDelCentro } from '@/utils/scheduler'
import { CONTESTO, fattoDel } from '@/utils/rapporto'
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

// the user's language, the European way (utils/locale.js)
const lingua = appLocale() || 'it-IT'

// a round key and its word: what the phone's own contact card looks like.
// No padding beside the word, and 2px between the keys: in a side panel 352px
// wide «WhatsApp» needs the whole of its column (60px, one more than it had)
const tasto =
  'touch-target group flex min-w-0 flex-col items-center gap-1.5 rounded-md py-1 text-xs font-medium text-ink-gray-7 outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 disabled:cursor-not-allowed'
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

// the agenda keeps the centre's clock: now is the centre's, not the phone's
const prossimo = computed(() =>
  prossimoAppuntamento(appuntamenti.data, adessoDelCentro()),
)

// how old they are and when they were born: after the name, what tells one
// patient from another with the same name (NISTIR 7804), on every tab. From
// the billing details the page reads anyway (the codice fiscale's date), for
// whoever may read them: the others see what they saw before. Never kept in
// the browser (no `cache`): a cached resource lands in IndexedDB, which no
// logout clears, and a colleague without the fiscal details at the same
// reception PC was shown the last reader's copy
const fiscali = puo('persone.dati_fiscali')
const anagrafica = createResource({
  url: 'crm.invoicing.anagrafica.get_billing_profile',
  params: { party_type: 'CRM Lead', party: props.doc.name },
  auto: fiscali,
  onError: () => anagrafica.setData(null),
})
const eta = computed(() =>
  fiscali
    ? etaENascita(anagrafica.data?.birth_date, adessoDelCentro(), lingua)
    : null,
)

// who they are to the centre, in a few words: a contact, a client since, a
// patient since (utils/rapporto.js); their age; the last visit
const fatti = computed(() => {
  const fatti = []
  const { frase, data } = fattoDel(props.doc)
  fatti.push(
    data ? __(frase, [giornoInBreve(data, lingua)]) : __(frase, null, CONTESTO),
  )
  if (eta.value)
    fatti.push(
      eta.value.anni < 1
        ? __('Under a year · {0}', [eta.value.nascita])
        : __('{0} years · {1}', [eta.value.anni, eta.value.nascita]),
    )
  if (props.doc.last_visit)
    fatti.push(
      __('Last visit {0}', [giornoInBreve(props.doc.last_visit, lingua)]),
    )
  return fatti
})

const altro = computed(() => props.more.filter(Boolean))

// how many keys the row draws, as the template decides each one
const tasti = computed(
  () =>
    [
      !soloMascherati.value,
      whatsappEnabled.value && scrive.value,
      smsEnabled.value && scrive.value,
      scrive.value,
      puoPrenotare.value,
      altro.value.length > 0,
    ].filter(Boolean).length || 1,
)

defineExpose({ reload: () => appuntamenti.reload() })
</script>
