<!--
  The product's icon, and the centre's logo beside it when the centre has one
  (Settings > General > Name & logo): the platform's brand comes first, everywhere.
-->
<template>
  <div class="flex shrink-0 items-center gap-1.5">
    <CRMLogo class="size-8 shrink-0 rounded" />
    <img
      v-if="centreLogo && !compact"
      :src="centreLogo"
      alt=""
      class="h-6 max-w-12 shrink-0 object-contain"
    />
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { computed } from 'vue'

const props = defineProps({
  // the centre's brand: its logo, if it uploaded one
  modelValue: { type: Object, default: () => ({}) },
  // a narrow place (the collapsed sidebar): the product's icon alone
  compact: { type: Boolean, default: false },
})

const centreLogo = computed(() => props.modelValue?.logo || '')
</script>
