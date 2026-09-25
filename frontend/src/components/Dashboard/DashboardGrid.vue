<template>
  <div class="p-3 sm:px-4">
    <!-- A 20-column grid on a 390px screen gives a four-column widget about
         78px: a chart nobody can read. On a phone the same widgets stack —
         numbers two per row, everything else full width — in the order the
         grid shows them, top to bottom and left to right. -->
    <div v-if="isMobileView" class="flex flex-wrap gap-3">
      <div
        v-for="item in mobileItems"
        :key="item.layout.i"
        class="min-w-0"
        :class="
          kindOf(item) === 'number' ? 'basis-[calc(50%_-_0.375rem)]' : 'w-full'
        "
        :style="{ height: mobileHeight(item) }"
      >
        <DashboardItem
          :item="item"
          :answer="answers[item.layout.i]"
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
      v-else-if="items.length"
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
            class="absolute right-3.5 top-3.5 z-10 flex items-center gap-0.5 rounded-lg border border-outline-gray-2 bg-surface-elevation-2 p-0.5 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 focus-within:opacity-100"
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
import { GRID_COLUMNS, ROW_HEIGHT, mobileOrder } from '@/utils/dashboard'
import { GridLayout, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

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

const byKey = computed(() =>
  Object.fromEntries(items.value.map((item) => [item.layout.i, item])),
)

function kindOf(item) {
  return props.answers[item.layout.i]?.kind || item.type
}

function mobileHeight(item) {
  const kind = kindOf(item)
  if (kind === 'number') return '128px'
  if (item.name === 'heading') return '40px'
  // A list or a table is as tall as what it has to say. Keeping the height the
  // desktop grid stored left three rows sitting above 300px of white, and put
  // a second scroll inside the page's own — the thing every phone list gets
  // wrong. A chart still needs a height given to it; these do not.
  if (kind === 'list' || kind === 'table') return 'auto'
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
