<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  Settings > Phone > Telephony: one's own line (the service one calls with, the
  number one calls from), the incoming calls and the providers' pages.
-->
<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 max-md:px-3 max-md:py-5">
    <!-- Header -->
    <div
      class="flex justify-between px-2 text-ink-gray-8 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1 w-9/12 max-md:w-full">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none text-ink-gray-8"
        >
          {{ __('Telephony') }}
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('The lines {brand} calls and answers on, and what it says when nobody picks up.') }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end impostazioni-strette:w-auto impostazioni-strette:justify-start"
      >
        <AzioneImpostazioni
          v-if="isDirty"
          :loading="
            isNewDoc ? insertResource.loading : telephonyAgent.save?.loading
          "
          @click="update"
        />
      </div>
    </div>

    <div v-if="telephonyAgent.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div
        v-if="piuMezzi"
        class="flex items-center justify-between gap-8 py-3 pl-2 pr-1"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Default Medium') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Default calling medium for logged-in user') }}
          </div>
        </div>
        <div class="flex items-center gap-1">
          <FormControl
            v-model="telephonyAgent.doc.default_medium"
            type="select"
            class="w-44 p-1"
            :options="mediumOptions"
            :placeholder="__('Select Medium')"
          />
          <Button
            :aria-label="__('Clear')"
            v-if="telephonyAgent.doc.default_medium"
            icon="lucide-x"
            :tooltip="__('Clear')"
            @click="telephonyAgent.doc.default_medium = ''"
          />
        </div>
      </div>
      <div
        v-if="piuMezzi && isEnabled('twilio')"
        class="h-px border-t mx-2 border-outline-elevation-2"
      />
      <div
        v-if="isEnabled('twilio')"
        class="flex items-center justify-between gap-8 py-3 pl-2 pr-1"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Twilio Number') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Set the Twilio number to be used for outgoing calls.') }}
          </div>
        </div>
        <div>
          <div
            v-if="callerIds.data?.length"
            class="flex flex-col items-end gap-1"
          >
            <Combobox
              v-model="telephonyAgent.doc.twilio_number"
              class="w-44"
              :options="callerIdOptions"
            />
            <span
              v-if="chosenCallerId && !chosenCallerId.routes_to_crm"
              class="w-56 text-right text-p-sm text-ink-red-8"
            >
              {{ __('Incoming calls to this number do not reach {brand}.') }}
            </span>
          </div>
          <FormControl
            v-else
            v-model="telephonyAgent.doc.twilio_number"
            v-bind="tastiera('telefono')"
            class="flex-1 truncate w-44 p-1"
            :placeholder="__('Enter Twilio Number')"
            :error="
              Boolean(telephonyAgent.doc.twilio_number) &&
              !validatePhone(telephonyAgent.doc.twilio_number)
                ? __('Enter a valid phone number')
                : undefined
            "
            placement="bottom-end"
          />
        </div>
      </div>
      <div
        v-if="puo('telefono.configura')"
        class="flex items-center justify-between text-lg-semibold text-ink-gray-8 mt-4 py-3 px-2"
      >
        {{ __('Incoming Calls') }}
      </div>

      <div
        v-if="puo('telefono.configura')"
        class="flex items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col gap-1">
          <span
            class="flex items-center gap-2 text-base-medium text-ink-gray-8"
          >
            {{ __('Answering Service') }}
            <Badge
              v-if="answeringEnabled"
              :label="__('On')"
              variant="subtle"
              theme="green"
            />
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'When nobody picks up, or for every call: an announcement answers and queues a callback.',
              )
            }}
          </span>
        </div>
        <Button
          :label="answeringEnabled ? __('Configure') : __('Set up')"
          @click="emit('updateStep', 'answering-settings')"
        />
      </div>

      <div
        v-if="puo('telefono.configura')"
        class="h-px border-t mx-2 border-outline-elevation-2"
      />

      <div
        v-if="puo('telefono.configura')"
        class="flex items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col gap-1">
          <span
            class="flex items-center gap-2 text-base-medium text-ink-gray-8"
          >
            {{ __('Transcription') }}
            <Badge
              v-if="transcriptionEnabled"
              :label="__('On')"
              variant="subtle"
              theme="green"
            />
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Turn call recordings into text a person or an AI agent can work with.',
              )
            }}
          </span>
        </div>
        <Button
          :label="transcriptionEnabled ? __('Configure') : __('Set up')"
          @click="emit('updateStep', 'transcription-settings')"
        />
      </div>

      <div
        v-if="puo('telefono.configura')"
        class="flex items-center justify-between text-lg-semibold text-ink-gray-8 mt-4 py-3 px-2"
      >
        {{ __('Integrations') }}
      </div>

      <div
        v-if="puo('telefono.configura')"
        class="flex items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __('Twilio') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              isEnabled('twilio')
                ? __('Connected: calls and messages go through Twilio.')
                : __(
                    'Connect your Twilio account: calls and messages from {brand}.',
                  )
            }}
          </span>
        </div>
        <Button
          class="shrink-0"
          :label="
            isEnabled('twilio') ? __('Open', null, 'Action') : __('Connect')
          "
          @click="emit('updateStep', 'twilio-settings')"
        />
      </div>
    </div>
    <ErrorMessage
      :message="isNewDoc ? insertResource.error : telephonyAgent.save?.error"
    />
  </div>
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import {
  FormControl,
  Badge,
  Combobox,
  ErrorMessage,
  createDocumentResource,
  createResource,
  toast,
} from 'frappe-ui'
import {
  answeringEnabled,
  providers,
  transcriptionEnabled,
  useTelephony,
} from '@/composables/telephony'
import { usersStore } from '@/stores/users'
import { validatePhone } from '@/utils'
import { tastiera } from '@/utils/tastiera'
import { ref, computed } from 'vue'

