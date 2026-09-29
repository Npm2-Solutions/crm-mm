<template>
  <div class="flex flex-col gap-2">
    <Button
      v-if="!active"
      class="self-start"
      size="sm"
      variant="ghost"
      icon-left="plus"
      :label="label"
      @click="start"
    />
    <div
      v-else
      class="flex flex-col gap-2 rounded-md border border-outline-gray-2 p-2.5"
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <div class="text-sm font-medium text-ink-gray-7">{{ label }}</div>
          <div v-if="hint" class="text-xs text-ink-gray-5">{{ hint }}</div>
        </div>
        <Button
          class="shrink-0"
          size="sm"
          variant="ghost"
          :label="__('Remove')"
          @click="groups = null"
        />
      </div>
      <p v-if="!fields.length" class="text-sm text-ink-gray-5">
        {{ __('There is no question before it to look at yet') }}
      </p>
      <!-- the automations' condition builder: one way of writing "if" -->
      <div v-else class="overflow-x-auto">
        <ConditionBuilder
          v-model="groups"
          class="min-w-[26rem]"
          :fields="fields"
        />
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup>
import ConditionBuilder from '@/components/Automations/ConditionBuilder.vue'
import { newConditionGroup } from '@/utils/automation'
import { Button } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  label: { type: String, required: true },
  hint: { type: String, default: '' },
  /** `conditionFields()` of what the condition may look at. */
  fields: { type: Array, default: () => [] },
})

const groups = defineModel({ type: [Array, null], default: null })
const active = computed(
  () => Array.isArray(groups.value) && groups.value.length > 0,
)

function start() {
  groups.value = [newConditionGroup()]
}
</script>
