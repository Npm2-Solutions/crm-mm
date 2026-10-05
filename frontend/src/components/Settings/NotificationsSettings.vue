<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Your notifications outside the panel. On your phone and computer at once,
  where you turn them on (crm/notifiche/spinta.py): this device first, what it
  can do in words, a test, the others that receive them. By email when you have
  not read them a few minutes after they came (crm/notifiche/posta.py). For each
  kind, a switch for the email and, once a device receives them, one for the
  devices. Each switch saves itself.
-->
<template>
  <SettingsLayoutBase
    :title="__('Notifications')"
    :description="
      __(
        'What reaches you outside the panel: on your phone and computer at once, where you turn them on, and by email when you have not read it in {brand} within {0} minutes.',
        [preferenze.data?.minutes || 5],
      )
    "
  >
    <template #content>
      <div class="flex flex-col gap-6">
        <!-- this phone or computer -->
        <section
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
          :aria-label="__('On this device')"
        >
          <div class="flex flex-col gap-1">
            <h3 class="text-base font-semibold text-ink-gray-8">
              {{ __('On this device') }}
            </h3>
            <p class="text-p-sm text-ink-gray-6">{{ spiegazione }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button
              v-if="statoQui === 'pronto' && !qui"
              variant="solid"
              :label="__('Turn on notifications here')"
              :loading="lavora"
              :disabled="!spinta.data"
              @click="accendi"
            />
            <template v-else-if="qui">
              <Button
                :label="__('Send me a test')"
                :loading="prova.loading"
                @click="prova.submit()"
              />
              <Button
                :label="__('Turn off here')"
                :loading="lavora"
                @click="spegni"
              />
            </template>
          </div>
          <!-- every device of yours that receives them, this one marked -->
          <div v-if="dispositivi.length" class="flex flex-col gap-1">
            <span class="text-sm font-medium text-ink-gray-7">
              {{ __('Receiving notifications') }}
            </span>
            <ul class="flex flex-col divide-y divide-outline-gray-1">
              <li
                v-for="dispositivo in dispositivi"
                :key="dispositivo.name"
                class="flex items-center gap-3 py-2"
              >
                <span
                  class="lucide-smartphone size-4 shrink-0 text-ink-gray-6"
                  aria-hidden="true"
                />
                <span class="flex min-w-0 flex-1 flex-col">
                  <span class="truncate text-base text-ink-gray-8">
                    {{ dispositivo.device }}
                  </span>
                  <span class="text-p-sm text-ink-gray-5">
                    {{ __('since {0}', [giorno(dispositivo.creation)]) }}
                  </span>
                </span>
                <Badge
                  v-if="dispositivo.endpoint_hash === improntaQui"
                  class="shrink-0"
                  variant="subtle"
                  theme="green"
                  :label="__('This one')"
                />
                <Button
                  v-else
                  class="shrink-0"
                  variant="ghost"
                  icon="x"
                  :aria-label="__('Remove {0}', [dispositivo.device])"
                  :loading="
                    togli.loading && togli.params?.name === dispositivo.name
                  "
                  @click="togli.submit({ name: dispositivo.name })"
                />
              </li>
            </ul>
          </div>
        </section>

        <!-- each kind: by email, and on the devices once one receives them -->
        <div class="flex flex-col divide-y divide-outline-gray-1">
          <SettingsRow
            v-for="gruppo in gruppi"
            :key="gruppo.key"
            :label="__(TESTI[gruppo.key]?.label || gruppo.key)"
            :description="__(TESTI[gruppo.key]?.description || '')"
          >
            <div class="flex items-start gap-5">
              <div class="flex w-16 flex-col items-center gap-1">
                <span class="text-p-xs text-ink-gray-6">{{ __('Email') }}</span>
                <Switch
                  :model-value="gruppo.on"
                  :disabled="salva.loading"
                  :aria-label="
                    __('{0} by email', [
                      __(TESTI[gruppo.key]?.label || gruppo.key),
                    ])
                  "
                  @update:model-value="(valore) => cambia(gruppo.key, valore)"
                />
              </div>
              <div
                v-if="dispositivi.length"
                class="flex w-16 flex-col items-center gap-1"
              >
                <span class="text-p-xs text-ink-gray-6">
                  {{ __('Devices') }}
                </span>
                <Switch
                  :model-value="sulDispositivo(gruppo.key)"
                  :disabled="salvaSpinta.loading"
                  :aria-label="
                    __('{0} on your devices', [
                      __(TESTI[gruppo.key]?.label || gruppo.key),
                    ])
                  "
                  @update:model-value="
                    (valore) => cambiaSpinta(gruppo.key, valore)
                  "
                />
              </div>
            </div>
          </SettingsRow>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import {
  abbonamentoQui,
  attiva,
  disattiva,
  improntaQui,
  statoQui,
} from '@/composables/spinta'
import { formatDate } from '@/utils'
import { Badge, Button, Switch, createResource, toast } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

// each group of the server's (regole.GRUPPI_EMAIL), in the words of the settings
const TESTI = {
  mentions: {
    label: 'Mentions',
    description: 'Who mentions you in a note or a comment.',
  },
  assignments: {
    label: 'Assignments and tasks',
    description: 'A person, a deal or a task given to you, or taken back.',
  },
  area: {
    label: 'Questions from the client area',
    description: 'What a person asks the centre from their area.',
  },
  messages: {
    label: 'WhatsApp, SMS, email and answering service',
    description:
      'The messages of the people you follow, those left on the answering service too: one email for each conversation.',
  },
  agenda: {
    label: 'Agenda',
    description: 'The appointments of the day still without an outcome.',
  },
  invoicing: {
    label: 'Invoicing',
    description: 'An invoice rejected or not delivered, a deadline.',
  },
  automations: {
    label: 'Automations',
    description: 'What an automation of the centre tells you.',
  },
  phone: {
    label: 'Phone numbers',
    description: "Twilio's answer on the documents of a new number.",
  },
}

// ------------------------------------------------------------------ by email

const preferenze = createResource({
  url: 'crm.notifiche.posta.get_email_preferences',
  auto: true,
})
const gruppi = computed(() => preferenze.data?.groups || [])

const salva = createResource({
  url: 'crm.notifiche.posta.save_email_preferences',
  onSuccess: (data) => preferenze.setData(data),
  onError: (error) =>
    toast.error(error.messages?.[0] || __('The choice was not saved')),
})

function cambia(chiave, valore) {
  const scelte = Object.fromEntries(gruppi.value.map((g) => [g.key, g.on]))
  scelte[chiave] = valore
  // the switch moves at once; the server's answer puts it right
  preferenze.setData({
    ...preferenze.data,
    groups: gruppi.value.map((g) =>
      g.key === chiave ? { ...g, on: valore } : g,
    ),
  })
  salva.submit({ groups: scelte })
}

// ------------------------------------------------------------------ on the devices

const spinta = createResource({
  url: 'crm.notifiche.spinta.get_push',
  auto: true,
})
const dispositivi = computed(() => spinta.data?.devices || [])
const qui = computed(
  () =>
    Boolean(improntaQui.value) &&
    dispositivi.value.some((d) => d.endpoint_hash === improntaQui.value),
)
const lavora = ref(false)

onMounted(() => abbonamentoQui().catch(() => {}))

const spiegazione = computed(() => {
  if (statoQui.value === 'installa-prima')
    return __(
      'On an iPhone or iPad notifications reach the app on the home screen: in Safari tap Share, then “Add to Home Screen”, open {brand} from there and come back here.',
    )
  if (statoQui.value === 'bloccato')
    return __(
      '{brand}’s notifications are blocked in this browser: allow them in the browser’s or the phone’s settings, then come back here.',
    )
  if (statoQui.value === 'non-supportato')
    return __(
      'This browser does not receive notifications: use an up-to-date Chrome, Edge, Firefox or Safari, or the app on the home screen.',
    )
  if (qui.value)
    return __('Notifications arrive here. Touching one opens it in {brand}.')
  return __(
    'Notifications reach this phone or computer even when {brand} is closed.',
  )
})

async function accendi() {
  lavora.value = true
  try {
    const stato = await attiva(spinta.data.public_key)
    if (stato) spinta.setData(stato)
    else if (statoQui.value === 'bloccato')
      toast.error(__('Notifications were not allowed on this device'))
  } catch (e) {
    toast.error(
      e.messages?.join(' ') || __('Notifications could not be turned on here'),
    )
  } finally {
    lavora.value = false
  }
}

async function spegni() {
  lavora.value = true
  try {
    spinta.setData(await disattiva())
  } catch (e) {
    toast.error(e.messages?.join(' ') || e.message)
  } finally {
    lavora.value = false
  }
}

const prova = createResource({
  url: 'crm.notifiche.spinta.send_test',
  onSuccess: (esito) =>
    esito.sent
      ? toast.success(__('Test sent: it arrives in a few seconds.'))
      : toast.error(
          __(
            'The browser’s service did not take the test: turn notifications off and on again here.',
          ),
        ),
  onError: (error) => toast.error(error.messages?.[0] || error.message),
})

const togli = createResource({
  url: 'crm.notifiche.spinta.unsubscribe',
  onSuccess: (stato) => spinta.setData(stato),
  onError: (error) => toast.error(error.messages?.[0] || error.message),
})

function giorno(data) {
  return formatDate(data, 'D MMM YYYY')
}

function sulDispositivo(chiave) {
  return (spinta.data?.groups || []).find((g) => g.key === chiave)?.on ?? true
}

const salvaSpinta = createResource({
  url: 'crm.notifiche.spinta.save_push_preferences',
  onSuccess: (stato) => spinta.setData(stato),
  onError: (error) =>
    toast.error(error.messages?.[0] || __('The choice was not saved')),
})

function cambiaSpinta(chiave, valore) {
  const gruppiSpinta = spinta.data?.groups || []
  const scelte = Object.fromEntries(gruppiSpinta.map((g) => [g.key, g.on]))
  scelte[chiave] = valore
  spinta.setData({
    ...spinta.data,
    groups: gruppiSpinta.map((g) =>
      g.key === chiave ? { ...g, on: valore } : g,
    ),
  })
  salvaSpinta.submit({ groups: scelte })
}
</script>
