<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A settings page's own action - «Update», «Send invites». On a desk it stays
  beside the page's title. On a phone it goes to the bar at the bottom of the
  screen (`#barra-impostazioni`, in Settings.vue), as wide as it: the title is
  a scroll away from the field just changed, and an «Update» up there was a
  change nobody saved.
-->
<template>
  <Teleport defer to="#barra-impostazioni" :disabled="!nellaBarra">
    <Button
      v-bind="$attrs"
      variant="solid"
      :label="label || __('Update')"
      :class="nellaBarra && 'w-full !text-base'"
    />
  </Teleport>
</template>

<script setup>
import { isMobileView } from '@/composables/settings'
import { computed, onMounted, ref } from 'vue'

defineOptions({ inheritAttrs: false })

defineProps({
  // the action's words, «Update» when not said
  label: { type: String, default: '' },
})

// the bar is there only in the settings' own window: a page drawn anywhere
// else keeps its button where it is
const barra = ref(false)
onMounted(() => {
  barra.value = Boolean(document.getElementById('barra-impostazioni'))
})
const nellaBarra = computed(() => isMobileView.value && barra.value)
</script>
