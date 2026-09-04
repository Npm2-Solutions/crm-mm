import {
  appointmentColor,
  blockStyle,
  buildTimeAxis,
  columnsFor,
  dateAtMinutes,
  formatMinutes,
  layoutLanes,
  minutesAtRatio,
  minutesFromMidnight,
  snapMinutes,
  unassigned,
  visibleWindow,
} from '@/utils/scheduler'

const at = (start, end) => ({ startMinutes: start, endMinutes: end })

describe('minutesFromMidnight', () => {
  it('reads a datetime string as minutes since midnight', () => {
    expect(minutesFromMidnight('2026-09-03 09:30:00')).toBe(9 * 60 + 30)
  })

  it('falls back to 0 for garbage instead of throwing', () => {
    expect(minutesFromMidnight('not a date')).toBe(0)
  })
})

describe('snapMinutes', () => {
  it('rounds to the nearest step', () => {
    expect(snapMinutes(547, 15)).toBe(540)
    expect(snapMinutes(553, 15)).toBe(555)
  })

  it('never leaves the day', () => {
    expect(snapMinutes(-30)).toBe(0)
    expect(snapMinutes(2000)).toBe(1440)
  })
})

describe('visibleWindow', () => {
  it('uses office hours when everything fits inside them', () => {
    expect(visibleWindow([at(600, 660)])).toEqual({
      startMinutes: 7 * 60,
      endMinutes: 21 * 60,
    })
  })

  it('opens up for an early appointment instead of clipping it', () => {
    expect(visibleWindow([at(6 * 60 + 30, 7 * 60)]).startMinutes).toBe(6 * 60)
  })

  it('opens up for a late appointment', () => {
    expect(visibleWindow([at(22 * 60, 23 * 60 + 30)]).endMinutes).toBe(24 * 60)
  })
})

describe('buildTimeAxis', () => {
  it('marks every hour of the window inclusive', () => {
    const axis = buildTimeAxis(9, 11)
    expect(axis.map((mark) => mark.label)).toEqual(['09:00', '10:00', '11:00'])
    expect(axis[0].minutes).toBe(540)
  })
})

describe('layoutLanes', () => {
  it('keeps back-to-back appointments in one lane', () => {
    const laid = layoutLanes([at(540, 600), at(600, 660)])
    expect(laid.map((item) => item.lane)).toEqual([0, 0])
    expect(laid.every((item) => item.lanes === 1)).toBe(true)
  })

  it('puts two overlapping appointments side by side', () => {
    const laid = layoutLanes([at(540, 620), at(600, 660)])
    expect(laid.map((item) => item.lane)).toEqual([0, 1])
    expect(laid.every((item) => item.lanes === 2)).toBe(true)
  })

  it('reuses a lane freed earlier in the same cluster', () => {
    // 9:00-10:00, 9:30-11:00, 10:00-10:30 → the third fits back in lane 0
    const laid = layoutLanes([at(540, 600), at(570, 660), at(600, 630)])
    expect(laid.map((item) => item.lane)).toEqual([0, 1, 0])
    expect(laid.every((item) => item.lanes === 2)).toBe(true)
  })

  it('sizes clusters independently', () => {
    const laid = layoutLanes([at(540, 620), at(600, 660), at(800, 830)])
    const last = laid.find((item) => item.startMinutes === 800)
    expect(last.lanes).toBe(1)
  })

  it('does not mutate the input', () => {
    const input = [at(540, 600)]
    layoutLanes(input)
    expect(input[0].lane).toBeUndefined()
  })
})

