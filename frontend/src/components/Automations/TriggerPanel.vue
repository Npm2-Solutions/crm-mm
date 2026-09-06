<template>
  <div v-if="trigger" class="flex h-full flex-col">
    <div
      class="flex items-start gap-2.5 border-b border-outline-gray-2 px-4 py-3"
    >
      <div
        class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-gray-2 text-ink-gray-7"
      >
        <FeatherIcon
          :name="triggerDefinition(trigger.event).icon"
          class="size-4"
        />
      </div>
      <div class="min-w-0 flex-1">
        <div class="text-base font-semibold text-ink-gray-8">
          {{ __('Trigger') }}
          <span v-if="draft.triggers.length > 1">{{ position }}</span>
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
          :name="triggerDefinition(trigger.event).icon"
          class="size-4 text-ink-gray-6"
        />
        <span class="flex-1 text-base font-medium text-ink-gray-8">
          {{ __(trigger.event) }}
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
          v-model="trigger.config.tag"
          type="text"
          :label="__('Only this tag (empty = any)')"
        />
        <FormControl
          v-else-if="configKind === 'link'"
          v-model="trigger.config.link"
          type="select"
          :label="__('Tracked link')"
          :options="linkOptions"
        />
        <template v-else-if="configKind === 'date'">
          <FormControl
            v-model="trigger.config.doctype"
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
              :modelValue="trigger.config.date_field"
              :options="dateFieldOptions"
              :placeholder="__('e.g. expected_closure_date')"
              @update:modelValue="
                (option) => (trigger.config.date_field = option?.value || '')
              "
            />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <FormControl
              v-model="trigger.config.offset_days"
              type="number"
              :label="__('Days offset')"
            />
            <FormControl
              v-model="trigger.config.direction"
              type="select"
              :label="__('Direction')"
              :options="[
                { label: __('Before'), value: 'before' },
                { label: __('After'), value: 'after' },
              ]"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="trigger.config.annual" size="sm" />
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
        v-if="!sharedTriggerDoctype(draft.triggers)"
        v-model="editor.fieldContext.value"
        type="select"
        :label="__('Fields to work with (the triggers do not agree)')"
        :options="[
          { label: __('Lead'), value: 'CRM Lead' },
          { label: __('Deal'), value: 'CRM Deal' },
        ]"
      />

      <!-- who gets in through this trigger -->
      <div class="flex flex-col gap-2">
        <div class="text-xs font-medium uppercase text-ink-gray-5">
          {{ __('Only enrol records matching') }}
        </div>
        <ConditionBuilder
          v-model="trigger.condition_groups"
          :fields="editor.fields.value"
        />
        <p class="text-xs text-ink-gray-4">
          {{ __('These conditions belong to this trigger alone.') }}
        </p>
      </div>
    </div>

    <div
      class="flex items-center justify-between border-t border-outline-gray-2 px-4 py-3"
    >
      <span class="text-xs text-ink-gray-5">
        {{ __('{0} trigger(s)', [draft.triggers.length]) }}
      </span>
      <Button
        variant="ghost"
        theme="red"
        iconLeft="trash-2"
        :label="__('Delete trigger')"
        :disabled="draft.triggers.length <= 1"
        @click="editor.removeTrigger(trigger.id)"
      />
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
  sharedTriggerDoctype,
  triggerConfigKind,
  triggerDefinition,
  triggerEntries,
} from '@/utils/automation'

const editor = inject('automation-editor')
const draft = editor.draft
const trigger = computed(() => editor.selectedTrigger.value)

const showPicker = ref(false)

const position = computed(
  () => draft.triggers.findIndex((row) => row.id === trigger.value?.id) + 1,
)

const configKind = computed(() => triggerConfigKind(trigger.value?.event))

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
  const doctype = trigger.value?.config?.doctype || 'CRM Lead'
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
  trigger.value.event = entry.key
  trigger.value.config = {}
}

function copyWebhook() {
  navigator.clipboard?.writeText(webhookUrl.value)
  toast.success(__('URL copied'))
}
</script>
