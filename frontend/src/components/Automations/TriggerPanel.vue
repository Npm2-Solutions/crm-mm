<template>
  <div class="flex h-full flex-col">
    <div
      class="flex items-start gap-2.5 border-b border-outline-gray-2 px-4 py-3"
    >
      <div
        class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-gray-2 text-ink-gray-7"
      >
        <FeatherIcon name="zap" class="size-4" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="text-base font-semibold text-ink-gray-8">
          {{ __('Trigger') }}
        </div>
        <div class="truncate text-sm text-ink-gray-5">
          {{ __('What puts a record into this automation') }}
        </div>
      </div>
      <Button
        variant="ghost"
        icon="lucide-x"
        :label="__('Close')"
        @click="editor.select(null)"
      />
    </div>

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
      <button
        class="flex items-center gap-2.5 rounded-lg border border-outline-gray-2 px-3 py-2.5 text-left hover:border-outline-gray-3 hover:bg-surface-gray-1"
        @click="showPicker = true"
      >
        <FeatherIcon
          :name="triggerDefinition(draft.trigger_event).icon"
          class="size-4 text-ink-gray-6"
        />
        <span class="flex-1 text-base font-medium text-ink-gray-8">
          {{ __(draft.trigger_event) }}
        </span>
        <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
      </button>

      <!-- event filters: which tag, which link, which date -->
      <div v-if="configKind" class="flex flex-col gap-2">
        <div class="text-xs font-medium uppercase text-ink-gray-5">
          {{ __('Event filters') }}
        </div>
        <FormControl
          v-if="configKind === 'tag'"
          v-model="draft.trigger_config.tag"
          type="text"
          :label="__('Only this tag (empty = any)')"
        />
        <FormControl
          v-else-if="configKind === 'link'"
          v-model="draft.trigger_config.link"
          type="select"
          :label="__('Tracked link')"
          :options="linkOptions"
        />
        <template v-else-if="configKind === 'date'">
          <FormControl
            v-model="draft.trigger_config.doctype"
            type="select"
            :label="__('Record')"
            :options="[
              { label: __('Lead'), value: 'CRM Lead' },
              { label: __('Deal'), value: 'CRM Deal' },
            ]"
          />
          <div>
            <div class="mb-1 text-xs text-ink-gray-5">
              {{ __('Date field') }}
            </div>
            <Autocomplete
              :modelValue="draft.trigger_config.date_field"
              :options="dateFieldOptions"
              :placeholder="__('e.g. expected_closure_date')"
              @update:modelValue="
                (option) =>
                  (draft.trigger_config.date_field = option?.value || '')
              "
            />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <FormControl
              v-model="draft.trigger_config.offset_days"
              type="number"
              :label="__('Days offset')"
            />
            <FormControl
              v-model="draft.trigger_config.direction"
              type="select"
              :label="__('Direction')"
              :options="[
                { label: __('Before'), value: 'before' },
                { label: __('After'), value: 'after' },
              ]"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="draft.trigger_config.annual" size="sm" />
            {{ __('Every year (birthdays and anniversaries)') }}
          </label>
        </template>
        <div v-else-if="configKind === 'webhook'" class="text-sm">
          <div v-if="draft.webhook_key" class="flex items-start gap-2">
            <code
              class="min-w-0 flex-1 break-all rounded bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-7"
            >
              POST {{ webhookUrl }}
            </code>
            <Button
              variant="ghost"
              icon="lucide-copy"
              :label="__('Copy')"
              @click="copyWebhook"
            />
          </div>
          <div v-else class="text-ink-gray-5">
            {{ __('Save the automation to get its webhook URL.') }}
          </div>
        </div>
      </div>

      <FormControl
        v-if="!triggerDefinition(draft.trigger_event).doctype"
        v-model="editor.fieldContext.value"
        type="select"
        :label="__('This trigger fires on both — pick the fields to work with')"
        :options="[
          { label: __('Lead'), value: 'CRM Lead' },
          { label: __('Deal'), value: 'CRM Deal' },
        ]"
      />

      <!-- who gets in -->
      <div class="flex flex-col gap-2">
        <div class="text-xs font-medium uppercase text-ink-gray-5">
          {{ __('Only enrol records matching') }}
        </div>
        <ConditionBuilder
          v-model="draft.trigger_condition_groups"
          :fields="editor.fields.value"
        />
      </div>

      <!-- re-entry rules -->
      <div class="flex flex-col gap-2 border-t border-outline-gray-1 pt-3">
        <label class="flex items-start gap-2 text-sm text-ink-gray-7">
          <Switch v-model="draft.allow_reenrollment" size="sm" class="mt-0.5" />
          <span>
            {{ __('Allow re-enrolment') }}
            <span class="block text-xs text-ink-gray-5">
              {{
                __(
                  'Off: a record enters once and never again. On: it can re-enter once it has left.',
                )
              }}
            </span>
          </span>
        </label>
        <label class="flex items-start gap-2 text-sm text-ink-gray-7">
          <Switch v-model="draft.exit_on_reply" size="sm" class="mt-0.5" />
          <span>
            {{ __('Stop on response') }}
            <span class="block text-xs text-ink-gray-5">
              {{ __('The record leaves as soon as it answers.') }}
            </span>
          </span>
        </label>
      </div>
    </div>

    <CatalogPicker
      v-model="showPicker"
      :title="__('Choose the trigger')"
      :categories="TRIGGER_CATEGORIES"
      :entries="triggerOptions"
      @select="pickTrigger"
    />
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import CatalogPicker from './CatalogPicker.vue'
import ConditionBuilder from './ConditionBuilder.vue'
import { Button, FeatherIcon, FormControl, Switch, toast } from 'frappe-ui'
import { computed, inject, ref } from 'vue'
import {
  TRIGGER_CATEGORIES,
  triggerConfigKind,
  triggerDefinition,
  triggerEntries,
} from '@/utils/automation'

const editor = inject('automation-editor')
const draft = editor.draft

const showPicker = ref(false)

const configKind = computed(() => triggerConfigKind(draft.trigger_event))

const triggerOptions = computed(() =>
  triggerEntries(editor.meta.data?.trigger_events || []),
)

const linkOptions = computed(() => [
  { label: '', value: '' },
  ...(editor.meta.data?.tracked_links || []).map((name) => ({
    label: name,
    value: name,
  })),
])

/** Date reminders only make sense on date fields of the chosen record. */
const dateFieldOptions = computed(() => {
  const doctype = draft.trigger_config.doctype || 'CRM Lead'
  return (editor.meta.data?.fields?.[doctype] || [])
    .filter((field) => ['Date', 'Datetime'].includes(field.fieldtype))
    .map((field) => ({
      label: field.label || field.fieldname,
      value: field.fieldname,
      description: field.fieldname,
    }))
})

const webhookUrl = computed(
  () =>
    `${window.location.origin}/api/method/crm.api.automation.inbound_webhook` +
    `?automation=${encodeURIComponent(draft.name || '')}&key=${draft.webhook_key}`,
)

function pickTrigger(entry) {
  draft.trigger_event = entry.key
  draft.trigger_config = {}
}

function copyWebhook() {
  navigator.clipboard?.writeText(webhookUrl.value)
  toast.success(__('URL copied'))
}
</script>
