<template>
  <div v-if="step" class="flex h-full flex-col">
    <div
      class="flex items-start gap-2.5 border-b border-outline-gray-2 px-4 py-3"
    >
      <div
        class="grid size-8 shrink-0 place-items-center rounded-md"
        :class="ICON_CLASSES[stepTheme(step.type)] || ICON_CLASSES.gray"
      >
        <FeatherIcon :name="stepIcon(step.type)" class="size-4" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="truncate text-base font-semibold text-ink-gray-8">
          {{ stepLabel(step.type) }}
        </div>
        <div class="truncate text-sm text-ink-gray-5">
          {{ stepDefinition(step.type).description }}
        </div>
      </div>
      <Button
        variant="ghost"
        icon="lucide-x"
        :label="__('Close')"
        @click="editor.select(null)"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-4 py-4">
      <div class="flex flex-col gap-3">
        <!-- email -->
        <template v-if="step.type === 'send_email'">
          <FormControl
            v-model="step.email_template"
            type="select"
            :label="__('Email template (optional)')"
            :options="templateOptions"
          />
          <MergeFieldInput
            v-model="step.subject"
            :label="__('Subject')"
            :placeholder="__('Hi {0}', ['{{ first_name }}'])"
          />
          <MergeFieldInput
            v-model="step.message"
            type="textarea"
            :rows="8"
            :label="__('Message')"
          />
        </template>

        <!-- sms / internal notification -->
        <template v-else-if="['send_sms', 'notify'].includes(step.type)">
          <MergeFieldInput
            v-model="step.message"
            type="textarea"
            :rows="6"
            :label="__('Message')"
          />
        </template>

        <!-- whatsapp -->
        <template v-else-if="step.type === 'send_whatsapp_template'">
          <FormControl
            v-model="step.template"
            type="select"
            :label="__('Template')"
            :options="whatsappOptions"
          />
          <div>
            <div class="mb-1 flex items-center justify-between">
              <span class="text-xs text-ink-gray-5">
                {{ __('Template variables') }}
              </span>
              <Button
                size="sm"
                variant="ghost"
                iconLeft="plus"
                :label="__('Add')"
                @click="addTemplateParameter"
              />
            </div>
            <div class="flex flex-col gap-2">
              <MergeFieldInput
                v-for="(value, index) in step.template_parameters || []"
                :key="index"
                :modelValue="value"
                :label="__('{{{0}}}', [index + 1])"
                @update:modelValue="
                  (updated) => (step.template_parameters[index] = updated)
                "
              />
            </div>
          </div>
        </template>

        <!-- task -->
        <template v-else-if="step.type === 'create_task'">
          <MergeFieldInput v-model="step.title" :label="__('Task title')" />
          <FormControl
            v-model="step.due_in_days"
            type="number"
            :label="__('Due in (days)')"
          />
          <FormControl
            v-model="step.assigned_to"
            type="select"
            :label="__('Assign to (optional)')"
            :options="userOptions"
          />
        </template>

        <!-- assignment -->
        <template v-else-if="step.type === 'assign'">
          <div class="text-xs text-ink-gray-5">
            {{ __('One user = fixed. Several = even round robin.') }}
          </div>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="user in editor.meta.data?.users || []"
              :key="user.name"
              size="sm"
              :variant="
                (step.users || []).includes(user.name) ? 'solid' : 'outline'
              "
              :label="user.full_name || user.name"
              @click="toggleUser(user.name)"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="step.only_if_unassigned" size="sm" />
            {{ __('Only when nobody is assigned yet') }}
          </label>
        </template>

        <!-- note -->
        <template
          v-else-if="['add_note', 'add_tag_comment'].includes(step.type)"
        >
          <MergeFieldInput
            v-model="step.comment"
            type="textarea"
            :rows="5"
            :label="__('Note')"
          />
        </template>

        <!-- tags -->
        <template v-else-if="['add_tag', 'remove_tag'].includes(step.type)">
          <FormControl v-model="step.tag" type="text" :label="__('Tag')" />
          <Dropdown v-if="tagOptions.length" :options="tagOptions">
            <Button
              variant="ghost"
              size="sm"
              class="self-start"
              :label="__('Pick an existing tag')"
            />
          </Dropdown>
        </template>

        <!-- update field -->
        <template v-else-if="step.type === 'set_field'">
          <div>
            <div class="mb-1 text-xs text-ink-gray-5">{{ __('Field') }}</div>
            <Autocomplete
              :modelValue="step.field"
              :options="fieldOptions"
              :placeholder="__('Pick a field')"
              @update:modelValue="
                (option) => (step.field = option?.value || '')
              "
            />
          </div>
          <div>
            <div class="mb-1 text-xs text-ink-gray-5">{{ __('Value') }}</div>
            <ValueInput
              v-model="step.value"
              :field="selectedField"
              :placeholder="__('value')"
            />
          </div>
          <p class="text-xs text-ink-gray-4">
            {{ __('Fields come from {0}.', [editor.recordDoctype.value]) }}
          </p>
        </template>

        <!-- convert -->
        <template v-else-if="step.type === 'convert_to_deal'">
          <p class="text-sm text-ink-gray-6">
            {{
              __(
                'Turns the lead into a deal — the "create opportunity" of GoHighLevel. Skipped when the record is already a deal.',
              )
            }}
          </p>
        </template>

        <!-- webhook -->
        <template v-else-if="step.type === 'webhook'">
          <FormControl
            v-model="step.method"
            type="select"
            :label="__('Method')"
            :options="
              ['POST', 'GET', 'PUT', 'DELETE'].map((m) => ({
                label: m,
                value: m,
              }))
            "
          />
          <FormControl v-model="step.url" type="text" :label="__('URL')" />
          <MergeFieldInput
            v-model="step.body"
            type="textarea"
            :rows="6"
            :label="__('JSON body (optional)')"
          />
        </template>

        <!-- other automations -->
        <template
          v-else-if="
            ['add_to_workflow', 'remove_from_workflow'].includes(step.type)
          "
        >
          <FormControl
            v-model="step.automation"
            type="select"
            :label="__('Automation')"
            :options="automationOptions"
          />
        </template>

        <!-- wait -->
        <template v-else-if="step.type === 'wait'">
          <FormControl
            v-model="step.mode"
            type="select"
            :label="__('Wait for')"
            :options="waitModeOptions"
          />
          <div
            v-if="(step.mode || 'duration') === 'duration'"
            class="grid grid-cols-3 gap-2"
          >
            <FormControl
              v-model="step.days"
              type="number"
              :label="__('Days')"
            />
            <FormControl
              v-model="step.hours"
              type="number"
              :label="__('Hours')"
            />
            <FormControl
              v-model="step.minutes"
              type="number"
              :label="__('Minutes')"
            />
          </div>
          <template v-else-if="step.mode === 'until_time'">
            <FormControl
              v-model="step.time"
              type="time"
              :label="__('Resume at')"
            />
            <div>
              <div class="mb-1 text-xs text-ink-gray-5">
                {{ __('Only on these days (optional)') }}
              </div>
              <div class="flex flex-wrap gap-1.5">
                <Button
                  v-for="day in WEEKDAYS"
                  :key="day"
                  size="sm"
                  :variant="
                    (step.weekdays || []).includes(day) ? 'solid' : 'outline'
                  "
                  :label="__(day).slice(0, 3)"
                  @click="toggleWeekday(day)"
                />
              </div>
            </div>
          </template>
          <template v-else>
            <FormControl
              v-if="step.mode === 'until_link_click'"
              v-model="step.link"
              type="select"
              :label="__('Tracked link')"
              :options="linkOptions"
            />
            <FormControl
              v-model="step.timeout_hours"
              type="number"
              :label="__('Timeout in hours (empty = wait forever)')"
            />
            <p class="text-xs text-ink-gray-4">
              {{
                __(
                  'After this wait an If / Else on the field «wait_result» tells the answer (event) from the timeout.',
                )
              }}
            </p>
          </template>
        </template>

        <!-- goal -->
        <template v-else-if="step.type === 'goal'">
          <FormControl
            v-model="step.event"
            type="select"
            :label="__('Goal')"
            :options="goalOptions"
          />
          <FormControl
            v-if="step.event === 'link_clicked'"
            v-model="step.value"
            type="select"
            :label="__('Tracked link (empty = any)')"
            :options="linkOptions"
          />
          <FormControl
            v-else-if="step.event === 'status_is'"
            v-model="step.value"
            type="select"
            :label="__('Status')"
            :options="statusOptions"
          />
          <FormControl
            v-else-if="step.event === 'tag_added'"
            v-model="step.value"
            type="text"
            :label="__('Tag (empty = any)')"
          />
          <FormControl
            v-model="step.outcome"
            type="select"
            :label="__('If the record gets here without meeting the goal')"
            :options="[
              { label: __('Carry on anyway'), value: 'continue' },
              { label: __('Wait until it is met'), value: 'wait' },
              { label: __('End the automation'), value: 'end' },
            ]"
          />
        </template>

        <!-- go to -->
        <template v-else-if="step.type === 'go_to'">
          <FormControl
            v-model="step.target"
            type="select"
            :label="__('Jump to the step labelled')"
            :options="labelOptions"
          />
          <p v-if="!labelOptions.length" class="text-xs text-ink-amber-3">
            {{
              __('No step carries a label yet — set one on the target step.')
            }}
          </p>
        </template>

        <!-- stop -->
        <template v-else-if="step.type === 'stop_if'">
          <div class="text-xs text-ink-gray-5">{{ __('Leave when') }}</div>
          <ConditionBuilder
            v-model="step.condition_groups"
            :fields="editor.fields.value"
          />
        </template>

        <!-- branches -->
        <template v-else-if="step.type === 'if_else'">
          <div
            v-for="(branch, index) in step.branches"
            :key="branch.id || index"
            class="rounded-md border border-outline-gray-2 p-2"
          >
            <div class="mb-2 flex items-center gap-2">
              <FormControl
                v-model="branch.label"
                type="text"
                class="flex-1"
                :placeholder="__('Branch {0}', [index + 1])"
              />
              <Button
                variant="ghost"
                icon="lucide-trash-2"
                :label="__('Remove branch')"
                :disabled="step.branches.length <= 1"
                @click="step.branches.splice(index, 1)"
              />
            </div>
            <ConditionBuilder
              v-model="branch.condition_groups"
              :fields="editor.fields.value"
            />
          </div>
          <Button
            variant="subtle"
            iconLeft="plus"
            class="self-start"
            :label="__('Add branch')"
            @click="step.branches.push(newBranch())"
          />
          <p class="text-xs text-ink-gray-4">
            {{
              __(
                'Branches are checked top to bottom; whatever matches none takes «None».',
              )
            }}
          </p>
        </template>

        <!-- split test -->
        <template v-else-if="step.type === 'split'">
          <div
            v-for="(path, index) in step.paths"
            :key="path.id || index"
            class="grid grid-cols-[1fr_88px_32px] items-end gap-2"
          >
            <FormControl
              v-model="path.label"
              type="text"
              :label="index === 0 ? __('Path') : ''"
              :placeholder="__('Path {0}', [index + 1])"
            />
            <FormControl
              v-model="path.percent"
              type="number"
              :label="index === 0 ? '%' : ''"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              :label="__('Remove path')"
              :disabled="step.paths.length <= 2"
              @click="step.paths.splice(index, 1)"
            />
          </div>
          <div class="flex items-center justify-between">
            <Button
              variant="ghost"
              iconLeft="plus"
              :label="__('Add path')"
              @click="step.paths.push(newPath('', 0))"
            />
            <span
              class="text-xs"
              :class="splitTotal === 100 ? 'text-ink-gray-5' : 'text-ink-red-3'"
            >
              {{ __('total') }} {{ splitTotal }}%
            </span>
          </div>
        </template>

        <template v-else-if="step.type === 'exit'">
          <p class="text-sm text-ink-gray-6">
            {{ __('The record stops here and leaves this automation.') }}
          </p>
        </template>

        <!-- gate + label, for every step that supports them -->
        <template v-if="stepDefinition(step.type).gateable">
          <div class="mt-2 border-t border-outline-gray-1 pt-3">
            <label class="flex items-center gap-2 text-sm text-ink-gray-7">
              <Switch
                :modelValue="Boolean(step.condition_groups)"
                size="sm"
                @update:modelValue="toggleGate"
              />
              {{ __('Run only if…') }}
            </label>
            <ConditionBuilder
              v-if="step.condition_groups"
              v-model="step.condition_groups"
              class="mt-2"
              :fields="editor.fields.value"
            />
          </div>
          <FormControl
            v-model="step.label"
            type="text"
            :label="__('Label (so a Go To can jump here)')"
          />
        </template>
      </div>
    </div>

    <div
      class="flex items-center justify-between border-t border-outline-gray-2 px-4 py-3"
    >
      <Button
        variant="ghost"
        iconLeft="copy"
        :label="__('Duplicate')"
        @click="editor.duplicate(step.id)"
      />
      <Button
        variant="ghost"
        theme="red"
        iconLeft="trash-2"
        :label="__('Delete')"
        @click="editor.remove(step.id)"
      />
    </div>
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import ConditionBuilder from './ConditionBuilder.vue'
import MergeFieldInput from './MergeFieldInput.vue'
import ValueInput from './ValueInput.vue'
import { Button, Dropdown, FeatherIcon, FormControl, Switch } from 'frappe-ui'
import { computed, inject } from 'vue'
import {
  GOAL_EVENTS,
  ICON_CLASSES,
  WAIT_MODES,
  WEEKDAYS,
  newBranch,
  newConditionGroup,
  newPath,
  stepDefinition,
  stepIcon,
  stepLabel,
  stepLabels,
  stepTheme,
} from '@/utils/automation'

