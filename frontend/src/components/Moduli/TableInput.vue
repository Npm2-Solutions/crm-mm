<template>
  <div class="flex flex-col gap-2">
    <!-- rows scroll sideways on a phone, each column keeping a readable width -->
    <div v-if="rows.length" class="overflow-x-auto">
      <table class="w-full min-w-max border-separate border-spacing-y-1.5 text-base">
        <thead>
          <tr class="text-left text-sm text-ink-gray-5">
            <th
              v-for="column in columns"
              :key="column.id"
              class="min-w-36 px-1 font-normal"
            >
              {{ column.label }}
            </th>
            <th v-if="!readonly" class="w-8" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in rows" :key="index">
            <td v-for="column in columns" :key="column.id" class="px-1 align-top">
              <div
                v-if="(column.type || 'text') === 'yesno'"
                class="flex h-7 items-center"
              >
                <Checkbox
                  :model-value="row[column.id] === true"
                  :disabled="readonly"
                  @update:model-value="(value) => setCell(index, column.id, value)"
                />
              </div>
              <input
                v-else
                class="form-input w-full min-w-0"
                :type="column.type === 'date' ? 'date' : 'text'"
                :inputmode="column.type === 'number' ? 'decimal' : undefined"
                :value="row[column.id] ?? ''"
                :disabled="readonly"
                @input="(e) => setCell(index, column.id, e.target.value)"
              />
            </td>
            <td v-if="!readonly" class="align-top">
              <Button
                class="touch-target"
                variant="ghost"
                icon="x"
                :label="__('Remove the row')"
                @click="removeRow(index)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Button
      v-if="!readonly"
      class="self-start"
      icon-left="plus"
      :label="rows.length ? __('Add another') : __('Add a row')"
      @click="addRow"
    />
    <span v-else-if="!rows.length" class="text-sm text-ink-gray-5">—</span>
  </div>
</template>

<script setup>
import { Button, Checkbox } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  /** `[{ id, label, type: text | number | date | yesno }]` */
  columns: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const rows = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))

function setCell(index, key, value) {
  const next = rows.value.map((row, i) => (i === index ? { ...row, [key]: value } : row))
  emit('update:modelValue', next)
}

function addRow() {
  emit('update:modelValue', [...rows.value, {}])
}

function removeRow(index) {
  emit(
    'update:modelValue',
    rows.value.filter((_, i) => i !== index),
  )
}
</script>
