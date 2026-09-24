import { describe, expect, it } from 'vitest'
import {
  bottomOf,
  describeDelta,
  duplicateItem,
  escapeHtml,
  formatDuration,
  formatRange,
  formatValue,
  groupByCategory,
  mobileOrder,
  newItem,
  newKey,
  periodRange,
  searchCatalog,
  toSavedLayout,
  usage,
} from '@/utils/dashboard'
import {
  axisOptions,
  colors,
  OTHER,
  seriesColors,
  donutOptions,
  heatColor,
  PALETTE,
  SEQUENTIAL,
  timeLabel,
} from '@/utils/dashboardCharts'

// Thursday 24 September 2026
const TODAY = new Date(2026, 8, 24)

describe('periodRange', () => {
  it('gives both ends of every preset, today included', () => {
    expect(periodRange('today', TODAY)).toEqual(['2026-09-24', '2026-09-24'])
    expect(periodRange('yesterday', TODAY)).toEqual([
      '2026-09-23',
      '2026-09-23',
    ])
    expect(periodRange('last_7_days', TODAY)).toEqual([
      '2026-09-18',
      '2026-09-24',
    ])
    expect(periodRange('last_30_days', TODAY)).toEqual([
      '2026-08-26',
      '2026-09-24',
    ])
    expect(periodRange('last_90_days', TODAY)).toEqual([
      '2026-06-27',
      '2026-09-24',
    ])
    expect(periodRange('this_month', TODAY)).toEqual([
      '2026-09-01',
      '2026-09-24',
    ])
    expect(periodRange('last_month', TODAY)).toEqual([
      '2026-08-01',
      '2026-08-31',
    ])
    expect(periodRange('this_quarter', TODAY)).toEqual([
      '2026-07-01',
      '2026-09-24',
    ])
    expect(periodRange('this_year', TODAY)).toEqual([
      '2026-01-01',
      '2026-09-24',
    ])
  })

  it('starts the week on Monday unless told otherwise', () => {
    expect(periodRange('this_week', TODAY)).toEqual([
      '2026-09-21',
      '2026-09-24',
    ])
    expect(periodRange('this_week', TODAY, 0)).toEqual([
      '2026-09-20',
      '2026-09-24',
    ])
  })

  it('handles last month across a year boundary', () => {
    expect(periodRange('last_month', new Date(2026, 0, 10))).toEqual([
      '2025-12-01',
      '2025-12-31',
    ])
  })

  it('falls back to the last 30 days for an unknown key', () => {
    expect(periodRange('nonsense', TODAY)).toEqual(
      periodRange('last_30_days', TODAY),
    )
  })
})

describe('formatRange', () => {
  it('drops the year when it is this one', () => {
    expect(formatRange('2026-09-01', '2026-09-30', 'en-US', TODAY)).toBe(
      'Sep 1 – Sep 30',
    )
    expect(formatRange('2026-09-24', '2026-09-24', 'en-US', TODAY)).toBe(
      'Sep 24',
    )
  })

  it('keeps it when either end is in another year', () => {
    expect(formatRange('2025-12-15', '2026-01-14', 'en-US', TODAY)).toBe(
      'Dec 15, 2025 – Jan 14, 2026',
    )
  })
})

describe('formatValue', () => {
  it('compacts large numbers and keeps small ones exact', () => {
    expect(formatValue(1284, 'number', { locale: 'en-US' })).toBe('1,284')
    expect(formatValue(12900, 'number', { locale: 'en-US' })).toBe('12.9K')
    expect(
      formatValue(12900, 'number', { locale: 'en-US', compact: false }),
    ).toBe('12,900')
    expect(formatValue(3.25, 'number', { locale: 'en-US' })).toBe('3.3')
  })

  it("formats money in the dashboard currency, in the reader's locale", () => {
    expect(
      formatValue(89.5, 'currency', { locale: 'en-US', currency: 'EUR' }),
    ).toBe('€89.5')
    expect(
      formatValue(1300000, 'currency', { locale: 'en-US', currency: 'EUR' }),
    ).toBe('€1.3M')
    // Intl separates with non-breaking spaces
    const italian = formatValue(1300000, 'currency', {
      locale: 'it-IT',
      currency: 'EUR',
    })
    expect(italian.replace(/\s/g, ' ')).toBe('1,3 Mln €')
  })

  it('does not break on an unknown currency', () => {
    expect(
      formatValue(10, 'currency', { locale: 'en-US', currency: 'NOPE!' }),
    ).toBe('10')
  })

  it('formats percentages, ratios and days', () => {
    expect(formatValue(72.7, 'percent', { locale: 'en-US' })).toBe('72.7%')
    expect(formatValue(3.21, 'ratio', { locale: 'en-US' })).toBe('3.2×')
    expect(formatValue(3.5, 'days', { locale: 'en-US' })).toBe('3.5 days')
  })

  it('shows a dash for nothing', () => {
    expect(formatValue(null)).toBe('–')
    expect(formatValue('')).toBe('–')
    expect(formatValue('abc')).toBe('–')
  })
})

