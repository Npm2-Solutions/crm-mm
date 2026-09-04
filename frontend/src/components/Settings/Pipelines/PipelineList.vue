<template>
  <SettingsLayoutBase
    :title="__('Pipelines')"
    :description="__('Every deal moves through the stages of one pipeline')"
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        variant="solid"
        icon-left="lucide-plus"
        @click="openNewPipelineDialog"
      />
    </template>
    <template #content>
      <div
        v-if="pipelines.loading && !pipelines.data?.length"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="-ml-2">
        <EmptyState
          v-if="!pipelines.data?.length"
          name="Pipeline"
          :title="__('No pipelines yet')"
          :description="__('Add one to get started.')"
          :icon="KanbanIcon"
        />
        <template v-else>
          <div
            class="grid grid-cols-8 items-center gap-3 text-sm text-ink-gray-5 ml-2"
          >
            <div class="col-span-5">{{ __('Pipeline') }}</div>
            <div class="col-span-1">{{ __('Stages') }}</div>
            <div class="col-span-1">{{ __('Deals') }}</div>
          </div>
          <hr class="mt-2 mx-2 border-outline-gray-2" />
          <div v-for="(pipeline, index) in pipelines.data" :key="pipeline.name">
            <div
              class="grid grid-cols-8 items-center gap-4 cursor-pointer hover:bg-surface-sidebar rounded"
            >
              <div
                class="w-full pl-2 col-span-5 flex items-center h-14 gap-2"
                @click="openPipeline(pipeline)"
              >
                <div class="text-base-medium text-ink-gray-7 truncate">
                  {{ pipeline.name || __('Without pipeline') }}
                </div>
                <Badge v-if="pipeline.is_default" theme="gray" size="sm">
                  {{ __('Default') }}
                </Badge>
                <Badge v-if="pipeline.disabled" theme="orange" size="sm">
                  {{ __('Disabled') }}
                </Badge>
              </div>
              <div
                class="col-span-1 text-ink-gray-8 text-sm"
                @click="openPipeline(pipeline)"
              >
                {{ pipeline.stages?.length || 0 }}
              </div>
              <div class="flex justify-between items-center w-full pr-2">
                <div class="text-ink-gray-8 text-sm">
                  {{ pipeline.deal_count || 0 }}
                </div>
                <Dropdown
                  v-if="pipeline.name"
                  placement="right"
                  :options="dropdownOptions(pipeline)"
                >
                  <Button
                    icon="lucide-more-horizontal"
                    variant="ghost"
                    @click="isConfirmingDelete = false"
                  />
                </Dropdown>
              </div>
            </div>
            <hr
              v-if="index !== pipelines.data.length - 1"
              class="mx-2 border-outline-gray-2"
            />
          </div>
        </template>
      </div>

      <Dialog v-model:open="newPipeline.show" :title="__('New Pipeline')">
        <template #body-content>
          <div class="flex flex-col gap-4">
            <FormControl
              v-model="newPipeline.name"
              :label="__('Name')"
              type="text"
              :placeholder="__('Onboarding')"
              maxlength="140"
              @keydown.enter="createPipeline"
            />
            <FormControl
              v-model="newPipeline.description"
              :label="__('Description')"
              type="textarea"
              :placeholder="__('What this pipeline is for')"
            />
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'It starts with the standard stages — rename, recolour and reorder them next.',
                )
              }}
            </p>
            <ErrorMessage :message="newPipeline.error" />
          </div>
        </template>
        <template #actions>
          <div class="flex gap-2 justify-end">
            <Button
              variant="subtle"
              :label="__('Cancel')"
              @click="newPipeline.show = false"
            />
            <Button
              variant="solid"
              :label="__('Create')"
              :loading="newPipeline.creating"
              @click="createPipeline"
            />
          </div>
        </template>
      </Dialog>

      <Dialog
        v-model:open="moveDeals.show"
        :title="__('Delete {0}', [moveDeals.pipeline])"
      >
        <template #body-content>
          <div class="flex flex-col gap-4">
            <p class="text-p-base text-ink-gray-7">
              {{
                __('{0} deals are in this pipeline. Where should they go?', [
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
              @click="deletePipeline(moveDeals.pipeline, moveDeals.target)"
            />
          </div>
        </template>
      </Dialog>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import { ConfirmDelete } from '@/utils'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  toast,
} from 'frappe-ui'
import { computed, inject, reactive, ref } from 'vue'

const pipelines = inject('pipelines')
const updateStep = inject('updateStep')
const reloadPipelines = inject('reloadPipelines')

const isConfirmingDelete = ref(false)

const newPipeline = reactive({
  show: false,
  name: '',
  description: '',
  error: null,
  creating: false,
})

const moveDeals = reactive({
  show: false,
  pipeline: '',
  count: 0,
  target: '',
  error: null,
  deleting: false,
})

const moveTargets = computed(() =>
  (pipelines.data || [])
    .filter((p) => p.name && p.name !== moveDeals.pipeline && !p.disabled)
    .map((p) => ({ label: p.name, value: p.name })),
)

// the "no pipeline yet" bucket is a reading aid, not a pipeline to edit
function openPipeline(pipeline) {
  if (pipeline.name) updateStep('view', pipeline.name)
}

function openNewPipelineDialog() {
  newPipeline.show = true
  newPipeline.name = ''
  newPipeline.description = ''
  newPipeline.error = null
}

async function createPipeline() {
  if (!newPipeline.name.trim()) {
    newPipeline.error = __('Pipeline name is required')
    return
  }

  newPipeline.creating = true
  newPipeline.error = null
  try {
    const pipeline = await call('crm.api.pipeline.create_pipeline', {
      pipeline_name: newPipeline.name.trim(),
      description: newPipeline.description,
    })
    reloadPipelines()
    newPipeline.show = false
    toast.success(__('Pipeline created'))
    updateStep('view', pipeline.name)
  } catch (error) {
    newPipeline.error = error.messages?.[0] || error.message
  } finally {
    newPipeline.creating = false
  }
}

function dropdownOptions(pipeline) {
  const options = []

  if (!pipeline.is_default && !pipeline.disabled) {
    options.push({
      label: __('Set as default'),
      icon: 'check-circle',
      onClick: () => setAsDefault(pipeline),
    })
  }

  if (!pipeline.is_default) {
    options.push({
      label: pipeline.disabled ? __('Enable') : __('Disable'),
      icon: pipeline.disabled ? 'eye' : 'eye-off',
      onClick: () => toggleDisabled(pipeline),
    })
    options.push(
      ...ConfirmDelete({
        onConfirmDelete: () => askToDelete(pipeline),
        isConfirmingDelete,
      }),
    )
  }

  return options
}

async function setAsDefault(pipeline) {
  try {
    await call('crm.api.pipeline.set_default_pipeline', { name: pipeline.name })
    reloadPipelines()
    toast.success(__('{0} is now the default pipeline', [pipeline.name]))
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

async function toggleDisabled(pipeline) {
  try {
    await call('crm.api.pipeline.update_pipeline', {
      name: pipeline.name,
      disabled: pipeline.disabled ? 0 : 1,
    })
    reloadPipelines()
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

function askToDelete(pipeline) {
  if (pipeline.deal_count) {
    moveDeals.show = true
    moveDeals.pipeline = pipeline.name
    moveDeals.count = pipeline.deal_count
    moveDeals.target = moveTargets.value[0]?.value || ''
    moveDeals.error = null
    return
  }

  deletePipeline(pipeline.name)
}

async function deletePipeline(name, moveTo = null) {
  moveDeals.deleting = true
  try {
    await call('crm.api.pipeline.delete_pipeline', {
      name,
      move_deals_to: moveTo,
    })
    moveDeals.show = false
    reloadPipelines()
    toast.success(__('Pipeline deleted'))
  } catch (error) {
    const message = error.messages?.[0] || error.message
    if (moveDeals.show) {
      moveDeals.error = message
    } else {
      toast.error(message)
    }
  } finally {
    moveDeals.deleting = false
  }
}
</script>
