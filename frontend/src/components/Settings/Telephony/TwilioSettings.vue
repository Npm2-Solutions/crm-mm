<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  Settings > Phone > Telephony > Twilio (doc 52).

  The centre connects its own Twilio account with the two codes of the console's
  first page, once: DottorCloud makes its own space in the account and keeps only
  that space's keys. Calls and messages are paid to Twilio by the centre; the rest
  is done here. The agency may connect its own account instead, for a centre with
  its front desk. What the centre decides on calls (recording) stays below.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Twilio')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="stato"
          :label="
            stato.connected
              ? __('Connected', null, 'Twilio')
              : __('Not connected', null, 'Twilio')
          "
          variant="subtle"
          :theme="stato.connected ? 'green' : 'gray'"
        />
        <Badge
          v-if="stato?.connected && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="stato?.connected && isDirty" class="flex gap-2">
        <Button
          :label="__('Discard Changes')"
          variant="subtle"
          @click="twilio.reload()"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="twilio.save.loading"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="connessione.loading && !stato"
        class="mt-[35%] flex items-center justify-center"
      >
        <LoadingIndicator class="size-6" />
      </div>

      <!-- not connected: three steps, two codes -->
      <div v-else-if="stato && !stato.connected" class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Calls and messages go through your own Twilio account: you pay Twilio, at Twilio's prices. Everything else you do here in {brand}.",
            )
          }}
        </p>

        <ol class="flex flex-col gap-3">
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >1</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <span class="text-p-base text-ink-gray-8">
                {{
                  __(
                    'Create your account on Twilio, if you have none, and upgrade it with a payment method.',
                  )
                }}
              </span>
              <a
                :href="TWILIO.registrazione"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ __('Open Twilio') }}
                <span class="lucide-external-link size-3.5" />
              </a>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >2</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <span class="text-p-base text-ink-gray-8">
                {{
                  __(
                    'On the first page of the Twilio console, copy the Account SID and the Auth Token.',
                  )
                }}
              </span>
              <a
                :href="TWILIO.console"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ __('Open the console') }}
                <span class="lucide-external-link size-3.5" />
              </a>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >3</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-3">
              <span class="text-p-base text-ink-gray-8">
                {{ __('Paste them here and connect.') }}
              </span>
              <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
                <FormControl
                  v-model="codici.account_sid"
                  :label="__('Account SID', null, 'Twilio console')"
                  type="text"
                  placeholder="AC…"
                  autocomplete="off"
                />
                <Password
                  v-model="codici.auth_token"
                  :label="__('Auth Token', null, 'Twilio console')"
                  placeholder="••••••••"
                />
              </div>
              <ErrorMessage :message="errore" />
              <div class="flex flex-wrap items-center gap-2">
                <Button
                  variant="solid"
                  :label="__('Connect')"
                  :loading="collega.loading"
                  @click="connetti"
                />
              </div>
            </div>
          </li>
        </ol>

        <div
          class="rounded-lg border border-outline-gray-2 px-4 py-3 text-p-sm text-ink-gray-6"
        >
          {{
            __(
              'The token is used only now. {brand} makes its own space in your account, with its own keys, and keeps only those: it neither reads nor touches the rest of your account.',
            )
          }}
        </div>

        <div
          v-if="stato.agency_account"
          class="flex items-center justify-between gap-4 border-t border-outline-elevation-2 pt-4 max-md:flex-col max-md:items-start"
        >
          <div class="flex min-w-0 flex-col gap-1">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __("The agency's account") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "For a centre with the agency's front desk: the space lives in the agency's account, and the agency pays.",
                )
              }}
            </span>
          </div>
          <Button
            class="shrink-0"
            :label="__('Use the agency\'s account')"
            :loading="collegaAgenzia.loading"
            @click="connettiAgenzia"
          />
        </div>
      </div>

      <!-- connected: whose account, which space, and what Check found -->
      <div v-else-if="stato" class="flex flex-col gap-4">
        <div
          class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="riga in righe"
            :key="riga.label"
            class="flex items-start justify-between gap-4 px-4 py-2.5 max-md:flex-col max-md:gap-0.5"
          >
            <span class="shrink-0 text-p-sm text-ink-gray-6">
              {{ riga.label }}
            </span>
            <span
              class="min-w-0 text-right text-p-sm text-ink-gray-8 max-md:text-left"
            >
              {{ riga.value }}
            </span>
          </div>
        </div>

        <div v-if="controllo" class="flex flex-col gap-1">
          <p v-if="!controllo.ok" class="text-p-sm text-ink-red-8">
            {{ controllo.error }}
          </p>
          <template v-else>
            <p class="text-p-sm text-ink-gray-8">
              {{ statoDelContoInParole }}
            </p>
            <p v-if="controllo.note" class="text-p-sm text-ink-amber-8">
              {{ controllo.note }}
            </p>
            <p
              v-for="riga in righeDelControllo(controllo)"
              :key="riga[0]"
              class="text-p-sm text-ink-gray-6"
            >
              {{ __(riga[0], [riga[1]]) }}
            </p>
          </template>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            :label="__('Check')"
            icon-left="lucide-refresh-cw"
            :loading="controlla.loading"
            @click="controlla.submit()"
          />
          <Button
            :label="__('Open Twilio')"
            icon-left="lucide-external-link"
            @click="apri(TWILIO.console)"
          />
          <Button
            v-if="stato.may_change"
            :label="__('Disconnect')"
            theme="red"
            variant="subtle"
            :loading="scollega.loading"
            @click="chiediDiScollegare"
          />
        </div>

        <div class="h-px border-t border-outline-elevation-2" />

        <div class="flex items-center justify-between gap-4">
          <div class="flex min-w-0 flex-col">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Numbers') }}
            </div>
            <div
              class="text-p-sm"
              :class="stato.not_reaching ? 'text-ink-red-8' : 'text-ink-gray-5'"
            >
              {{ numeriInParole }}
            </div>
          </div>
          <Button
            class="shrink-0"
            :label="__('Manage')"
            @click="emit('updateStep', 'caller-id-settings')"
          />
        </div>

        <template v-if="twilio.doc">
          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between gap-4">
            <div class="flex min-w-0 flex-col">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Record Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  __('Enable call recording for incoming and outgoing calls')
                }}
              </div>
            </div>
            <Switch v-model="twilio.doc.record_calls" size="sm" />
          </div>

          <div v-if="twilio.doc.record_calls" class="pt-1">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Recording Notice') }}
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Spoken to the other party before they are connected. Empty means no announcement — check what your jurisdiction requires.',
                )
              }}
            </div>
            <FormControl
              v-model="twilio.doc.recording_notice"
              type="textarea"
              rows="2"
              class="mt-2"
              :placeholder="
                __('This call may be recorded for quality purposes.')
              "
            />
          </div>
        </template>

        <template v-if="stato.agency">
          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between gap-4">
            <div class="flex min-w-0 flex-col">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('SIP Trunking') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  trunks.length
                    ? __('{0} elastic SIP trunk(s) on this account', [
                        trunks.length,
                      ])
                    : __(
                        'Read the Elastic SIP trunks configured on this account.',
                      )
                }}
              </div>
            </div>
            <Button
              class="shrink-0"
              :label="__('Refresh')"
              icon-left="lucide-refresh-cw"
              :loading="twilio.fetchSipTrunks?.loading"
              @click="twilio.fetchSipTrunks.fetch"
            />
          </div>

          <div
            v-for="trunk in trunks"
            :key="trunk.sid"
            class="rounded-md border border-outline-gray-2 px-3 py-2"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-p-base-medium text-ink-gray-8">
                {{ trunk.friendly_name || trunk.sid }}
              </span>
              <div class="flex shrink-0 gap-1">
                <Badge
                  v-if="trunk.secure"
                  :label="__('Secure')"
                  variant="subtle"
                  theme="green"
                />
                <Badge
                  :label="
                    __('{0} number(s)', [trunk.phone_numbers?.length || 0])
                  "
                  variant="subtle"
                  theme="gray"
                />
              </div>
            </div>
            <div class="mt-1 text-p-sm text-ink-gray-6">
              {{ __('Termination') }}:
              <code class="text-ink-gray-8">{{
                trunk.termination_uri || '—'
              }}</code>
            </div>
            <p
              v-if="trunk.phone_numbers?.length"
              class="mt-1.5 text-p-sm text-ink-red-8"
            >
              {{
                __(
                  'Calls to these numbers go straight to your SIP infrastructure — Twilio ignores their voice webhook, so the answering service cannot run on them.',
                )
              }}
            </p>
          </div>
        </template>
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { setEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  TWILIO,
  chiPaga,
  cosaManca,
  righeDelControllo,
  statoDelConto,
} from '@/utils/twilio'
import {
  Badge,
  ErrorMessage,
  FormControl,
  Switch,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits(['updateStep'])
const { $dialog } = globalStore()

const codici = reactive({ account_sid: '', auth_token: '' })
const errore = ref('')
const controllo = ref(null)

const connessione = createResource({
  url: 'crm.telephony.collegamento.get_twilio_connection',
  auto: true,
})
const stato = computed(() => connessione.data)

// what the centre decides on calls: recording, its notice; the keys are the
// connection's, never typed here
const { document: twilio } = useDocument(
  'CRM Twilio Settings',
  'CRM Twilio Settings',
  {
    whitelistedMethods: {
      fetchSipTrunks: {
        method: 'fetch_sip_trunks',
        onSuccess: () => twilio.reload(),
      },
    },
  },
)

function dopo(dati, messaggio) {
  connessione.data = dati
  controllo.value = null
  setEnabled('twilio', Boolean(dati?.connected))
  twilio.reload()
  if (messaggio) toast.success(messaggio)
}

const collega = createResource({
  url: 'crm.telephony.collegamento.connect_twilio',
  method: 'POST',
  onSuccess: (dati) => {
    codici.account_sid = ''
    codici.auth_token = ''
    dopo(dati, __('Twilio is connected'))
    controllo.value = { ok: true, ...dati }
  },
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})

const collegaAgenzia = createResource({
  url: 'crm.telephony.collegamento.connect_agency_twilio',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Twilio is connected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const controlla = createResource({
  url: 'crm.telephony.collegamento.check_twilio_connection',
  method: 'POST',
  onSuccess: (dati) => {
    connessione.data = dati
    controllo.value = dati
  },
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const scollega = createResource({
  url: 'crm.telephony.collegamento.disconnect_twilio',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Twilio is disconnected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

function connetti() {
  errore.value = ''
  const manca = cosaManca(codici.account_sid, codici.auth_token)
  if (manca) {
    errore.value = __(manca)
    return
  }
  collega.submit({ ...codici })
}

function connettiAgenzia() {
  collegaAgenzia.submit()
}

function chiediDiScollegare() {
  $dialog({
    title: __('Disconnect Twilio?'),
    message: __(
      'Calls and messages from {brand} stop. The space and its numbers stay in your Twilio account, and the numbers keep costing until you release them.',
    ),
    actions: [
      {
        label: __('Disconnect'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          scollega.submit()
        },
      },
    ],
  })
}

function apri(indirizzo) {
  window.open(indirizzo, '_blank', 'noopener')
}

const righe = computed(() => {
  const s = stato.value || {}
  const conto = s.main_account || {}
  const spazio = s.space || {}
  const tutte = [
    {
      label: __('Twilio account'),
      value: [conto.name, conto.sid].filter(Boolean).join(' · ') || '—',
    },
    {
      label: __("{brand}'s space"),
      value: [spazio.name, spazio.sid].filter(Boolean).join(' · ') || '—',
    },
    { label: __('Who pays'), value: __(chiPaga(s.owner)) || '—' },
  ]
  if (s.connected_on) {
    tutte.push({
      label: __('Connected', null, 'Twilio'),
      value: s.connected_by
        ? __('{0} by {1}', [formatDate(s.connected_on), s.connected_by])
        : formatDate(s.connected_on),
    })
  }
  return tutte
})

const statoDelContoInParole = computed(() => {
  const parola = statoDelConto(controllo.value?.status)
  const prova = controllo.value?.type === 'Trial'
  if (!parola) return ''
  return prova
    ? __('Twilio account: {0}, on trial', [__(parola)])
    : __('Twilio account: {0}', [__(parola)])
})

const numeriInParole = computed(() => {
  const s = stato.value || {}
  if (!s.numbers) return __('No number in the space yet.')
  if (s.not_reaching) {
    return __('{0} numbers, {1} of them do not reach {brand}.', [
      s.numbers,
      s.not_reaching,
    ])
  }
  return s.numbers === 1
    ? __('One number, and it reaches {brand}.')
    : __('{0} numbers, and they all reach {brand}.', [s.numbers])
})

const trunks = computed(() => {
  try {
    return JSON.parse(twilio.doc?.sip_trunks || '[]')
  } catch {
    // a half-written cache must not blank the whole settings page
    return []
  }
})

function update() {
  twilio.save.submit(null, { onSuccess: () => twilio.reload() })
}

const isDirty = computed(() => {
  const doc = twilio.doc
  const prima = twilio.originalDoc
  if (!doc || !prima) return false
  return (
    Boolean(doc.record_calls) !== Boolean(prima.record_calls) ||
    (doc.recording_notice || '') !== (prima.recording_notice || '')
  )
})
</script>
