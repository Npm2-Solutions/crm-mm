<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A person's summary: what one needs to know of them at a glance, the page
  they open on from the People list and the agenda - one person, two doors
  (docs/crm/54). From the conversations they open on the chat, and
  this sits beside it (`compatto`). Who they are and their next appointment are
  in the head of the page; this says the rest, each line a tap from the tab
  that holds it: the last thing said, the appointments, what they have going,
  what is left to collect and to do, the forms they owe, the quotes, the deals.
  What the session may not read is not here (crm/persone/riepilogo.py).
-->
<template>
  <div
    class="mx-auto flex w-full flex-col"
    :class="compatto ? 'gap-3' : 'max-w-3xl px-3 pb-6 pt-1 sm:px-7 md:pt-0'"
  >
    <div v-if="!pronto" class="flex justify-center py-10">
      <LoaderMark />
    </div>
    <EmptyState
      v-else-if="!qualcosa"
      :title="__('Nothing to sum up yet')"
      :text="
        __(
          'The next appointment, the last message, what is left to pay and to do: they all show here.',
        )
      "
    />
    <!-- cards side by side where two fit, one under the other where not: a
         column each 20rem wide at least -->
    <div
      v-else
      :class="
        compatto
          ? 'flex flex-col gap-3'
          : '[columns:2_20rem] [column-gap:0.75rem] [&>section]:mb-3'
      "
    >
      <!-- the last thing said: the chat a tap away -->
      <section v-if="messaggio" :class="carta">
        <button type="button" :class="testata" @click="apri('activity')">
          <span>{{ __('Last message') }}</span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <button type="button" :class="riga" @click="apri('activity')">
          <component
            :is="iconaDelCanale(messaggio.canale)"
            class="mt-0.5 size-4 shrink-0 text-ink-gray-6"
          />
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span
              class="line-clamp-2 break-words text-base"
              :class="
                messaggio.daLeggere ? 'text-ink-gray-9' : 'text-ink-gray-7'
              "
            >
              <span v-if="!messaggio.loro" class="text-ink-gray-6">
                {{ __('You') }}:
              </span>
              {{ messaggio.testo || __(messaggio.canale) }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ quandoDelMessaggio(messaggio.quando) }}
            </span>
          </span>
          <Badge
            v-if="messaggio.daLeggere"
            class="shrink-0"
            variant="subtle"
            theme="blue"
            :label="__('Unread')"
          />
        </button>
      </section>

      <!-- the appointments: the next ones, then the last one -->
      <section v-if="vedeLAgenda && (futuri.length || passato)" :class="carta">
        <button type="button" :class="testata" @click="apri('events')">
          <span>{{ __('Appointments') }}</span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <span v-if="futuri.length" :class="gruppo">{{ __('Coming up') }}</span>
        <button
          v-for="a in futuri"
          :key="a.name"
          type="button"
          :class="riga"
          @click="inAgenda(a)"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ quandoInBreve(a.starts_on, lingua, adesso) }}
            </span>
            <span class="break-words text-p-sm text-ink-gray-6">
              {{
                [nomeDellAppuntamento(a, titolo), laSeduta(a.cycle, t)]
                  .filter(Boolean)
                  .join(' · ')
              }}
            </span>
          </span>
        </button>
        <div
          v-if="!futuri.length"
          class="flex flex-wrap items-center justify-between gap-2 px-2 py-1.5"
        >
          <span class="text-p-sm text-ink-gray-6">
            {{ __('Nothing booked') }}
          </span>
          <Button
            v-if="puoPrenotare"
            class="shrink-0"
            icon-left="lucide-calendar-plus"
            :label="__('Book')"
            @click="prenota"
          />
        </div>
        <template v-if="passato">
          <span :class="gruppo">{{ __('Last time') }}</span>
          <button type="button" :class="riga" @click="inAgenda(passato)">
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="break-words text-base text-ink-gray-8">
                {{ nomeDellAppuntamento(passato, titolo) }}
              </span>
              <span class="break-words text-p-sm text-ink-gray-6">
                {{ quandoInBreve(passato.starts_on, lingua, adesso) }}
              </span>
            </span>
            <Badge
              class="shrink-0"
              variant="subtle"
              :theme="TEMA_DELLO_STATO[passato.status] || 'gray'"
              :label="__(passato.status)"
            />
          </button>
        </template>
        <!-- the ones they did not show up to: the desk thinks twice -->
        <button
          v-if="righe.no_shows"
          type="button"
          :class="riga"
          @click="apri('events')"
        >
          <span
            class="lucide-calendar-x size-4 shrink-0 text-ink-red-7"
            aria-hidden="true"
          />
          <span class="min-w-0 flex-1 break-words text-p-sm text-ink-gray-8">
            {{ fraseDelleAssenze(righe.no_shows, (s, v) => __(s, v)) }}
          </span>
        </button>
      </section>

      <!-- what they have going: cycles, subscriptions, a place in the line;
           the first three, the rest on their tab -->
      <section v-if="inCorso.length" :class="carta">
        <button type="button" :class="testata" @click="apri('subscriptions')">
          <span>{{ __('Going on') }}</span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <button
          v-for="voce in inCorso.slice(0, QUANTI)"
          :key="voce.chiave"
          type="button"
          :class="riga"
          @click="apri('subscriptions')"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ voce.titolo }}
            </span>
            <span class="break-words text-p-sm text-ink-gray-6">
              {{ voce.riga }}
            </span>
          </span>
          <Badge
            v-if="voce.badge"
            class="shrink-0"
            variant="subtle"
            :theme="voce.badge.theme"
            :label="voce.badge.label"
          />
        </button>
        <button
          v-if="inCorso.length > QUANTI"
          type="button"
          :class="[riga, 'text-p-sm text-ink-gray-6']"
          @click="apri('subscriptions')"
        >
          <span class="inline-block first-letter:uppercase">
            {{ __('{0} more', [inCorso.length - QUANTI]) }}
          </span>
        </button>
      </section>

      <!-- the funds and conventions that cover them today (doc 61): who
           pays, before the desk asks -->
      <section v-if="righe.covers" :class="carta">
        <div :class="[testata, 'cursor-default hover:bg-transparent']">
          <span>{{ __('Funds and conventions') }}</span>
        </div>
        <div
          v-for="(copertura, i) in righe.covers.covers"
          :key="i"
          :class="[riga, 'cursor-default hover:bg-transparent']"
        >
          <span
            class="lucide-shield-check mt-0.5 size-4 shrink-0 text-ink-green-7"
            aria-hidden="true"
          />
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ copertura.convention_name }}
            </span>
            <span class="break-words text-p-sm text-ink-gray-6">
              {{
                [
                  nomeDelTipo(copertura.kind, t),
                  rigaDellaCopertura(copertura, t, (g) =>
                    formatDate(g, 'D MMM YYYY'),
                  ),
                ]
                  .filter(Boolean)
                  .join(' · ')
              }}
            </span>
          </span>
        </div>
      </section>

      <!-- what is left to collect: the invoices issued, the drafts -->
      <section v-if="righe.to_collect" :class="carta">
        <div :class="[testata, 'cursor-default hover:bg-transparent']">
          <span>{{ __('To collect') }}</span>
          <span
            v-if="righe.to_collect.count"
            class="tabular-nums text-ink-gray-9"
          >
            {{ soldi(righe.to_collect.total, righe.to_collect.currency) }}
          </span>
        </div>
        <button
          v-for="fattura in righe.to_collect.invoices"
          :key="fattura.name"
          type="button"
          :class="riga"
          @click="apriFattura(fattura.name, { alCambio: ricarica })"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ fattura.document_number || __('Invoice') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ formatDate(fattura.posting_date, 'D MMM YYYY') }}
            </span>
            <span
              v-if="fattura.reminders?.count"
              class="text-p-sm text-ink-gray-6"
            >
              {{
                fraseDeiSolleciti(
                  fattura.reminders,
                  (testo, valori) => __(testo, valori),
                  (giorno) => formatDate(giorno, 'D MMM YYYY'),
                )
              }}
            </span>
          </span>
          <span class="shrink-0 text-base tabular-nums text-ink-gray-8">
            {{ soldi(fattura.amount, righe.to_collect.currency) }}
          </span>
        </button>
        <button
          v-if="righe.to_collect.drafts"
          type="button"
          :class="riga"
          @click="apriFattura(righe.to_collect.draft, { alCambio: ricarica })"
        >
          <span class="flex-1 text-base text-ink-gray-8">
            {{
              righe.to_collect.drafts === 1
                ? __('1 draft to issue')
                : __('{0} drafts to issue', [righe.to_collect.drafts])
            }}
          </span>
        </button>
      </section>

      <!-- what is left to do, the ones due first -->
      <section v-if="righe.tasks" :class="carta">
        <button type="button" :class="testata" @click="apri('tasks')">
          <span>
            {{ __('Tasks') }}
            <span class="tabular-nums text-ink-gray-5">
              {{ righe.tasks.count }}
            </span>
          </span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <button
          v-for="compito in righe.tasks.tasks"
          :key="compito.name"
          type="button"
          :class="riga"
          @click="apri('tasks')"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ compito.title }}
            </span>
            <span
              v-if="compito.due_date"
              class="text-p-sm"
              :class="
                scadenza(compito.due_date, oggi) === 'late'
                  ? 'text-ink-red-7'
                  : 'text-ink-gray-6'
              "
            >
              {{ quandoScade(compito.due_date) }}
            </span>
          </span>
        </button>
      </section>

      <!-- the forms they owe, for their next appointment or in general -->
      <section v-if="righe.forms_due" :class="carta">
        <button type="button" :class="testata" @click="apri('forms')">
          <span>{{ __('Forms') }}</span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <span :class="gruppo">
          {{
            righe.forms_due.appointment
              ? __('To sign for the appointment of {0}', [
                  formatDate(
                    righe.forms_due.appointment.starts_on,
                    'D MMM, HH:mm',
                  ),
                ])
              : __('To sign')
          }}
        </span>
        <button
          v-for="modulo in righe.forms_due.forms"
          :key="modulo.template"
          type="button"
          :class="riga"
          @click="apri('forms')"
        >
          <span class="min-w-0 flex-1 break-words text-base text-ink-gray-8">
            {{ modulo.title }}
          </span>
          <Badge
            v-if="IN_CORSO[modulo.pending]"
            class="shrink-0"
            variant="subtle"
            theme="blue"
            :label="IN_CORSO[modulo.pending]()"
          />
        </button>
      </section>

      <!-- the quotes waiting for an answer, and the ones going on -->
      <section v-if="righe.quotes" :class="carta">
        <button type="button" :class="testata" @click="apri('quotes')">
          <span>{{ __('Quotes') }}</span>
          <span class="lucide-chevron-right size-4 text-ink-gray-5" />
        </button>
        <button
          v-for="preventivo in righe.quotes.quotes"
          :key="preventivo.name"
          type="button"
          :class="riga"
          @click="apri('quotes')"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ preventivo.title }}
            </span>
            <span class="break-words text-p-sm text-ink-gray-6">
              {{ soldi(preventivo.total_net, preventivo.currency) }} ·
              {{
                __('{0} of {1} services done', [
                  preventivo.done,
                  preventivo.services,
                ])
              }}
            </span>
          </span>
          <Badge
            class="shrink-0"
            variant="subtle"
            :theme="STATO_PREVENTIVO[preventivo.status] || 'gray'"
            :label="__(preventivo.status, null, 'Quote')"
          />
        </button>
      </section>

      <!-- the deals still open, each at its stage -->
      <section v-if="righe.deals" :class="carta">
        <div :class="[testata, 'cursor-default hover:bg-transparent']">
          <span>{{ __('Deals') }}</span>
        </div>
        <router-link
          v-for="trattativa in righe.deals.deals"
          :key="trattativa.name"
          :to="{ name: 'Deal', params: { dealId: trattativa.name } }"
          :class="riga"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="break-words text-base text-ink-gray-8">
              {{ __(trattativa.status) }}
            </span>
            <span
              v-if="trattativa.pipeline"
              class="break-words text-p-sm text-ink-gray-6"
            >
              {{ __(trattativa.pipeline) }}
            </span>
          </span>
          <span
            v-if="trattativa.deal_value"
            class="shrink-0 text-base tabular-nums text-ink-gray-8"
          >
            {{ soldi(trattativa.deal_value, trattativa.currency) }}
          </span>
        </router-link>
      </section>
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import { useSchedulerMeta } from '@/composables/scheduling'
import { useFattura } from '@/composables/fattura'
import { fraseDeiSolleciti } from '@/utils/fattura'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { appLocale } from '@/utils/locale'
import { listTime } from '@/utils/conversation'
import { comeVa, daPrenotare, laSeduta } from '@/utils/cicli'
import {
  TEMA_DELLO_STATO as TEMA_ABBONAMENTO,
  questoPeriodo,
} from '@/utils/abbonamenti'
import { APERTE, STATO as STATO_ATTESA, quandoPuo } from '@/utils/attese'
import { STATO as STATO_PREVENTIVO } from '@/utils/preventivi'
import {
  TEMA_DELLO_STATO,
  fraseDelleAssenze,
  prossimi,
  qualcosaDaDire,
  scadenza,
  ultimo,
  ultimoMessaggio,
} from '@/utils/riepilogo'
import { nomeDellAppuntamento, quandoInBreve } from '@/utils/schedaPersona'
import { adessoDelCentro, oggiDelCentro } from '@/utils/scheduler'
import {
  Badge,
  Button,
  createResource,
  dayjsLocal,
  getCachedResource,
} from 'frappe-ui'
import { nomeDelTipo, rigaDellaCopertura } from '@/utils/convenzioni'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: String, required: true },
  // the person as the page holds them: their name, the last thing said
  persona: { type: Object, default: () => ({}) },
  // beside the conversation: the chat is there already, and the column narrow
  compatto: { type: Boolean, default: false },
})

