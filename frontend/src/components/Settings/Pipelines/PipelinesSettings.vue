<template>
  <PipelineList v-if="step.screen === 'list'" />
  <PipelineView v-else :name="step.data" />
</template>

<script setup>
import PipelineList from './PipelineList.vue'
import PipelineView from './PipelineView.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { statusesStore } from '@/stores/statuses'
import { createResource } from 'frappe-ui'
import { provide, ref } from 'vue'

// deal counts are what tells the manager whether a stage can be deleted safely,
// so this screen asks for them -- the app-wide store does not
const pipelines = createResource({
  url: 'crm.api.pipeline.get_pipelines',
  params: { with_counts: 1 },
  cache: 'pipelines-with-counts',
  initialData: [],
  auto: true,
})

const step = ref({ screen: 'list', data: null })

function updateStep(screen, data = null) {
  step.value = { screen, data }
}

/** Pipelines and stages are read all over the app -- refresh every reader at once. */
function reloadPipelines() {
  pipelines.reload()
  pipelinesStore().pipelines.reload()
  statusesStore().dealStatuses.reload()
}

provide('pipelines', pipelines)
provide('updateStep', updateStep)
provide('reloadPipelines', reloadPipelines)
</script>