describe('formatDuration', () => {
  it('uses the two most significant units', () => {
    expect(formatDuration(45, 'en-US')).toBe('45 sec')
    expect(formatDuration(754, 'en-US')).toBe('12 min')
    expect(formatDuration(12000, 'en-US')).toBe('3 hr 20 min')
    expect(formatDuration(7200, 'en-US')).toBe('2 hr')
    expect(formatDuration(190000, 'en-US')).toBe('2 days 4 hr')
  })
})

describe('describeDelta', () => {
  it('says whether a rise is good news', () => {
    expect(
      describeDelta({ delta: 12.5, deltaUnit: 'percent' }, 'en-US'),
    ).toEqual({
      text: '+13%',
      tone: 'good',
      direction: 'up',
    })
    expect(
      describeDelta(
        { delta: 12.5, deltaUnit: 'percent', negativeIsBetter: true },
        'en-US',
      ).tone,
    ).toBe('bad')
    expect(
      describeDelta({ delta: -3.2, deltaUnit: 'points' }, 'en-US'),
    ).toEqual({
      text: '−3.2 pts',
      tone: 'bad',
      direction: 'down',
    })
  })

  it('is neutral when nothing moved and absent when there is nothing to compare', () => {
    expect(
      describeDelta({ delta: 0, deltaUnit: 'percent' }, 'en-US').tone,
    ).toBe('neutral')
    expect(describeDelta({ value: 3 })).toBeNull()
  })
})

describe('the grid', () => {
  const items = [
    { name: 'a', layout: { x: 0, y: 0, w: 4, h: 3, i: 'a' } },
    {
      name: 'b',
      layout: { x: 4, y: 0, w: 10, h: 8, i: 'b' },
      config: { measure: 'value' },
    },
    { name: 'spacer', layout: { x: 0, y: 3, w: 4, h: 3, i: 's' } },
  ]
  const random = () => 0.123456

  it('puts new widgets at the bottom, at their default size', () => {
    expect(bottomOf(items)).toBe(8)
    const item = newItem(
      { id: 'won_deals', kind: 'number', size: [4, 3] },
      items,
      random,
    )
    expect(item.layout).toMatchObject({ x: 0, y: 8, w: 4, h: 3 })
    expect(item.layout.i.startsWith('won_deals_')).toBe(true)
  })

  it('never reuses a key', () => {
    let calls = 0
    const sequence = () => (calls++ < 2 ? 0.5 : 0.9)
    const taken = [{ layout: { i: newKey('x', [], () => 0.5) } }]
    expect(newKey('x', taken, sequence)).not.toBe(taken[0].layout.i)
  })

  it('duplicates below the original with its settings', () => {
    const copy = duplicateItem(items[1], items, random)
    expect(copy.config).toEqual({ measure: 'value' })
    expect(copy.layout.y).toBe(8)
    expect(copy.layout.i).not.toBe('b')
  })

  it('saves only place and settings', () => {
    const saved = toSavedLayout([
      { ...items[1], data: { kind: 'axis' }, unavailable: {} },
    ])
    expect(saved).toEqual([
      {
        name: 'b',
        type: undefined,
        layout: items[1].layout,
        config: { measure: 'value' },
      },
    ])
  })

  it('stacks top to bottom, left to right, without spacers, on a phone', () => {
    const order = mobileOrder([
      { name: 'c', layout: { x: 10, y: 3 } },
      { name: 'b', layout: { x: 10, y: 0 } },
      { name: 'spacer', layout: { x: 0, y: 1 } },
      { name: 'a', layout: { x: 0, y: 0 } },
    ])
    expect(order.map((item) => item.name)).toEqual(['a', 'b', 'c'])
  })

  it('counts the widgets already placed', () => {
    expect(usage([{ name: 'a' }, { name: 'a' }, { name: 'b' }])).toEqual({
      a: 2,
      b: 1,
    })
  })
})

