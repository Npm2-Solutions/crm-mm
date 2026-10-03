<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The phone's «+» (docs/progetto-ghl/34): what a list adds - a person, a task,
  a deal - where the thumb is, above the bar at the bottom, in the brand's
  colour like every primary action.
-->
<template>
  <Button
    variant="solid"
    icon="lucide-plus"
    class="!fixed !bottom-[calc(env(safe-area-inset-bottom)+5rem)] !right-4 z-20 !size-14 !rounded-2xl shadow-lg [&_svg]:!size-6 [&_span]:!size-6"
    :aria-label="label"
    @click="emit('click')"
  />
</template>

<script setup>
import { Button } from 'frappe-ui'

defineProps({ label: { type: String, required: true } })
const emit = defineEmits(['click'])
</script>
