<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Invoicing > Online payments (crm/pagamenti, doc 60).

  The centre connects its own Stripe account with its secret key, once: the money
  of a payment goes there and stays there, DottorCloud never holds it. What it
  makes on the account (the webhook endpoint) is said; the key never comes back
  to the page. Below, the deposits' rule: a cancellation in time gives it back.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex flex-wrap items-center gap-2">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Online payments') }}
        </h2>
        <Badge
          v-if="stato"
          :label="
            stato.connected
              ? modo.label || __('Connected', null, 'Stripe')
              : __('Not connected', null, 'Stripe')
          "
          variant="subtle"
          :theme="stato.connected ? modo.theme : 'gray'"
        />
      </div>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            "Invoices and deposits paid online by card, on the centre's own Stripe account.",
          )
        }}
      </p>
    </template>
    <template v-if="stato?.connected" #header-actions>
      <AzioneImpostazioni
        :loading="salvataggio.loading"
        :disabled="!modificato"
        @click="salva"
      />
    </template>
    <template #content>
      <div
        v-if="connessione.loading && !stato"
        class="mt-[35%] flex items-center justify-center"
      >
        <LoadingIndicator class="size-6" />
      </div>

      <!-- not connected: three steps, one key -->
      <div v-else-if="stato && !stato.connected" class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "The money goes straight to your Stripe account, at Stripe's prices: {brand} never holds it. The person pays by card on Stripe's page; the invoice is marked collected by itself.",
            )
          }}
        </p>
        <ol class="flex flex-col gap-3">
          <li
            v-for="(passo, i) in passi"
            :key="i"
            class="flex items-start gap-3"
          >
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >{{ i + 1 }}</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <span class="text-p-base text-ink-gray-8">{{ passo.testo }}</span>
              <a
                v-if="passo.link"
                :href="passo.link"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ passo.etichetta }}
                <span
                  class="lucide-external-link size-3.5"
                  aria-hidden="true"
                />
              </a>
              <div v-if="i === passi.length - 1" class="flex flex-col gap-3">
                <Password
                  v-model="chiave"
                  :label="__('Secret key', null, 'Stripe')"
                  placeholder="sk_live_…"
                  autocomplete="off"
                />
                <ErrorMessage :message="errore" />
                <div>
                  <Button
                    variant="solid"
                    :label="__('Connect Stripe')"
                    :loading="collega.loading"
                    @click="connetti"
                  />
                </div>
              </div>
            </div>
          </li>
        </ol>
      </div>

      <!-- connected: whose account, in which mode, the deposits' rule -->
      <div v-else-if="stato" class="flex flex-col gap-5 pb-6">
        <p
          v-if="modo.riga"
          class="rounded-lg px-4 py-2.5 text-p-sm"
          :class="
            stato.mode === 'test'
              ? 'bg-surface-amber-1 text-ink-amber-8'
              : 'bg-surface-green-1 text-ink-green-8'
          "
        >
          {{ modo.riga }}
        </p>
        <div
          class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="riga in righe"
            :key="riga[0]"
            class="flex items-start justify-between gap-4 px-4 py-2.5 max-md:flex-col max-md:gap-0.5"
          >
            <span class="shrink-0 text-p-sm text-ink-gray-6">{{
              riga[0]
            }}</span>
            <span
              class="min-w-0 text-right text-p-sm text-ink-gray-8 [overflow-wrap:anywhere] max-md:text-left"
            >
              {{ riga[1] }}
            </span>
          </div>
        </div>

        <div v-if="controllo" class="flex flex-col gap-1">
          <p v-if="!controllo.ok" class="text-p-sm text-ink-red-8">
            {{ controllo.error }}
          </p>
          <p v-else class="text-p-sm text-ink-gray-8">
            {{
              controllo.repaired
                ? __(
                    'The account answers. The webhook endpoint was missing on Stripe: it was made again.',
                  )
                : __('The account answers, and its webhook endpoint is there.')
            }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            :label="__('Check')"
            icon-left="lucide-refresh-cw"
            :loading="controlla.loading"
            @click="controlla.submit().catch(() => {})"
          />
          <Button
            :label="__('Open Stripe')"
            icon-left="lucide-external-link"
            :link="STRIPE.dashboard"
          />
          <Button
            :label="__('Disconnect')"
            theme="red"
            variant="subtle"
            :loading="scollega.loading"
            @click="chiediDiScollegare"
          />
        </div>

        <section class="flex flex-col">
          <h3 class="px-2 text-base-semibold text-ink-gray-8">
            {{ __('Deposits at online booking') }}
          </h3>
          <p class="px-2 pb-1 text-p-sm text-ink-gray-6">
            {{
              __(
                'Which services ask a deposit, or the whole price, is chosen on each service: Agenda > Services > Online rules.',
              )
            }}
          </p>
          <SettingsRow
            :label="__('Give the deposit back when the person cancels in time')"
            :description="__('Refunded on Stripe by itself, the same day.')"
          >
            <Switch
              v-model="regola.refund_on_cancel"
              :aria-label="
                __('Give the deposit back when the person cancels in time')
              "
            />
          </SettingsRow>
          <SettingsRow
            v-if="regola.refund_on_cancel"
            :label="__('Hours before the appointment')"
            :description="__('A later cancellation keeps the deposit.')"
          >
            <FormControl
              v-model="regola.refund_hours"
              class="w-28"
              type="number"
              inputmode="numeric"
              min="0"
              :aria-label="__('Hours before the appointment')"
            />
          </SettingsRow>
        </section>
      </div>

      <p
        v-if="stato"
        class="mt-2 rounded-lg border border-outline-gray-2 px-4 py-3 text-p-sm text-ink-gray-6"
      >
        {{
          __(
            "Payment data are handled by Stripe as the centre's own processor: {brand} never sees the card. The key is kept encrypted and used only to make the payment links, read their outcome and give a deposit back.",
          )
        }}
      </p>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import Password from '@/components/Controls/Password.vue'
import { globalStore } from '@/stores/global'
import { chiedi } from '@/utils/chiedi'
import { formatDate } from '@/utils'
import {
  modoInParole,
  oreValide,
  problemaDellaChiave,
  righeDelCollegamento,
} from '@/utils/pagamentiOnline'
import {
  Badge,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const { $dialog } = globalStore()

const STRIPE = {
  registrazione: 'https://dashboard.stripe.com/register',
  chiavi: 'https://dashboard.stripe.com/apikeys',
  dashboard: 'https://dashboard.stripe.com/',
}

const passi = [
  {
    testo: __(
      "Create your account on Stripe, if you have none, and activate it with the centre's details and bank account.",
    ),
    link: STRIPE.registrazione,
    etichetta: __('Open Stripe'),
  },
  {
    testo: __(
      'In the Stripe dashboard, Developers > API keys, copy the secret key: start in test mode (sk_test_…) to try it.',
    ),
    link: STRIPE.chiavi,
    etichetta: __('Open the API keys'),
  },
  { testo: __('Paste it here and connect.') },
]

const stato = ref(null)
const chiave = ref('')
const errore = ref('')
const controllo = ref(null)
const regola = reactive({ refund_on_cancel: true, refund_hours: 24 })
const salvata = ref('')

function prendi(dati) {
  stato.value = dati
  regola.refund_on_cancel = Boolean(dati.refund_on_cancel)
  regola.refund_hours = dati.refund_hours
  salvata.value = JSON.stringify(regola)
}

const modo = computed(() => modoInParole(stato.value?.mode, __))
const righe = computed(() =>
  righeDelCollegamento(stato.value, __, (giorno) =>
    formatDate(giorno, 'D MMMM YYYY'),
  ),
)
const modificato = computed(() => JSON.stringify(regola) !== salvata.value)

const connessione = chiedi({
  url: 'crm.pagamenti.collegamento.get_stripe_connection',
  onSuccess: prendi,
  onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
})

const collega = createResource({
  url: 'crm.pagamenti.collegamento.connect_stripe',
  onSuccess(dati) {
    chiave.value = ''
    errore.value = ''
    prendi(dati)
    toast.success(__('Stripe connected'))
  },
  onError(e) {
    errore.value = e.messages?.[0] || e.message
  },
})

function connetti() {
  errore.value = problemaDellaChiave(chiave.value, __)
  if (errore.value) return
  collega.submit({ stripe_secret: chiave.value }).catch(() => {})
}

const controlla = createResource({
  url: 'crm.pagamenti.collegamento.check_stripe',
  onSuccess(dati) {
    controllo.value = dati
    prendi(dati)
  },
  onError: (e) => toast.error(e.messages?.[0] || __('Could not check')),
})

const scollega = createResource({
  url: 'crm.pagamenti.collegamento.disconnect_stripe',
  onSuccess(dati) {
    controllo.value = null
    prendi(dati)
    toast.success(__('Stripe disconnected'))
  },
  onError: (e) => toast.error(e.messages?.[0] || __('Could not disconnect')),
})

function chiediDiScollegare() {
  $dialog({
    title: __('Disconnect Stripe?'),
    message: __(
      'Nobody will be able to pay online: the links already sent stop working. The payments made stay in your Stripe account.',
    ),
    actions: [
      {
        label: __('Disconnect'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          scollega.submit().catch(() => {})
        },
      },
    ],
  })
}

const salvataggio = createResource({
  url: 'crm.pagamenti.collegamento.save_stripe_options',
  onSuccess(dati) {
    prendi(dati)
    toast.success(__('Saved'))
  },
  onError: (e) => toast.error(e.messages?.[0] || __('Could not save')),
})

function salva() {
  salvataggio
    .submit({
      refund_on_cancel: regola.refund_on_cancel ? 1 : 0,
      refund_hours: oreValide(regola.refund_hours),
    })
    .catch(() => {})
}
</script>
