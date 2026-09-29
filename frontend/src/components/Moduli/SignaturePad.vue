<!--
  A signature drawn with a finger, a pen or the mouse (docs/gestionale-medico,
  design, "La firma").

  Only the picture of the stroke leaves this component, as a PNG: no pressure, no
  timing of the points, which `signature_pad` can read and which would make it a
  biometric signature, with the Garante's rules of 2014. The points are kept in
  memory only to redraw the stroke when the box changes size.

  The box is white paper in the dark theme too: ink is dark on a signature, and
  the PNG goes into a PDF printed on white.
-->
<template>
  <div class="flex flex-col gap-2">
    <div
      v-if="readonly || showSaved"
      class="flex h-40 max-w-md items-center justify-center overflow-hidden rounded-lg border border-outline-gray-2 max-md:max-w-none"
      :style="{ background: PAPER }"
    >
      <img
        v-if="modelValue"
        :src="modelValue"
        :alt="placeholder"
        class="max-h-full max-w-full object-contain"
      />
      <span v-else class="text-sm text-ink-gray-5">{{ __('Not signed') }}</span>
    </div>
    <div
      v-else
      ref="box"
      class="relative h-40 max-w-md overflow-hidden rounded-lg border max-md:max-w-none"
      :class="missing ? 'border-outline-red-2' : 'border-outline-gray-3'"
      :style="{ background: PAPER }"
    >
      <canvas
        ref="canvas"
        class="absolute inset-0 size-full cursor-crosshair touch-none"
        :aria-label="placeholder"
        @pointerdown="start"
        @pointermove="move"
        @pointerup="end"
        @pointercancel="end"
        @pointerleave="end"
      />
      <span
        class="pointer-events-none absolute inset-x-4 bottom-3 border-t pt-1 text-sm"
        :style="{ borderColor: LINE, color: HINT }"
      >
        {{ placeholder }}
      </span>
    </div>
    <div v-if="!readonly" class="flex gap-2">
      <Button
        v-if="showSaved"
        size="sm"
        :label="__('Sign again')"
        @click="showSaved = false"
      />
      <Button
        v-else
        size="sm"
        :label="__('Clear')"
        :disabled="!strokes.length"
        @click="clear"
      />
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const PAPER = '#ffffff'
const INK = '#1f2328'
const LINE = '#c9ccd1'
const HINT = '#8a8f98'

const props = defineProps({
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
  missing: { type: Boolean, default: false },
})

/** A PNG data URL, or the file it was saved to. */
const modelValue = defineModel({ type: [String, null], default: null })

const box = ref(null)
const canvas = ref(null)
const strokes = ref([])
// a signature already there is shown, not redrawn: signing again is a choice
const showSaved = ref(Boolean(modelValue.value))
let drawing = null
let observer = null

function context() {
  const ctx = canvas.value.getContext('2d')
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = INK
  ctx.fillStyle = INK
  ctx.lineWidth = 2.2 * (window.devicePixelRatio || 1)
  return ctx
}

function point(event) {
  const rect = canvas.value.getBoundingClientRect()
  const scale = window.devicePixelRatio || 1
  return [
    (event.clientX - rect.left) * scale,
    (event.clientY - rect.top) * scale,
  ]
}

function start(event) {
  if (props.readonly) return
  event.preventDefault()
  canvas.value.setPointerCapture?.(event.pointerId)
  drawing = [point(event)]
  strokes.value.push(drawing)
  const ctx = context()
  const [x, y] = drawing[0]
  ctx.beginPath()
  ctx.arc(x, y, ctx.lineWidth / 2, 0, Math.PI * 2)
  ctx.fill()
}

function move(event) {
  if (!drawing) return
  event.preventDefault()
  drawing.push(point(event))
  const n = drawing.length
  if (n < 3) return
  // a curve through the middles of the last points: a smooth line, not a zigzag
  const [x0, y0] = drawing[n - 3]
  const [x1, y1] = drawing[n - 2]
  const [x2, y2] = drawing[n - 1]
  const ctx = context()
  ctx.beginPath()
  ctx.moveTo((x0 + x1) / 2, (y0 + y1) / 2)
  ctx.quadraticCurveTo(x1, y1, (x1 + x2) / 2, (y1 + y2) / 2)
  ctx.stroke()
}

function end() {
  if (!drawing) return
  drawing = null
  modelValue.value = strokes.value.length
    ? canvas.value.toDataURL('image/png')
    : null
}

function redraw() {
  const ctx = context()
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  for (const stroke of strokes.value) {
    ctx.beginPath()
    ctx.moveTo(...stroke[0])
    for (let i = 1; i < stroke.length - 1; i++) {
      const [x1, y1] = stroke[i]
      const [x2, y2] = stroke[i + 1]
      ctx.quadraticCurveTo(x1, y1, (x1 + x2) / 2, (y1 + y2) / 2)
    }
    ctx.stroke()
  }
}

function size() {
  if (!canvas.value || !box.value) return
  const scale = window.devicePixelRatio || 1
  const width = Math.round(box.value.clientWidth * scale)
  const height = Math.round(box.value.clientHeight * scale)
  if (canvas.value.width === width && canvas.value.height === height) return
  // points were taken at the old size: stretch them to the new one
  const sx = canvas.value.width ? width / canvas.value.width : 1
  const sy = canvas.value.height ? height / canvas.value.height : 1
  strokes.value = strokes.value.map((stroke) =>
    stroke.map(([x, y]) => [x * sx, y * sy]),
  )
  canvas.value.width = width
  canvas.value.height = height
  redraw()
}

function clear() {
  strokes.value = []
  redraw()
  modelValue.value = null
}

function watchSize() {
  observer?.disconnect()
  if (!box.value) return
  size()
  observer = new ResizeObserver(() => size())
  observer.observe(box.value)
}

onMounted(watchSize)
watch(showSaved, async (saved) => {
  if (saved) return
  strokes.value = []
  modelValue.value = null
  await nextTick()
  watchSize()
})
onBeforeUnmount(() => observer?.disconnect())
</script>
