<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  frappe-ui's IconPicker, once every icon is in the page: it lists them from
  the sprite when it mounts (utils/icone.js puts only the icons drawn there).
  Until then, a field of the same size.
-->
<template>
  <IconPicker v-if="pronte" v-bind="$attrs" />
  <div
    v-else
    data-campo
    class="h-7 w-full rounded bg-surface-gray-2"
    :class="$attrs.class"
    aria-busy="true"
  />
</template>

<script setup>
import { IconPicker } from 'frappe-ui/icons'
import { mettiTutteLeIcone } from '@/utils/icone'
import { ref } from 'vue'

defineOptions({ inheritAttrs: false })

const pronte = ref(false)
mettiTutteLeIcone().then(() => (pronte.value = true))
</script>
