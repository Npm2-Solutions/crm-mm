<!-- In the centre's preview, what the person sees here and whoever previews does
     not read in DottorCloud: its place, and when, with nothing of it. -->
<template>
  <div
    class="flex flex-col gap-1 rounded-lg border border-dashed border-outline-gray-3 p-4 text-p-sm text-ink-gray-5"
  >
    <span
      v-if="when"
      class="font-medium text-ink-gray-7 first-letter:uppercase"
    >
      {{ when }}
    </span>
    {{ __('Here {0} sees something you do not read in {brand}.', [chi]) }}
  </div>
</template>

<script setup>
import { chi } from '../anteprima'

defineProps({ when: { type: String, default: '' } })
</script>
