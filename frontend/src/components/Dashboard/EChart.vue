<!--
  One ECharts chart that lives and dies with its element.

  frappe-ui's ECharts started watching its element's size half a second after
  mounting. A chart that was gone by then — a dashboard switched with `?d=`,
  which rebuilds the page, or a widget redrawn as its numbers came in — asked
  to watch `undefined`, and the console filled with «Failed to execute
  'observe' on 'ResizeObserver': parameter 1 is not of type 'Element'». It
  never let go of the chart either. Here the size is watched from the start,
  and the watch and the chart end with the element.
-->
<template>
  <div ref="el" dir="ltr" />
</template>

<script setup>
import { init } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  options: { type: Object, required: true },
})

const el = ref(null)
let chart = null
let observer = null
let settling = null

onMounted(() => {
  chart = init(el.value, 'light', { renderer: 'svg' })
  chart.setOption(props.options, true)
  // redrawn once the size has settled, not at every pixel of a drag; a chart
  // first laid out at no size at all is drawn when it gets one
  observer = new ResizeObserver(() => {
    clearTimeout(settling)
    settling = setTimeout(
      () => chart?.resize({ animation: { duration: 300 } }),
      250,
    )
  })
  observer.observe(el.value)
})

watch(
  () => props.options,
  (options) => chart?.setOption(options, true),
  { deep: true },
)

onBeforeUnmount(() => {
  clearTimeout(settling)
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>
