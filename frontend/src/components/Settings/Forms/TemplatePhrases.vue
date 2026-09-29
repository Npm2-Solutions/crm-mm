<template>
  <div class="flex flex-col gap-1.5">
    <span class="text-sm text-ink-gray-5">{{ label }}</span>
    <div v-if="modelValue.length" class="flex flex-wrap gap-1.5">
      <Button
        v-for="(phrase, index) in modelValue"
        :key="phrase"
        size="sm"
        variant="subtle"
        icon-right="x"
        :label="phrase"
        @click="
          $emit(
            'update:modelValue',
            modelValue.filter((_, i) => i !== index),
          )
        "
      />
    </div>
    <div class="flex gap-2">
      <input
        v-model="typed"
        class="form-input min-w-0 flex-1"
        :placeholder="placeholder"
        @keydown.enter.prevent="add"
      />
      <Button :label="__('Add')" @click="add" />
    </div>
    <span v-if="hint" class="text-sm text-ink-gray-5">{{ hint }}</span>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, required: true },
  hint: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const typed = ref('')

function add() {
  const phrase = typed.value.trim()
  if (phrase && !props.modelValue.includes(phrase)) {
    emit('update:modelValue', [...props.modelValue, phrase])
  }
  typed.value = ''
}
</script>
