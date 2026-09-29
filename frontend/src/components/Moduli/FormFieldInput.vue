<template>
  <div class="flex flex-col gap-2" :data-field="field.id">
    <!-- a text to read is not a question: its words are the whole of it -->
    <div
      v-if="field.type === 'paragraph'"
      class="whitespace-pre-line rounded-lg bg-surface-gray-1 px-4 py-3 text-p-base leading-relaxed text-ink-gray-8"
    >
      {{ field.text }}
    </div>

    <template v-else>
      <div class="flex min-w-0 flex-col gap-0.5">
        <span class="text-base font-medium text-ink-gray-8">
          {{ field.label }}
          <span v-if="required" class="text-ink-red-4">*</span>
        </span>
        <span
          v-if="field.description"
          class="whitespace-pre-line text-sm text-ink-gray-5"
        >
          {{ field.description }}
        </span>
      </div>

      <!-- text, with the phrases that write it -->
      <template v-if="field.type === 'text'">
        <FormControl
          :type="field.multiline ? 'textarea' : 'text'"
          :rows="field.multiline ? 4 : undefined"
          :model-value="modelValue ?? ''"
          :placeholder="field.placeholder || ''"
          :disabled="readonly"
          @update:model-value="(value) => emit(value)"
        />
        <div v-if="field.phrases?.length && !readonly" class="flex flex-wrap gap-1.5">
          <Button
            v-for="phrase in field.phrases"
            :key="phrase"
            size="sm"
            variant="subtle"
            :label="phrase"
            @click="addPhrase(phrase)"
          />
        </div>
      </template>

      <div v-else-if="field.type === 'number'" class="flex items-center gap-2">
        <input
          class="form-input w-40 max-md:w-full"
          inputmode="decimal"
          :value="modelValue ?? ''"
          :placeholder="field.placeholder || ''"
          :disabled="readonly"
          @input="(e) => emit(e.target.value)"
        />
        <span v-if="field.unit" class="shrink-0 text-base text-ink-gray-5">
          {{ field.unit }}
        </span>
      </div>

      <template v-else-if="field.type === 'choice'">
        <FormControl
          v-if="field.display === 'dropdown' && !field.multiple"
          type="select"
          :options="[{ label: '', value: '' }, ...options]"
          :model-value="modelValue ?? ''"
          :disabled="readonly"
          @update:model-value="(value) => emit(value || null)"
        />
        <div v-else class="flex flex-col gap-1.5">
          <button
            v-for="option in options"
            :key="option.value"
            type="button"
            class="touch-target flex w-full min-w-0 items-center gap-2.5 rounded-md border px-3 py-2 text-left text-base"
            :class="
              picked(option.value)
                ? 'border-outline-gray-5 bg-surface-gray-2 text-ink-gray-9'
                : 'border-outline-gray-2 text-ink-gray-7'
            "
            :disabled="readonly"
            @click="pick(option.value)"
          >
            <span
              class="flex size-4 shrink-0 items-center justify-center border"
              :class="[
                field.multiple ? 'rounded' : 'rounded-full',
                picked(option.value) ? 'border-outline-gray-5' : 'border-outline-gray-3',
              ]"
            >
              <span
                v-if="picked(option.value)"
                class="size-2 bg-surface-gray-7"
                :class="field.multiple ? 'rounded-sm' : 'rounded-full'"
              />
            </span>
            <span class="min-w-0">{{ option.label }}</span>
          </button>
        </div>
      </template>

      <div v-else-if="field.type === 'yesno'" class="flex gap-2">
        <Button
          class="touch-target min-w-20"
          :variant="modelValue === true ? 'solid' : 'outline'"
          :label="__('Yes')"
          :disabled="readonly"
          @click="emit(modelValue === true ? null : true)"
        />
        <Button
          class="touch-target min-w-20"
          :variant="modelValue === false ? 'solid' : 'outline'"
          :label="__('No')"
          :disabled="readonly"
          @click="emit(modelValue === false ? null : false)"
        />
      </div>

      <FormControl
        v-else-if="field.type === 'date'"
        class="w-48 max-md:w-full"
        type="date"
        :model-value="modelValue ?? ''"
        :disabled="readonly"
        @update:model-value="(value) => emit(value || null)"
      />

      <div v-else-if="field.type === 'scale'" class="flex flex-col gap-1.5">
        <div v-if="steps.length <= 11" class="flex flex-wrap gap-1.5">
          <Button
            v-for="step in steps"
            :key="step"
            class="touch-target min-w-9"
            :variant="modelValue === step ? 'solid' : 'outline'"
            :label="String(step)"
            :disabled="readonly"
            @click="emit(modelValue === step ? null : step)"
          />
        </div>
        <input
          v-else
          class="form-input w-32"
          type="number"
          :min="scaleMin"
          :max="scaleMax"
          step="1"
          :value="modelValue ?? ''"
          :disabled="readonly"
          @input="(e) => emit(e.target.value === '' ? null : Number(e.target.value))"
        />
        <div
          v-if="field.min_label || field.max_label"
          class="flex justify-between gap-4 text-sm text-ink-gray-5"
          :class="steps.length <= 11 ? 'max-w-md' : 'max-w-40'"
        >
          <span>{{ field.min_label }}</span>
          <span class="text-right">{{ field.max_label }}</span>
        </div>
      </div>

      <TableInput
        v-else-if="field.type === 'table'"
        :columns="field.columns || []"
        :model-value="modelValue || []"
        :readonly="readonly"
        @update:model-value="(rows) => emit(rows)"
      />

      <div
        v-else-if="field.type === 'sides'"
        class="grid max-w-md grid-cols-2 gap-3 max-md:max-w-none"
      >
        <label
          v-for="side in ['left', 'right']"
          :key="side"
          class="flex min-w-0 flex-col gap-1"
        >
          <span class="text-sm text-ink-gray-5">
            {{ side === 'left' ? __('Left') : __('Right') }}
          </span>
          <span class="flex items-center gap-2">
            <input
              class="form-input w-full min-w-0"
              :inputmode="field.input === 'text' ? 'text' : 'decimal'"
              :value="modelValue?.[side] ?? ''"
              :disabled="readonly"
              @input="(e) => emit({ ...(modelValue || {}), [side]: e.target.value })"
            />
            <span v-if="field.unit" class="shrink-0 text-base text-ink-gray-5">
              {{ field.unit }}
            </span>
          </span>
        </label>
      </div>

      <div
        v-else-if="field.type === 'attachment'"
        class="flex items-center gap-2 rounded-md border border-dashed border-outline-gray-3 px-3 py-3 text-sm text-ink-gray-5"
      >
        <LucidePaperclip class="size-4 shrink-0" />
        {{ __('A file is attached here when the form is filled') }}
      </div>

      <div
        v-else-if="field.type === 'calc'"
        class="flex w-fit items-baseline gap-1.5 rounded-md bg-surface-gray-2 px-3 py-1.5"
      >
        <span class="text-lg font-semibold text-ink-gray-9">
          {{ workedOut ?? '—' }}
        </span>
        <span v-if="field.unit && workedOut !== null" class="text-sm text-ink-gray-5">
          {{ field.unit }}
        </span>
      </div>

      <div v-else-if="field.type === 'score'" class="flex items-center gap-2">
        <span
          class="rounded-md bg-surface-gray-2 px-3 py-1.5 text-lg font-semibold text-ink-gray-9"
        >
          {{ workedOut ?? '—' }}
        </span>
        <Badge v-if="band" :label="band" theme="blue" variant="subtle" size="md" />
        <span v-else-if="workedOut === null" class="text-sm text-ink-gray-5">
          {{ __('Worked out once every question it counts is answered') }}
        </span>
      </div>

      <div
        v-else-if="field.type === 'consent'"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 px-4 py-3"
      >
        <p class="whitespace-pre-line text-p-base leading-relaxed text-ink-gray-7">
          {{ consentText }}
        </p>
        <label
          v-if="field.must_accept"
          class="touch-target flex items-center gap-2 text-base text-ink-gray-8"
        >
          <Checkbox
            :model-value="modelValue === true"
            :disabled="readonly"
            @update:model-value="(value) => emit(value ? true : null)"
          />
          {{ __('I agree') }}
        </label>
        <div v-else class="flex flex-wrap gap-2">
          <Button
            class="touch-target"
            :variant="modelValue === true ? 'solid' : 'outline'"
            :label="__('I agree')"
            :disabled="readonly"
            @click="emit(true)"
          />
          <Button
            class="touch-target"
            :variant="modelValue === false ? 'solid' : 'outline'"
            :label="__('I do not agree')"
            :disabled="readonly"
            @click="emit(false)"
          />
        </div>
      </div>

      <div
        v-else-if="field.type === 'signature'"
        class="flex h-28 max-w-md items-end rounded-lg border border-dashed border-outline-gray-3 px-4 pb-3 text-sm text-ink-gray-5 max-md:max-w-none"
      >
        <span class="w-full border-t border-outline-gray-3 pt-1">
          {{ signerLabel }}
        </span>
      </div>

      <p v-if="missing" class="text-sm text-ink-red-4">
        {{
          field.must_accept
            ? __('To go on, this has to be accepted')
            : __('This is required')
        }}
      </p>
    </template>

    <div
      v-if="stop !== undefined"
      class="flex items-start gap-2 rounded-md bg-surface-red-1 px-3 py-2 text-sm text-ink-red-4"
      role="alert"
    >
      <LucideTriangleAlert class="mt-0.5 size-4 shrink-0" />
      <span>{{ stop || __('Stop here and tell the operator') }}</span>
    </div>
  </div>
