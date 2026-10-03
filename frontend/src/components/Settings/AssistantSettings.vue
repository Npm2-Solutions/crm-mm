<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The assistant: documentation support the professional reviews. Where the
  model runs - provider, address, model, key, region, the contract that keeps
  nothing - is the agency's; whether the centre uses it, and for what, the
  manager's. Below, the register: every request, and what became of it.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <h2 class="text-2xl-semibold text-ink-gray-9">{{ __('Assistant') }}</h2>
        <Badge
          v-if="status.data"
          variant="subtle"
          :theme="status.data.enabled ? 'green' : 'gray'"
          :label="status.data.enabled ? __('On') : __('Off')"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="canConfigure && settings.doc" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="settings.reload()"
        />
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
      <div v-if="settings.doc || !canConfigure" class="flex flex-col pb-6">
        <div class="mb-2 rounded-md bg-surface-gray-2 px-3 py-2">
          <p class="text-p-sm text-ink-gray-7">
            {{
              __(
                'Documentation support: the professional reviews every draft. The assistant writes only what was said or written, saves nothing by itself, and every request stays in the register below.',
              )
            }}
          </p>
        </div>

        <template v-if="canConfigure">
          <SettingRow
            :label="__('Use the assistant')"
            :description="
              __(
                'It starts only when the agency has set where the model runs, and the contract says the provider keeps nothing and trains on nothing.',
              )
            "
          >
            <Switch v-model="settings.doc.enabled" size="sm" />
          </SettingRow>
          <SettingRow
            :label="__('Forms from paper')"
            :description="
              __(
                'The PDF of a paper form becomes a draft template, checked in the builder.',
              )
            "
          >
            <Switch v-model="settings.doc.paper_forms" size="sm" />
          </SettingRow>
          <SettingRow
            v-if="status.data?.switches?.includes('note_drafts')"
            :label="__('Drafts from a note')"
            :description="
              __(
                'From a signed visit: a letter to the family doctor, the instructions after the visit. The practitioner checks and signs.',
              )
            "
          >
            <Switch v-model="settings.doc.note_drafts" size="sm" />
          </SettingRow>
          <SettingRow
            v-if="status.data?.switches?.includes('dictation')"
            :label="__('A visit from dictation')"
            :description="
              __(
                'The words of the practitioner into the fields of the sheet. Medicines, allergies and doses are confirmed one by one.',
              )
            "
          >
            <Switch v-model="settings.doc.dictation" size="sm" />
          </SettingRow>
          <SettingRow
            v-if="status.data?.switches?.includes('summaries')"
            :label="__('A summary before the visit')"
            :description="
              __(
                'What the record says, citing its sources: no scores, no alerts.',
              )
            "
          >
            <Switch v-model="settings.doc.summaries" size="sm" />
          </SettingRow>
          <SettingRow
            v-if="status.data?.switches?.includes('menus')"
            :label="__('Recipes for a meal plan')"
            :description="
              __(
                'Recipes of the library’s foods for a meal: the targets are the nutritionist’s, the nutrients come from the food tables.',
              )
            "
          >
            <Switch v-model="settings.doc.menus" size="sm" />
          </SettingRow>

          <template v-if="status.data?.switches?.includes('patient_chat')">
            <div class="pb-1 pt-6 text-base-semibold text-ink-gray-9">
              {{ __('The patients’ chat') }}
            </div>
            <SettingRow
              :label="__('On in the patient area')"
              :description="
                __(
                  'Hours, bookings and your frequent questions. It says it is an AI; health questions go to a person, an emergency to 112.',
                )
              "
            >
              <Switch v-model="settings.doc.patient_chat" size="sm" />
            </SettingRow>
            <div class="flex flex-col gap-3 px-2 py-3">
              <FormControl
                v-model="settings.doc.chat_about"
                type="textarea"
                :rows="4"
                :label="__('What the chat may say about the centre')"
                :placeholder="
                  __(
                    'Address, how to get there, parking, payments, what to bring',
                  )
                "
              />
              <span class="text-sm text-ink-gray-5">
                {{ __('Frequent questions') }}
              </span>
              <div
                v-for="(row, index) in settings.doc.chat_faq || []"
                :key="row.name || index"
                class="flex flex-col gap-2 rounded-md border border-outline-gray-2 p-3"
              >
                <div class="flex items-start gap-2">
                  <div class="min-w-0 flex-1">
                    <FormControl
                      v-model="row.question"
                      :placeholder="__('The question')"
                    />
                  </div>
                  <Button
                    variant="ghost"
                    icon="x"
                    class="touch-target shrink-0"
                    :aria-label="__('Remove')"
                    @click="settings.doc.chat_faq.splice(index, 1)"
                  />
                </div>
                <FormControl
                  v-model="row.answer"
                  type="textarea"
                  :rows="2"
                  :placeholder="__('The centre’s answer')"
                />
              </div>
              <Button
                class="w-fit"
                icon-left="plus"
                :label="__('Add a question')"
                @click="addQuestion"
              />
            </div>
          </template>

          <template v-if="tecnico">
            <div class="pb-1 pt-6 text-base-semibold text-ink-gray-9">
              {{ __('Where the model runs') }}
            </div>
            <div class="grid grid-cols-2 gap-4 px-2 py-3 max-md:grid-cols-1">
              <FormControl
                v-model="settings.doc.provider"
                type="select"
                :label="__('Provider')"
                :options="providers"
              />
              <FormControl
                v-model="settings.doc.model"
                :label="__('Model')"
                autocomplete="off"
              />
              <FormControl
                v-model="settings.doc.base_url"
                :label="__('Endpoint')"
                placeholder="https://"
                autocomplete="off"
              />
              <Password
                v-model="settings.doc.api_key"
                :label="__('API key')"
                placeholder="************"
              />
              <FormControl
                v-model="settings.doc.region"
                :label="__('Region')"
                :placeholder="
                  __('As the contract says, for example EU (Milan)')
                "
              />
              <div class="grid grid-cols-2 gap-4">
                <FormControl
                  v-model.number="settings.doc.request_timeout"
                  type="number"
                  :label="__('Timeout (seconds)')"
                />
                <FormControl
                  v-model.number="settings.doc.max_output_tokens"
                  type="number"
                  :label="__('Longest answer (tokens)')"
                />
              </div>
            </div>
            <SettingRow
              :label="__('No retention, no training')"
              :description="
                __(
                  'The contract with the provider says so. Without it the assistant does not start.',
                )
              "
            >
              <Switch v-model="settings.doc.no_retention" size="sm" />
            </SettingRow>
          </template>
          <ErrorMessage class="mt-2" :message="settings.save?.error" />
        </template>

        <template v-if="canReadRegister">
          <div class="pb-1 pt-8 text-base-semibold text-ink-gray-9">
            {{ __('The register') }}
          </div>
          <p class="px-2 pb-2 text-p-sm text-ink-gray-6">
            {{
              __(
                'Every request: which model, where, what came of the draft. Re-read a sample every month and mark it.',
              )
            }}
          </p>
          <p
            v-if="events.data && !events.data.events.length"
            class="px-2 text-p-sm text-ink-gray-5"
          >
            {{ __('Nothing asked yet.') }}
          </p>
          <button
            v-for="event in events.data?.events || []"
            :key="event.name"
            type="button"
            class="flex items-center justify-between gap-3 rounded px-2 py-2 text-left hover:bg-surface-gray-2"
            @click="openEvent(event.name)"
          >
            <span class="flex min-w-0 flex-col">
              <span class="truncate text-base text-ink-gray-8">
                {{ functionLabel(event.function) }} · {{ event.user_name }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ formatDate(event.creation, 'D MMM YYYY, HH:mm') }} ·
                {{ event.model }}
                <template v-if="event.region"> · {{ event.region }}</template>
              </span>
            </span>
            <span class="flex shrink-0 items-center gap-2">
              <span
                v-if="event.status === 'Accepted' && event.change_ratio != null"
                class="text-p-xs text-ink-gray-5 max-md:hidden"
              >
                {{ __('{0}% changed', [Math.round(event.change_ratio * 100)]) }}
              </span>
              <Badge
                v-if="event.reviewed_on"
                variant="subtle"
                theme="blue"
                :label="__('Reviewed')"
              />
              <Badge
                variant="subtle"
                :theme="statusTheme[event.status] || 'gray'"
                :label="__(event.status)"
              />
            </span>
          </button>
        </template>
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>

  <Dialog
    v-model="detail.show"
    :options="{ title: __('An event of the register'), size: '3xl' }"
  >
    <template #body-content>
      <div v-if="detail.event" class="flex flex-col gap-3 text-p-sm">
        <div
          class="grid grid-cols-2 gap-x-4 gap-y-1 text-ink-gray-7 max-md:grid-cols-1"
        >
          <span>{{ __('Asked by') }}: {{ detail.event.user_name }}</span>
          <span>{{
            formatDate(detail.event.creation, 'D MMM YYYY, HH:mm')
          }}</span>
          <span>{{ __('Provider') }}: {{ detail.event.provider }}</span>
          <span>{{ __('Model') }}: {{ detail.event.model }}</span>
          <span>{{ __('Region') }}: {{ detail.event.region || '—' }}</span>
          <span>
            {{ __('Tokens') }}: {{ detail.event.input_tokens }} →
            {{ detail.event.output_tokens }}
          </span>
        </div>
        <p v-if="detail.event.error" class="text-ink-red-7">
          {{ detail.event.error }}
        </p>
        <p
          v-if="detail.event.status === 'Accepted' && !detail.event.difference"
          class="text-ink-gray-6"
        >
          {{ __('Taken as it was.') }}
        </p>
        <template v-if="detail.event.difference">
          <span class="font-medium text-ink-gray-8">
            {{ __('What the person changed') }}
          </span>
          <pre
            class="max-h-72 overflow-auto whitespace-pre-wrap rounded bg-surface-gray-2 p-3 font-mono text-xs text-ink-gray-8"
            >{{ detail.event.difference }}</pre
          >
        </template>
        <template v-else-if="detail.event.draft">
          <span class="font-medium text-ink-gray-8">{{ __('The draft') }}</span>
          <pre
            class="max-h-72 overflow-auto whitespace-pre-wrap rounded bg-surface-gray-2 p-3 font-mono text-xs text-ink-gray-8"
            >{{ detail.event.draft }}</pre
          >
        </template>
        <FormControl
          v-model="detail.note"
          type="textarea"
          :rows="2"
          :label="__('Review note')"
          :placeholder="__('What you found re-reading it')"
        />
        <span v-if="detail.event.reviewed_on" class="text-ink-gray-5">
          {{
            __('Reviewed on {0}', [
              formatDate(detail.event.reviewed_on, 'D MMM YYYY'),
            ])
          }}
        </span>
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Close')" @click="detail.show = false" />
        <Button
          variant="solid"
          :label="__('Mark as reviewed')"
          :loading="detail.busy"
          @click="review"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingRow from '@/components/Settings/Telephony/SettingRow.vue'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Password,
  Switch,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive } from 'vue'

