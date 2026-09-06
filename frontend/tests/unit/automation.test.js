import {
  cleanGroups,
  cloneStep,
  countSteps,
  duplicateStep,
  findStep,
  groupsSummary,
  hasErrors,
  moveStep,
  newStep,
  normalizeSteps,
  removeStep,
  stepFromPalette,
  stepLabels,
  stepSummary,
  triggerDoctype,
  validateAutomation,
  waitSummary,
  PALETTE,
} from '@/utils/automation'

const flowWithBranch = () => {
  const branch = newStep('if_else')
  branch.branches[0].label = 'VIP'
  branch.branches[0].steps = [newStep('add_tag', { tag: 'vip' })]
  branch.else_steps = [newStep('add_tag', { tag: 'standard' })]
  return [newStep('send_sms', { message: 'ciao' }), branch]
}

describe('newStep', () => {
  it('gives every step an id and the defaults of its type', () => {
    const step = newStep('send_email')
    expect(step.id).toBeTruthy()
    expect(step.type).toBe('send_email')
    expect(step).toMatchObject({ subject: '', message: '', email_template: '' })
  })

  it('builds the nested lists that branching steps need', () => {
    const branch = newStep('if_else')
    expect(branch.branches).toHaveLength(1)
    expect(branch.branches[0].condition_groups[0]).toHaveLength(1)
    expect(branch.else_steps).toEqual([])

    const split = newStep('split')
    expect(split.paths.map((p) => p.percent)).toEqual([50, 50])

    expect(newStep('stop_if').condition_groups).toHaveLength(1)
  })

  it('applies the values of a palette preset', () => {
    const preset = PALETTE.find((entry) => entry.key === 'deal_stage')
    const step = stepFromPalette(preset)
    expect(step.type).toBe('set_field')
    expect(step.field).toBe('status')
  })
})

describe('cloneStep', () => {
  it('copies the whole subtree with fresh ids', () => {
    const [, branch] = flowWithBranch()
    const copy = cloneStep(branch)
    expect(copy.id).not.toBe(branch.id)
    expect(copy.branches[0].id).not.toBe(branch.branches[0].id)
    expect(copy.branches[0].steps[0].id).not.toBe(
      branch.branches[0].steps[0].id,
    )
    expect(copy.branches[0].steps[0].tag).toBe('vip')
    expect(copy.else_steps[0].id).not.toBe(branch.else_steps[0].id)
  })
})

describe('normalizeSteps', () => {
  it('upgrades legacy single conditions and fills in missing ids', () => {
    const steps = normalizeSteps([
      {
        type: 'add_note',
        comment: 'x',
        condition: { field: 'status', operator: 'equals', value: 'New' },
      },
      {
        type: 'if_else',
        branches: [{ steps: [{ type: 'add_tag', tag: 'a' }] }],
        else_steps: [{ type: 'exit' }],
      },
    ])
    expect(steps[0].id).toBeTruthy()
    expect(steps[0].condition).toBeUndefined()
    expect(steps[0].condition_groups).toEqual([
      [{ field: 'status', operator: 'equals', value: 'New' }],
    ])
    expect(steps[1].branches[0].id).toBeTruthy()
    expect(steps[1].branches[0].condition_groups).toHaveLength(1)
    expect(steps[1].branches[0].steps[0].id).toBeTruthy()
    expect(steps[1].else_steps[0].id).toBeTruthy()
  })
})

describe('tree surgery', () => {
  it('finds a step nested inside a branch', () => {
    const steps = flowWithBranch()
    const target = steps[1].branches[0].steps[0]
    const found = findStep(steps, target.id)
    expect(found.step).toBe(target)
    expect(found.index).toBe(0)
    expect(findStep(steps, 'nope')).toBeNull()
  })

  it('removes a nested step from the list holding it', () => {
    const steps = flowWithBranch()
    const target = steps[1].else_steps[0]
    expect(removeStep(steps, target.id)).toBe(target)
    expect(steps[1].else_steps).toHaveLength(0)
    expect(removeStep(steps, 'nope')).toBeNull()
  })

  it('duplicates a step right after the original, with new ids', () => {
    const steps = flowWithBranch()
    const copy = duplicateStep(steps, steps[0].id)
    expect(steps).toHaveLength(3)
    expect(steps[1]).toBe(copy)
    expect(copy.id).not.toBe(steps[0].id)
    expect(copy.message).toBe('ciao')
  })

  it('moves a step only inside the list bounds', () => {
    const steps = flowWithBranch()
    const first = steps[0]
    expect(moveStep(steps, 0, -1)).toBe(false)
    expect(moveStep(steps, 0, 1)).toBe(true)
    expect(steps[1]).toBe(first)
  })

  it('counts and labels the whole tree', () => {
    const steps = flowWithBranch()
    steps[0].label = 'greeting'
    expect(countSteps(steps)).toBe(4)
    expect(stepLabels(steps)).toEqual(['greeting'])
  })
})

