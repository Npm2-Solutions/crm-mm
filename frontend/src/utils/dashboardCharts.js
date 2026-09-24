// How the dashboard's charts look: ECharts options built from the widgets' data.
// Pure functions (tests/unit/dashboardCharts.test.js); the components only draw.
//
// The colours are a validated categorical palette (colour-blind separation and
// contrast checked against the app's light and dark surfaces), assigned in a
// fixed order and never cycled. Text never wears a series colour: labels, axes
// and legends use the app's ink tokens. One value axis per chart, always.

import { escapeHtml, formatValue, parseISODate } from '@/utils/dashboard'

export const PALETTE = {
  light: [
    '#2a78d6',
    '#eb6834',
    '#1baf7a',
    '#eda100',
    '#e87ba4',
    '#008300',
    '#4a3aa7',
    '#e34948',
  ],
  dark: [
    '#3987e5',
    '#d95926',
    '#199e70',
    '#c98500',
    '#d55181',
    '#008300',
    '#9085e9',
    '#e66767',
  ],
}

// one hue, light to dark: for magnitude (heatmaps)
export const SEQUENTIAL = [
  '#cde2fb',
  '#b7d3f6',
  '#9ec5f4',
  '#86b6ef',
  '#6da7ec',
  '#5598e7',
  '#3987e5',
  '#2a78d6',
  '#256abf',
  '#1c5cab',
  '#184f95',
  '#104281',
  '#0d366b',
]

const INK = 'var(--ink-gray-8)'
const INK_MUTED = 'var(--ink-gray-5)'
const GRID_LINE = 'var(--outline-gray-1)'
const AXIS_LINE = 'var(--outline-gray-2)'
// the card the chart sits on (WidgetFrame): gaps between marks are cut in it
const SURFACE = 'var(--surface-elevation-1)'

export function isDark() {
  if (typeof document === 'undefined') return false
  return document.documentElement.getAttribute('data-theme') === 'dark'
}

// The palette's slots by name (crm/dashboard/charts.py COLORS): a series that
// stands for one known thing (a status, a direction) keeps its slot, so "No
// show" is never green because it came third. Which named slots sit well
// together was checked with the palette validator, per chart, in both themes.
export const SLOTS = [
  'blue',
  'orange',
  'green',
  'amber',
  'pink',
  'darkgreen',
  'violet',
  'red',
]

// "the rest" of a donut: neutral, not one more thing to tell apart
export const OTHER = { light: '#a3a29d', dark: '#6f6e69' }

export function colors(count, dark = false) {
  const palette = dark ? PALETTE.dark : PALETTE.light
  return palette.slice(0, Math.max(0, Math.min(count, palette.length)))
}

// One colour per series or slice: its named slot, grey for "Other", else the
// next slot nobody named, in the palette's order.
export function seriesColors(items, dark = false) {
  const palette = dark ? PALETTE.dark : PALETTE.light
  const named = new Set(
    items.map((item) => item.color).filter((name) => SLOTS.includes(name)),
  )
  const free = palette.filter((_color, index) => !named.has(SLOTS[index]))
  let next = 0
  return items.map((item) => {
    if (item.other) return dark ? OTHER.dark : OTHER.light
    if (SLOTS.includes(item.color)) return palette[SLOTS.indexOf(item.color)]
    return free[Math.min(next++, free.length - 1)]
  })
}

// The label of one bucket on a time axis: "12 set" for days and weeks, "set 26" for months.
export function timeLabel(iso, grain, locale) {
  const date = parseISODate(iso)
  if (grain === 'month') {
    return new Intl.DateTimeFormat(locale, {
      month: 'short',
      year: '2-digit',
    }).format(date)
  }
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
  }).format(date)
}

function xLabels(payload, locale) {
  const values = payload.x?.values || []
  if (payload.x?.type === 'time')
    return values.map((value) => timeLabel(value, payload.x.grain, locale))
  return values.map((value) => String(value))
}