const { isEnabled } = useTelephony()

// what the account can actually present; typing a number Twilio has never heard
// of is the quiet way calls stop working
const callerIds = createResource({
  url: 'crm.telephony.caller_ids.get_caller_ids',
  params: { provider: 'twilio' },
  cache: 'twilio-caller-ids',
  auto: true,
})

const callerIdOptions = computed(() =>
  (callerIds.data || []).map((row) => ({
    label: row.label ? `${row.label} · ${row.phone_number}` : row.phone_number,
    value: row.phone_number,
  })),
)

// the number an agent presents can be perfectly valid outbound and still never
// receive anything — say so here rather than leaving it to be discovered
const chosenCallerId = computed(() =>
  (callerIds.data || []).find(
    (row) => row.phone_number === telephonyAgent.doc?.twilio_number,
  ),
)

// the options follow the provider registry, so a new carrier shows up here
// without this file having to learn its name
const mediumOptions = computed(() => [
  { label: '', value: '' },
  ...providers.value
    .filter((p) => p.enabled)
    .map((p) => ({ label: p.label, value: p.label })),
])

// with one carrier there is nothing to choose: one calls with it
const piuMezzi = computed(() => mediumOptions.value.length > 2)

const emit = defineEmits(['updateStep'])

const { getUser, puo } = usersStore()

const isNewDoc = ref(false)

// one's own line, made the first time it is saved: asked for only once the
// server says it is there, so a user who never saved it gets an empty page and
// not a document that does not exist
const telephonyAgent = createDocumentResource({
  doctype: 'CRM Telephony Agent',
  name: getUser().name,
  auto: false,
  setValue: {
    onSuccess: () => toast.success(__('Saved')),
    onError: (err) => {
      err.messages?.forEach((msg) => toast.error(msg))
    },
  },
})

createResource({
  url: 'frappe.client.get_count',
  params: {
    doctype: 'CRM Telephony Agent',
    filters: { name: getUser().name },
  },
  auto: true,
  onSuccess: (quanti) => {
    if (quanti) return telephonyAgent.reload()
    isNewDoc.value = true
    telephonyAgent.doc = {}
    telephonyAgent.originalDoc = {}
  },
})

const insertResource = createResource({
  url: 'frappe.client.insert',
  onSuccess: (data) => {
    isNewDoc.value = false
    telephonyAgent.doc = data
    telephonyAgent.originalDoc = JSON.parse(JSON.stringify(data))
    toast.success(__('Saved'))
  },
  onError: (err) => {
    err.messages?.forEach((msg) => toast.error(msg))
  },
})

function update() {
  if (!isDirty.value) return

  if (isNewDoc.value) {
    insertResource.submit({
      doc: {
        doctype: 'CRM Telephony Agent',
        user: getUser().name,
        ...telephonyAgent.doc,
      },
    })
  } else {
    telephonyAgent.save.submit()
  }
}

const isDirty = computed(() => {
  return (
    telephonyAgent.doc &&
    telephonyAgent.originalDoc &&
    JSON.stringify(telephonyAgent.doc) !==
      JSON.stringify(telephonyAgent.originalDoc)
  )
})
</script>
