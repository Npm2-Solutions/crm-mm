<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The centre's tile: its logo when it is square, else its initials in the brand's
  colour and in a cloud, as the design system draws an avatar, else the
  product's icon. The client area's head, the previews in
  Settings. A wide logo is drawn on its own row instead: squeezed into a tile it
  would read as a line.
-->
<template>
  <!-- flex, not a grid: a grid's row grows with the logo, and a logo taller
       than wide came out of the tile's size, cut at the bottom -->
  <span
    class="flex shrink-0 items-center justify-center overflow-hidden rounded-md"
  >
    <img
      v-if="logo && forma !== 'wide'"
      :src="logo"
      alt=""
      class="size-full rounded-md border border-outline-gray-2 bg-white object-contain p-0.5"
    />
    <span
      v-else-if="lettere"
      class="grid size-full place-items-center rounded-[50%_50%_50%_22%] bg-[var(--brand-action)] font-semibold leading-none text-white dark:text-[#111]"
      :class="grande ? 'text-2xl' : 'text-sm'"
      aria-hidden="true"
    >
      {{ lettere }}
    </span>
    <CRMLogo v-else class="size-full rounded-md" />
  </span>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { iniziali } from '@/utils/marchio'
import { computed } from 'vue'

const props = defineProps({
  logo: { type: String, default: '' },
  // 'wide', 'square' or '' (not known yet: drawn in the tile)
  forma: { type: String, default: '' },
  nome: { type: String, default: '' },
  // the door's tile, its initials large
  grande: { type: Boolean, default: false },
})

const lettere = computed(() => iniziali(props.nome))
</script>
