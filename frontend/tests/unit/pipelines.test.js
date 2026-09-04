import {
  defaultPipeline,
  kanbanColumnsForPipeline,
  pipelineOfColumns,
  stageNames,
  stagesOfPipeline,
} from '@/utils/pipelines'

const stages = [
  { name: 'Qualification', pipeline: 'Sales', color: 'gray' },
  { name: 'Negotiation', pipeline: 'Sales', color: 'yellow' },
  { name: 'Kickoff', pipeline: 'Onboarding', color: 'blue' },
]

const stagesByName = Object.fromEntries(
  stages.map((stage) => [stage.name, stage]),
)

describe('stagesOfPipeline', () => {
  it('keeps only the stages of the given pipeline, in order', () => {
    expect(stagesOfPipeline(stages, 'Sales').map((s) => s.name)).toEqual([
      'Qualification',
      'Negotiation',
    ])
  })

  it('returns every stage when no pipeline is given', () => {
    expect(stagesOfPipeline(stages).length).toBe(3)
  })

  it('survives an empty list', () => {
    expect(stagesOfPipeline(undefined, 'Sales')).toEqual([])
  })
})

describe('stageNames', () => {
  it('returns the stage names of one pipeline', () => {
    expect(stageNames(stages, 'Onboarding')).toEqual(['Kickoff'])
  })
})

describe('pipelineOfColumns', () => {
  it('finds the pipeline a board belongs to', () => {
    const columns = [{ name: 'Qualification' }, { name: 'Negotiation' }]
    expect(pipelineOfColumns(columns, stagesByName)).toBe('Sales')
  })

  it('returns an empty string when the columns span two pipelines', () => {
    const columns = [{ name: 'Qualification' }, { name: 'Kickoff' }]
    expect(pipelineOfColumns(columns, stagesByName)).toBe('')
  })

  it('ignores hidden columns', () => {
    const columns = [
      { name: 'Qualification' },
      { name: 'Kickoff', delete: true },
    ]
    expect(pipelineOfColumns(columns, stagesByName)).toBe('Sales')
  })

  it('returns an empty string when nothing is known', () => {
    expect(pipelineOfColumns([{ name: 'Unknown' }], stagesByName)).toBe('')
    expect(pipelineOfColumns()).toBe('')
  })
})

describe('kanbanColumnsForPipeline', () => {
  it('builds one column per stage, in board order', () => {
    const columns = kanbanColumnsForPipeline(stagesOfPipeline(stages, 'Sales'))
    expect(columns).toEqual([
      { name: 'Qualification', color: 'gray' },
      { name: 'Negotiation', color: 'yellow' },
    ])
  })

  it('keeps what the user had set on the columns that stay', () => {
    const existing = [
      {
        name: 'Negotiation',
        color: 'red',
        page_length: 40,
        order: ['CRM-DEAL-1'],
      },
    ]
    const columns = kanbanColumnsForPipeline(
      stagesOfPipeline(stages, 'Sales'),
      existing,
    )

    expect(columns[1]).toEqual({
      name: 'Negotiation',
      color: 'red',
      page_length: 40,
      order: ['CRM-DEAL-1'],
    })
  })
})

describe('defaultPipeline', () => {
  it('picks the one flagged as default', () => {
    const pipelines = [{ name: 'Sales' }, { name: 'Onboarding', is_default: 1 }]
    expect(defaultPipeline(pipelines).name).toBe('Onboarding')
  })

  it('skips a disabled default and falls back to a usable one', () => {
    const pipelines = [
      { name: 'Onboarding', is_default: 1, disabled: 1 },
      { name: 'Sales' },
    ]
    expect(defaultPipeline(pipelines).name).toBe('Sales')
  })

  it('returns null without pipelines', () => {
    expect(defaultPipeline([])).toBe(null)
  })
})
