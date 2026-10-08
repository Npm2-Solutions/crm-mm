<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Where it hurts: the body's outline from the front and from the back, and the
  person or the practitioner marks it. A tap puts a numbered point, with its
  words and how much it hurts from 0 to 10; «Draw» takes the finger as a pen,
  as the signature pad does, for an area or where the pain goes.

  The answer is points and strokes as fractions of the outline (`moduli.js`,
  `cleanBodyChart`), never a picture: the signed PDF draws the same outlines
  from them (`crm/moduli/corpo.py`). A tap to mark leaves the page free to
  scroll under the finger; only while drawing does the outline keep it.

  White paper in the dark theme too, as the signature's box: the PDF is printed
  on white, and the marks read the same on both.
-->
<template>
  <div class="flex flex-col gap-3">
    <div
      v-if="!readonly && field.drawing"
      class="flex flex-wrap items-center gap-2"
      role="group"
      :aria-label="__('How to mark')"
    >
      <Button
        class="touch-target"
        :variant="mode === 'points' ? 'solid' : 'outline'"
        :aria-pressed="mode === 'points'"
        :label="__('Mark a point')"
        @click="mode = 'points'"
      >
        <template #prefix><LucideMapPin class="size-4" /></template>
      </Button>
      <Button
        class="touch-target"
        :variant="mode === 'draw' ? 'solid' : 'outline'"
        :aria-pressed="mode === 'draw'"
        :label="__('Draw')"
        @click="mode = 'draw'"
      >
        <template #prefix><LucidePencil class="size-4" /></template>
      </Button>
    </div>
    <p v-if="!readonly" class="text-sm text-ink-gray-5">
      {{
        mode === 'draw'
          ? __('Draw on the body with your finger, or with the mouse')
          : __('Tap the body where it hurts: each tap is a numbered point')
      }}
    </p>

    <div
      class="corpo-carta grid gap-3 rounded-lg border px-3 pb-2 pt-3"
      :class="[
        missing ? 'border-outline-red-2' : 'border-outline-gray-2',
        views.length === 1 ? 'max-w-[15rem]' : 'max-w-md max-md:max-w-none',
      ]"
      :style="{
        background: PAPER,
        gridTemplateColumns: `repeat(${views.length}, minmax(0, 1fr))`,
      }"
    >
      <figure
        v-for="view in views"
        :key="view"
        class="flex min-w-0 flex-col items-center gap-1"
      >
        <svg
          viewBox="0 0 200 460"
          class="corpo-sagoma w-full"
          :class="{
            'cursor-crosshair': !readonly,
            'corpo-disegna': mode === 'draw' && !readonly,
          }"
          :data-disegno="readonly ? undefined : ''"
          role="img"
          :aria-label="viewLabel(view)"
          @click="(event) => tap(view, event)"
          @pointerdown="(event) => startStroke(view, event)"
          @pointermove="moveStroke"
          @pointerup="endStroke"
          @pointercancel="endStroke"
        >
          <path
            :d="BODY_OUTLINES.body"
            :fill="INSIDE"
            :stroke="OUTLINE"
            stroke-width="1.4"
          />
          <path
            :d="BODY_OUTLINES.head"
            :fill="INSIDE"
            :stroke="OUTLINE"
            stroke-width="1.4"
          />
          <path
            v-for="(line, i) in BODY_OUTLINES[view]"
            :key="i"
            :d="line"
            fill="none"
            :stroke="DETAIL"
            stroke-width="1"
          />
          <!-- whose right is on which side: from the front, on the reader's left -->
          <text x="8" y="40" font-size="13" :fill="DETAIL" aria-hidden="true">
            {{ view === 'front' ? sideRight : sideLeft }}
          </text>
          <text
            x="192"
            y="40"
            font-size="13"
            text-anchor="end"
            :fill="DETAIL"
            aria-hidden="true"
          >
            {{ view === 'front' ? sideLeft : sideRight }}
          </text>
          <path
            v-for="(stroke, i) in strokesOf(view)"
            :key="`s${i}`"
            :d="smoothPath(stroke.points)"
            fill="none"
            :stroke="MARK"
            stroke-opacity="0.75"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <g
            v-for="mark in marksOf(view)"
            :key="`m${mark.number}`"
            class="corpo-segno"
            :class="{ 'pointer-events-none': mode === 'draw' }"
            @click.stop="select(mark.number)"
          >
            <!-- a finger's room around a small point -->
            <circle
              :cx="mark.x * 200"
              :cy="mark.y * 460"
              r="16"
              fill="transparent"
            />
            <circle
              :cx="mark.x * 200"
              :cy="mark.y * 460"
              r="9"
              :fill="MARK"
              :stroke="selected === mark.number ? INK : PAPER"
              :stroke-width="selected === mark.number ? 2.5 : 1.5"
            />
            <text
              :x="mark.x * 200"
              :y="mark.y * 460 + 3.8"
              font-size="11"
              font-weight="700"
              text-anchor="middle"
              :fill="PAPER"
            >
              {{ mark.number }}
            </text>
          </g>
        </svg>
        <figcaption class="text-sm" :style="{ color: OUTLINE }">
          {{ viewLabel(view) }}
        </figcaption>
      </figure>
    </div>

    <div
      v-if="!readonly && (marks.length || strokes.length)"
      class="flex flex-wrap gap-2"
    >
      <Button
        v-if="strokes.length"
        class="touch-target"
        :label="__('Undo the last stroke')"
        @click="undoStroke"
      >
        <template #prefix><LucideUndo2 class="size-4" /></template>
      </Button>
      <Button
        class="touch-target"
        variant="ghost"
        :label="__('Clear all')"
        @click="clearAll"
      />
    </div>
    <p v-if="!readonly && full" class="text-sm text-ink-amber-7">
      {{ __('That is as many as a body chart holds') }}
    </p>

    <!-- the point chosen: its words and how much -->
    <div
      v-if="!readonly && current"
      class="flex max-w-md flex-col gap-3 rounded-lg border border-outline-gray-2 p-3 max-md:max-w-none"
    >
      <div class="flex items-center justify-between gap-2">
        <span class="min-w-0 text-base font-medium text-ink-gray-8">
          {{ __('Point {0}', [current.number]) }} ·
          {{ viewLabel(current.view) }}
        </span>
        <Button
          class="touch-target shrink-0"
          variant="ghost"
          theme="red"
          :label="__('Remove the point')"
          @click="removeMark(current.number)"
        />
      </div>
      <label class="flex flex-col gap-1">
        <span class="text-sm text-ink-gray-5">{{
          __('What it feels like, where')
        }}</span>
        <input
          class="form-input w-full"
          enterkeyhint="done"
          maxlength="120"
          :value="current.label || ''"
          :placeholder="__('Burning, down the leg')"
          @input="(e) => setMark(current.number, { label: e.target.value })"
        />
      </label>
      <div class="flex flex-col gap-1.5">
        <span :id="intensityId" class="text-sm text-ink-gray-5">
          {{ __('How much, from 0 (nothing) to 10 (the worst)') }}
        </span>
        <div
          class="flex flex-wrap gap-1.5"
          role="group"
          :aria-labelledby="intensityId"
        >
          <Button
            v-for="n in 11"
            :key="n"
            class="touch-target min-w-9"
            :variant="current.intensity === n - 1 ? 'solid' : 'outline'"
            :aria-pressed="current.intensity === n - 1"
            :label="String(n - 1)"
            @click="
              setMark(current.number, {
                intensity: current.intensity === n - 1 ? null : n - 1,
              })
            "
          />
        </div>
      </div>
    </div>

    <!-- every point in words: on the screen as on the PDF -->
    <ul
      v-if="marks.length || (readonly && strokes.length)"
      class="flex max-w-md flex-col gap-1 max-md:max-w-none"
    >
      <li v-for="(line, i) in inWords" :key="i">
        <button
          v-if="!readonly && i < marks.length"
          type="button"
          class="touch-target w-full rounded-md px-2 py-1.5 text-left text-base"
          :class="
            selected === i + 1
              ? 'bg-surface-gray-2 text-ink-gray-9'
              : 'text-ink-gray-7'
          "
          @click="select(i + 1)"
        >
          {{ line }}
        </button>
        <span v-else class="block px-2 py-0.5 text-base text-ink-gray-7">
          {{ line }}
        </span>
      </li>
    </ul>
    <p v-else-if="readonly" class="text-base text-ink-gray-5">
      {{ __('Nothing marked') }}
    </p>
  </div>