describe('blockStyle', () => {
  const window = { startMinutes: 540, endMinutes: 1080 } // 09:00 → 18:00

  it('places a block proportionally in the window', () => {
    const style = blockStyle({ ...at(630, 690), lane: 0, lanes: 1 }, window)
    expect(style.top).toBe(`${(90 / 540) * 100}%`)
    expect(style.height).toBe(`${(60 / 540) * 100}%`)
    expect(style.left).toBe('0%')
    expect(style.width).toBe('100%')
  })

  it('splits the width across lanes', () => {
    const style = blockStyle({ ...at(630, 690), lane: 1, lanes: 2 }, window)
    expect(style.left).toBe('50%')
    expect(style.width).toBe('50%')
  })

  it('keeps a very short appointment clickable', () => {
    const style = blockStyle({ ...at(630, 632), lane: 0, lanes: 1 }, window)
    expect(parseFloat(style.height)).toBeGreaterThanOrEqual(1.6)
  })
})

describe('minutesAtRatio', () => {
  it('turns a click position into a snapped time', () => {
    const window = { startMinutes: 540, endMinutes: 1080 }
    expect(minutesAtRatio(0, window)).toBe(540)
    expect(minutesAtRatio(0.5, window)).toBe(810)
  })
})

describe('formatMinutes', () => {
  it('formats as HH:mm', () => {
    expect(formatMinutes(540)).toBe('09:00')
    expect(formatMinutes(1439)).toBe('23:59')
  })
})

describe('dateAtMinutes', () => {
  it('builds a local date from an ISO day and a minute offset', () => {
    const date = dateAtMinutes('2026-09-03', 585)
    expect(date.getFullYear()).toBe(2026)
    expect(date.getMonth()).toBe(8)
    expect(date.getDate()).toBe(3)
    expect(date.getHours()).toBe(9)
    expect(date.getMinutes()).toBe(45)
  })
})

describe('columnsFor', () => {
  const appointments = [
    {
      name: 'A',
      staff: [{ user: 'anna@x.it' }, { user: 'bruno@x.it' }],
      resources: [{ resource: 'Room 1' }],
    },
    {
      name: 'B',
      staff: [{ user: 'bruno@x.it' }],
      resources: [],
    },
  ]

  it('shows a two-professional appointment in both columns', () => {
    const buckets = columnsFor(appointments, 'staff', [
      'anna@x.it',
      'bruno@x.it',
    ])
    expect(buckets.get('anna@x.it').map((a) => a.name)).toEqual(['A'])
    expect(buckets.get('bruno@x.it').map((a) => a.name)).toEqual(['A', 'B'])
  })

  it('buckets by room when asked', () => {
    const buckets = columnsFor(appointments, 'resource', ['Room 1', 'Room 2'])
    expect(buckets.get('Room 1').map((a) => a.name)).toEqual(['A'])
    expect(buckets.get('Room 2')).toEqual([])
  })

  it('ignores columns that are not on screen', () => {
    const buckets = columnsFor(appointments, 'staff', ['anna@x.it'])
    expect(buckets.has('bruno@x.it')).toBe(false)
    expect(buckets.get('anna@x.it')).toHaveLength(1)
  })
})

describe('unassigned', () => {
  it('reports appointments that no visible column would show', () => {
    const appointments = [
      { name: 'A', staff: [{ user: 'anna@x.it' }] },
      { name: 'B', staff: [{ user: 'carla@x.it' }] },
    ]
    expect(
      unassigned(appointments, 'staff', ['anna@x.it']).map((a) => a.name),
    ).toEqual(['B'])
  })
})

describe('appointmentColor', () => {
  it('prefers the appointment colour', () => {
    expect(
      appointmentColor({ color: '#123456', service: 'X' }, { X: '#abcdef' }),
    ).toBe('#123456')
  })

  it('falls back to the service colour', () => {
    expect(appointmentColor({ service: 'X' }, { X: '#abcdef' })).toBe('#abcdef')
  })

  it('falls back to a status colour when nothing is set', () => {
    expect(appointmentColor({ status: 'Cancelled' }, {})).toBe('#E24C4C')
    expect(appointmentColor({}, {})).toBe('#4C7EFF')
  })
})
