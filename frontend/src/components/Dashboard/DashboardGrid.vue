<template>
  <div class="flex-1 overflow-y-auto p-3">
    <!-- A 20-column grid on a 390px screen gives a five-column widget about
         97px: a chart nobody can read. On a phone the same widgets stack —
         number charts two per row, everything else full width — and the saved
         x/y/w layout is ignored, keeping only the height as a hint. -->
    <div v-if="isMobileView" class="flex flex-wrap gap-3">
      <div
        v-for="(item, index) in mobileItems"
        :key="index"
        class="min-w-0"
        :class="
          item.type === 'number_chart'
            ? 'basis-[calc(50%_-_0.375rem)]'
            : 'w-full'
        "
        :style="{ height: mobileHeight(item) }"
      >
        <DashboardItem :index="index" :item="item" />
      </div>
    </div>
    <GridLayout
      v-else-if="items.length > 0"
      class="h-fit w-full"
      :class="[editing ? 'mb-[20rem] !select-none' : '']"
      :cols="20"
      :rowHeight="42"
      :disabled="!editing"
      :modelValue="items.map((item) => item.layout)"
      @update:modelValue="
        (newLayout) => {
          items.forEach((item, idx) => {
            item.layout = newLayout[idx]
          })
        }
      "
    >
      <template #item="{ index }">
        <div class="group relative flex h-full w-full p-2 text-ink-gray-8">
          <div
            class="flex h-full w-full items-center justify-center"
            :class="
              editing
                ? 'pointer-events-none  [&>div:first-child]:rounded [&>div:first-child]:group-hover:ring-2 [&>div:first-child]:group-hover:ring-outline-gray-2'
                : ''
            "
          >
            <DashboardItem
              :index="index"
              :item="items[index]"
              :editing="editing"
            />
          </div>
          <div
            v-if="editing"
            class="flex absolute right-0 top-0 bg-surface-gray-9 rounded cursor-pointer opacity-0 group-hover:opacity-100"
          >
            <div
              class="rounded p-1 hover:bg-surface-gray-8"
              @click="items.splice(index, 1)"
            >
              <span
                class="lucide-trash-2 size-3 text-ink-base"
                aria-hidden="true"
              />
            </div>
          </div>
        </div>
      </template>
    </GridLayout>
  </div>
</template>
<script setup>
import DashboardItem from '@/components/Dashboard/DashboardItem.vue'
import { isMobileView } from '@/composables/breakpoints'
import { GridLayout } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  editing: { type: Boolean, default: false },
})

const items = defineModel({ type: Array, default: () => [] })

// Spacers only exist to push things around the grid; stacked, they are blank gaps.
const mobileItems = computed(() =>
  items.value.filter((item) => item.type !== 'spacer'),
)

function mobileHeight(item) {
  if (item.type === 'number_chart') return '104px'
  // The stored height is in 42px grid rows; a chart below ~260px stops being
  // readable once it is the full width of a phone.
  return `${Math.max((item.layout?.h || 6) * 42, 260)}px`
}
</script>