</template>

<script setup>
import {
  BODY_OUTLINES,
  bodyChartInWords,
  bodyViews,
  numberedMarks,
  roundHalfUp,
  smoothPath,
} from '@/utils/moduli'
import LucideMapPin from '~icons/lucide/map-pin'
import LucidePencil from '~icons/lucide/pencil'
import LucideUndo2 from '~icons/lucide/undo-2'
import { Button } from 'frappe-ui'
import { computed, getCurrentInstance, ref, watch } from 'vue'

// the same colours as the PDF's (crm/moduli/corpo.py)
const PAPER = '#ffffff'
const INK = '#1f2328'
const MARK = '#c2410c'
const OUTLINE = '#5f6368'
const INSIDE = '#f3f4f6'
const DETAIL = '#a3a7ad'
// as many as the server keeps (schema.MAX_SEGNI, MAX_TRATTI, MAX_PUNTI)
const MAX_MARKS = 40
const MAX_STROKES = 40
const MAX_POINTS = 500

const props = defineProps({
  field: { type: Object, required: true },
  readonly: { type: Boolean, default: false },
  missing: { type: Boolean, default: false },
})

const modelValue = defineModel({ type: [Object, null], default: null })

const views = computed(() => bodyViews(props.field))
const mode = ref('points')
const selected = ref(null)
const drawing = ref(null)
// the outline a stroke is being drawn on: its box places the points
let drawingOn = null
const intensityId = `intensita-${getCurrentInstance()?.uid}`

