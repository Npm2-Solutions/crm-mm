<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Answering Service')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 active:bg-transparent active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
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
          <!-- how incoming calls are answered -->
          <div class="text-base-semibold text-ink-gray-9 pb-1">
            {{ __('Incoming Calls') }}
          </div>

          <SettingRow
            :label="__('Answer with')"
            :description="
              __(
                'A fixed choice, never guessed from who happens to be online — the same number behaves the same way at every hour.',
              )
            "
          >
            <FormControl
              v-model="settings.doc.answer_mode"
              type="select"
              class="w-56"
              :options="[
                {
                  label: __('Always the announcement'),
                  value: 'Always Answering Service',
                },
                { label: __('Ring agents first'), value: 'Ring Agents First' },
              ]"
            />
          </SettingRow>

          <div class="rounded-md bg-surface-gray-2 px-3 py-2 my-2">
            <p class="text-p-sm text-ink-gray-6">
              {{ modeExplanation }}
            </p>
          </div>

          <SettingRow
            :label="__('Respect working hours')"
            :description="
              __(
                'Play a different announcement when closed, and count the promised time in working hours only. Hours come from Agenda → Working Hours.',
              )
            "
          >
            <Switch v-model="settings.doc.use_working_hours" size="sm" />
          </SettingRow>

          <!-- the promise -->
          <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
            {{ __('Callback Promise') }}
          </div>

          <SettingRow
            :label="__('Call back within')"
            :description="
              settings.doc.use_working_hours
                ? __(
                    'Counted in working hours, so an evening call is due the next morning.',
                  )
                : __('Counted in plain clock hours.')
            "
          >
            <FormControl
              v-model.number="settings.doc.callback_hours"
              type="number"
              class="w-24"
              :suffix="__('hours')"
            />
          </SettingRow>

          <SettingRow
            :label="__('Merge repeat calls within')"
            :description="
              __(
                'Someone who hears the announcement often rings straight back. Inside this window they join the callback already queued instead of appearing twice. 0 queues every call.',
              )
            "
          >
            <FormControl
              v-model.number="settings.doc.dedupe_window_hours"
              type="number"
              class="w-24"
            />
          </SettingRow>

          <SettingRow
            :label="__('Maximum attempts')"
            :description="
              __(
                'After this many unanswered attempts the callback closes as unreachable. 0 keeps trying.',
              )
            "
          >
            <FormControl
              v-model.number="settings.doc.max_callback_attempts"
              type="number"
              class="w-24"
            />
          </SettingRow>

          <SettingRow
            :label="__('Retry after')"
            :description="
              __(
                'How long an unanswered callback waits before coming back around.',
              )
            "
          >
            <FormControl
              v-model.number="settings.doc.retry_after_hours"
              type="number"
              class="w-24"
              :suffix="__('hours')"
            />
          </SettingRow>

          <!-- what the caller hears -->
          <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
            {{ __('Announcement') }}
          </div>

          <SettingRow
            :label="__('Source')"
            :description="
              __(
                'A recorded file sounds better to callers. Text to speech is there to get started without a studio recording.',
              )
            "
          >
            <FormControl
              v-model="settings.doc.greeting_source"
              type="select"
              class="w-44"
              :options="[
                { label: __('Text to speech'), value: 'Text to Speech' },
                { label: __('Audio file'), value: 'Audio File' },
              ]"
            />
          </SettingRow>

          <!-- text announcements -->
          <template v-if="isText">
            <div class="py-3 px-2">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('During working hours') }}
              </div>
              <FormControl
                v-model="settings.doc.greeting_text"
                type="textarea"
                class="mt-2"
                rows="3"
                :placeholder="__(defaultOpenGreeting)"
              />
              <p class="mt-1 text-p-sm text-ink-gray-5">
                {{
                  __(
                    '{hours} becomes the promised hours and {time} the moment the caller is called back by. Left empty, a default sentence is used.',
                  )
                }}
              </p>
            </div>

            <div v-if="settings.doc.use_working_hours" class="py-3 px-2">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Outside working hours') }}
              </div>
              <FormControl
                v-model="settings.doc.after_hours_greeting_text"
                type="textarea"
                class="mt-2"
                rows="3"
                :placeholder="__(defaultClosedGreeting)"
              />
            </div>

            <div class="text-base-semibold text-ink-gray-9 pt-6 pb-1">
              {{ __('Voice') }}
            </div>

            <SettingRow
              :label="__('Language')"
              :description="
                __('Language tag the announcement is spoken in, e.g. it-IT.')
              "
            >
              <FormControl
                v-model="settings.doc.language"
                class="w-32"
                placeholder="it-IT"
              />
            </SettingRow>

            <SettingRow
              :label="__('Voice')"
              :description="__('Speaking voice.')"
            >
              <FormControl
                v-model="settings.doc.voice"
                type="select"
                class="w-44"
                :options="voiceOptions"
              />
            </SettingRow>
          </template>

          <!-- audio announcements -->
          <template v-else>
            <AudioRow
              :label="__('During working hours')"
              :description="
                __(
                  'MP3 or WAV. Must be public — the telephony provider fetches it without logging in.',
                )
              "
              :url="settings.doc.greeting_audio"
              @picked="(url) => (settings.doc.greeting_audio = url)"
              @cleared="() => (settings.doc.greeting_audio = '')"
            />
            <AudioRow
              v-if="settings.doc.use_working_hours"
              :label="__('Outside working hours')"
              :description="
                __(
                  'Optional. Without it, callers outside working hours hear the open-hours recording.',
                )
              "
              :url="settings.doc.after_hours_greeting_audio"
              @picked="(url) => (settings.doc.after_hours_greeting_audio = url)"
              @cleared="() => (settings.doc.after_hours_greeting_audio = '')"
            />
          </template>

          <ErrorMessage class="mt-4" :message="settings.save?.error" />
        </div>

        <!-- disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-80 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '30%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg-medium text-ink-gray-8">
                {{ __('Answering Service Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Answer incoming calls with an announcement and queue a callback, instead of ringing an agent. Requires Twilio.',
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
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import SettingRow from '@/components/Settings/Telephony/SettingRow.vue'
import AudioRow from '@/components/Settings/Telephony/AudioRow.vue'
import { answeringEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import {
  Badge,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: settings } = useDocument(
  'CRM Answering Settings',
  'CRM Answering Settings',
)

const defaultOpenGreeting =
  'Thank you for calling. We cannot take your call right now, but we will call you back within {hours} hours.'
const defaultClosedGreeting =
  'Thank you for calling. We are closed at the moment. We will call you back as soon as we reopen.'

const voiceOptions = [
  { label: 'Bianca (it)', value: 'Polly.Bianca' },
  { label: 'Carla (it)', value: 'Polly.Carla' },
  { label: 'Giorgio (it)', value: 'Polly.Giorgio' },
  { label: 'Alice', value: 'alice' },
  { label: __('Man'), value: 'man' },
  { label: __('Woman'), value: 'woman' },
]

const isText = computed(() => settings.doc?.greeting_source !== 'Audio File')

const modeExplanation = computed(() =>
  settings.doc?.answer_mode === 'Ring Agents First'
    ? __(
        'Calls ring the agent who owns the number first. The announcement answers only when nobody picks up.',
      )
    : __(
        'Every incoming call hears the announcement and is added to the callback queue. Nobody is rung.',
      ),
)

const isDirty = computed(
  () =>
    settings.doc &&
    settings.originalDoc &&
    JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc),
)

function enable() {
  settings.doc.enabled = true
  if (!settings.doc.callback_hours) settings.doc.callback_hours = 3
}

function disable() {
  settings.doc.enabled = false
  update()
}

function update() {
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      answeringEnabled.value = Boolean(settings.doc.enabled)
      toast.success(__('Answering service updated'))
    },
  })
}
</script>
