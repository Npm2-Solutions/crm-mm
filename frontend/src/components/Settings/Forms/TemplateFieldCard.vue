<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <div
    class="rounded border bg-surface-elevation-2 text-ink-gray-8"
    :class="[
      expanded ? 'border-outline-gray-3' : 'border-outline-gray-2',
      problems.length ? 'ring-1 ring-outline-amber-2' : '',
    ]"
    :data-field="field.id"
  >
    <!-- grip · kind · words · what applies to it · open · menu -->
    <div class="flex items-center gap-2 px-2.5 py-2">
      <DragVerticalIcon
        class="drag-handle h-3.5 shrink-0 cursor-grab text-ink-gray-5"
      />
      <component
        :is="componentIcon(field.type)"
        class="size-4 shrink-0 text-ink-gray-5"
        :title="kindLabel"
      />
      <button
        type="button"
        class="flex min-w-0 flex-1 items-center gap-1.5 text-left"
        @click="$emit('toggle')"
      >
        <span
          class="min-w-0 truncate text-base"
          :class="headline ? 'text-ink-gray-8' : 'italic text-ink-gray-5'"
        >
          {{ headline || __('Write the question') }}
        </span>
        <span
          v-if="field.required || field.must_accept"
          class="shrink-0 text-ink-red-7"
        >
          *
        </span>
      </button>
      <div class="flex shrink-0 items-center gap-1 max-md:hidden">
        <!-- the person's field it fills, on a form of the website -->
        <Badge
          v-if="personLabel"
          :label="personLabel"
          theme="blue"
          size="sm"
          variant="subtle"
        />
        <Badge
          v-if="has(field.show_if)"
          :label="__('Conditional')"
          size="sm"
          variant="subtle"
        />
        <Badge
          v-if="has(field.stop_if)"
          :label="__('Stops')"
          theme="red"
          size="sm"
          variant="subtle"
        />
        <Badge
          v-if="problems.length"
          :label="__('To fix')"
          theme="orange"
          size="sm"
          variant="subtle"
        />
      </div>
      <Button
        :aria-label="expanded ? __('Collapse') : __('Edit')"
        class="touch-target"
        variant="ghost"
        :tooltip="expanded ? __('Collapse') : __('Edit')"
        @click="$emit('toggle')"
      >
        <template #icon>
          <LucideChevronDown
            class="size-4 text-ink-gray-5 transition-transform"
            :class="expanded ? 'rotate-180' : ''"
          />
        </template>
      </Button>
      <Dropdown :options="menu">
        <Button
          :aria-label="__('Options')"
          class="touch-target"
          variant="ghost"
          icon="lucide-more-horizontal"
        />
      </Dropdown>
    </div>

    <div
      v-if="expanded"
      class="flex flex-col gap-4 border-t border-outline-gray-2 px-3 py-3"
    >
      <ul
        v-if="problems.length"
        class="flex flex-col gap-1 rounded-md bg-surface-amber-1 px-3 py-2 text-sm text-ink-amber-7"
      >
        <li v-for="problem in problems" :key="problem">{{ problem }}</li>
      </ul>

      <template v-if="field.type === 'paragraph'">
        <FormControl
          v-model="field.text"
          type="textarea"
          :rows="6"
          :label="__('The words to read')"
          :placeholder="
            __('A notice, an explanation: shown exactly as written')
          "
        />
      </template>
      <template v-else>
        <FormControl
          v-model="field.label"
          :label="labelCaption"
          :placeholder="__('Your weight')"
        />
        <FormControl
          v-model="field.description"
          :label="__('Help under it')"
          :placeholder="__('Optional')"
        />
      </template>

      <!-- what this kind of question carries -->
      <template v-if="field.type === 'text'">
        <TemplateSwitch
          v-model="field.multiline"
          :label="__('A longer answer')"
        />
        <FormControl
          v-model="field.placeholder"
          :label="__('Placeholder')"
          :placeholder="__('Optional')"
        />
        <TemplatePhrases
          v-model="phrases"
          :label="__('Ready phrases')"
          :hint="
            __(
              'One tap writes them into the answer: the operator\'s usual words',
            )
          "
          :placeholder="__('No pain at rest')"
        />
      </template>

      <div
        v-else-if="field.type === 'number'"
        class="grid grid-cols-4 gap-2 max-md:grid-cols-2"
      >
        <FormControl
          v-model="field.unit"
          :label="__('Unit')"
          placeholder="kg"
        />
        <TemplateNumber v-model="field.min" :label="__('Least')" />
        <TemplateNumber v-model="field.max" :label="__('Most')" />
        <TemplateNumber v-model="field.decimals" :label="__('Decimals')" />
      </div>

      <template v-else-if="field.type === 'choice'">
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{
            __('Options, and their score')
          }}</span>
          <div
            v-for="(option, index) in field.options"
            :key="index"
            class="flex items-center gap-2"
          >
            <input
              v-model="option.label"
              class="form-input min-w-0 flex-1"
              :placeholder="__('Option {0}', [index + 1])"
            />
            <!-- «Punti»: «Punteggio» was «Punte…» in its 80 pixels -->
            <input
              class="form-input w-20 shrink-0"
              inputmode="decimal"
              :placeholder="__('Score', null, 'Form option placeholder')"
              :value="option.score ?? ''"
              @input="(e) => setScore(option, e.target.value)"
            />
            <Button
              class="touch-target shrink-0"
              variant="ghost"
              icon="x"
              :label="__('Remove the option')"
              @click="field.options.splice(index, 1)"
            />
          </div>
          <Button
            class="self-start"
            size="sm"
            icon-left="plus"
            :label="__('Add an option')"
            @click="addOption"
          />
        </div>
        <TemplateSwitch
          v-model="field.multiple"
          :label="__('More than one can be picked')"
        />
        <FormControl
          v-if="!field.multiple"
          v-model="field.display"
          type="select"
          :label="__('Shown as')"
          :options="[
            { label: __('A list to tap'), value: '' },
            { label: __('A dropdown'), value: 'dropdown' },
          ]"
        />
      </template>

      <div v-else-if="field.type === 'yesno'" class="grid grid-cols-2 gap-2">
        <TemplateNumber v-model="scores.yes" :label="__('Score for yes')" />
        <TemplateNumber v-model="scores.no" :label="__('Score for no')" />
      </div>

      <div
        v-else-if="field.type === 'scale'"
        class="grid grid-cols-4 gap-2 max-md:grid-cols-2"
      >
        <TemplateNumber
          v-model="field.min"
          :label="__('From')"
          placeholder="0"
        />
        <TemplateNumber
          v-model="field.max"
          :label="__('To')"
          placeholder="10"
        />
        <FormControl
          v-model="field.min_label"
          :label="__('Words at the start')"
          :placeholder="__('None')"
        />
        <FormControl
          v-model="field.max_label"
          :label="__('Words at the end')"
          :placeholder="__('The worst')"
        />
      </div>

      <div v-else-if="field.type === 'table'" class="flex flex-col gap-1.5">
        <span class="text-sm text-ink-gray-5">{{ __('Columns') }}</span>
        <div
          v-for="(column, index) in field.columns"
          :key="index"
          class="flex items-center gap-2"
        >
          <input
            class="form-input min-w-0 flex-1"
            :value="column.label"
            :placeholder="__('Column {0}', [index + 1])"
            @input="(e) => renameColumn(column, e.target.value)"
          />
          <FormControl
            v-model="column.type"
            class="w-32 shrink-0"
            type="select"
            :options="columnTypes"
          />
          <Button
            class="touch-target shrink-0"
            variant="ghost"
            icon="x"
            :label="__('Remove the column')"
            @click="field.columns.splice(index, 1)"
          />
        </div>
        <Button
          class="self-start"
          size="sm"
          icon-left="plus"
          :label="__('Add a column')"
          @click="addColumn"
        />
      </div>

      <div v-else-if="field.type === 'sides'" class="grid grid-cols-2 gap-2">
        <FormControl
          v-model="field.input"
          type="select"
          :label="__('Each side is')"
          :options="[
            { label: __('A number'), value: 'number' },
            { label: __('Words'), value: 'text' },
          ]"
        />
        <FormControl v-model="field.unit" :label="__('Unit')" placeholder="°" />
      </div>

      <div
        v-else-if="field.type === 'body_chart'"
        class="grid grid-cols-2 gap-2 max-md:grid-cols-1"
      >
        <FormControl
          :model-value="bodyViewsChoice"
          type="select"
          :label="__('The body seen')"
          :options="[
            { label: __('From the front and from the back'), value: 'both' },
            { label: __('From the front'), value: 'front' },
            { label: __('From the back'), value: 'back' },
          ]"
          @update:model-value="
            (value) =>
              (field.views = value === 'both' ? ['front', 'back'] : [value])
          "
        />
        <TemplateSwitch
          v-model="field.drawing"
          :label="__('Drawing by hand too')"
        />
      </div>

      <div
        v-else-if="field.type === 'attachment'"
        class="grid grid-cols-2 gap-2 max-md:grid-cols-1"
      >
        <FormControl
          v-model="field.accept"
          type="select"
          :label="__('Files')"
          :options="[
            { label: __('Any'), value: '' },
            { label: __('Images'), value: 'image/*' },
            { label: __('PDF'), value: 'application/pdf' },
            { label: __('Images and PDF'), value: 'image/*,application/pdf' },
          ]"
        />
        <TemplateSwitch
          v-model="field.multiple"
          :label="__('More than one file')"
        />
      </div>

      <template v-else-if="field.type === 'calc'">
        <FormControl
          v-model="field.formula"
          :label="__('Formula')"
          placeholder="weight / (height / 100) ^ 2"
        />
        <div
          class="flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-5"
        >
          <span>{{
            numbersBefore.length
              ? __('It can use')
              : __('Add a number before it to use it here')
          }}</span>
          <Button
            v-for="name in numbersBefore"
            :key="name.id"
            size="sm"
            variant="subtle"
            :label="name.id"
            :tooltip="name.label"
            @click="insertName(name.id)"
          />
          <span class="w-full">
            {{ __('+ − * / ^ and round, min, max, abs, sqrt') }}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <TemplateNumber v-model="field.decimals" :label="__('Decimals')" />
          <FormControl
            v-model="field.unit"
            :label="__('Unit')"
            placeholder="kg/m²"
          />
        </div>
      </template>

      <template v-else-if="field.type === 'score'">
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('It adds up') }}</span>
          <p v-if="!scorableBefore.length" class="text-sm text-ink-gray-5">
            {{ __('Add choices, yes or no, scales or numbers before it') }}
          </p>
          <label
            v-for="source in scorableBefore"
            :key="source.id"
            class="flex items-center gap-2 text-base"
          >
            <Checkbox
              :model-value="(field.sources || []).includes(source.id)"
              @update:model-value="(on) => toggleSource(source.id, on)"
            />
            <span class="min-w-0 truncate">{{
              source.label || source.id
            }}</span>
          </label>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{
            __('Bands: from, to, what it means')
          }}</span>
          <div
            v-for="(band, index) in field.bands"
            :key="index"
            class="flex items-center gap-2"
          >
            <input
              class="form-input w-20 shrink-0"
              inputmode="decimal"
              :value="band.from ?? ''"
              @input="(e) => (band.from = numberOrNull(e.target.value))"
            />
            <input
              class="form-input w-20 shrink-0"
              inputmode="decimal"
              :value="band.to ?? ''"
              @input="(e) => (band.to = numberOrNull(e.target.value))"
            />
            <input
              v-model="band.label"
              class="form-input min-w-0 flex-1"
              :placeholder="__('Moderate')"
            />
            <Button
              class="touch-target shrink-0"
              variant="ghost"
              icon="x"
              :label="__('Remove the band')"
              @click="field.bands.splice(index, 1)"
            />
          </div>
          <Button
            class="self-start"
            size="sm"
            icon-left="plus"
            :label="__('Add a band')"
            @click="addBand"
          />
        </div>
      </template>

      <template v-else-if="field.type === 'consent'">
        <FormControl
          :model-value="field.consent_type || ''"
          type="select"
          :label="__('The consent it records')"
          :options="[{ label: '', value: '' }, ...consentOptions]"
          @update:model-value="pickConsent"
        />
        <p
          v-if="consentText"
          class="whitespace-pre-line rounded-md bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-6"
        >
          {{ consentText }}
        </p>
        <TemplateSwitch
          v-model="field.must_accept"
          :label="__('It has to be accepted to go on')"
          :hint="
            __(
              'A notice read, an informed consent. Marketing never is: a no is an answer',
            )
          "
        />
      </template>

      <template v-else-if="field.type === 'signature'">
        <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
          <FormControl
            v-model="field.signer"
            type="select"
            :label="__('Who signs')"
            :options="[
              { label: __('The patient'), value: 'patient' },
              { label: __('The operator'), value: 'operator' },
              { label: __('A parent or guardian'), value: 'guardian' },
            ]"
          />
          <FormControl
            v-model="field.level"
            type="select"
            :label="__('Signature')"
            :options="[
              { label: __('Simple: the stroke, who, when'), value: 'simple' },
              {
                label: __('Advanced: with a code, by a provider'),
                value: 'advanced',
              },
              {
                label: __('Qualified: the professional\'s digital signature'),
                value: 'qualified',
              },
            ]"
          />
        </div>
        <p class="text-sm text-ink-gray-5">
          {{
            __(
              'The form decides the signature, not who has it signed: simple for notices and questionnaires, advanced for an informed consent. Without a signature provider an advanced one is signed on paper.',
            )
          }}
        </p>
      </template>

      <TemplateSwitch
        v-if="answers && field.type !== 'consent'"
        v-model="field.required"
        :label="__('Required')"
      />
      <TemplateSwitch
        v-else-if="field.type === 'consent' && !field.must_accept"
        v-model="field.required"
        :label="__('An answer is required, yes or no')"
      />

      <!-- on a form of the website: the answer is one of the person's fields -->
      <FormControl
        v-if="field.type === 'text' && personFields.length"
        :model-value="field.person || ''"
        type="select"
        :label="__('Fills the person\'s')"
        :options="[{ label: __('Nothing'), value: '' }, ...personFields]"
        :description="
          __(
            'Whoever sends the form is found by their email or mobile, or made: what they write fills what the centre did not know yet.',
          )
        "
        @update:model-value="(value) => (field.person = value || undefined)"
      />

      <!-- with the medical centre: the answer proposed to the patient's summary -->
      <FormControl
        v-if="answers && summaryKeys.length"
        :model-value="field.summary || ''"
        type="select"
        :label="__('Goes to the patient\'s summary as')"
        :options="[{ label: __('Nowhere'), value: '' }, ...summaryKeys]"
        @update:model-value="(value) => (field.summary = value || undefined)"
      />

      <!-- when it shows, when it is required, when to stop -->
      <ConditionsBlock
        v-model="field.show_if"
        :label="__('Show it only if')"
        :hint="__('Asked on the answers before it')"
        :fields="conditionsBefore"
      />
      <ConditionsBlock
        v-if="answers"
        v-model="field.required_if"
        :label="__('Required only if')"
        :fields="conditionsAll"
      />
      <ConditionsBlock
        v-model="field.stop_if"
        :label="__('Stop and warn the operator if')"
        :hint="__('The pacemaker before the shock waves')"
        :fields="conditionsAll"
      >
        <FormControl
          v-model="field.stop_message"
          :label="__('What the warning says')"
          :placeholder="__('Tell the operator before going on')"
        />
      </ConditionsBlock>

      <div class="flex items-end gap-2 border-t border-outline-gray-2 pt-3">
        <FormControl
          v-model="keyDraft"
          class="min-w-0 flex-1"
          :label="__('Key')"
          :description="
            __(
              'How the answer is kept, and how conditions and formulas name it',
            )
          "
        />
        <Button
          :label="__('Rename')"
          :disabled="keyDraft === field.id"
          @click="$emit('rename', keyDraft)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import ConditionsBlock from './TemplateConditions.vue'
