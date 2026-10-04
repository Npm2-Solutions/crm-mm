<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What it holds is mounted once the page around it is drawn, when the phone
  is idle: a part below the first screen does not hold up the tap that opened
  the page, and is there before anybody scrolls to it.
-->
<template>
  <slot v-if="pronto" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const pronto = ref(false)
let annulla = null

onMounted(() => {
  const via = () => (pronto.value = true)
  if (typeof requestIdleCallback === 'function') {
    const id = requestIdleCallback(via, { timeout: 400 })
    annulla = () => cancelIdleCallback(id)
  } else {
    const id = setTimeout(via, 100)
    annulla = () => clearTimeout(id)
  }
})

onBeforeUnmount(() => annulla?.())
</script>
