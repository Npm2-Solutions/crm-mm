import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import {
  defaultPipeline as pickDefaultPipeline,
  stageNames,
  stagesOfPipeline,
} from '@/utils/pipelines'
import { parseColor } from '@/utils'
import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, h, reactive } from 'vue'

export const pipelinesStore = defineStore('crm-pipelines', () => {
  const pipelinesByName = reactive({})

  // one call gives both the pipelines and their stages (with raw colours, which
  // the kanban columns need); deal counts are asked for by the settings screen only
  const pipelines = createResource({
    url: 'crm.api.pipeline.get_pipelines',
    cache: 'pipelines',
    initialData: [],
    auto: true,
    transform(data) {
      for (const key of Object.keys(pipelinesByName))
        delete pipelinesByName[key]
      for (const pipeline of data) {
        pipelinesByName[pipeline.name] = pipeline
      }
      return data
    },
  })

  const defaultPipeline = computed(() =>
    pickDefaultPipeline(pipelines.data || []),
  )

  function getPipeline(name) {
    if (!name) return defaultPipeline.value
    return pipelinesByName[name]
  }

  /** Stages of a pipeline, in board order. Without a pipeline: every stage. */
  function getStages(pipeline) {
    if (!pipeline) {
      return (pipelines.data || []).flatMap((p) => p.stages || [])
    }
    return stagesOfPipeline(getPipeline(pipeline)?.stages || [], pipeline)
  }

  function getStageNames(pipeline) {
    return stageNames(getStages(pipeline), pipeline)
  }

  /** The pipeline a deal stage belongs to. */
  function getPipelineOfStage(stage) {
    if (!stage) return null
    for (const pipeline of pipelines.data || []) {
      if ((pipeline.stages || []).some((s) => s.name === stage))
        return pipeline.name
    }
    return null
  }

  /** Dropdown options — one entry per usable pipeline. */
  function pipelineOptions(onClick, { includeAll = false } = {}) {
    const options = (pipelines.data || [])
      .filter((pipeline) => pipeline.name && !pipeline.disabled)
      .map((pipeline) => ({
        label: __(pipeline.name),
        value: pipeline.name,
        onClick: () => onClick?.(pipeline.name),
      }))

    if (includeAll) {
      options.unshift({
        label: __('All pipelines'),
        value: '',
        onClick: () => onClick?.(''),
      })
    }

    return options
  }

  /** Stage options for a status dropdown, coloured like the board. */
  function stageOptions(pipeline, onClick) {
    return getStages(pipeline).map((stage) => ({
      label: __(stage.name),
      value: stage.name,
      icon: () => h(IndicatorIcon, { class: parseColor(stage.color) }),
      onClick: () => onClick?.(stage.name),
    }))
  }

  return {
    pipelines,
    defaultPipeline,
    getPipeline,
    getStages,
    getStageNames,
    getPipelineOfStage,
    pipelineOptions,
    stageOptions,
  }
})