describe('the catalogue', () => {
  const widgets = [
    {
      id: 'whatsapp_received',
      category: 'whatsapp',
      title: 'WhatsApp ricevuti',
      description: 'Messaggi',
    },
    {
      id: 'won_deals',
      category: 'sales',
      title: 'Trattative vinte',
      description: '',
      keywords: ['closed'],
    },
    {
      id: 'calls',
      category: 'calls',
      title: 'Chiamate',
      description: 'Entrate e uscite',
    },
  ]

  it('matches every word, ignoring accents and case', () => {
    expect(searchCatalog(widgets, 'WHATSAPP').map((w) => w.id)).toEqual([
      'whatsapp_received',
    ])
    expect(
      searchCatalog(widgets, 'trattative closed').map((w) => w.id),
    ).toEqual(['won_deals'])
    expect(searchCatalog(widgets, 'entrate').map((w) => w.id)).toEqual([
      'calls',
    ])
    expect(
      searchCatalog([{ title: 'Attività', description: '' }], 'attivita'),
    ).toHaveLength(1)
  })

  it('filters by category', () => {
    expect(searchCatalog(widgets, '', 'sales').map((w) => w.id)).toEqual([
      'won_deals',
    ])
  })

  it('groups in the catalogue order and drops empty groups', () => {
    const groups = groupByCategory(widgets, [
      'sales',
      'people',
      'whatsapp',
      'calls',
    ])
    expect(groups.map((group) => group.category)).toEqual([
      'sales',
      'whatsapp',
      'calls',
    ])
  })
})

describe('escapeHtml', () => {
  it('neutralises markup coming from data', () => {
    expect(escapeHtml('<img src=x onerror="alert(1)">')).toBe(
      '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;',
    )
    expect(escapeHtml(null)).toBe('')
  })
})

