<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex min-w-0 items-center gap-2">
        <Breadcrumbs :items="breadcrumbs" />
        <input
          v-model="draft.title"
          :placeholder="__('Untitled automation')"
          class="min-w-0 max-w-64 border-0 bg-transparent p-0 text-base font-medium text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
        />
        <Badge
          :label="draft.enabled ? __('Active') : __('Draft')"
          :theme="draft.enabled ? 'green' : 'gray'"
          size="sm"
        />
        <Badge
          v-if="dirty"
          :label="__('Not saved')"
          theme="orange"
          variant="subtle"
          size="sm"
        />
      </div>
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Dropdown
          v-if="issues.length"
          :options="issueOptions"
          placement="right"
        >
          <Button variant="ghost" :label="issueLabel">
            <template #prefix>
              <FeatherIcon
                name="alert-triangle"
                class="size-4"
                :class="blocking ? 'text-ink-red-3' : 'text-ink-amber-3'"
              />
            </template>
          </Button>
        </Dropdown>
        <Button
          v-if="draft.name"
          :variant="showStats ? 'subtle' : 'ghost'"
          :label="__('Stats')"
          @click="toggleStats"
        >
          <template #prefix>
            <FeatherIcon name="bar-chart-2" class="size-4" />
          </template>
        </Button>
        <Button :label="__('Test run')" @click="showPreview = true">
          <template #prefix>
            <FeatherIcon name="play" class="size-4" />
          </template>
        </Button>
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          @click="save"
        />
        <Dropdown :options="moreOptions" placement="right">
          <Button variant="ghost" icon="lucide-more-horizontal" />
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>

  <div
    class="flex items-center gap-1 border-b border-outline-gray-2 px-4 py-1.5"
  >
    <Button
      v-for="entry in TABS"
      :key="entry.name"
      size="sm"
      :variant="tab === entry.name ? 'subtle' : 'ghost'"
      :label="__(entry.label)"
      :disabled="entry.name === 'enrollments' && !draft.name"
      @click="tab = entry.name"
    />
    <div class="flex-1" />
    <label class="flex items-center gap-2 text-sm text-ink-gray-7">
      <Switch
        :modelValue="Boolean(draft.enabled)"
        size="sm"
        @update:modelValue="togglePublish"
      />
      {{ __('Live') }}
    </label>
  </div>

  <div class="relative flex flex-1 overflow-hidden">
    <!-- builder -->
    <AutomationCanvas v-if="tab === 'builder'" />

    <!-- settings -->
    <div v-else-if="tab === 'settings'" class="flex-1 overflow-y-auto">
      <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4 py-6">
        <FormControl
          v-model="draft.title"
          type="text"
          :label="__('Title')"
          :placeholder="__('e.g. Welcome sequence')"
        />
        <FormControl
          v-model="draft.description"
          type="textarea"
          :rows="2"
          :label="__('Description')"
        />

        <div class="rounded-lg border border-outline-gray-2 p-3">
          <label class="flex items-start gap-2 text-sm text-ink-gray-7">
            <Switch
              v-model="draft.time_window_enabled"
              size="sm"
              class="mt-0.5"
            />
            <span>
              {{ __('Only send messages inside a time window') }}
              <span class="block text-xs text-ink-gray-5">
                {{
                  __(
                    'Outside the window the record waits: nobody gets a text at 3am.',
                  )
                }}
              </span>
            </span>
          </label>
          <div v-if="draft.time_window_enabled" class="mt-3">
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="draft.window_start"
                type="time"
                :label="__('From')"
              />
              <FormControl
                v-model="draft.window_end"
                type="time"
                :label="__('To')"
              />
            </div>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <Button
                v-for="day in WEEKDAYS"
                :key="day"
                size="sm"
                :variant="draft.window_days.includes(day) ? 'solid' : 'outline'"
                :label="__(day).slice(0, 3)"
                @click="toggleWindowDay(day)"
              />
            </div>
          </div>
        </div>

        <div
          v-if="draft.name"
          class="rounded-lg border border-outline-red-2 p-3 text-sm"
        >
          <div class="font-medium text-ink-gray-8">{{ __('Danger zone') }}</div>
          <div class="mt-1 flex items-center justify-between gap-3">
            <span class="text-ink-gray-5">
              {{ __('Deleting an automation also drops its enrolments.') }}
            </span>
            <Button
              theme="red"
              variant="subtle"
              :label="__('Delete')"
              @click="remove"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- enrollments -->
    <div v-else class="flex-1 overflow-y-auto">
      <EnrollmentsPanel v-if="draft.name" :automation="draft.name" />
    </div>

    <!-- side panel -->
    <aside
      v-if="tab === 'builder' && selectedId"
      class="absolute inset-y-0 right-0 z-10 w-full max-w-[400px] border-l border-outline-gray-2 bg-surface-white shadow-lg sm:static sm:z-auto sm:shadow-none"
    >
      <TriggerPanel v-if="selectedId === 'trigger'" />
      <StepPanel v-else-if="selectedStep" />
    </aside>
  </div>

  <CatalogPicker
    v-model="showPicker"
    :title="__('Add a step')"
    :categories="paletteCategories"
    :entries="paletteEntries"
    @select="insertFromPalette"
  />
  <RunPreviewDialog
    v-model="showPreview"
    :steps="draft.steps"
    :default-doctype="recordDoctype"
  />