import TemplateNumber from './TemplateNumber.vue'
import TemplatePhrases from './TemplatePhrases.vue'
import TemplateSwitch from './TemplateSwitch.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import { componentIcon } from '@/components/Moduli/moduliIcons'
import { bodyViews, component, conditionFields } from '@/utils/moduli'
import LucideChevronDown from '~icons/lucide/chevron-down'
import { Badge, Button, Checkbox, Dropdown, FormControl } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  expanded: { type: Boolean, default: false },
  /** The fields before it: what its visibility, formula and score may use. */
  before: { type: Array, default: () => [] },
  /** Every field: required-if and stop-if may look anywhere. */
  all: { type: Array, default: () => [] },
  consentTypes: { type: Array, default: () => [] },
  /** The lines of the patient's summary an answer may go to (the clinic's). */
  summaryKeys: { type: Array, default: () => [] },
  /** The person's fields a question of a form on the website may fill. */
  personFields: { type: Array, default: () => [] },
  problems: { type: Array, default: () => [] },
})

const emit = defineEmits(['toggle', 'remove', 'duplicate', 'rename'])

// the builder's own object: edited in place, the builder watches it
const field = defineModel('field', { type: Object, required: true })

const kind = computed(() => component(field.value.type))
const kindLabel = computed(() => __(kind.value?.label || field.value.type))
const answers = computed(() => Boolean(kind.value?.answer))
const headline = computed(() =>
  field.value.type === 'paragraph'
    ? (field.value.text || '').split('\n')[0]
    : field.value.label,
)
const personLabel = computed(
  () =>
    field.value.person &&
    props.personFields.find((option) => option.value === field.value.person)
      ?.label,
)
// both outlines unless the question names one (moduli.js, bodyViews)
const bodyViewsChoice = computed(() => {
  const views = bodyViews(field.value)
  return views.length === 2 ? 'both' : views[0]
})
const labelCaption = computed(() =>
  kind.value?.answer ? __('The question') : __('Its name'),
)