const editor = inject('automation-editor')
const step = computed(() => editor.selectedStep.value)

const withEmpty = (options) => [{ label: '', value: '' }, ...options]

const templateOptions = computed(() =>
  withEmpty(
    (editor.meta.data?.email_templates || []).map((template) => ({
      label: template.subject
        ? `${template.name} — ${template.subject}`
        : template.name,
      value: template.name,
    })),
  ),
)

const whatsappOptions = computed(() =>
  withEmpty(
    (editor.meta.data?.whatsapp_templates || []).map((name) => ({
      label: name,
      value: name,
    })),
  ),
)

const userOptions = computed(() =>
  withEmpty(
    (editor.meta.data?.users || []).map((user) => ({
      label: user.full_name || user.name,
      value: user.name,
    })),
  ),
)

const automationOptions = computed(() => {
  const options = (editor.meta.data?.automations || [])
    .filter((automation) => automation.name !== editor.draft.name)
    .map((automation) => ({
      label: automation.title || automation.name,
      value: automation.name,
    }))
  if (step.value?.type === 'remove_from_workflow') {
    return [{ label: __('All automations'), value: 'all' }, ...options]
  }
  return withEmpty(options)
})

const linkOptions = computed(() =>
  withEmpty(
    (editor.meta.data?.tracked_links || []).map((name) => ({
      label: name,
      value: name,
    })),
  ),
)