</template>

<script setup>
import AutomationCanvas from '@/components/Automations/AutomationCanvas.vue'
import CatalogPicker from '@/components/Automations/CatalogPicker.vue'
import EnrollmentsPanel from '@/components/Automations/EnrollmentsPanel.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import RunPreviewDialog from '@/components/Automations/RunPreviewDialog.vue'
import StepPanel from '@/components/Automations/StepPanel.vue'
import TriggerPanel from '@/components/Automations/TriggerPanel.vue'
import {
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  FeatherIcon,
  FormControl,
  Switch,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import {
  computed,
  onBeforeUnmount,
  onMounted,
  provide,
  reactive,
  ref,
} from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  PALETTE,
  STEP_CATEGORIES,
  WEEKDAYS,
  cleanGroups,
  cloneStep,
  duplicateStep,
  findStep,
  hasErrors,
  moveStep,
  normalizeGroups,
  normalizeSteps,
  removeStep,
  stepFromPalette,
  triggerDoctype,
  validateAutomation,
} from '@/utils/automation'

const route = useRoute()
const router = useRouter()

const TABS = [
  { name: 'builder', label: 'Builder' },
  { name: 'settings', label: 'Settings' },
  { name: 'enrollments', label: 'Enrolments' },
]

const emptyDraft = () => ({
  name: null,
  title: '',
  description: '',
  enabled: false,
  trigger_event: 'Lead Created',
  trigger_condition_groups: normalizeGroups(null),
  trigger_config: {},
  allow_reenrollment: false,
  exit_on_reply: false,
  time_window_enabled: false,
  window_start: '',
  window_end: '',
  window_days: [],
  webhook_key: '',
  steps: [],
})

const draft = reactive(emptyDraft())
const tab = ref('builder')
const saving = ref(false)
const selectedId = ref('trigger')
const showPicker = ref(false)
const showPreview = ref(false)
const showStats = ref(false)
const stats = ref(null)
const clipboard = ref(null)
const saved = ref('')
let pickerTarget = null

const meta = createResource({
  url: 'crm.api.automation.get_builder_meta',
  cache: 'crm-automation-meta',
  auto: true,
})

// --- derived state ---------------------------------------------------------

const breadcrumbs = [
  { label: __('Automations'), route: { name: 'Automations' } },
]

/** Some triggers fire on both leads and deals; then the author picks the side. */
const fieldContext = ref('CRM Lead')

const recordDoctype = computed(
  () => triggerDoctype(draft.trigger_event) || fieldContext.value,
)

