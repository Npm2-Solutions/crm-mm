<template>
  <div class="relative flex h-full w-full justify-center">
    <div
      class="absolute left-1/2 flex -translate-x-1/2 flex-col items-center gap-3"
      :class="widthClass"
      :style="{ top: top }"
    >
      <!-- the design system's picture, the same for every empty list: the
           title says what is missing -->
      <EmptyArt />
      <div class="flex flex-col items-center gap-1">
        <span class="text-center text-lg-semibold text-ink-gray-9">
          {{ computedTitle }}
        </span>
        <span class="text-center text-p-sm text-ink-gray-5">
          {{ computedDescription }}
        </span>
      </div>
    </div>
  </div>
</template>
<script setup>
import EmptyArt from '@/components/Espresso/EmptyArt.vue'
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  // kept for the pages that pass one: the picture is the design system's
  icon: {
    type: [String, Object],
    default: 'file-text',
  },
  top: { type: String, default: '35%' },
  width: { type: String, default: 'md' },
})

const computedTitle = computed(() => {
  // a title handed as it is written in the code goes through the translator too
  return props.title ? __(props.title) : __('No {0} Found', [__(props.name)])
})

const computedDescription = computed(() => {
  return props.description
    ? __(props.description)
    : __(
        'It appears that there are currently no {0} available. You can create more {0} by using the Create button.',
        [__(props.name)],
      )
})

// a third of a phone is 130px: the sentence ran to four lines
const widthClass = computed(() => {
  switch (props.width) {
    case 'sm':
      return 'w-8/12 sm:w-2/12'
    case 'lg':
      return 'w-10/12 sm:w-8/12'
    default:
      return 'w-10/12 max-w-sm sm:w-4/12'
  }
})
</script>