const menu = computed(() => [
  {
    label: __('Duplicate'),
    icon: 'lucide-copy',
    onClick: () => emit('duplicate'),
  },
  {
    label: __('Remove'),
    icon: 'lucide-trash-2',
    theme: 'red',
    onClick: () => emit('remove'),
  },
])

const has = (groups) =>
  Array.isArray(groups) && groups.some((g) => g?.some?.((c) => c?.field))

const conditionsBefore = computed(() => conditionFields(props.before))
// required-if and stop-if look anywhere, the question itself included
const conditionsAll = computed(() => conditionFields(props.all))
const numbersBefore = computed(() =>
  props.before.filter((f) => component(f.type)?.numeric),
)
const scorableBefore = computed(() =>
  props.before.filter((f) =>
    ['choice', 'yesno', 'scale', 'number'].includes(f.type),
  ),
)

const columnTypes = [
  { label: __('Words'), value: 'text' },
  { label: __('Number'), value: 'number' },
  { label: __('Date'), value: 'date' },
  { label: __('Yes or no'), value: 'yesno' },
]

const numberOrNull = (value) => {
  const text = String(value ?? '')
    .trim()
    .replace(',', '.')
  if (text === '' || text === '-') return null
  const number = Number(text)
  return Number.isFinite(number) ? number : text
}

