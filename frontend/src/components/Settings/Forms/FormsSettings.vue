<!--
  One builder of forms (docs/gestionale-medico, design, "Il builder"): what the
  person fills and signs, the sheet the operator writes, the form on the website
  that finds the person or makes them. Each shows to whoever may build it: the
  centre its forms and sheets, marketing the website's.
-->
<template>
  <div class="flex h-full flex-col">
    <TemplatesList v-if="screen === 'list'" ref="listRef" @open="open" />
    <TemplateBuilder
      v-else
      :key="activeName"
      :name="activeName"
      @back="backToList"
    />
  </div>
</template>

<script setup>
import TemplatesList from './TemplatesList.vue'
import TemplateBuilder from './TemplateBuilder.vue'
import { nextTick, ref } from 'vue'

const screen = ref('list')
const activeName = ref(null)
const listRef = ref(null)

function open(name) {
  activeName.value = name
  screen.value = 'builder'
}

async function backToList() {
  screen.value = 'list'
  await nextTick()
  listRef.value?.reload?.()
}
</script>