describe('summaries', () => {
  it('describes every wait mode', () => {
    expect(waitSummary({ mode: 'duration', days: 1, hours: 2 })).toBe('1d 2h')
    expect(waitSummary({ mode: 'duration' })).toBe('no delay')
    expect(waitSummary({ mode: 'until_time', time: '09:30' })).toBe(
      'until 09:30',
    )
    expect(waitSummary({ mode: 'until_reply', timeout_hours: 48 })).toContain(
      'max 48h',
    )
  })

  it('reads condition groups as AND inside, OR between', () => {
    const groups = [
      [
        { field: 'status', operator: 'equals', value: 'New' },
        { field: 'email', operator: 'is_set' },
      ],
      [{ field: 'source', operator: 'equals', value: 'Web' }],
    ]
    expect(groupsSummary(groups)).toBe(
      'status is New and email is set or source is Web',
    )
    expect(groupsSummary([])).toBe('Always')
  })

  it('summarises steps for the canvas', () => {
    expect(
      stepSummary(newStep('set_field', { field: 'status', value: 'Won' })),
    ).toBe('status → Won')
    expect(stepSummary(newStep('split'))).toBe('A 50% · B 50%')
    expect(stepSummary(newStep('send_sms'))).toBe('No message')
  })
})

describe('cleanGroups', () => {
  it('drops rows without a field and returns null when nothing is left', () => {
    expect(cleanGroups([[{ field: '' }], []])).toBeNull()
    expect(
      cleanGroups([[{ field: 'email', operator: 'is_set' }, { field: '' }]]),
    ).toEqual([[{ field: 'email', operator: 'is_set' }]])
  })
})

describe('validateAutomation', () => {
  const draft = (steps, extra = {}) => ({
    title: 'Flow',
    trigger_event: 'Lead Created',
    steps,
    ...extra,
  })

  it('flags what the backend would refuse as an error', () => {
    const issues = validateAutomation(
      draft([
        newStep('wait', { mode: 'duration', days: 0, hours: 0, minutes: 0 }),
        newStep('go_to', { target: 'nowhere' }),
        newStep('stop_if'),
      ]),
    )
    const errors = issues.filter((i) => i.level === 'error')
    expect(errors).toHaveLength(3)
    expect(hasErrors(issues)).toBe(true)
  })

  it('flags a split that does not add up to 100', () => {
    const split = newStep('split')
    split.paths[1].percent = 10
    expect(
      validateAutomation(draft([split])).some(
        (issue) => issue.level === 'error',
      ),
    ).toBe(true)
  })

  it('warns about steps that would run but do nothing', () => {
    const sms = newStep('send_sms')
    const issues = validateAutomation(draft([sms]))
    expect(hasErrors(issues)).toBe(false)
    expect(issues[0].level).toBe('warning')
    expect(issues[0].node).toBe(sms.id)
  })

  it('requires a title and at least one step', () => {
    const issues = validateAutomation({ title: '', steps: [] })
    expect(issues.filter((i) => i.level === 'error')).toHaveLength(2)
  })

  it('accepts a go_to pointing at an existing label', () => {
    const first = newStep('add_note', { comment: 'hi' })
    first.label = 'start'
    const issues = validateAutomation(
      draft([first, newStep('go_to', { target: 'start' })]),
    )
    expect(hasErrors(issues)).toBe(false)
  })
})

describe('triggerDoctype', () => {
  it('knows which record a trigger enrols', () => {
    expect(triggerDoctype('Lead Created')).toBe('CRM Lead')
    expect(triggerDoctype('Deal Status Changed')).toBe('CRM Deal')
    expect(triggerDoctype('Tag Added')).toBeNull()
  })
})