function setScore(option, value) {
  const number = numberOrNull(value)
  if (number === null) delete option.score
  else option.score = number
}

function addOption() {
  if (!Array.isArray(field.value.options)) field.value.options = []
  field.value.options.push({
    label: __('Option {0}', [field.value.options.length + 1]),
  })
}

function addColumn() {
  if (!Array.isArray(field.value.columns)) field.value.columns = []
  const n = field.value.columns.length + 1
  field.value.columns.push({
    id: uniqueColumnId(`column_${n}`),
    label: '',
    type: 'text',
  })
}

function uniqueColumnId(base) {
  const taken = new Set((field.value.columns || []).map((c) => c.id))
  let id = base
  let n = 2
  while (taken.has(id)) id = `${base}_${n++}`
  return id
}

function renameColumn(column, label) {
  column.label = label
  // the key follows the words while the form is a draft
  const key = label
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/^[0-9_]+/, '')
  if (key && key !== column.id) {
    const taken = new Set(
      field.value.columns.filter((c) => c !== column).map((c) => c.id),
    )
    let id = key.slice(0, 40)
    let n = 2
    while (taken.has(id)) id = `${key.slice(0, 40)}_${n++}`
    column.id = id
  }
}

function addBand() {
  if (!Array.isArray(field.value.bands)) field.value.bands = []
  const last = field.value.bands.at(-1)
  const from = last && typeof last.to === 'number' ? last.to + 1 : 0
  field.value.bands.push({ from, to: from + 4, label: '' })
}

