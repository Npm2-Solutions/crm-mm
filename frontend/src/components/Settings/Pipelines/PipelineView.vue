<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Pipelines')"
          size="md"
          class="-ml-4 !text-2xl-semibold !pr-0 hover:opacity-70 hover:bg-transparent"
          @click="updateStep('list')"
        />
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          theme="orange"
          variant="subtle"
        />
      </div>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Stages are the columns of the deal board, in this order') }}
      </p>
    </template>

    <template #header-actions>
      <Button
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        :disabled="!isDirty"
        @click="save"
      />
    </template>

    <template #content>
      <div v-if="!pipeline" class="flex items-center justify-center mt-12">
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="flex flex-col gap-6 max-w-3xl">
        <div class="flex gap-4">
          <FormControl
            v-model="form.name"
            class="flex-1"
            :label="__('Name')"
            type="text"
            maxlength="140"
          />
          <FormControl
            v-model="form.description"
            class="flex-1"
            :label="__('Description')"
            type="text"
          />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Stages') }}
            </span>
            <span class="text-sm text-ink-gray-5">
              {{ __('Drag to reorder') }}
            </span>
          </div>

          <Draggable
            :list="form.stages"
            item-key="key"
            handle=".stage-handle"
            class="flex flex-col gap-2"
          >
            <template #item="{ element: stage }">
              <div
                class="flex items-center gap-2 rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5"
              >
                <DragVerticalIcon
                  class="stage-handle h-3.5 cursor-grab text-ink-gray-5"
                />
                <Popover>
                  <template #trigger="{ toggle }">
                    <Button
                      variant="ghost"
                      :tooltip="__('Colour')"
                      @click="toggle"
                    >
                      <IndicatorIcon :class="parseColor(stage.color)" />
                    </Button>
                  </template>
                  <template #default="{ close }">
                    <div class="flex gap-1">
                      <Button
                        v-for="color in colors"
                        :key="color"
                        variant="ghost"
                        @click="
                          () => {
                            stage.color = color
                            close()
                          }
                        "
                      >
                        <IndicatorIcon :class="parseColor(color)" />
                      </Button>
                    </div>
                  </template>
                </Popover>
                <TextInput
                  v-model="stage.stage"
                  class="flex-1"
                  type="text"
                  :placeholder="__('Stage name')"
                />
                <Select
                  v-model="stage.type"
                  class="w-32"
                  :options="stageTypes"
                />
                <TextInput
                  v-model="stage.probability"
                  class="w-20"
                  type="number"
                  :placeholder="__('%')"
                />
                <Tooltip
                  :text="
                    stage.deal_count
                      ? __('{0} deals in this stage', [stage.deal_count])
                      : __('No deals in this stage')
                  "
                >
                  <span class="w-8 text-center text-sm text-ink-gray-5">
                    {{ stage.deal_count || 0 }}
                  </span>
                </Tooltip>
                <Button
                  icon="lucide-trash-2"
                  variant="ghost"
                  @click="askToDeleteStage(stage)"
                />
              </div>
            </template>
          </Draggable>

          <Button
            class="w-full mt-1"
            :label="__('Add stage')"
            icon-left="lucide-plus"
            @click="addStage"
          />
          <ErrorMessage :message="error" />
        </div>
      </div>

      <Dialog
        v-model:open="moveDeals.show"
        :title="__('Delete {0}', [moveDeals.stage])"
      >
        <template #body-content>
          <div class="flex flex-col gap-4">
            <p class="text-p-base text-ink-gray-7">
              {{
                __('{0} deals are in this stage. Where should they go?', [
                  moveDeals.count,
                ])
              }}
            </p>
            <FormControl
              v-model="moveDeals.target"
              type="select"
              :label="__('Move deals to')"
              :options="moveTargets"
            />
            <ErrorMessage :message="moveDeals.error" />
          </div>
        </template>
        <template #actions>
          <div class="flex gap-2 justify-end">
            <Button
              variant="subtle"
              :label="__('Cancel')"
              @click="moveDeals.show = false"
            />
            <Button
              variant="solid"
              theme="red"
              :label="__('Move and delete')"
              :loading="moveDeals.deleting"
              @click="deleteStage(moveDeals.stage, moveDeals.target)"
            />
          </div>
        </template>
      </Dialog>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { colors, parseColor } from '@/utils'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Popover,
  Select,
  TextInput,
  Tooltip,
  call,
  toast,
} from 'frappe-ui'
import Draggable from 'vuedraggable'
import { computed, inject, reactive, ref, watch } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
})