/** Fields offered to conditions, plus the wait outcome the engine exposes. */
const fields = computed(() => [
  ...(meta.data?.fields?.[recordDoctype.value] || []),
  {
    fieldname: 'wait_result',
    label: __('Wait result'),
    fieldtype: 'Select',
    options: 'event\ntimeout',
  },
])

const issues = computed(() => validateAutomation(draft))

const blocking = computed(() => hasErrors(issues.value))

const issueLabel = computed(() => __('{0} issue(s)', [issues.value.length]))

const issueOptions = computed(() =>
  issues.value.slice(0, 12).map((issue) => ({
    label: issue.message,
    icon: issue.level === 'error' ? 'alert-circle' : 'alert-triangle',
    onClick: () => {
      if (issue.node) select(issue.node)
      else tab.value = 'settings'
    },
  })),
)

const issuesByNode = computed(() => {
  const map = {}
  for (const issue of issues.value) {
    if (!issue.node) continue
    ;(map[issue.node] = map[issue.node] || []).push(issue)
  }
  return map
})

const selectedEntry = computed(() =>
  selectedId.value && selectedId.value !== 'trigger'
    ? findStep(draft.steps, selectedId.value)
    : null,
)

const selectedStep = computed(() => selectedEntry.value?.step || null)

const dirty = computed(() => saved.value !== JSON.stringify(payload()))

const paletteCategories = computed(() =>
  clipboard.value
    ? [
        { name: 'clipboard', label: 'Clipboard', icon: 'clipboard' },
        ...STEP_CATEGORIES,
      ]
    : STEP_CATEGORIES,
)

const paletteEntries = computed(() =>
  clipboard.value
    ? [
        {
          key: '__paste',
          type: clipboard.value.type,
          label: __('Paste «{0}»', [clipboard.value.type]),
          description: __('The step you copied, with its nested steps'),
          icon: 'clipboard',
          theme: 'gray',
          category: 'clipboard',
        },
        ...PALETTE,
      ]
    : PALETTE,
)

const moreOptions = computed(() => [
  {
    label: __('Duplicate automation'),
    icon: 'copy',
    condition: () => Boolean(draft.name),
    onClick: duplicate,
  },
  {
    label: __('Back to the list'),
    icon: 'arrow-left',
    onClick: () => router.push({ name: 'Automations' }),
  },
])

// --- editor context shared with the canvas and the panels ------------------

function select(id) {
  selectedId.value = id
}

function openPicker(list, index) {
  pickerTarget = { list, index }
  showPicker.value = true
}

function insertFromPalette(entry) {
  const step =
    entry.key === '__paste'
      ? cloneStep(clipboard.value)
      : stepFromPalette(entry)
  const target = pickerTarget || {
    list: draft.steps,
    index: draft.steps.length,
  }
  target.list.splice(target.index, 0, step)
  pickerTarget = null
  select(step.id)
}

provide('automation-editor', {
  draft,
  meta,
  fields,
  recordDoctype,
  selectedId,
  selectedStep,
  fieldContext,
  issuesByNode,
  stats,
  showStats,
  clipboard,
  select,
  openPicker,
  move: (list, index, delta) => moveStep(list, index, delta),
  remove: (id) => {
    removeStep(draft.steps, id)
    if (selectedId.value === id) selectedId.value = null
  },
  duplicate: (id) => {
    const copy = duplicateStep(draft.steps, id)
    if (copy) select(copy.id)
  },
  copy: (id) => {
    const entry = findStep(draft.steps, id)
    if (!entry) return
    clipboard.value = cloneStep(entry.step)
    toast.success(__('Step copied — paste it from any + on the canvas'))
  },
})

// --- loading and saving ----------------------------------------------------

function payload() {
  return {
    title: draft.title,
    description: draft.description,
    trigger_event: draft.trigger_event,
    trigger_condition: cleanGroups(draft.trigger_condition_groups),
    trigger_config: draft.trigger_config,
    allow_reenrollment: draft.allow_reenrollment,
    exit_on_reply: draft.exit_on_reply,
    time_window_enabled: draft.time_window_enabled,
    window_start: draft.window_start,
    window_end: draft.window_end,
    window_days: draft.window_days,
    steps: draft.steps,
  }
}