function toggleSource(id, on) {
  const sources = new Set(field.value.sources || [])
  if (on) sources.add(id)
  else sources.delete(id)
  // in the order of the form
  field.value.sources = props.before
    .map((f) => f.id)
    .filter((key) => sources.has(key))
}

function insertName(name) {
  const formula = (field.value.formula || '').trimEnd()
  field.value.formula = formula ? `${formula} ${name}` : name
}

// phrases and yes/no scores, kept on the field only when there is something
const phrases = computed({
  get: () => field.value.phrases || [],
  set: (list) => {
    if (list.length) field.value.phrases = list
    else delete field.value.phrases
  },
})
const scores = new Proxy(
  {},
  {
    get: (_, side) => field.value.scores?.[side] ?? null,
    set: (_, side, value) => {
      const next = { ...(field.value.scores || {}) }
      if (value === null || value === '') delete next[side]
      else next[side] = value
      if (Object.keys(next).length) field.value.scores = next
      else delete field.value.scores
      return true
    },
  },
)

const consentOptions = computed(() =>
  props.consentTypes.map((type) => ({ label: type.label, value: type.key })),
)
const consentText = computed(
  () =>
    props.consentTypes.find((type) => type.key === field.value.consent_type)
      ?.text || '',
)

function pickConsent(key) {
  const type = props.consentTypes.find((t) => t.key === key)
  const previous = props.consentTypes.find(
    (t) => t.key === field.value.consent_type,
  )
  field.value.consent_type = key
  // the words follow the consent until somebody writes their own
  if (type && (!field.value.label || field.value.label === previous?.label)) {
    field.value.label = type.label
  }
  if (type?.kind === 'Acknowledgement') field.value.must_accept = true
}

const keyDraft = ref(field.value.id)
watch(
  () => field.value.id,
  (id) => (keyDraft.value = id),
)
</script>