const { puo } = usersStore()
// where the model runs, and with which key, is the agency's (doc 30); whether
// to use it, the manager's; the clinic's events, the medical director's to read
const tecnico = puo('tecnico.integrazioni')
// reading the register is not setting it up: the medical director reads it too
const canConfigure = puo('impostazioni.generali') || tecnico
const canReadRegister =
  puo('assistente.registro') || puo('assistente.registro_clinico')

const providers = [
  { label: 'Anthropic', value: 'Anthropic' },
  { label: __('OpenAI compatible'), value: 'OpenAI compatible' },
]
const statusTheme = {
  Draft: 'orange',
  Accepted: 'green',
  Discarded: 'gray',
  Failed: 'red',
  Answered: 'blue',
}
const functionLabels = {
  form_from_paper: __('A form from paper'),
  letter_from_note: __('A letter from the note'),
  instructions_from_note: __('Instructions from the note'),
  visit_from_dictation: __('A visit from dictation'),
  summary_before_visit: __('A summary before the visit'),
  menu_recipes: __('Recipes for a meal plan'),
  patient_chat: __('The patients’ chat'),
}

function functionLabel(key) {
  return functionLabels[key] || key
}

// the settings only for who configures: the medical director reads the register
const settings = canConfigure
  ? useDocument('CRM Assistant Settings', 'CRM Assistant Settings').document
  : reactive({ doc: null, originalDoc: null, save: {} })
const status = createResource({
  url: 'crm.assistente.modello.get_status',
  auto: true,
})
const events = createResource({
  url: 'crm.assistente.modello.get_events',
  auto: canReadRegister,
})

const isDirty = computed(
  () =>
    settings.doc &&
    settings.originalDoc &&
    JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc),
)

function addQuestion() {
  if (!settings.doc.chat_faq) settings.doc.chat_faq = []
  settings.doc.chat_faq.push({
    doctype: 'CRM Assistant FAQ',
    question: '',
    answer: '',
  })
}

function update() {
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      status.reload()
      toast.success(__('Assistant updated'))
    },
  })
}

const detail = reactive({ show: false, event: null, note: '', busy: false })

async function openEvent(name) {
  detail.event = await call('crm.assistente.modello.get_event', { name })
  detail.note = detail.event.review_note || ''
  detail.show = true
}

async function review() {
  detail.busy = true
  try {
    detail.event = await call('crm.assistente.modello.mark_reviewed', {
      name: detail.event.name,
      note: detail.note,
    })
    events.reload()
    toast.success(__('Marked as reviewed'))
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  } finally {
    detail.busy = false
  }
}
</script>