const tagOptions = computed(() =>
  (editor.meta.data?.tags || []).map((tag) => ({
    label: tag,
    onClick: () => (step.value.tag = tag),
  })),
)

const statusOptions = computed(() => {
  const statuses =
    editor.recordDoctype.value === 'CRM Deal'
      ? editor.meta.data?.deal_statuses
      : editor.meta.data?.lead_statuses
  return withEmpty(
    (statuses || []).map((name) => ({ label: name, value: name })),
  )
})

const goalOptions = computed(() =>
  GOAL_EVENTS.map((goal) => ({ label: __(goal.label), value: goal.value })),
)

const waitModeOptions = computed(() =>
  WAIT_MODES.map((mode) => ({ label: __(mode.label), value: mode.value })),
)

const fieldOptions = computed(() =>
  editor.fields.value.map((field) => ({
    label: field.label || field.fieldname,
    value: field.fieldname,
    description: field.fieldname,
  })),
)

const selectedField = computed(
  () =>
    editor.fields.value.find(
      (field) => field.fieldname === step.value?.field,
    ) || { fieldtype: 'Data', options: '' },
)

const labelOptions = computed(() =>
  stepLabels(editor.draft.steps)
    .filter((label) => label !== step.value?.label)
    .map((label) => ({ label, value: label })),
)

const splitTotal = computed(() =>
  (step.value?.paths || []).reduce(
    (total, path) => total + (Number(path.percent) || 0),
    0,
  ),
)

function toggleGate(enabled) {
  if (enabled) step.value.condition_groups = [newConditionGroup()]
  else delete step.value.condition_groups
}

function toggleUser(user) {
  const users = step.value.users || (step.value.users = [])
  const index = users.indexOf(user)
  if (index === -1) users.push(user)
  else users.splice(index, 1)
}

function toggleWeekday(day) {
  const days = step.value.weekdays || (step.value.weekdays = [])
  const index = days.indexOf(day)
  if (index === -1) days.push(day)
  else days.splice(index, 1)
}

function addTemplateParameter() {
  if (!step.value.template_parameters) step.value.template_parameters = []
  step.value.template_parameters.push('')
}
</script>
