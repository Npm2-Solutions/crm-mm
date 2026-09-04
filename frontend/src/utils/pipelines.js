/**
 * Pipelines and their stages — pure helpers (no Vue, no network).
 *
 * A stage is a `CRM Deal Status` record carrying a `pipeline` link. A deal board
 * shows the stages of one pipeline, in the order the stages come in (the backend
 * returns them by `position`).
 */

/** Stages of one pipeline, board order preserved. No pipeline given: all of them. */
export function stagesOfPipeline(stages = [], pipeline) {
  if (!pipeline) return [...stages]
  return stages.filter((stage) => stage.pipeline === pipeline)
}

/** Just the names of those stages — what `status` links to. */
export function stageNames(stages = [], pipeline) {
  return stagesOfPipeline(stages, pipeline).map((stage) => stage.name)
}

/**
 * Which pipeline a set of kanban columns belongs to.
 * Empty string when the columns span more than one pipeline, or none is known.
 */
export function pipelineOfColumns(columns = [], stagesByName = {}) {
  const pipelines = new Set()

  for (const column of columns) {
    if (column?.delete) continue
    const pipeline = stagesByName[column?.name]?.pipeline
    if (pipeline) pipelines.add(pipeline)
  }

  return pipelines.size === 1 ? [...pipelines][0] : ''
}

/**
 * Kanban columns for a pipeline: one per stage, in board order, keeping what the
 * user already set on the columns that stay (card order, page length, colour).
 */
export function kanbanColumnsForPipeline(stages = [], existingColumns = []) {
  const existing = {}
  for (const column of existingColumns) {
    if (column?.name) existing[column.name] = column
  }

  return stages.map((stage) => ({
    ...(existing[stage.name] || {}),
    name: stage.name,
    color: existing[stage.name]?.color || stage.color,
  }))
}

/** The pipeline new deals land in. */
export function defaultPipeline(pipelines = []) {
  return (
    pipelines.find((pipeline) => pipeline.is_default && !pipeline.disabled) ||
    pipelines.find((pipeline) => !pipeline.disabled) ||
    pipelines[0] ||
    null
  )
}
