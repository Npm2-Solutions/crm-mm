<!-- eslint-disable vue/no-v-html -->
<template>
  <div class="flex flex-col gap-3">
    <FormControl
      :modelValue="context?.script || ''"
      type="select"
      :label="__('Script')"
      :options="scriptOptions"
      @update:modelValue="(value) => emit('pick', value || null)"
    />

    <div v-if="!context?.scripts?.length" class="text-sm text-ink-gray-5">
      {{
        __(
          'No call scripts yet. A manager can add them in Settings → Call Scripts.',
        )
      }}
    </div>

    <template v-else-if="script">
      <p v-if="script.description" class="text-sm text-ink-gray-6">
        {{ script.description }}
      </p>

      <div class="flex items-center gap-2">
        <div class="h-1.5 flex-1 overflow-hidden rounded bg-surface-gray-2">
          <div
            class="h-full rounded bg-surface-gray-7 transition-all"
            :style="{ width: progress + '%' }"
          />
        </div>
        <span class="shrink-0 text-xs text-ink-gray-5">
          {{ doneCount }} / {{ script.steps.length }}
        </span>
      </div>

      <ol class="flex flex-col gap-1">
        <li
          v-for="step in script.steps"
          :key="step.name"
          class="rounded-md border border-outline-gray-2 px-3 py-2"
          :class="isDone(step) && 'bg-surface-gray-1'"
        >
          <label class="flex cursor-pointer items-start gap-2">
            <Checkbox
              class="mt-0.5"
              :modelValue="isDone(step)"
              @update:modelValue="(on) => toggle(step, on)"
            />
            <span class="min-w-0 flex-1">
              <span
                class="text-sm font-medium"
                :class="
                  isDone(step)
                    ? 'text-ink-gray-5 line-through'
                    : 'text-ink-gray-8'
                "
              >
                {{ step.title }}
              </span>
              <span v-if="step.optional" class="ml-1.5 text-xs text-ink-gray-4">
                {{ __('optional') }}
              </span>
            </span>
          </label>
          <div
            v-if="step.body"
            class="prose-sm mt-1.5 pl-6 text-ink-gray-7"
            v-html="sanitizeHTML(step.body)"
          />
        </li>
      </ol>
    </template>
  </div>
</template>

<script setup>
import { sanitizeHTML } from '@/utils'
import { Checkbox, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  context: { type: Object, default: null },
})

const emit = defineEmits(['pick', 'toggle'])

const scriptOptions = computed(() => [
  { label: __('None'), value: '' },
  ...(props.context?.scripts || []).map((s) => ({
    label: s.script_name,
    value: s.name,
  })),
])

const script = computed(
  () =>
    (props.context?.scripts || []).find(
      (s) => s.name === props.context?.script,
    ) || null,
)

const doneSet = computed(() => new Set(props.context?.steps_done || []))
const doneCount = computed(
  () =>
    (script.value?.steps || []).filter((s) => doneSet.value.has(s.name)).length,
)
const progress = computed(() =>
  script.value?.steps?.length
    ? (doneCount.value / script.value.steps.length) * 100
    : 0,
)

function isDone(step) {
  return doneSet.value.has(step.name)
}

function toggle(step, on) {
  const next = new Set(doneSet.value)
  if (on) next.add(step.name)
  else next.delete(step.name)
  emit('toggle', [...next])
}
</script>
