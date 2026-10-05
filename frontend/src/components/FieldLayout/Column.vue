<template>
  <div class="column flex min-w-0 flex-1 flex-col gap-4 sm:basis-44">
    <div
      v-if="column.label && !column.hideLabel"
      class="text-ink-gray-9 max-w-fit text-base"
    >
      {{ column.label }}
    </div>
    <template v-for="field in column.fields" :key="field.fieldname">
      <Field :field="field" :data-name="field.fieldname" />
    </template>
  </div>
</template>
<script setup>
import Field from '@/components/FieldLayout/Field.vue'

defineProps({
  column: { type: Object, required: true },
})
</script>