function tooltipBox() {
  return {
    backgroundColor: 'var(--surface-elevation-2)',
    borderColor: AXIS_LINE,
    borderWidth: 1,
    padding: [8, 10],
    textStyle: { color: INK, fontSize: 12 },
    extraCssText:
      'border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);',
    confine: true,
  }
}

function key(color, shape) {
  const styles = {
    line: `width:12px;height:2px;border-radius:1px;background:${color}`,
    dashed: `width:12px;height:0;border-top:2px dashed ${color}`,
    bar: `width:8px;height:8px;border-radius:2px;background:${color}`,
  }
  return `<span style="display:inline-block;${styles[shape] || styles.bar}"></span>`
}

function shapeOf(item) {
  if (item?.type === 'bar') return 'bar'
  return item?.dashed ? 'dashed' : 'line'
}

// One row of a tooltip: the value leads, the series follows; everything that
// came from data is escaped.
function tooltipRow(color, shape, name, value) {
  return (
    '<div style="display:flex;align-items:center;justify-content:space-between;gap:16px;line-height:20px">' +
    `<span style="display:flex;align-items:center;gap:6px;color:var(--ink-gray-6)">${key(color, shape)}${escapeHtml(name)}</span>` +
    `<span style="font-weight:600;color:var(--ink-gray-9)">${escapeHtml(value)}</span>` +
    '</div>'
  )
}

export function axisOptions(
  payload,
  { dark = false, locale, currency, width = 0 } = {},
) {
  const series = payload.series || []
  const labels = xLabels(payload, locale)
  const palette = seriesColors(series, dark)
  const format = payload.format || 'number'
  const money = currency || payload.currency
  const horizontal = Boolean(payload.horizontal)
  const stacked = Boolean(payload.stacked)
  const fmt = (value, compact = true) =>
    formatValue(value, format, { locale, currency: money, compact })
  const bars = series.every((item) => item.type === 'bar')
  const legend = series.length > 1
  const lastBar = series.map((item) => item.type).lastIndexOf('bar')
  const labelEnds = bars && series.length === 1 && labels.length <= 15
  // under vertical bars, category names wrap to their bar's room instead of
  // every other one being dropped (the value axis and padding take ~56px)
  const room =
    !horizontal && payload.x?.type !== 'time' && width && labels.length
      ? (width - 56) / labels.length
      : 0

  const categoryAxis = {
    type: 'category',
    data: labels,
    inverse: horizontal,
    axisTick: { show: false },
    axisLine: { show: !horizontal, lineStyle: { color: AXIS_LINE } },
    axisLabel: {
      color: INK_MUTED,
      fontSize: 11,
      hideOverlap: true,
      ...(horizontal ? { width: 120, overflow: 'truncate' } : {}),
      ...(room >= 40
        ? {
            interval: 0,
            width: Math.floor(room - 6),
            overflow: 'break',
            lineHeight: 13,
          }
        : {}),
    },
  }
  const valueAxis = {
    type: 'value',
    splitNumber: 4,
    axisLabel: {
      color: INK_MUTED,
      fontSize: 11,
      formatter: (value) => fmt(value),
    },
    splitLine: { lineStyle: { color: GRID_LINE, type: 'solid' } },
  }

  return {
    animationDuration: 400,
    color: palette,
    textStyle: { fontFamily: 'InterVar, Inter, system-ui, sans-serif' },
    grid: {
      left: 4,
      right: horizontal && labelEnds ? 56 : 12,
      top: 12,
      bottom: legend ? 34 : 4,
      containLabel: true,
    },
    legend: {
      show: legend,
      bottom: 0,
      left: 0,
      icon: bars ? 'roundRect' : 'circle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      textStyle: { color: 'var(--ink-gray-7)', fontSize: 12 },
    },
    tooltip: {
      ...tooltipBox(),
      trigger: 'axis',
      axisPointer: {
        type: bars ? 'shadow' : 'line',
        lineStyle: { color: AXIS_LINE },
      },
      formatter: (params) => {
        const rows = Array.isArray(params) ? params : [params]
        if (!rows.length) return ''
        const title = `<div style="margin-bottom:4px;color:var(--ink-gray-5)">${escapeHtml(rows[0].name)}</div>`
        return (
          title +
          rows
            .map((row) =>
              tooltipRow(
                row.color,
                shapeOf(series[row.seriesIndex]),
                row.seriesName,
                fmt(row.value, false),
              ),
            )
            .join('')
        )
      },
    },
    xAxis: horizontal ? valueAxis : categoryAxis,
    yAxis: horizontal ? categoryAxis : valueAxis,
    series: series.map((item, index) => {
      const bar = item.type === 'bar'
      const base = {
        name: item.label,
        type: bar ? 'bar' : 'line',
        data: item.values,
        stack: stacked ? 'total' : undefined,
        emphasis: { focus: 'series' },
      }
      if (bar) {
        const top = !stacked || index === lastBar
        const radius = top ? (horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]) : 0
        return {
          ...base,
          barMaxWidth: 24,
          barGap: '20%',
          itemStyle: {
            color: palette[index],
            borderRadius: radius,
            borderColor: stacked ? SURFACE : undefined,
            borderWidth: stacked ? 1 : 0,
          },
          label: labelEnds
            ? {
                show: true,
                position: horizontal ? 'right' : 'top',
                color: 'var(--ink-gray-7)',
                fontSize: 11,
                formatter: ({ value }) => fmt(value),
              }
            : { show: false },
        }
      }
      const few = (item.values || []).length <= 14
      return {
        ...base,
        smooth: false,
        symbol: 'circle',
        symbolSize: 7,
        showSymbol: few,
        lineStyle: {
          width: 2,
          color: palette[index],
          type: item.dashed ? 'dashed' : 'solid',
        },
        itemStyle: {
          color: palette[index],
          borderColor: SURFACE,
          borderWidth: 2,
        },
        areaStyle:
          series.length === 1
            ? { color: palette[index], opacity: 0.08 }
            : undefined,
      }
    }),
  }
}

