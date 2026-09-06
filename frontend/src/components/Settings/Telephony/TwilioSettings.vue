<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Twilio Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="twilio.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="twilio.doc?.enabled && !twilio.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="twilio.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="twilio.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="twilio.doc" class="h-full">
        <div v-if="twilio.doc.enabled" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="twilio.doc.account_sid"
              :label="__('Account SID')"
              type="text"
              placeholder="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
              required
              autocomplete="off"
            />
            <Password
              v-model="twilio.doc.auth_token"
              :label="__('Auth Token')"
              placeholder="************"
              required
            />
          </div>
          <div
            v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
            class="h-px border-t border-outline-elevation-2"
          />
          <div
            v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
            class="flex items-center justify-between gap-8"
          >
            <div class="flex flex-col">
              <div class="text-p-base-medium text-ink-gray-7 truncate">
                {{ __('Twilio App Name') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Select a Twilio app for your CRM') }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Combobox v-model="twilio.doc.app_name" :options="twilioApps">
                <template #footer>
                  <Button
                    :label="__('Refresh Apps')"
                    theme="gray"
                    variant="subtle"
                    class="w-full"
                    icon-left="lucide-refresh-cw"
                    :loading="twilio.fetchTwilioApps.loading"
                    @click="twilio.fetchTwilioApps.fetch"
                  />
                </template>
              </Combobox>
            </div>
          </div>
          <div class="flex items-center justify-between gap-4">
            <div class="flex flex-col min-w-0">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Connection') }}
              </div>
              <div
                v-if="connection"
                class="text-p-sm truncate"
                :class="connection.ok ? 'text-ink-green-3' : 'text-ink-red-3'"
              >
                {{
                  connection.ok
                    ? __('Reached {0} ({1})', [
                        connection.account,
                        connection.status,
                      ])
                    : connection.error
                }}
              </div>
              <div v-else class="text-p-sm text-ink-gray-5">
                {{ __('Check the credentials actually reach your account.') }}
              </div>
            </div>
            <Button
              :label="__('Test')"
              :loading="twilio.testConnection.loading"
              @click="testConnection"
            />
          </div>

          <div
            v-if="connection?.ok"
            class="rounded-md bg-surface-gray-2 px-3 py-2"
          >
            <div class="text-p-sm text-ink-gray-6">
              {{ __("Point your Twilio number's voice webhook here:") }}
            </div>
            <code class="text-p-sm text-ink-gray-8 break-all">
              {{ connection.callback_url }}
            </code>
          </div>

          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between gap-4">
            <div class="flex flex-col min-w-0">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Numbers') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  numberCount
                    ? __('{0} usable caller IDs on this account', [numberCount])
                    : __(
                        'Fetch the numbers this account owns, so agents pick one instead of typing it.',
                      )
                }}
              </div>
            </div>
            <Button
              :label="__('Refresh')"
              icon-left="lucide-refresh-cw"
              :loading="twilio.fetchNumbers.loading"
              @click="twilio.fetchNumbers.fetch"
            />
          </div>

          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <div class="text-p-base-medium text-ink-gray-7 truncate">
                {{ __('Record Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{
                  __('Enable call recording for incoming and outgoing calls')
                }}
              </div>
            </div>
            <div>
              <Switch v-model="twilio.doc.record_calls" size="sm" />
            </div>
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
        </div>
        <!--  Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg-medium text-ink-gray-8">
                {{ __('Twilio Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Twilio integration to make and receive calls directly from your CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="twilio.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { setEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { Combobox, FormControl, Switch } from 'frappe-ui'
import { computed, ref } from 'vue'

const emit = defineEmits(['updateStep'])

const connection = ref(null)

const { document: twilio } = useDocument(
  'CRM Twilio Settings',
  'CRM Twilio Settings',
  {
    whitelistedMethods: {
      fetchTwilioApps: {
        method: 'fetch_applications',
        onSuccess: () => twilio.reload(),
      },
      fetchNumbers: {
        method: 'fetch_numbers',
        onSuccess: () => twilio.reload(),
      },
      testConnection: {
        method: 'test_connection',
        onSuccess: (data) => (connection.value = data),
      },
    },
  },
)

const numberCount = computed(() => {
  const raw = `${twilio.doc?.twilio_numbers || ''},${
    twilio.doc?.verified_caller_ids || ''
  }`
  return new Set(raw.split(',').filter(Boolean)).size
})

function testConnection() {
  connection.value = null
  twilio.testConnection.fetch()
}

const twilioApps = computed(() => {
  if (!twilio.doc?.account_sid) return []
  let comma_separated_apps = twilio.doc?.twilio_apps
  let apps = []
  if (comma_separated_apps) {
    apps = comma_separated_apps.split(',').map((app) => {
      return { label: app, value: app }
    })
  }
  return apps
})

function enable() {
  twilio.doc.enabled = true
}

function disable() {
  twilio.doc.enabled = false
  update()
}

function update() {
  twilio.save.submit(null, {
    onSuccess: () => twilio.reload(),
  })

  setEnabled('twilio', twilio.doc.enabled)
}

const isDirty = computed(() => {
  return (
    twilio.doc &&
    twilio.originalDoc &&
    JSON.stringify(twilio.doc) !== JSON.stringify(twilio.originalDoc)
  )
})
</script>