// the tab to open: its name, lowercase, as the address names it
const emit = defineEmits(['apri'])

const router = useRouter()
const { puo } = usersStore()
const { apriFattura } = useFattura()
const scheduling = useSchedulerMeta()

const lingua = appLocale() || 'it-IT'
const t = (text, args, context) => __(text, args, context)
// the agenda keeps the centre's clock: now and today are the centre's
const adesso = adessoDelCentro()
const oggi = oggiDelCentro()

const carta =
  'flex break-inside-avoid flex-col gap-0.5 rounded-lg border border-outline-gray-2 p-2'
const testata =
  'flex min-h-9 w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-base-semibold text-ink-gray-8 hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none'
const riga =
  'flex w-full items-start gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none'
const gruppo = 'px-2 pt-1 text-p-sm font-medium text-ink-gray-5'

// What the modules have for this person, in one call. Asked again each time
// the tab opens: what was decided on another tab shows on coming back.
const riepilogo = createResource({
  url: 'crm.persone.riepilogo.get_summary',
  params: { lead: props.lead },
  cache: ['person-summary', props.lead],
  auto: true,
})

function ricarica() {
  riepilogo.reload()
}

const righe = computed(() => riepilogo.data || {})

// The appointments the head of the page asked for already: the same resource,
// never a second request. Made here where there is no head (the conversations'
// side), and left to fetch once: a resource made with `auto` is asked again by
// every component that makes it after.
const vedeLAgenda = puo('agenda.vedi')
const chiave = ['person-appointments', props.lead]
const appuntamenti = vedeLAgenda
  ? getCachedResource(chiave) ||
    createResource({
      url: 'crm.api.appointments.get_person_appointments',
      params: { doctype: 'CRM Lead', name: props.lead },
      cache: chiave,
    })
  : null
