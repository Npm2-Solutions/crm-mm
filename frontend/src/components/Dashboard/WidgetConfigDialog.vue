<template>
  <Dialog v-model:open="show" :title="dialogTitle">
    <template #default>
      <div class="flex flex-col gap-4">
        <p v-if="widget?.description" class="text-p-sm text-ink-gray-5">
          {{ widget.description }}
        </p>
        <FormControl
          v-model="draft.title"
          type="text"
          size="md"
          :label="isHeading ? __('Section title') : __('Title')"
          :placeholder="isHeading ? __('e.g. Sales') : widget?.title"
        />
        <template v-for="option in options" :key="option.key">
          <FormControl
            v-if="option.type === 'int'"
            v-model="draft[option.key]"
            type="number"
            size="md"
            :label="option.label"
            :min="option.min"
            :max="option.max"
            :placeholder="String(option.default ?? '')"
          />
          <FormControl
            v-else
            v-model="draft[option.key]"
            type="select"
            size="md"
            :label="option.label"
            :options="choicesOf(option)"
          />
        </template>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button variant="solid" :label="__('Apply')" @click="apply" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { pipelinesStore } from '@/stores/pipelines'
import { Dialog, FormControl } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  item: { type: Object, default: null },
  widget: { type: Object, default: null },
})

const emit = defineEmits(['apply'])

const show = defineModel({ type: Boolean, default: false })

const { pipelineOptions } = pipelinesStore()

const draft = reactive({})

const isHeading = computed(() => props.item?.name === 'heading')
const options = computed(() => props.widget?.options || [])

const dialogTitle = computed(() =>
  isHeading.value ? __('Section title') : __('Widget settings'),
)

watch(
  () => [show.value, props.item],
  () => {
    if (!show.value || !props.item) return
    for (const key of Object.keys(draft)) delete draft[key]
    draft.title = props.item.config?.title || ''
    for (const option of options.value) {
      draft[option.key] =
        props.item.config?.[option.key] ?? option.default ?? ''
    }
  },
  { immediate: true },
)

function choicesOf(option) {
  if (option.type === 'pipeline') {
    return [
      { label: __('All pipelines'), value: '' },
      ...pipelineOptions().map(({ label, value }) => ({ label, value })),
    ]
  }
  return option.choices.map((choice) => ({
    label: choice.label,
    value: choice.value,
  }))
}

function apply() {
  const config = {}
  if (draft.title?.trim()) config.title = draft.title.trim()
  for (const option of options.value) {
    let value = draft[option.key]
    if (option.type === 'int')
      value = value === '' || value == null ? null : Number(value)
    if (value !== null && value !== '' && value !== option.default)
      config[option.key] = value
  }
  emit('apply', config)
  show.value = false
}
</script>
