<template>
  <div class="flex w-full flex-col items-center">
    <Draggable
      :list="steps"
      item-key="id"
      group="automation-steps"
      handle=".step-grip"
      class="flex w-full flex-col items-center"
      ghost-class="opacity-40"
      :animation="150"
    >
      <template #item="{ element: step, index }">
        <div class="flex w-full flex-col items-center">
          <FlowConnector @insert="editor.openPicker(steps, index)" />
          <StepNode :step="step" :list="steps" :index="index" />

          <!-- branching steps carry their own columns of nested flows -->
          <template v-if="isBranching(step.type)">
            <div class="h-4 w-px bg-outline-gray-3" />
            <div
              class="flex w-full items-stretch justify-center gap-4 overflow-x-auto pb-1"
            >
              <div
                v-for="column in columnsOf(step)"
                :key="column.key"
                class="flex min-w-[352px] flex-col rounded-lg border border-dashed p-2"
                :class="
                  column.muted
                    ? 'border-outline-gray-2 bg-surface-gray-1'
                    : 'border-outline-gray-3 bg-surface-gray-1'
                "
              >
                <button
                  class="mb-1 flex items-center justify-between gap-2 rounded px-1 py-0.5 text-left hover:bg-surface-gray-2"
                  @click.stop="editor.select(step.id)"
                >
                  <span class="truncate text-sm font-medium text-ink-gray-7">
                    {{ column.label }}
                  </span>
                  <span class="shrink-0 text-xs text-ink-gray-5">
                    {{ column.hint }}
                  </span>
                </button>
                <StepFlow :steps="column.steps" :depth="depth + 1" />
              </div>
            </div>
          </template>
        </div>
      </template>
    </Draggable>

    <FlowConnector
      :always="!steps.length"
      @insert="editor.openPicker(steps, steps.length)"
    />
    <div
      class="rounded-full bg-surface-gray-2 px-3 py-1 text-xs text-ink-gray-6"
    >
      {{ depth ? __('end of this path') : __('End of the automation') }}
    </div>
  </div>
</template>

<script setup>
import Draggable from 'vuedraggable'
import FlowConnector from './FlowConnector.vue'
import StepNode from './StepNode.vue'
import { inject } from 'vue'
import { groupsSummary, isBranching } from '@/utils/automation'

defineOptions({ name: 'StepFlow' })

defineProps({
  steps: { type: Array, required: true },
  depth: { type: Number, default: 0 },
})

const editor = inject('automation-editor')

/** if/else shows one column per branch plus the mandatory "None"; split shows its paths. */
function columnsOf(step) {
  if (step.type === 'split') {
    return (step.paths || []).map((path, index) => ({
      key: path.id || index,
      label: path.label || __('Path {0}', [index + 1]),
      hint: `${path.percent || 0}%`,
      steps: path.steps,
    }))
  }
  const columns = (step.branches || []).map((branch, index) => ({
    key: branch.id || index,
    label: branch.label || __('Branch {0}', [index + 1]),
    hint: groupsSummary(branch.condition_groups),
    steps: branch.steps,
  }))
  columns.push({
    key: 'else',
    label: __('None (else)'),
    hint: '',
    steps: step.else_steps,
    muted: true,
  })
  return columns
}
</script>