</template>

<script setup>
import TableInput from '@/components/Moduli/TableInput.vue'
import LucidePaperclip from '~icons/lucide/paperclip'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import { Badge, Button, Checkbox, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Boolean, Array, Object], default: null },
  /** What a calculation or a score gives with the answers so far. */
  workedOut: { type: [Number, null], default: null },
  band: { type: [String, null], default: null },
  required: { type: Boolean, default: false },
  missing: { type: Boolean, default: false },
  /** The message of a stop that holds; undefined when none does. */
  stop: { type: String, default: undefined },
  readonly: { type: Boolean, default: false },
  consentTexts: { type: Object, default: () => ({}) },
})

const emits = defineEmits(['update:modelValue'])
const emit = (value) => emits('update:modelValue', value)

const options = computed(() =>
  (props.field.options || [])
    .filter((option) => option?.label)
    .map((option) => ({ label: option.label, value: option.label })),
)

function picked(value) {
  const current = props.modelValue
  return props.field.multiple
    ? Array.isArray(current) && current.includes(value)
    : current === value
}

function pick(value) {
  if (!props.field.multiple) {
    emit(props.modelValue === value ? null : value)
    return
  }
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  const next = current.includes(value)
    ? current.filter((v) => v !== value)
    : [...current, value]
  // in the order of the options, as the server keeps them
  emit(options.value.map((o) => o.value).filter((v) => next.includes(v)))
}

function addPhrase(phrase) {
  const current = (props.modelValue || '').trimEnd()
  const glue = props.field.multiline ? '\n' : ' '
  emit(current ? `${current}${glue}${phrase}` : phrase)
}

const scaleMin = computed(() => Number(props.field.min ?? 0))
const scaleMax = computed(() => Number(props.field.max ?? 10))
const steps = computed(() => {
  const found = []
  for (let n = scaleMin.value; n <= scaleMax.value && found.length <= 101; n++) {
    found.push(n)
  }
  return found
})

// frozen into a version; in a draft's preview, the register's words today
const consentText = computed(
  () =>
    props.field.text ||
    props.consentTexts[props.field.consent_type] ||
    __('The words of this consent come from the register when the form is published.'),
)

const signerLabel = computed(
  () =>
    ({
      patient: __('Signature of the patient'),
      operator: __('Signature of the operator'),
      guardian: __('Signature of the parent or guardian'),
    })[props.field.signer || 'patient'],
)
</script>
