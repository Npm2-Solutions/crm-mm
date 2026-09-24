<template>
  <div
    class="group/frame relative flex h-full w-full flex-col overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-elevation-1 shadow-sm"
    :class="
      clickable
        ? 'cursor-pointer transition-colors hover:border-outline-gray-3'
        : ''
    "
    @click="open"
  >
    <div class="flex min-h-9 items-start justify-between gap-2 px-4 pt-3">
      <div class="flex min-w-0 items-center gap-1.5">
        <span
          class="truncate text-sm font-medium text-ink-gray-7"
          :title="title"
        >
          {{ title }}
        </span>
        <Tooltip v-if="description" :text="description" :hoverDelay="0.4">
          <span
            class="lucide-info size-3.5 shrink-0 text-ink-gray-4"
            aria-hidden="true"
          />
        </Tooltip>
      </div>
      <WidgetBadge v-if="badge && !badgeInBody" :badge="badge" />
    </div>

    <div
      class="relative min-h-0 flex-1 transition-opacity duration-200"
      :class="refreshing ? 'opacity-50' : ''"
    >
      <div v-if="!answer" class="flex h-full flex-col gap-2 px-4 pb-4 pt-1">
        <div class="h-7 w-1/2 animate-pulse rounded bg-surface-gray-2" />
        <div class="h-3 w-1/3 animate-pulse rounded bg-surface-gray-2" />
      </div>

      <div
        v-else-if="answer.unavailable"
        class="flex h-full flex-col items-start justify-center gap-2 px-4 pb-3"
      >
        <div class="flex items-center gap-1.5 text-sm text-ink-gray-6">
          <span class="lucide-lock size-3.5 shrink-0" aria-hidden="true" />
          <span class="line-clamp-2">{{ answer.unavailable.message }}</span>
        </div>
        <Button
          v-if="!editing && answer.unavailable.feature"
          size="sm"
          :label="__('Set up {0}', [answer.unavailable.feature.label])"
          @click.stop="$emit('setup', answer.unavailable.feature)"
        />
      </div>

      <div
        v-else-if="answer.error"
        class="flex h-full items-center gap-1.5 px-4 pb-3 text-sm text-ink-red-8"
      >
        <span class="lucide-circle-alert size-4 shrink-0" aria-hidden="true" />
        {{ answer.error }}
      </div>

      <slot v-else :badge="badgeInBody ? badge : null" />
    </div>
  </div>
</template>

<script setup>
import WidgetBadge from '@/components/Dashboard/WidgetBadge.vue'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  answer: { type: Object, default: null },
  editing: { type: Boolean, default: false },
  refreshing: { type: Boolean, default: false },
  userFiltered: { type: Boolean, default: false },
  onlyMine: { type: Boolean, default: false },
  // widgets whose whole card is the link (a KPI); charts link from inside
  cardLink: { type: Boolean, default: false },
  // a KPI shows its badge under the value, where its title has no room to lose
  badgeInBody: { type: Boolean, default: false },
})

const emit = defineEmits(['navigate', 'setup'])

const title = computed(
  () =>
    props.item.config?.title || props.answer?.title || props.item.title || '',
)
const description = computed(() => props.answer?.description || '')

// what the numbers cover when that is not what the page's filters say
const badge = computed(() => {
  const answer = props.answer
  if (!answer || answer.error || answer.unavailable) return null
  if (answer.live) {
    return {
      live: true,
      label: __('Now'),
      hint: __('Shows the present, whatever the period'),
    }
  }
  if (answer.scope === 'site' && props.userFiltered) {
    return {
      label: __('Everyone'),
      hint: __('Counts the whole business, not one person'),
    }
  }
  if (answer.scope === 'me' && !props.onlyMine) {
    return { label: __('Mine'), hint: __('Counts only your own work') }
  }
  return null
})

const clickable = computed(
  () =>
    props.cardLink &&
    !props.editing &&
    !!(props.answer?.route || props.answer?.settings) &&
    !props.answer?.error &&
    !props.answer?.unavailable,
)

function open() {
  if (!clickable.value) return
  emit('navigate', props.answer)
}
</script>
