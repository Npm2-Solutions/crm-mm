<!--
  Answer it, react to it: the two things done to a message you are reading.

  Beside the bubble, on its outer side, when the pointer is on it. They used to
  be a chevron inside the bubble's top corner on a white radial gradient — a
  white blot on a green bubble, a lit patch on a dark one — opening a menu with
  one item in it, plus a smiley floating in the margin. Two round buttons say
  the same with nothing to open.
-->
<template>
  <div class="flex items-center gap-1">
    <Tooltip :text="__('Reply')">
      <button
        class="grid size-7 place-items-center rounded-full bg-surface-elevation-2 text-ink-gray-6 shadow-sm ring-1 ring-outline-gray-1 transition-colors hover:text-ink-gray-9"
        :aria-label="__('Reply')"
        @click="emit('reply')"
      >
        <span class="lucide-reply size-3.5" aria-hidden="true" />
      </button>
    </Tooltip>
    <IconPicker
      v-slot="{ togglePopover }"
      v-model="emoji"
      v-model:reaction="quick"
      @update:modelValue="(value) => emit('react', value)"
    >
      <Tooltip :text="__('React')">
        <button
          class="grid size-7 place-items-center rounded-full bg-surface-elevation-2 text-ink-gray-6 shadow-sm ring-1 ring-outline-gray-1 transition-colors hover:text-ink-gray-9"
          :aria-label="__('React')"
          @click="open(togglePopover)"
        >
          <span class="lucide-smile-plus size-3.5" aria-hidden="true" />
        </button>
      </Tooltip>
    </IconPicker>
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import { Tooltip } from 'frappe-ui'
import { ref } from 'vue'

const emit = defineEmits(['reply', 'react'])

const emoji = ref('')
// the six quick ones first; the whole picker is one click further
const quick = ref(true)

function open(togglePopover) {
  quick.value = true
  togglePopover()
}
</script>
