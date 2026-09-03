<template>
  <Popover placement="bottom-start">
    <template #target="{ togglePopover }">
      <Button @click="togglePopover">
        <template #prefix>
          <span :class="[icon, 'size-4 text-ink-gray-6']" aria-hidden="true" />
        </template>
        {{ buttonLabel }}
        <template #suffix>
          <span
            class="lucide-chevron-down size-3.5 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </Button>
    </template>
    <template #body-main>
      <div class="flex max-h-72 w-60 flex-col gap-1 overflow-y-auto p-1.5">
        <div class="flex items-center justify-between px-1.5 pb-1">
          <span class="text-xs-medium text-ink-gray-5">{{ label }}</span>
          <Button
            v-if="modelValue.length"
            variant="ghost"
            size="sm"
            :label="__('Clear')"
            @click="$emit('update:modelValue', [])"
          />
        </div>
        <label
          v-for="option in options"
          :key="option.value"
          class="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-2"
        >
          <Checkbox
            :modelValue="modelValue.includes(option.value)"
            @update:modelValue="toggle(option.value)"
          />
          <span
            v-if="option.color"
            class="size-2 shrink-0 rounded-full"
            :style="{ backgroundColor: option.color }"
          />
          <span class="truncate text-p-sm text-ink-gray-8">{{
            option.label
          }}</span>
        </label>
        <p v-if="!options.length" class="px-1.5 py-2 text-p-sm text-ink-gray-5">
          {{ emptyText || __('Nothing to filter yet') }}
        </p>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Button, Checkbox, Popover } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  /** `[{ label, value, color? }]` */
  options: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  icon: { type: String, default: 'lucide-filter' },
  emptyText: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const buttonLabel = computed(() => {
  if (!props.modelValue.length) return props.label
  if (props.modelValue.length === 1) {
    const first = props.options.find((o) => o.value === props.modelValue[0])
    return first?.label || props.label
  }
  return `${props.label} · ${props.modelValue.length}`
})

function toggle(value) {
  const next = props.modelValue.includes(value)
    ? props.modelValue.filter((v) => v !== value)
    : [...props.modelValue, value]
  emit('update:modelValue', next)
}
</script>