function load(name) {
  createResource({
    url: 'crm.api.automation.get_automation',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(draft, emptyDraft(), data, {
        enabled: Boolean(data.enabled),
        allow_reenrollment: Boolean(data.allow_reenrollment),
        exit_on_reply: Boolean(data.exit_on_reply),
        time_window_enabled: Boolean(data.time_window_enabled),
        trigger_config: data.trigger_config || {},
        trigger_condition_groups: normalizeGroups(data.trigger_condition),
        window_days: data.window_days || [],
        steps: normalizeSteps(data.steps || []),
      })
      saved.value = JSON.stringify(payload())
      selectedId.value = 'trigger'
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Could not load the automation'))
      router.push({ name: 'Automations' })
    },
  })
}

async function save() {
  if (!draft.title.trim()) {
    tab.value = 'settings'
    toast.error(__('The automation needs a title'))
    return false
  }
  if (blocking.value) {
    toast.error(issues.value.find((issue) => issue.level === 'error').message)
    return false
  }
  saving.value = true
  try {
    const data = await call('crm.api.automation.save_automation', {
      name: draft.name,
      automation: payload(),
    })
    draft.name = data.name
    draft.webhook_key = data.webhook_key || ''
    draft.steps = normalizeSteps(data.steps || [])
    saved.value = JSON.stringify(payload())
    if (route.params.automationId === 'new') {
      router.replace({
        name: 'Automation',
        params: { automationId: data.name },
      })
    }
    toast.success(__('Automation saved'))
    return true
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save'))
    return false
  } finally {
    saving.value = false
  }
}

async function togglePublish(enabled) {
  if (enabled && issues.value.length) {
    toast.error(
      __('Fix the {0} issue(s) before going live', [issues.value.length]),
    )
    return
  }
  // pausing must always work, even while the draft still has problems
  if (enabled && (dirty.value || !draft.name) && !(await save())) return
  if (!draft.name) return
  try {
    await call('crm.api.automation.toggle_automation', {
      name: draft.name,
      enabled,
    })
    draft.enabled = enabled
    toast.success(enabled ? __('Automation is live') : __('Automation paused'))
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not change the state'))
  }
}

async function toggleStats() {
  showStats.value = !showStats.value
  if (!showStats.value || !draft.name) return
  try {
    stats.value = await call('crm.api.automation.get_step_stats', {
      name: draft.name,
    })
  } catch {
    stats.value = null
  }
}

async function duplicate() {
  // the copy is made from what is stored, so unsaved edits go in first
  if (dirty.value && !(await save())) return
  const data = await call('crm.api.automation.duplicate_automation', {
    name: draft.name,
  })
  saved.value = JSON.stringify(payload())
  router.push({ name: 'Automation', params: { automationId: data.name } })
  toast.success(__('Copy created'))
}

async function remove() {
  if (!window.confirm(__('Delete «{0}»?', [draft.title]))) return
  await call('crm.api.automation.delete_automation', { name: draft.name })
  saved.value = JSON.stringify(payload())
  router.push({ name: 'Automations' })
}

function toggleWindowDay(day) {
  const index = draft.window_days.indexOf(day)
  if (index === -1) draft.window_days.push(day)
  else draft.window_days.splice(index, 1)
}

// --- shortcuts and guards --------------------------------------------------

function onKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key === 's') {
    event.preventDefault()
    save()
  }
  if (event.key === 'Escape') selectedId.value = null
}

function warnOnUnload(event) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  const id = route.params.automationId
  if (id && id !== 'new') {
    load(id)
  } else {
    saved.value = JSON.stringify(payload())
    const recipe = window.history.state?.recipe
    if (recipe) Object.assign(draft, recipe)
  }
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('beforeunload', warnOnUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('beforeunload', warnOnUnload)
})

onBeforeRouteLeave(() => {
  if (!dirty.value) return true
  return window.confirm(__('You have unsaved changes. Leave anyway?'))
})
</script>
