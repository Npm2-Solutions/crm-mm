<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  «In progress» - on a call, a cycle under way: the brand's soft green with the
  cross in place of the dot (the design system's Badge). One a row.
-->
<template>
  <span class="dc-in-corso">
    <span class="dc-cross" aria-hidden="true" />
    {{ label }}
  </span>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
})
</script>
