<template>
  <div
    data-node
    class="w-[320px] cursor-pointer rounded-lg border bg-surface-white px-3 py-2.5 shadow-sm transition-colors"
    :class="[
      selected
        ? 'border-outline-gray-4 ring-2 ring-outline-gray-3'
        : 'border-outline-gray-2 hover:border-outline-gray-3',
      disabledLook ? 'opacity-60' : '',
    ]"
    @click.stop="editor.select(step.id)"
  >
    <div class="flex items-start gap-2.5">
      <div
        class="step-grip grid size-8 shrink-0 cursor-grab place-items-center rounded-md"
        :class="ICON_CLASSES[stepTheme(step.type)] || ICON_CLASSES.gray"
        :title="__('Drag to move')"
      >
        <FeatherIcon :name="stepIcon(step.type)" class="size-4" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="truncate text-base font-medium text-ink-gray-8">
            {{ stepLabel(step.type) }}
          </span>
          <Badge
            v-if="step.label"
            size="sm"
            theme="gray"
            :label="'#' + step.label"
          />
          <FeatherIcon
            v-if="issues.length"
            name="alert-triangle"
            class="size-3.5 shrink-0"
            :class="hasError ? 'text-ink-red-3' : 'text-ink-amber-3'"
            :title="issues.map((issue) => issue.message).join('\n')"
          />
        </div>
        <div class="truncate text-sm text-ink-gray-5">
          {{ stepSummary(step) }}
        </div>
        <div
          v-if="gateSummary"
          class="mt-1 flex items-center gap-1 truncate text-xs text-ink-gray-5"
        >
          <FeatherIcon name="filter" class="size-3 shrink-0" />
          {{ __('only if') }} {{ gateSummary }}
        </div>
      </div>
      <Dropdown :options="menuOptions" placement="right">
        <Button
          variant="ghost"
          icon="lucide-more-horizontal"
          :label="__('Step options')"
          @click.stop
        />
      </Dropdown>
    </div>

    <div
      v-if="editor.showStats.value && stats"
      class="mt-2 flex items-center gap-3 border-t border-outline-gray-1 pt-1.5 text-xs text-ink-gray-5"
    >
      <span class="flex items-center gap-1">
        <FeatherIcon name="check-circle" class="size-3" />{{ stats.success }}
      </span>
      <span v-if="stats.failed" class="flex items-center gap-1 text-ink-red-3">
        <FeatherIcon name="alert-triangle" class="size-3" />{{ stats.failed }}
      </span>
      <span v-if="stats.skipped" class="flex items-center gap-1">
        <FeatherIcon name="corner-down-right" class="size-3" />{{
          stats.skipped
        }}
      </span>
      <span v-if="stats.here" class="flex items-center gap-1 text-ink-blue-3">
        <FeatherIcon name="user" class="size-3" />{{ stats.here }}
        {{ __('here now') }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { Badge, Button, Dropdown, FeatherIcon } from 'frappe-ui'
import { computed, inject } from 'vue'
import {
  ICON_CLASSES,
  groupsSummary,
  stepIcon,
  stepLabel,
  stepSummary,
  stepTheme,
} from '@/utils/automation'

const props = defineProps({
  step: { type: Object, required: true },
  list: { type: Array, required: true },
  index: { type: Number, required: true },
})

const editor = inject('automation-editor')

const selected = computed(() => editor.selectedId.value === props.step.id)

const issues = computed(() => editor.issuesByNode.value[props.step.id] || [])

const hasError = computed(() =>
  issues.value.some((issue) => issue.level === 'error'),
)

const stats = computed(() => editor.stats.value?.nodes?.[props.step.id] || null)

const gateSummary = computed(() => {
  if (!props.step.condition_groups?.length) return ''
  const summary = groupsSummary(props.step.condition_groups)
  return summary === __('Always') ? '' : summary
})

/** Exit-like steps read as dead ends; dimming them says so at a glance. */
const disabledLook = computed(() =>
  ['exit', 'remove_from_workflow'].includes(props.step.type),
)

const menuOptions = computed(() => [
  {
    label: __('Configure'),
    icon: 'settings',
    onClick: () => editor.select(props.step.id),
  },
  {
    label: __('Duplicate'),
    icon: 'copy',
    onClick: () => editor.duplicate(props.step.id),
  },
  {
    label: __('Copy'),
    icon: 'clipboard',
    onClick: () => editor.copy(props.step.id),
  },
  {
    label: __('Move up'),
    icon: 'arrow-up',
    onClick: () => editor.move(props.list, props.index, -1),
  },
  {
    label: __('Move down'),
    icon: 'arrow-down',
    onClick: () => editor.move(props.list, props.index, 1),
  },
  {
    label: __('Delete'),
    icon: 'trash-2',
    onClick: () => editor.remove(props.step.id),
  },
])
</script>
