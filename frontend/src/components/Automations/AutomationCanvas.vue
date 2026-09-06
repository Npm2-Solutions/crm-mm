<template>
  <div
    ref="viewport"
    class="relative flex-1 overflow-auto bg-surface-gray-1"
    :class="panning ? 'cursor-grabbing select-none' : 'cursor-grab'"
    @mousedown="startPan"
    @wheel="onWheel"
  >
    <div
      class="mx-auto w-max px-16 py-10"
      :style="{ transform: `scale(${zoom})`, transformOrigin: 'top center' }"
    >
      <div class="flex flex-col items-center">
        <!-- trigger: what puts a record into this automation -->
        <div
          data-node
          class="w-[320px] cursor-pointer rounded-lg border bg-surface-white px-3 py-2.5 shadow-sm transition-colors"
          :class="
            editor.selectedId.value === 'trigger'
              ? 'border-outline-gray-4 ring-2 ring-outline-gray-3'
              : 'border-outline-gray-2 hover:border-outline-gray-3'
          "
          @click.stop="editor.select('trigger')"
        >
          <div class="flex items-start gap-2.5">
            <div
              class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-gray-2 text-ink-gray-7"
            >
              <FeatherIcon
                :name="triggerDefinition(draft.trigger_event).icon"
                class="size-4"
              />
            </div>
            <div class="min-w-0 flex-1">
              <div
                class="text-xs font-medium uppercase tracking-wide text-ink-gray-5"
              >
                {{ __('Trigger') }}
              </div>
              <div class="truncate text-base font-medium text-ink-gray-8">
                {{ __(draft.trigger_event) }}
              </div>
              <div class="truncate text-sm text-ink-gray-5">
                {{ enrolmentSummary }}
              </div>
            </div>
            <Button
              variant="ghost"
              icon="lucide-settings-2"
              :label="__('Trigger settings')"
              @click.stop="editor.select('trigger')"
            />
          </div>
        </div>

        <StepFlow :steps="draft.steps" :depth="0" />
      </div>
    </div>

    <div
      class="pointer-events-none absolute inset-x-0 bottom-4 flex justify-center"
    >
      <div
        class="pointer-events-auto flex items-center gap-0.5 rounded-full border border-outline-gray-2 bg-surface-white px-1.5 py-1 shadow-sm"
      >
        <Button
          variant="ghost"
          icon="lucide-zoom-out"
          :label="__('Zoom out')"
          @click="setZoom(zoom - 0.1)"
        />
        <button
          class="min-w-12 rounded px-1 text-xs text-ink-gray-6 hover:bg-surface-gray-2"
          @click="setZoom(1)"
        >
          {{ Math.round(zoom * 100) }}%
        </button>
        <Button
          variant="ghost"
          icon="lucide-zoom-in"
          :label="__('Zoom in')"
          @click="setZoom(zoom + 0.1)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import StepFlow from './StepFlow.vue'
import { Button, FeatherIcon } from 'frappe-ui'
import { computed, inject, ref } from 'vue'
import {
  cleanGroups,
  groupsSummary,
  triggerDefinition,
} from '@/utils/automation'

const editor = inject('automation-editor')
const draft = editor.draft

const viewport = ref(null)
const zoom = ref(1)
const panning = ref(false)

const enrolmentSummary = computed(() => {
  const groups = cleanGroups(draft.trigger_condition_groups)
  return groups
    ? __('only when {0}', [groupsSummary(groups)])
    : __('every record')
})

function setZoom(value) {
  zoom.value = Math.min(1.4, Math.max(0.5, Math.round(value * 10) / 10))
}

/** Ctrl/⌘ + wheel zooms; a plain wheel keeps scrolling the canvas. */
function onWheel(event) {
  if (!event.ctrlKey && !event.metaKey) return
  event.preventDefault()
  setZoom(zoom.value + (event.deltaY > 0 ? -0.1 : 0.1))
}

/** Drag the background to pan; dragging a node is the sortable's business. */
function startPan(event) {
  if (event.button !== 0 || event.target.closest('[data-node]')) return
  const element = viewport.value
  const origin = {
    x: event.clientX,
    y: event.clientY,
    left: element.scrollLeft,
    top: element.scrollTop,
  }
  panning.value = true

  const move = (moveEvent) => {
    element.scrollLeft = origin.left - (moveEvent.clientX - origin.x)
    element.scrollTop = origin.top - (moveEvent.clientY - origin.y)
  }
  const stop = () => {
    panning.value = false
    window.removeEventListener('mousemove', move)
    window.removeEventListener('mouseup', stop)
  }
  window.addEventListener('mousemove', move)
  window.addEventListener('mouseup', stop)
}
</script>
