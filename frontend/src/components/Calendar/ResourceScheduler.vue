<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- column headers -->
    <div class="flex border-b border-outline-gray-2 bg-surface-white">
      <div class="w-14 shrink-0 border-r border-outline-gray-2" />
      <div class="flex flex-1 overflow-hidden">
        <div
          v-for="column in columns"
          :key="column.key"
          class="flex min-w-0 flex-1 items-center gap-2 border-r border-outline-gray-2 px-2.5 py-2 last:border-r-0"
        >
          <UserAvatar
            v-if="mode === 'staff'"
            :user="column.key"
            size="sm"
            class="shrink-0"
          />
          <span
            v-else
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: column.color || '#8B8B8B' }"
          />
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-sm-medium text-ink-gray-8">
              {{ column.label }}
            </div>
            <div class="truncate text-p-xs text-ink-gray-5">
              {{ column.caption }}
            </div>
          </div>
          <Badge
            v-if="column.count"
            :label="String(column.count)"
            theme="gray"
            size="sm"
            class="shrink-0"
          />
        </div>
        <div
          v-if="!columns.length"
          class="flex flex-1 items-center justify-center py-3 text-p-sm text-ink-gray-5"
        >
          {{
            mode === 'staff'
              ? __('No professionals to show — add them to a service first')
              : __('No rooms or equipment yet')
          }}
        </div>
      </div>
    </div>

    <!-- grid -->
    <div ref="scrollArea" class="flex flex-1 overflow-auto">
      <!-- time gutter -->
      <div
        class="relative w-14 shrink-0 border-r border-outline-gray-2 bg-surface-white"
        :style="{ height: gridHeight }"
      >
        <div
          v-for="mark in axis"
          :key="mark.minutes"
          class="absolute -translate-y-1/2 pr-2 text-right text-p-xs text-ink-gray-5"
          :style="{ top: offsetOf(mark.minutes), width: '100%' }"
        >
          {{ mark.label }}
        </div>
      </div>

      <!-- columns -->
      <div class="flex flex-1" :style="{ height: gridHeight }">
        <div
          v-for="column in columns"
          :key="column.key"
          class="relative min-w-0 flex-1 border-r border-outline-gray-2 last:border-r-0"
          @click="onCellClick($event, column)"
          @dragover.prevent
          @drop.prevent="onDrop($event, column)"
        >
          <!-- hour lines -->
          <div
            v-for="mark in axis"
            :key="mark.minutes"
            class="pointer-events-none absolute inset-x-0 border-t border-outline-gray-1"
            :style="{ top: offsetOf(mark.minutes) }"
          />
          <!-- closed hours -->
          <div
            v-for="(band, i) in column.closed"
            :key="`closed-${i}`"
            class="pointer-events-none absolute inset-x-0 bg-surface-gray-2 opacity-50"
            :style="{
              top: offsetOf(band.from),
              height: spanOf(band.from, band.to),
            }"
          />
          <!-- now -->
          <div
            v-if="nowMinutes !== null"
            class="pointer-events-none absolute inset-x-0 z-10 border-t border-red-500"
            :style="{ top: offsetOf(nowMinutes) }"
          >
            <span
              class="absolute -left-0.5 -top-1 size-2 rounded-full bg-red-500"
            />
          </div>

          <!-- appointments -->
          <button
            v-for="block in column.blocks"
            :key="`${column.key}-${block.name}`"
            type="button"
            draggable="true"
            class="absolute overflow-hidden rounded-md border-l-[3px] px-1.5 py-1 text-left transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            :class="[
              block.status === 'Cancelled' ? 'opacity-50 line-through' : '',
              selected === block.name ? 'ring-2 ring-outline-gray-4' : '',
            ]"
            :style="blockBoxStyle(block)"
            @click.stop="$emit('select', block.name)"
            @dblclick.stop="$emit('edit', block.name)"
            @dragstart="onDragStart($event, block, column)"
          >
            <div class="flex items-center gap-1">
              <span class="truncate text-p-xs-medium text-ink-gray-8">
                {{ formatMinutes(block.startMinutes) }}
              </span>
              <span
                v-if="block.conflict_note"
                class="lucide-triangle-alert size-3 shrink-0 text-ink-amber-3"
                :title="block.conflict_note"
              />
            </div>
            <div class="truncate text-p-xs text-ink-gray-7">
              {{ block.title }}
            </div>
            <div
              v-if="block.showDetail"
              class="mt-0.5 flex flex-wrap items-center gap-1 text-p-xs text-ink-gray-5"
            >
              <span v-if="block.participants?.length > 1">
                {{ block.participants.length }} {{ __('people') }}
              </span>
              <span
                v-for="row in block.resources || []"
                :key="row.resource"
                class="truncate"
              >
                · {{ row.resource }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
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
  visibleWindow,
} from '@/utils/scheduler'
import { Badge } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  /** `staff` = one column per professional, `resource` = one per room/equipment */
  mode: { type: String, default: 'staff' },
  date: { type: String, required: true },
  appointments: { type: Array, default: () => [] },
  /** `[{ key, label, caption, color, closed: [{ from, to }] }]` */
  columnDefs: { type: Array, default: () => [] },
  serviceColors: { type: Object, default: () => ({}) },
  selected: { type: String, default: '' },
  pxPerMinute: { type: Number, default: 1.1 },
})