export function donutOptions(payload, { dark = false, locale, currency } = {}) {
  const slices = payload.slices || []
  const palette = seriesColors(slices, dark)
  const total = slices.reduce(
    (sum, slice) => sum + (Number(slice.value) || 0),
    0,
  )
  const money = currency || payload.currency
  return {
    animationDuration: 400,
    color: palette,
    tooltip: {
      ...tooltipBox(),
      trigger: 'item',
      formatter: (params) => {
        const share = total ? Math.round((params.value / total) * 100) : 0
        const value = formatValue(params.value, payload.format, {
          locale,
          currency: money,
          compact: false,
        })
        return tooltipRow(
          params.color,
          'bar',
          params.name,
          `${value} · ${share}%`,
        )
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['58%', '84%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        emphasis: { scale: true, scaleSize: 4 },
        itemStyle: { borderColor: SURFACE, borderWidth: 2, borderRadius: 4 },
        data: slices.map((slice, index) => ({
          name: slice.label,
          value: slice.value,
          itemStyle: { color: palette[index] },
        })),
      },
    ],
  }
}

// The magnitude ramp for a theme: light to dark on a light page, and the other
// way round on a dark one, so "a little" always recedes into the surface.
export function sequential(dark = false) {
  return dark ? [...SEQUENTIAL].reverse() : SEQUENTIAL
}

// A heatmap cell's colour: the ramp by share of the busiest cell. Empty cells
// stay neutral, so "nothing" never reads as "a little".
export function heatColor(value, max, dark = false) {
  if (!value || !max) return null
  const ramp = sequential(dark)
  const share = Math.min(1, value / max)
  const index = Math.min(
    ramp.length - 1,
    Math.max(1, Math.round(share * (ramp.length - 1))),
  )
  return ramp[index]
}
