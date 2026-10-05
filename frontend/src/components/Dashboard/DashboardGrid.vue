<template>
  <div ref="radice" class="p-3 sm:px-4">
    <!-- A 20-column grid on a 390px screen gives a four-column widget about
         78px: a chart nobody can read. On a phone, and wherever the grid is
         narrower than GRIGLIA_MINIMA (a tablet held upright, beside the menu),
         the same widgets stack in the order the grid shows them, top to bottom
         and left to right: the numbers two to a row on a phone, three or four
         on a tablet, everything else the whole width or two to a row
         (`perRiga`). While the board is arranged the grid stays: it is what
         is being arranged. Nothing is drawn before the width is known, or a
         tablet would build the grid only to put it away. -->
    <!-- `data-impilata`: a widget stacked reads as on a phone, its title on
         two lines and its comparison under the change (WidgetFrame,
         NumberWidget), on a tablet too -->
    <div v-if="impilata" class="flex flex-wrap gap-3" data-impilata>
      <div
        v-for="item in mobileItems"
        :key="item.layout.i"
        class="min-w-0"
        :style="stileImpilato(item)"
      >
        <DashboardItem
          :item="item"
          :answer="answers[item.layout.i]"
          :blocco="blocchi.has(item.layout.i)"
          :refreshing="refreshing"
          :userFiltered="userFiltered"
          :onlyMine="onlyMine"
          :locale="locale"
          @navigate="(target) => $emit('navigate', target)"
          @setup="(feature) => $emit('setup', feature)"
        />
      </div>
    </div>

    <!-- :responsive="false" overrides frappe-ui's default: below 768px of
         grid (a laptop with the widget library open) the responsive grid
         drops to one column and hands that layout back as the new positions,
         which saving would then keep. -->
    <GridLayout
      v-else-if="items.length && (larghezza || editing)"
      class="h-fit w-full"
      :class="editing ? 'mb-[20rem] select-none' : ''"
      :cols="GRID_COLUMNS"
      :rowHeight="ROW_HEIGHT"
      :disabled="!editing"
      :responsive="false"
      :modelValue="items.map((item) => item.layout)"
      @update:modelValue="updatePositions"
    >
      <!-- by key, not by index: the grid's order is its own business -->
      <template #item="{ i }">
        <div
          v-if="byKey[i]"
          class="group relative h-full w-full p-2"
          :data-widget="i"
        >
          <div
            class="h-full w-full rounded-xl transition-shadow"
            :class="[
              editing
                ? 'pointer-events-none cursor-move ring-offset-2 group-hover:ring-2 group-hover:ring-outline-gray-3'
                : '',
              highlighted === i ? 'ring-2 ring-[#2a78d6] ring-offset-2' : '',
            ]"
          >
            <DashboardItem
              :item="byKey[i]"
              :answer="answers[i]"
              :blocco="blocchi.has(i)"
              :editing="editing"
              :refreshing="refreshing"
              :userFiltered="userFiltered"
              :onlyMine="onlyMine"
              :locale="locale"
              @navigate="(target) => $emit('navigate', target)"
              @setup="(feature) => $emit('setup', feature)"
            />
          </div>
          <div
            v-if="editing"
            class="absolute right-3.5 top-3.5 z-10 flex items-center gap-0.5 rounded-lg border border-outline-gray-2 bg-surface-elevation-2 p-0.5 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 focus-within:opacity-100 [@media(hover:none)]:opacity-100"
          >
            <Tooltip v-if="configurable(byKey[i])" :text="__('Settings')">
              <button
                class="grid size-6 place-items-center rounded-md text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
                :aria-label="__('Settings')"
                @click="$emit('configure', byKey[i])"
              >
                <span class="lucide-settings-2 size-3.5" aria-hidden="true" />
              </button>
            </Tooltip>
            <Tooltip :text="__('Duplicate')">
              <button
                class="grid size-6 place-items-center rounded-md text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
                :aria-label="__('Duplicate')"
                @click="$emit('duplicate', byKey[i])"
              >
                <span class="lucide-copy size-3.5" aria-hidden="true" />
              </button>
            </Tooltip>
            <Tooltip :text="__('Remove')">
              <button
                class="grid size-6 place-items-center rounded-md text-ink-gray-6 hover:bg-surface-red-2 hover:text-ink-red-8"
                :aria-label="__('Remove')"
                @click="$emit('remove', byKey[i])"
              >
                <span class="lucide-trash-2 size-3.5" aria-hidden="true" />
              </button>
            </Tooltip>
          </div>
        </div>
      </template>
    </GridLayout>
  </div>
