<template>
  <div class="flex flex-col gap-2">
    <template v-for="(group, groupIndex) in groups" :key="groupIndex">
      <div
        v-if="groupIndex > 0"
        class="flex items-center gap-2 text-xs font-medium uppercase text-ink-gray-4"
      >
        <div class="h-px flex-1 bg-outline-gray-2" />
        {{ __('or') }}
        <div class="h-px flex-1 bg-outline-gray-2" />
      </div>
      <div class="rounded-md border border-outline-gray-2 bg-surface-white p-2">
        <div class="flex flex-col gap-2">
          <template v-for="(condition, index) in group" :key="index">
            <div
              v-if="index > 0"
              class="text-xs font-medium uppercase text-ink-gray-4"
            >
              {{ __('and') }}
            </div>
            <ConditionRow
              v-model="group[index]"
              :fields="fields"
              @remove="removeCondition(groupIndex, index)"
            />
          </template>
        </div>
        <Button
          class="mt-2"
          variant="ghost"
          size="sm"
          iconLeft="plus"
          :label="__('And')"
          @click="group.push(newCondition())"
        />
      </div>
    </template>
    <Button
      variant="ghost"
      size="sm"
      iconLeft="plus"
      class="self-start"
      :label="__('Or a different set')"
      @click="groups.push(newConditionGroup())"
    />
  </div>
</template>

<script setup>
import ConditionRow from './ConditionRow.vue'
import { Button } from 'frappe-ui'
import { newCondition, newConditionGroup } from '@/utils/automation'

defineProps({
  fields: { type: Array, default: () => [] },
})

const groups = defineModel({ type: Array, required: true })

/** An empty group would read as "always true", so it goes when its last row does. */
function removeCondition(groupIndex, index) {
  const group = groups.value[groupIndex]
  group.splice(index, 1)
  if (!group.length && groups.value.length > 1) {
    groups.value.splice(groupIndex, 1)
  }
}
</script>
