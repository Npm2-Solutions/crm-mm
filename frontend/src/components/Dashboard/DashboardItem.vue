<template>
  <div
    v-if="item.name === 'heading'"
    class="flex h-full w-full items-end gap-3 px-1 pb-1"
  >
    <h3
      class="shrink-0 text-base font-semibold"
      :class="item.config?.title ? 'text-ink-gray-8' : 'text-ink-gray-4'"
    >
      {{ item.config?.title || __('Section title') }}
    </h3>
    <div class="mb-2.5 flex-1 border-t border-outline-gray-1" />
  </div>

  <div
    v-else-if="item.name === 'spacer'"
    class="h-full w-full rounded-xl"
    :class="
      editing
        ? 'flex items-center justify-center border border-dashed border-outline-gray-2 text-xs text-ink-gray-4'
        : ''
    "
  >
    {{ editing ? __('Empty space') : '' }}
  </div>

  <WidgetFrame
    v-else
    :item="item"
    :answer="frameAnswer"
    :editing="editing"
    :refreshing="refreshing"
    :userFiltered="userFiltered"
    :onlyMine="onlyMine"
    :cardLink="kind === 'number'"
    :badgeInBody="kind === 'number'"
    @navigate="(target) => $emit('navigate', target)"
    @setup="(feature) => $emit('setup', feature)"
  >
    <template #default="{ badge }">
      <NumberWidget
        v-if="kind === 'number'"
        :answer="answer"
        :badge="badge"
        :locale="locale"
      />
      <ChartWidget
        v-else-if="kind === 'axis' || kind === 'donut'"
        :answer="answer"
        :locale="locale"
      />
      <FunnelWidget
        v-else-if="kind === 'funnel'"
        :answer="answer"
        :locale="locale"
      />
      <ListWidget
        v-else-if="kind === 'list'"
        :answer="answer"
        :locale="locale"
        @navigate="(target) => $emit('navigate', target)"
      />
      <TableWidget
        v-else-if="kind === 'table'"
        :answer="answer"
        :locale="locale"
      />
      <HeatmapWidget
        v-else-if="kind === 'heatmap'"
        :answer="answer"
        :locale="locale"
      />
    </template>
  </WidgetFrame>
</template>

<script setup>
import WidgetFrame from '@/components/Dashboard/WidgetFrame.vue'
import NumberWidget from '@/components/Dashboard/widgets/NumberWidget.vue'
import ChartWidget from '@/components/Dashboard/widgets/ChartWidget.vue'
import FunnelWidget from '@/components/Dashboard/widgets/FunnelWidget.vue'
import ListWidget from '@/components/Dashboard/widgets/ListWidget.vue'
import TableWidget from '@/components/Dashboard/widgets/TableWidget.vue'
import HeatmapWidget from '@/components/Dashboard/widgets/HeatmapWidget.vue'
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  answer: { type: Object, default: null },
  editing: { type: Boolean, default: false },
  refreshing: { type: Boolean, default: false },
  userFiltered: { type: Boolean, default: false },
  onlyMine: { type: Boolean, default: false },
  locale: { type: String, default: undefined },
})

defineEmits(['navigate', 'setup'])

const kind = computed(() => props.answer?.kind || props.item.type)

// a widget the layout says is unavailable is shown so before any answer arrives
const frameAnswer = computed(() => {
  if (props.item.unavailable && !props.answer) {
    return { unavailable: props.item.unavailable, title: props.item.title }
  }
  return props.answer
})
</script>