const marks = computed(() => numberedMarks(modelValue.value))
const strokes = computed(() => {
  const kept = Array.isArray(modelValue.value?.strokes)
    ? modelValue.value.strokes
    : []
  return drawing.value ? [...kept, drawing.value] : kept
})
const current = computed(
  () => marks.value.find((mark) => mark.number === selected.value) || null,
)
const full = computed(
  () =>
    (mode.value === 'points' && marks.value.length >= MAX_MARKS) ||
    (mode.value === 'draw' && strokes.value.length >= MAX_STROKES),
)
const inWords = computed(() =>
  bodyChartInWords(modelValue.value).split('\n').filter(Boolean),
)

const sideRight = __('R', null, 'Body chart side')
const sideLeft = __('L', null, 'Body chart side')
const viewLabel = (view) =>
  view === 'back'
    ? __('Back', null, 'Body chart')
    : __('Front', null, 'Body chart')

const marksOf = (view) => marks.value.filter((mark) => mark.view === view)
const strokesOf = (view) =>
  strokes.value.filter((stroke) => stroke?.view === view)

// drawing, no point is being written about
watch(mode, (now) => {
  if (now === 'draw') selected.value = null
})
// a point chosen that is gone (cleared, signed again) chooses nothing
watch(marks, (now) => {
  if (selected.value && selected.value > now.length) selected.value = null
})

function save(nextMarks, nextStrokes) {
  const value = {}
  if (nextMarks.length) value.marks = nextMarks
  if (nextStrokes.length) value.strokes = nextStrokes
  modelValue.value = Object.keys(value).length ? value : null
}

// the points as they are kept: their number is their place, not an answer
const keptMarks = () =>
  marks.value.map((mark) => {
    const kept = { ...mark }
    delete kept.number
    return kept
  })
const keptStrokes = () =>
  Array.isArray(modelValue.value?.strokes) ? [...modelValue.value.strokes] : []

/** Where on the outline, as fractions of it, to the thousandth. */
function where(outline, event) {
  const box = outline.getBoundingClientRect()
  const fraction = (value) => roundHalfUp(Math.min(1, Math.max(0, value)), 3)
  return [
    fraction((event.clientX - box.left) / box.width),
    fraction((event.clientY - box.top) / box.height),
  ]
}

function tap(view, event) {
  if (props.readonly || mode.value !== 'points') return
  if (marks.value.length >= MAX_MARKS) return
  const [x, y] = where(event.currentTarget, event)
  const next = [...keptMarks(), { view, x, y }]
  save(next, keptStrokes())
  // the new point is the one to write about: its number is its place
  selected.value = next.length
}

function select(number) {
  // a point chosen is a point to write about: back to marking
  mode.value = 'points'
  selected.value = selected.value === number ? null : number
}

function setMark(number, changes) {
  const next = keptMarks()
  const mark = next[number - 1]
  if (!mark) return
  for (const [key, value] of Object.entries(changes)) {
    if (value === null || value === '') delete mark[key]
    else mark[key] = value
  }
  save(next, keptStrokes())
}

function removeMark(number) {
  save(
    keptMarks().filter((_, i) => i !== number - 1),
    keptStrokes(),
  )
  selected.value = null
}

function startStroke(view, event) {
  if (props.readonly || mode.value !== 'draw') return
  if (keptStrokes().length >= MAX_STROKES) return
  event.preventDefault()
  event.currentTarget.setPointerCapture?.(event.pointerId)
  drawingOn = event.currentTarget
  drawing.value = { view, points: [where(drawingOn, event)] }
}

function moveStroke(event) {
  if (!drawing.value) return
  event.preventDefault()
  const points = drawing.value.points
  if (points.length >= MAX_POINTS) return
  const [x, y] = where(drawingOn, event)
  const [px, py] = points[points.length - 1]
  // a point every few pixels: a line as smooth, an answer a tenth as long
  if (Math.abs(x - px) + Math.abs(y - py) < 0.008) return
  drawing.value = { ...drawing.value, points: [...points, [x, y]] }
}

function endStroke() {
  if (!drawing.value) return
  const { view, points } = drawing.value
  drawing.value = null
  drawingOn = null
  save(keptMarks(), [...keptStrokes(), { view, points }])
}

function undoStroke() {
  save(keptMarks(), keptStrokes().slice(0, -1))
}

function clearAll() {
  selected.value = null
  save([], [])
}
</script>

<style scoped>
/* the outline keeps its shape: a tap's place is a fraction of it */
.corpo-sagoma {
  aspect-ratio: 200 / 460;
  height: auto;
  /* marking leaves the page to the finger: a tap is a click, a swipe scrolls */
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
}
/* drawing, the outline keeps the finger: the page stays where it is */
.corpo-disegna {
  touch-action: none;
}
.corpo-segno {
  cursor: pointer;
}
</style>
