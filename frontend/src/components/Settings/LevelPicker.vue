<template>
  <div class="flex flex-col gap-4">
    <div v-for="group in groups" :key="group.key" class="flex flex-col gap-1">
      <div v-if="group.title" class="px-2 text-p-sm text-ink-gray-5">
        {{ group.title }}
      </div>
      <label
        v-for="level in group.levels"
        :key="level.key"
        class="flex cursor-pointer items-start gap-2.5 rounded-lg px-2 py-2 hover:bg-surface-gray-2"
        :class="{ 'cursor-not-allowed opacity-60': disabled }"
      >
        <Checkbox
          class="mt-0.5 shrink-0"
          :modelValue="modelValue.includes(level.key)"
          :disabled="disabled"
          @update:modelValue="toggle(level.key)"
        />
        <span class="flex min-w-0 flex-col gap-0.5">
          <span class="text-base-medium text-ink-gray-8">
            {{ __(level.label) }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ __(level.description) }}
          </span>
        </span>
      </label>
    </div>
  </div>
</template>

<script setup>
// Levels as checkboxes: a person may hold more than one - the owner who also
// sees patients is Manager and Practitioner. The optional ones sit apart, as
// in doc 30: most centres never need them.
import { Checkbox } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  levels: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const groups = computed(() => {
  const base = props.levels.filter((l) => l.base)
  const optional = props.levels.filter((l) => !l.base && !l.additive)
  // Read only adds to the levels above and takes their writes away
  const additive = props.levels.filter((l) => l.additive)
  return [
    { key: 'base', title: '', levels: base },
    ...(optional.length
      ? [
          {
            key: 'optional',
            title: __('Optional levels, for whoever needs them'),
            levels: optional,
          },
        ]
      : []),
    ...(additive.length
      ? [
          {
            key: 'additive',
            title: __('Added to the levels above'),
            levels: additive,
          },
        ]
      : []),
  ]
})

function toggle(key) {
  if (props.disabled) return
  const next = props.modelValue.includes(key)
    ? props.modelValue.filter((k) => k !== key)
    : [...props.modelValue, key]
  // in the registry's order, whatever the order of the clicks
  const order = props.levels.map((l) => l.key)
  emit(
    'update:modelValue',
    next.sort((a, b) => order.indexOf(a) - order.indexOf(b)),
  )
}
</script>
