<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Answer it, react to it: the two things done to a message you are reading.
  Where the clinic is on, a file the person sent can also go to their clinical
  archive (`archivable`).

  Beside the bubble, on its outer side, when the pointer is on it. They used to
  be a chevron inside the bubble's top corner on a white radial gradient — a
  white blot on a green bubble, a lit patch on a dark one — opening a menu with
  one item in it, plus a smiley floating in the margin. Two round buttons say
  the same with nothing to open.

  Where nothing hovers they are one bar above the message, shown by a tap on
  it, each button the size of a fingertip: 28px round buttons 4px apart were
  too small to hit one and not the next.
-->
<template>
  <div
    class="flex items-center gap-1 [@media(hover:none)]:gap-0.5 [@media(hover:none)]:rounded-full [@media(hover:none)]:bg-surface-elevation-2 [@media(hover:none)]:p-0.5 [@media(hover:none)]:shadow-md [@media(hover:none)]:ring-1 [@media(hover:none)]:ring-outline-gray-1"
  >
    <Tooltip :text="__('Reply', null, 'Answer a message')">
      <button
        :class="PULSANTE"
        :aria-label="__('Reply', null, 'Answer a message')"
        @click="emit('reply')"
      >
        <span class="lucide-reply" :class="ICONA" aria-hidden="true" />
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
          :class="PULSANTE"
          :aria-label="__('React')"
          @click="open(togglePopover)"
        >
          <span class="lucide-smile-plus" :class="ICONA" aria-hidden="true" />
        </button>
      </Tooltip>
    </IconPicker>
    <Tooltip v-if="archivable" :text="__('Add to the clinical archive')">
      <button
        :class="PULSANTE"
        :aria-label="__('Add to the clinical archive')"
        @click="emit('archive')"
      >
        <span class="lucide-folder-input" :class="ICONA" aria-hidden="true" />
      </button>
    </Tooltip>
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import { Tooltip } from 'frappe-ui'
import { ref } from 'vue'

defineProps({ archivable: { type: Boolean, default: false } })
const emit = defineEmits(['reply', 'react', 'archive'])

// round, each its own, beside the bubble; 40px in the bar where nothing hovers
const PULSANTE =
  'grid size-7 place-items-center rounded-full bg-surface-elevation-2 text-ink-gray-6 shadow-sm ring-1 ring-outline-gray-1 transition-colors hover:text-ink-gray-9 [@media(hover:none)]:size-10 [@media(hover:none)]:shadow-none [@media(hover:none)]:ring-0 [@media(hover:none)]:active:bg-surface-gray-3'
const ICONA = 'size-3.5 [@media(hover:none)]:size-[18px]'

const emoji = ref('')
// the six quick ones first; the whole picker is one click further
const quick = ref(true)

function open(togglePopover) {
  quick.value = true
  togglePopover()
}
</script>