</template>

<script setup>
import DashboardItem from '@/components/Dashboard/DashboardItem.vue'
import { isMobileView } from '@/composables/breakpoints'
import {
  GRID_COLUMNS,
  GRIGLIA_MINIMA,
  ROW_HEIGHT,
  highlightedNumbers,
  larghezzaDiUno,
  mobileOrder,
  perRiga,
} from '@/utils/dashboard'
import { useElementSize } from '@vueuse/core'
import { GridLayout, Tooltip } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  answers: { type: Object, default: () => ({}) },
  editing: { type: Boolean, default: false },
  refreshing: { type: Boolean, default: false },
  userFiltered: { type: Boolean, default: false },
  onlyMine: { type: Boolean, default: false },
  locale: { type: String, default: undefined },
  highlighted: { type: String, default: '' },
  // which widgets have settings beyond their title
  configurable: { type: Function, default: () => true },
})

defineEmits(['navigate', 'setup', 'configure', 'duplicate', 'remove'])

const items = defineModel({ type: Array, default: () => [] })

const mobileItems = computed(() => mobileOrder(items.value))

// the grid's own width, its padding included: the same at mount (offsetWidth)
// as when it is observed, so a width near the line does not flip it once
const radice = ref(null)
const { width: larghezza } = useElementSize(radice, undefined, {
  box: 'border-box',
})
const impilata = computed(
  () =>
    isMobileView.value ||
    (!props.editing && larghezza.value > 0 && larghezza.value < GRIGLIA_MINIMA),
)

// a number keeps its share of the row; the others share what a row leaves,
// so the last one alone in its row takes all of it
function stileImpilato(item) {
  const { numeri, altri } = perRiga(larghezza.value)
  if (kindOf(item) === 'number')
    return {
      flex: `0 0 ${larghezzaDiUno(numeri)}`,
      minHeight: mobileHeight(item),
    }
  const n = item.name === 'heading' ? 1 : altri
  return { flex: `1 1 ${larghezzaDiUno(n)}`, height: mobileHeight(item) }
}

const byKey = computed(() =>
  Object.fromEntries(items.value.map((item) => [item.layout.i, item])),
)

function kindOf(item) {
  return props.answers[item.layout.i]?.kind || item.type
}

// the first number of each row is the design system's deep block
const blocchi = computed(() => highlightedNumbers(items.value, kindOf))

// A number sets its own height, from 128px up, so a two-line title and a
// comparison on a line of its own fit whole; the ones in a row grow together.
// Everything else keeps the height it is given.
function mobileHeight(item) {
  const kind = kindOf(item)
  if (kind === 'number') return '128px'
  if (item.name === 'heading') return '40px'
  // the stored height is in grid rows; below ~280px a chart stops being
  // readable once it is the full width of a phone
  return `${Math.max((item.layout?.h || 6) * ROW_HEIGHT, 280)}px`
}

function updatePositions(positions) {
  // matched by key, not by index: compaction may hand them back in another order
  const byKey = Object.fromEntries(
    positions.map((position) => [position.i, position]),
  )
  for (const item of items.value) {
    const position = byKey[item.layout.i]
    if (position) {
      const { x, y, w, h, i } = position
      item.layout = { x, y, w, h, i }
    }
  }
}
</script>
