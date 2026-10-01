<!--
  How the centre runs its waiting lists: whether a place that frees up is offered
  by itself, to how many at once, how long they have to answer, how far ahead the
  list looks; where one joins (the booking page, the client area); the channels
  the offers go by besides the email.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Waiting list') }}
      </h2>
    </template>
    <template #header-actions>
      <Button
        variant="solid"
        :label="__('Update')"
        :loading="saving"
        :disabled="!dirty"
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
              'When an appointment is cancelled or moved, a seat in a class frees up or a new shift opens, the place goes to who waits for it, in the line’s order, with a link: the first who confirms takes it.',
            )
          }}
        </p>

        <section class="flex flex-col gap-3 px-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Offers') }}
          </h3>
          <label
            class="flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-outline-gray-2 px-3 py-2.5 hover:bg-surface-gray-1"
          >
            <span class="flex min-w-0 flex-col">
              <span class="text-p-sm-medium text-ink-gray-8">
                {{ __('Offer freed places by themselves') }}
              </span>
              <span class="text-p-xs text-ink-gray-5">
                {{
                  __(
                    'Off: the list is kept, and the desk offers or books by hand.',
                  )
                }}
              </span>
            </span>
            <Switch v-model="form.enabled" size="sm" class="shrink-0" />
          </label>
          <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
            <div class="flex flex-col gap-1.5">
              <FormControl
                v-model.number="form.offers_at_once"
                type="number"
                min="1"
                max="10"
                :label="__('Offered at once to')"
              />
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'The first ones in the line: one is the fairest, more is faster.',
                  )
                }}
              </span>
            </div>
            <div class="flex flex-col gap-1.5">
              <FormControl
                v-model.number="form.hours_to_answer"
                type="number"
                min="1"
                max="72"
                :label="__('Hours to answer')"
              />
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Then the place goes to the next ones; never later than an hour before it starts.',
                  )
                }}
              </span>
            </div>
            <div class="flex flex-col gap-1.5">
              <FormControl
                v-model.number="form.min_notice_hours"
                type="number"
                min="0"
                :label="__('Offer places starting in at least (hours)')"
              />
              <span class="text-p-sm text-ink-gray-5">
                {{ __('A place closer than this is booked by the desk.') }}
              </span>
            </div>
            <div class="flex flex-col gap-1.5">
              <FormControl
                v-model.number="form.days_ahead"
                type="number"
                min="1"
                max="90"
                :label="__('Look ahead (days)')"
              />
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __('Places further ahead are offered when they come closer.')
                }}
              </span>
            </div>
          </div>
        </section>

        <section class="flex flex-col gap-3 px-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Joining') }}
          </h3>
          <div
            class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
          >
            <label
              v-for="where in joinings"
              :key="where.field"
              class="flex cursor-pointer items-center justify-between gap-4 px-3 py-2.5 hover:bg-surface-gray-1"
            >
              <span class="flex min-w-0 flex-col">
                <span class="text-p-sm-medium text-ink-gray-8">
                  {{ where.label }}
                </span>
                <span class="text-p-xs text-ink-gray-5">{{ where.hint }}</span>
              </span>
              <Switch v-model="form[where.field]" size="sm" class="shrink-0" />
            </label>
          </div>
          <div class="flex max-w-sm flex-col gap-1.5">
            <FormControl
              v-model.number="form.default_until_days"
              type="number"
              min="1"
              max="365"
              :label="__('An entry made online waits (days)')"
            />
            <span class="text-p-sm text-ink-gray-5">
              {{ __('Unless the person says until when.') }}
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
                'The email always. WhatsApp and SMS go to the person’s mobile when they choose them; without a number, the email.',
              )
            }}
          </p>
          <div class="flex flex-col gap-1.5">
            <FormControl
              v-model="form.whatsapp_template"
              type="select"
              :label="__('WhatsApp template')"
              :options="templateOptions"
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                settings.data.templates.length
                  ? __(
                      'An approved template. Its variables, in order: the person’s name, the service, the day and time, the link to confirm.',
                    )
                  : __(
                      'No approved WhatsApp template yet: create it in Settings > WhatsApp > Templates, then choose it here.',
                    )
              }}
            </span>
          </div>
          <div class="flex flex-col gap-1.5">
            <FormControl
              v-model="form.sms_number"
              :label="__('SMS from')"
              placeholder="+39…"
              :disabled="!settings.data.twilio"
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                settings.data.twilio
                  ? __('The centre’s Twilio number. Empty: no SMS.')
                  : __('Twilio is not connected: SMS are not offered.')
              }}
            </span>
          </div>
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
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
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
  'offers_at_once',
  'hours_to_answer',
  'min_notice_hours',
  'days_ahead',
  'default_until_days',
  'online_join',
  'area_join',
  'whatsapp_template',
  'sms_number',
]
const TICKS = ['enabled', 'online_join', 'area_join']

const form = reactive({})
const saved = reactive({})
const saving = ref(false)
const error = ref('')

function fill(data) {
  for (const target of [form, saved]) {
    for (const field of CAMPI) {
      target[field] = TICKS.includes(field)
        ? Boolean(data[field])
        : data[field] ?? ''
    }
  }
}

const settings = createResource({
  url: 'crm.scheduling.attese.get_settings',
  auto: true,
  onSuccess: fill,
})

const joinings = computed(() => [
  {
    field: 'online_join',
    label: __('From the booking page'),
    hint: __('When no time suits, and for a class that is full.'),
  },
  {
    field: 'area_join',
    label: __('From the client area'),
    hint: __('For the services of the booking page.'),
  },
])

const templateOptions = computed(() => [
  { label: __('None: no WhatsApp'), value: '' },
  ...(settings.data?.templates || []).map((t) => ({
    label: t.template_name || t.name,
    value: t.name,
  })),
])

const dirty = computed(() =>
  CAMPI.some((field) => String(form[field]) !== String(saved[field])),
)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.scheduling.attese.save_settings', {
      data: JSON.stringify({
        ...Object.fromEntries(CAMPI.map((field) => [field, form[field]])),
        enabled: form.enabled ? 1 : 0,
        online_join: form.online_join ? 1 : 0,
        area_join: form.area_join ? 1 : 0,
        whatsapp_template: form.whatsapp_template || null,
        sms_number: form.sms_number || null,
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
</script>