const pipelines = inject('pipelines')
const updateStep = inject('updateStep')
const reloadPipelines = inject('reloadPipelines')

const stageTypes = ['Open', 'Ongoing', 'On Hold', 'Won', 'Lost']

const currentName = ref(props.name)
const saving = ref(false)
const error = ref(null)
let key = 0

const form = reactive({ name: '', description: '', stages: [] })

const pipeline = computed(() =>
  (pipelines.data || []).find((p) => p.name === currentName.value),
)

/** Editing works on a copy — nothing reaches the server until Save. */
function resetForm() {
  if (!pipeline.value) return
  form.name = pipeline.value.name
  form.description = pipeline.value.description || ''
  form.stages = (pipeline.value.stages || []).map((stage) => ({
    key: `stage-${key++}`,
    name: stage.name,
    stage: stage.name,
    color: stage.color || 'gray',
    type: stage.type || 'Open',
    probability: stage.probability || 0,
    deal_count: stage.deal_count || 0,
  }))
}

watch(pipeline, resetForm, { immediate: true })

const isDirty = computed(() => {
  if (!pipeline.value) return false
  if (form.name !== pipeline.value.name) return true
  if ((form.description || '') !== (pipeline.value.description || ''))
    return true

  const saved = pipeline.value.stages || []
  if (saved.length !== form.stages.length) return true

  return form.stages.some((stage, index) => {
    const original = saved[index]
    return (
      !original ||
      original.name !== stage.stage ||
      (original.color || 'gray') !== stage.color ||
      (original.type || 'Open') !== stage.type ||
      Number(original.probability || 0) !== Number(stage.probability || 0)
    )
  })
})

function addStage() {
  form.stages.push({
    key: `stage-${key++}`,
    name: '',
    stage: '',
    color: colors[form.stages.length % colors.length],
    type: 'Ongoing',
    probability: 0,
    deal_count: 0,
  })
}

const moveDeals = reactive({
  show: false,
  stage: '',
  count: 0,
  target: '',
  error: null,
  deleting: false,
})

const moveTargets = computed(() =>
  form.stages
    .filter((stage) => stage.name && stage.name !== moveDeals.stage)
    .map((stage) => ({ label: stage.name, value: stage.name })),
)

function askToDeleteStage(stage) {
  // never saved: dropping the row is all it takes
  if (!stage.name) {
    form.stages = form.stages.filter((s) => s.key !== stage.key)
    return
  }

  if (stage.deal_count) {
    moveDeals.show = true
    moveDeals.stage = stage.name
    moveDeals.count = stage.deal_count
    moveDeals.error = null
    moveDeals.target = moveTargets.value[0]?.value || ''
    return
  }

  deleteStage(stage.name)
}

async function deleteStage(name, moveTo = null) {
  moveDeals.deleting = true
  try {
    await call('crm.api.pipeline.delete_stage', {
      stage: name,
      move_deals_to: moveTo,
    })
    moveDeals.show = false
    reloadPipelines()
    toast.success(__('Stage deleted'))
  } catch (err) {
    const message = err.messages?.[0] || err.message
    if (moveDeals.show) {
      moveDeals.error = message
    } else {
      toast.error(message)
    }
  } finally {
    moveDeals.deleting = false
  }
}

async function save() {
  error.value = null

  if (form.stages.some((stage) => !stage.stage.trim())) {
    error.value = __('Every stage needs a name')
    return
  }

  saving.value = true
  try {
    if (
      form.name !== pipeline.value.name ||
      (form.description || '') !== (pipeline.value.description || '')
    ) {
      const updated = await call('crm.api.pipeline.update_pipeline', {
        name: currentName.value,
        pipeline_name: form.name,
        description: form.description,
      })
      currentName.value = updated.name
    }

    await call('crm.api.pipeline.save_stages', {
      pipeline: currentName.value,
      stages: form.stages.map((stage) => ({
        name: stage.name,
        stage: stage.stage.trim(),
        color: stage.color,
        type: stage.type,
        probability: Number(stage.probability || 0),
      })),
    })

    reloadPipelines()
    toast.success(__('Pipeline updated'))
  } catch (err) {
    error.value = err.messages?.[0] || err.message
  } finally {
    saving.value = false
  }
}
</script>
