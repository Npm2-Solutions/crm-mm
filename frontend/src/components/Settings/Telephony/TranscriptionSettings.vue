<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Transcription')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 active:bg-transparent active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="settings.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>

    <template #header-actions>
      <div
        v-if="settings.doc?.enabled && !settings.get.loading"
        class="flex gap-2"
      >
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="settings.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="settings.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>

    <template #content>
      <div v-if="settings.doc" class="h-full">
        <div v-if="settings.doc.enabled" class="flex flex-col">
          <div class="rounded-md bg-surface-gray-2 px-3 py-2 mb-2">
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Any endpoint that speaks the OpenAI audio-transcription API works here: a Whisper server you run yourself, OpenAI, or Azure OpenAI. Only the URL and the key change — so where the audio is processed stays your decision.',
                )
              }}
            </p>
          </div>

          <SettingRow
            :label="__('Transcribe automatically')"
            :description="
              __(
                'Every recording is transcribed as soon as the provider hands it over. With this off, transcription only runs when asked for on a call.',
              )
            "
          >
            <Switch v-model="settings.doc.auto_transcribe" size="sm" />
          </SettingRow>

          <SettingRow
            :label="__('Language')"
            :description="
              __(
                'ISO code of the language spoken on calls. Empty lets the model detect it, which is slower and weaker on short calls.',
              )
            "
          >
            <FormControl
              v-model="settings.doc.language"
              class="w-24"
              placeholder="it"
            />
          </SettingRow>

          <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
            {{ __('Endpoint') }}
          </div>

          <div class="grid grid-cols-2 gap-4 px-2 py-3">
            <FormControl
              v-model="settings.doc.base_url"
              :label="__('Base URL')"
              placeholder="https://api.openai.com/v1"
              autocomplete="off"
            />
            <Password
              v-model="settings.doc.api_key"
              :label="__('API Key')"
              placeholder="************"
            />
          </div>

          <SettingRow
            :label="__('Model')"
            :description="
              __('For example whisper-1, or the name your own server serves.')
            "
          >
            <FormControl v-model="settings.doc.model" class="w-56" />
          </SettingRow>

          <div class="py-3 px-2">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Vocabulary hint') }}
            </div>
            <FormControl
              v-model="settings.doc.prompt"
              type="textarea"
              rows="2"
              class="mt-2"
              :placeholder="
                __(
                  'Names, jargon or product terms the model should spell correctly',
                )
              "
            />
          </div>

          <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
            {{ __('Retention') }}
          </div>
          <p class="text-p-sm text-ink-gray-6 px-2 pb-1">
            {{
              __(
                'What was said on a call is personal data, and in a health practice a special category of it. Keep it only as long as there is a reason to.',
              )
            }}
          </p>

          <SettingRow
            :label="__('Delete transcripts after')"
            :description="__('Nightly. 0 keeps them forever.')"
          >
            <FormControl
              v-model.number="settings.doc.transcript_retention_days"
              type="number"
              class="w-24"
              :suffix="__('days')"
            />
          </SettingRow>

          <SettingRow
            :label="__('Forget recording links after')"
            :description="
              __(
                'Drops the recording link so the audio is no longer reachable from the CRM. Deleting it at the provider is a separate step. 0 keeps the links.',
              )
            "
          >
            <FormControl
              v-model.number="settings.doc.recording_retention_days"
              type="number"
              class="w-24"
              :suffix="__('days')"
            />
          </SettingRow>

          <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
            {{ __('Limits') }}
          </div>

          <SettingRow
            :label="__('Maximum recording size')"
            :description="
              __(
                'Larger recordings are not sent, guarding both the provider limit and this server.',
              )
            "
          >
            <FormControl
              v-model.number="settings.doc.max_recording_mb"
              type="number"
              class="w-24"
              suffix="MB"
            />
          </SettingRow>

          <SettingRow
            :label="__('Request timeout')"
            :description="
              __('How long to wait for the transcription to come back.')
            "
          >
            <FormControl
              v-model.number="settings.doc.request_timeout"
              type="number"
              class="w-24"
              :suffix="__('seconds')"
            />
          </SettingRow>

          <ErrorMessage class="mt-4" :message="settings.save?.error" />
        </div>

        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-80 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '30%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <FeatherIcon name="file-text" class="size-7 text-ink-gray-7" />
              <span class="text-lg-medium text-ink-gray-8">
                {{ __('Transcription Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Turn call recordings into text a person — or an AI agent reading over the API — can work with.',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>

      <div
        v-else-if="settings.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingRow from '@/components/Settings/Telephony/SettingRow.vue'
import { transcriptionEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import {
  Badge,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  LoadingIndicator,
  Password,
  Switch,
  toast,
} from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: settings } = useDocument(
  'CRM Transcription Settings',
  'CRM Transcription Settings',
)

const isDirty = computed(
  () =>
    settings.doc &&
    settings.originalDoc &&
    JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc),
)

function enable() {
  settings.doc.enabled = true
  if (!settings.doc.model) settings.doc.model = 'whisper-1'
  if (!settings.doc.max_recording_mb) settings.doc.max_recording_mb = 25
  if (!settings.doc.request_timeout) settings.doc.request_timeout = 300
}

function disable() {
  settings.doc.enabled = false
  update()
}

function update() {
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      transcriptionEnabled.value = Boolean(settings.doc.enabled)
      toast.success(__('Transcription updated'))
    },
  })
}
</script>