if (appuntamenti && !appuntamenti.data && !appuntamenti.loading)
  appuntamenti.fetch()

const futuri = computed(() => prossimi(appuntamenti?.data, adesso))
const passato = computed(() => ultimo(appuntamenti?.data, adesso))

const titolo = computed(
  () =>
    props.persona?.lead_name ||
    [props.persona?.first_name, props.persona?.last_name]
      .filter(Boolean)
      .join(' '),
)

// the last thing said, for whoever reads the person's conversations; beside
// the conversation itself it would only say it twice
const messaggio = computed(() =>
  props.compatto || !puo('conversazioni.vedi')
    ? null
    : ultimoMessaggio(props.persona),
)

const pronto = computed(
  () => riepilogo.data !== null && riepilogo.data !== undefined,
)
const qualcosa = computed(() =>
  qualcosaDaDire({
    messaggio: messaggio.value,
    appuntamenti: vedeLAgenda ? futuri.value : [],
    ultimoAppuntamento: vedeLAgenda ? passato.value : null,
    righe: righe.value,
  }),
)

const ICONE = { WhatsApp: WhatsAppIcon, SMS: SMSIcon, Email: Email2Icon }
function iconaDelCanale(canale) {
  return ICONE[canale] || DotIcon
}

// as the conversations list says it: the clock today, «Ieri», the weekday
function quandoDelMessaggio(quando) {
  return listTime(
    dayjsLocal(quando).format('YYYY-MM-DD HH:mm:ss'),
    dayjsLocal().format('YYYY-MM-DD HH:mm:ss'),
    lingua,
  )
}