describe('charts', () => {
  const trend = {
    kind: 'axis',
    x: { type: 'time', grain: 'day', values: ['2026-09-01', '2026-09-02'] },
    series: [
      { name: 'in', label: 'Received', type: 'line', values: [3, 5] },
      { name: 'out', label: 'Sent', type: 'line', values: [2, 4] },
    ],
    format: 'number',
  }

  it('assigns palette colours in order and never more than it has', () => {
    expect(colors(2)).toEqual(PALETTE.light.slice(0, 2))
    expect(colors(2, true)).toEqual(PALETTE.dark.slice(0, 2))
    expect(colors(20)).toHaveLength(8)
  })

  it('keeps a named slot for a known thing, whatever its rank', () => {
    const items = [{ label: 'Failed' }, { label: 'Read', color: 'darkgreen' }]
    // the unnamed one takes the first slot nobody named, not its rank's
    expect(seriesColors(items)).toEqual([PALETTE.light[0], PALETTE.light[5]])
    expect(seriesColors([{ color: 'blue' }, {}])).toEqual([
      PALETTE.light[0],
      PALETTE.light[1],
    ])
    expect(seriesColors([{ color: 'pink' }], true)).toEqual([PALETTE.dark[4]])
    expect(seriesColors([{ label: 'Other', other: true }])).toEqual([
      OTHER.light,
    ])
  })

  it('wraps names under vertical bars when each bar has room', () => {
    const buckets = {
      x: { type: 'category', values: ['Under 5 min', '5–15 min', 'No answer'] },
      series: [{ label: 'Chats', type: 'bar', values: [3, 2, 1] }],
    }
    const roomy = axisOptions(buckets, { width: 500 }).xAxis.axisLabel
    expect(roomy.interval).toBe(0)
    expect(roomy.overflow).toBe('break')
    expect(roomy.width).toBe(Math.floor((500 - 56) / 3 - 6))
    // too tight to wrap: let ECharts drop what overlaps
    expect(axisOptions(buckets, { width: 150 }).xAxis.axisLabel.interval).toBe(
      undefined,
    )
  })

  it('draws a dashed series dashed', () => {
    const options = axisOptions({
      x: { type: 'category', values: ['a', 'b'] },
      series: [
        { label: 'Calls', type: 'line', values: [1, 2] },
        { label: 'Missed', type: 'line', values: [0, 1], dashed: true },
      ],
    })
    expect(options.series.map((item) => item.lineStyle.type)).toEqual([
      'solid',
      'dashed',
    ])
  })

  it('labels time buckets by grain', () => {
    expect(timeLabel('2026-09-12', 'day', 'en-US')).toBe('Sep 12')
    expect(timeLabel('2026-09-01', 'month', 'en-US')).toBe('Sep 26')
  })

  it('draws a trend with one value axis and a legend for two series', () => {
    const options = axisOptions(trend, { locale: 'en-US' })
    expect(options.xAxis.data).toEqual(['Sep 1', 'Sep 2'])
    expect(options.yAxis.type).toBe('value')
    expect(Array.isArray(options.yAxis)).toBe(false)
    expect(options.legend.show).toBe(true)
    expect(options.series.map((s) => s.name)).toEqual(['Received', 'Sent'])
  })

  it('escapes series and category names in the tooltip', () => {
    const options = axisOptions(
      {
        kind: 'axis',
        x: { type: 'category', values: ['<b>x</b>'] },
        series: [{ name: 'n', label: 'Deals', type: 'bar', values: [2] }],
        horizontal: true,
      },
      { locale: 'en-US' },
    )
    const html = options.tooltip.formatter([
      {
        name: '<b>x</b>',
        seriesName: '<i>Deals</i>',
        seriesIndex: 0,
        color: '#000',
        value: 2,
      },
    ])
    expect(html).not.toContain('<b>')
    expect(html).not.toContain('<i>')
    expect(html).toContain('&lt;b&gt;')
  })

  it('lays rankings sideways with labels at the bar end and one legend-less series', () => {
    const options = axisOptions(
      {
        kind: 'axis',
        x: { type: 'category', values: ['A', 'B'] },
        series: [{ name: 'n', label: 'Deals', type: 'bar', values: [5, 2] }],
        horizontal: true,
      },
      { locale: 'en-US' },
    )
    expect(options.yAxis.type).toBe('category')
    expect(options.yAxis.inverse).toBe(true)
    expect(options.legend.show).toBe(false)
    expect(options.series[0].label.show).toBe(true)
    expect(options.series[0].barMaxWidth).toBe(24)
  })

  it('rounds only the top of a stack', () => {
    const options = axisOptions(
      {
        kind: 'axis',
        x: { type: 'category', values: ['A'] },
        series: [
          { name: 'a', label: 'A', type: 'bar', values: [1] },
          { name: 'b', label: 'B', type: 'bar', values: [2] },
        ],
        stacked: true,
      },
      { locale: 'en-US' },
    )
    expect(options.series[0].itemStyle.borderRadius).toBe(0)
    expect(options.series[1].itemStyle.borderRadius).toEqual([4, 4, 0, 0])
  })

  it('gives a donut its slices with shares in the tooltip', () => {
    const options = donutOptions(
      {
        kind: 'donut',
        slices: [
          { label: 'WhatsApp', value: 3 },
          { label: 'Email', value: 1 },
        ],
      },
      { locale: 'en-US' },
    )
    expect(options.series[0].data.map((d) => d.name)).toEqual([
      'WhatsApp',
      'Email',
    ])
    expect(
      options.tooltip.formatter({ name: 'WhatsApp', value: 3, color: '#000' }),
    ).toContain('75%')
  })

  it('colours heat by share of the busiest cell, and leaves empty cells neutral', () => {
    expect(heatColor(0, 10)).toBeNull()
    expect(heatColor(10, 10)).toBe(SEQUENTIAL[SEQUENTIAL.length - 1])
    expect(SEQUENTIAL.indexOf(heatColor(1, 100))).toBeGreaterThanOrEqual(1)
    // on a dark page the busiest cell is the lightest
    expect(heatColor(10, 10, true)).toBe(SEQUENTIAL[0])
  })
})
