<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The reminders of the appointments (crm/scheduling/promemoria.py, doc 59):
  whether they leave, how many hours before, what a «cannot come» does; the
  ways - WhatsApp with its buttons (a template the number that sends can send,
  or DottorCloud's own, made on it here), the SMS from the centre's one sender,
  the email -; the last ones, how they went and what was answered.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Appointment reminders') }}
      </h2>
    </template>
    <template #header-actions>
      <AzioneImpostazioni
        :loading="saving"
        :disabled="!dirty || Boolean(problemaSecondo)"
        @click="save"
      />
    </template>
    <template #content>
      <div v-if="settings.data" class="flex flex-col gap-6 pb-6">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The day before, each person gets a reminder of their appointment: by WhatsApp with the buttons to confirm, cancel or move it, else by SMS, else by email. What they answer is in the agenda.',
            )
          }}
        </p>

        <section class="flex flex-col gap-3 px-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Reminders') }}
          </h3>
          <div
            class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
          >
            <label
              v-for="tick in ticks"
              :key="tick.field"
              class="flex cursor-pointer items-center justify-between gap-4 px-3 py-2.5 hover:bg-surface-gray-1"
            >
              <span class="flex min-w-0 flex-col">
                <span class="text-p-sm-medium text-ink-gray-8">
                  {{ tick.label }}
                </span>
                <span class="text-p-xs text-ink-gray-5">{{ tick.hint }}</span>
              </span>
              <Switch
                v-model="form[tick.field]"
                size="sm"
                class="shrink-0"
                :aria-label="tick.label"
              />
            </label>
          </div>
          <div class="flex max-w-sm flex-col gap-1.5">
            <FormControl
              v-model.number="form.hours_before"
              type="number"
              inputmode="numeric"
              min="2"
              max="72"
              :label="__('Hours before')"
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'At night, from 21 to 8, it leaves in the morning, or the evening before; never in the last hour, nor for what was just booked.',
                )
              }}
            </span>
          </div>
          <div class="flex max-w-sm flex-col gap-1.5">
            <FormControl
              v-model.number="form.second_hours_before"
              type="number"
              inputmode="numeric"
              min="1"
              max="12"
              :placeholder="__('None')"
              :label="__('Second reminder: hours before')"
            />
            <ErrorMessage v-if="problemaSecondo" :message="problemaSecondo" />
            <span v-else class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Optional: a second reminder the same day, 1 to 12 hours before. Never at night, nor to whoever already said they are coming or cannot come.',
                )
              }}
            </span>
          </div>
        </section>

        <section class="flex flex-col gap-3 px-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Channels') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The first one the person can receive: WhatsApp, then SMS, then email.',
              )
            }}
          </p>

          <!-- WhatsApp: a template with the buttons, or ours to make -->
          <div v-if="settings.data.whatsapp" class="flex flex-col gap-1.5">
            <FormControl
              v-model="form.whatsapp_template"
              type="select"
              :label="__('WhatsApp template')"
              :options="templateOptions"
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                adatti.length
                  ? __(
                      'An approved template with the buttons to confirm and to cancel. Its variables, in order: the name, what, when, where.',
                    )
                  : __(
                      'No approved template has the buttons to confirm and to cancel yet.',
                    )
              }}
            </span>
            <div
              v-if="nostro === 'da_fare' && settings.data.can_make_template"
              class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-2"
            >
              <Button
                :label="__('Create the reminder template')"
                icon-left="lucide-message-square-plus"
                :loading="creating"
                @click="createTemplate"
              />
              <span class="min-w-[15rem] flex-1 text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Ready, with the three buttons, on the number that sends: Meta reviews it, usually within a day, then choose it here.',
                  )
                }}
              </span>
            </div>
            <p
              v-else-if="nostro === 'in_attesa'"
              class="mt-1 flex items-start gap-1.5 text-p-sm text-ink-gray-6"
            >
              <span
                class="lucide-hourglass mt-0.5 size-3.5 shrink-0"
                aria-hidden="true"
              />
              {{
                __(
                  'The reminder template is waiting for Meta’s review: once approved, choose it here.',
                )
              }}
            </p>
            <p
              v-else-if="nostro === 'rifiutato'"
              class="mt-1 flex items-start gap-1.5 text-p-sm text-ink-red-7"
            >
              <span
                class="lucide-circle-alert mt-0.5 size-3.5 shrink-0"
                aria-hidden="true"
              />
              {{
                __(
                  'Meta refused the reminder template: see why in Settings > WhatsApp > Templates.',
                )
              }}
            </p>
          </div>
          <p v-else class="text-p-sm text-ink-gray-5">
            {{
              __(
                'WhatsApp is not connected: the reminders go by SMS or email. Connect it in Settings > WhatsApp.',
              )
            }}
          </p>

          <div
            class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
          >
            <label
              v-for="way in ways"
              :key="way.field"
              class="flex items-center justify-between gap-4 px-3 py-2.5"
              :class="
                way.disabled
                  ? 'cursor-not-allowed'
                  : 'cursor-pointer hover:bg-surface-gray-1'
              "
            >
              <span class="flex min-w-0 flex-col">
                <span class="text-p-sm-medium text-ink-gray-8">
                  {{ way.label }}
                </span>
                <span class="text-p-xs text-ink-gray-5">{{ way.hint }}</span>
              </span>
              <Switch
                v-model="form[way.field]"
                size="sm"
                class="shrink-0"
                :disabled="way.disabled"
                :aria-label="way.label"
              />
            </label>
          </div>
        </section>

        <section
          v-if="settings.data.recent?.length"
          class="flex flex-col gap-3 px-2"
        >
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('The last reminders') }}
          </h3>
          <ul
            class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
          >
            <li
              v-for="row in settings.data.recent"
              :key="row.name"
              class="flex items-start gap-3 px-3 py-2.5"
            >
              <span
                :class="[
                  segnoDelPromemoria(row, __)?.icona ||
                    (row.status === 'Sent' ? 'lucide-bell' : 'lucide-bell-off'),
                  'mt-0.5 size-4 shrink-0 text-ink-gray-6',
                ]"
                aria-hidden="true"
              />
              <span class="flex min-w-0 flex-1 flex-col">
                <span class="truncate text-p-sm-medium text-ink-gray-8">
                  {{ row.person || __('Someone') }}
                </span>
                <span class="text-p-xs text-ink-gray-6">{{ row.when }}</span>
                <span class="text-p-xs text-ink-gray-6">
                  {{ rigaDelPromemoria(row, __) }}
                </span>
                <span
                  v-if="row.status !== 'Sent' && row.reason"
                  class="text-p-xs text-ink-gray-5"
                >
                  {{ row.reason }}
                </span>
              </span>
            </li>
          </ul>
        </section>
        <ErrorMessage :message="error" />
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import {
  modelliAdatti,
  problemaDelSecondo,
  rigaDelPromemoria,
  segnoDelPromemoria,
  statoDelNostro,
} from '@/utils/promemoriaAppuntamenti'
import { leggibile } from '@/utils/telefono'
import {
  Button,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const CAMPI = [
  'enabled',
  'hours_before',
  'second_hours_before',
  'cancel_on_reply',
  'whatsapp_template',
  'use_sms',
  'use_email',
]
const TICKS = ['enabled', 'cancel_on_reply', 'use_sms', 'use_email']

const form = reactive({})
const saved = reactive({})
const saving = ref(false)
const creating = ref(false)
const error = ref('')

function fill(data) {
  for (const target of [form, saved]) {
    for (const field of CAMPI) {
      target[field] = TICKS.includes(field)
        ? Boolean(data[field])
        : (data[field] ?? '')
    }
  }
}

const settings = createResource({
  url: 'crm.scheduling.promemoria.get_settings',
  auto: true,
  onSuccess: fill,
})

const adatti = computed(() => modelliAdatti(settings.data?.templates))
const nostro = computed(() => statoDelNostro(settings.data?.our_template))

const ticks = computed(() => [
  {
    field: 'enabled',
    label: __('Remind of the appointments'),
    hint: __('Off: nobody receives them.'),
  },
  {
    field: 'cancel_on_reply',
    label: __('A «cannot come» cancels the appointment'),
    hint: __(
      'The time goes to whoever waits for it. Off: the desk is told, and decides.',
    ),
  },
])

const ways = computed(() => {
  const mittente = settings.data?.sms_sender
  return [
    {
      field: 'use_sms',
      label: __('By SMS without WhatsApp'),
      hint: !mittente
        ? __('The SMS need the phone: set it up in Settings > Phone.')
        : settings.data.sms_replies
          ? __('From {0}: the person answers YES or NO.', [leggibile(mittente)])
          : __('From {0}: the person answers from the link.', [mittente]),
      disabled: !mittente,
    },
    {
      field: 'use_email',
      label: __('By email without WhatsApp or SMS'),
      hint: __('With the link to confirm, move or cancel.'),
      disabled: false,
    },
  ]
})

// the chosen one stays offered even when it is no longer suitable: saving says why
const templateOptions = computed(() => {
  const scelti = new Set(adatti.value.map((t) => t.name))
  const attuale = (settings.data?.templates || []).find(
    (t) => t.name === saved.whatsapp_template && !scelti.has(t.name),
  )
  return [
    { label: __('None: no WhatsApp'), value: '' },
    ...[...adatti.value, ...(attuale ? [attuale] : [])].map((t) => ({
      label: t.template_name || t.name,
      value: t.name,
    })),
  ]
})

const problemaSecondo = computed(() =>
  problemaDelSecondo(form.second_hours_before, form.hours_before, __),
)

const dirty = computed(() =>
  CAMPI.some((field) => String(form[field]) !== String(saved[field])),
)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.scheduling.promemoria.save_settings', {
      data: JSON.stringify({
        ...Object.fromEntries(CAMPI.map((field) => [field, form[field]])),
        ...Object.fromEntries(
          TICKS.map((field) => [field, form[field] ? 1 : 0]),
        ),
        whatsapp_template: form.whatsapp_template || null,
        second_hours_before: form.second_hours_before || 0,
      }),
    })
    settings.data = data
    fill(data)
    toast.success(__('Saved'))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}

async function createTemplate() {
  creating.value = true
  error.value = ''
  try {
    const data = await call('crm.scheduling.promemoria.create_template')
    settings.data = data
    fill(data)
    toast.success(__('Sent to Meta for review'))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    creating.value = false
  }
}
</script>