function soldi(importo, valuta) {
  return new Intl.NumberFormat(lingua, {
    style: 'currency',
    currency: valuta || 'EUR',
  }).format(importo || 0)
}

function quandoScade(dueDate) {
  const quando = scadenza(dueDate, oggi)
  const giorno = formatDate(dueDate, 'D MMM')
  if (quando === 'late') return __('Late since {0}', [giorno])
  if (quando === 'today') return __('Due today')
  return __('Due by {0}', [giorno])
}

function rigaDelCiclo(ciclo) {
  const parti = [comeVa(ciclo.counts, t)]
  if (ciclo.next)
    parti.push(
      __('Next session {0}', [formatDate(ciclo.next, 'ddd D MMM, HH:mm')]),
    )
  else if (ciclo.counts?.left) parti.push(daPrenotare(ciclo.counts, t))
  return parti.filter(Boolean).join(' · ')
}

function rigaDellAbbonamento(sub) {
  const parti = []
  const periodo = questoPeriodo(sub, t)
  if (periodo) parti.push(periodo)
  if (sub.suspended_until)
    parti.push(
      __('suspended until {0}', [formatDate(sub.suspended_until, 'D MMM')]),
    )
  parti.push(__('until {0}', [formatDate(sub.ends_on, 'D MMM YYYY')]))
  return parti.join(' · ')
}