const emit = defineEmits(['select', 'edit', 'create', 'move'])

const scrollArea = ref(null)

/** Appointments of the shown day, projected onto the minute axis. */
const dayItems = computed(() =>
  props.appointments
    .filter((a) => String(a.starts_on).slice(0, 10) === props.date)
    .map((a) => ({
      ...a,
      startMinutes: minutesFromMidnight(a.starts_on),
      endMinutes: Math.max(
        minutesFromMidnight(a.ends_on),
        minutesFromMidnight(a.starts_on) + 10,
      ),
    })),
)

const viewWindow = computed(() => visibleWindow(dayItems.value))
const axis = computed(() =>
  buildTimeAxis(
    Math.floor(viewWindow.value.startMinutes / 60),
    Math.floor(viewWindow.value.endMinutes / 60),
  ),
)
const gridHeight = computed(
  () =>
    `${(viewWindow.value.endMinutes - viewWindow.value.startMinutes) * props.pxPerMinute}px`,
)

const nowMinutes = computed(() => {
  const today = new Date()
  const iso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
    today.getDate(),
  ).padStart(2, '0')}`
  if (iso !== props.date) return null
  return minutesFromMidnight(today)
})

const columns = computed(() => {
  const keys = props.columnDefs.map((c) => c.key)
  const buckets = columnsFor(dayItems.value, props.mode, keys)
  return props.columnDefs.map((def) => {
    const blocks = layoutLanes(buckets.get(def.key) || [])
    return {
      ...def,
      count: blocks.filter((b) => b.status !== 'Cancelled').length,
      blocks: blocks.map((block) => ({
        ...block,
        showDetail: block.endMinutes - block.startMinutes >= 45,
      })),
    }
  })
})

function offsetOf(minutes) {
  return `${(minutes - viewWindow.value.startMinutes) * props.pxPerMinute}px`
}

function spanOf(from, to) {
  return `${Math.max(to - from, 0) * props.pxPerMinute}px`
}

function blockBoxStyle(block) {
  const color = appointmentColor(block, props.serviceColors)
  return {
    ...blockStyle(block, viewWindow.value),
    borderLeftColor: color,
    backgroundColor: `${color}1f`,
  }
}

/** Where in the day did the pointer land inside this column? */
function minutesAt(event) {
  const box = event.currentTarget.getBoundingClientRect()
  const ratio = (event.clientY - box.top) / Math.max(box.height, 1)
  return minutesAtRatio(Math.min(Math.max(ratio, 0), 1), viewWindow.value, 15)
}

function onCellClick(event, column) {
  emit('create', {
    date: props.date,
    minutes: minutesAt(event),
    mode: props.mode,
    key: column.key,
  })
}

function onDragStart(event, block, column) {
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData(
    'text/plain',
    JSON.stringify({
      name: block.name,
      from: column.key,
      grab: minutesFromMidnight(block.starts_on),
      length: block.endMinutes - block.startMinutes,
    }),
  )
}

function onDrop(event, column) {
  let payload
  try {
    payload = JSON.parse(event.dataTransfer.getData('text/plain'))
  } catch {
    return
  }
  if (!payload?.name) return
  const start = minutesAt(event)
  emit('move', {
    name: payload.name,
    startsOn: dateAtMinutes(props.date, start),
    endsOn: dateAtMinutes(props.date, start + (payload.length || 30)),
    mode: props.mode,
    from: payload.from,
    to: column.key,
  })
}

defineExpose({ scrollArea })
</script>