// how many lines of a kind the summary names, the rest on their tab
const QUANTI = 3

// cycles, subscriptions, places in the line: one list, each a line of words
const inCorso = computed(() => {
  const dati = righe.value.in_progress || {}
  return [
    ...(dati.cycles || []).map((ciclo) => ({
      chiave: ciclo.name,
      titolo: ciclo.service,
      riga: rigaDelCiclo(ciclo),
      badge: null,
    })),
    ...(dati.subscriptions || []).map((sub) => ({
      chiave: sub.name,
      titolo: sub.subscription_type,
      riga: rigaDellAbbonamento(sub),
      badge:
        sub.status === 'Active'
          ? null
          : {
              theme: TEMA_ABBONAMENTO[sub.status] || 'gray',
              label: __(sub.status),
            },
    })),
    ...(dati.waiting || []).map((voce) => ({
      chiave: voce.name,
      titolo: voce.service_name,
      riga: rigaDellAttesa(voce),
      badge: {
        theme: STATO_ATTESA[voce.status]?.theme || 'gray',
        label: __(STATO_ATTESA[voce.status]?.label || voce.status),
      },
    })),
  ]
})

function rigaDellAttesa(voce) {
  const parti = [
    voce.class_session
      ? __('A seat in the class of {0}', [
          formatDate(voce.class_starts_on, 'ddd D MMM, HH:mm'),
        ])
      : quandoPuo(voce, t, lingua),
  ]
  if (voce.staff_name) parti.push(voce.staff_name)
  if (voce.until && APERTE.includes(voce.status))
    parti.push(__('until {0}', [formatDate(voce.until, 'D MMM')]))
  return parti.filter(Boolean).join(' · ')
}

// a form under way, as the Forms tab says it
const IN_CORSO = {
  draft: () => __('Started', null, 'Form filled half-way'),
  sent: () => __('Link sent'),
  to_sign_at_desk: () => __('To sign at the desk'),
}

const puoPrenotare = computed(
  () => puo('agenda.prenota') && (scheduling.data?.services || []).length > 0,
)

function prenota() {
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: props.lead },
  })
}

// on the agenda, open: where it can be moved, changed or cancelled
function inAgenda(appuntamento) {
  router.push({
    name: 'Calendar',
    query: {
      appointment: appuntamento.name,
      date: String(appuntamento.starts_on).slice(0, 10),
    },
  })
}

function apri(scheda) {
  emit('apri', scheda)
}

defineExpose({ reload: ricarica })
</script>
