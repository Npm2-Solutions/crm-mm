<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <!-- lucide icon from the sprite the IconPicker reads (lucide is a superset of
       feather, so legacy names still resolve). No width/height attrs so size
       classes like `h-4` control it, matching the old FeatherIcon behaviour.
       The icon goes into the sprite when it is first drawn (utils/icone.js),
       and is used once it is there. -->
  <svg
    v-else-if="typeof icon == 'string'"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="shrink-0"
    v-bind="$attrs"
  >
    <use v-if="pronta" :href="`#${nome}`" />
  </svg>
  <component :is="icon" v-else v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from '@/utils'
import { inPagina, mettiIcona } from '@/utils/icone'
import { computed, ref, watch } from 'vue'

const props = defineProps({ icon: { type: [String, Object], required: true } })

const nome = computed(() =>
  typeof props.icon == 'string' && !isEmoji(props.icon)
    ? props.icon.replace(/^lucide-/, '')
    : '',
)
const pronta = ref(false)
watch(
  nome,
  async (adesso) => {
    pronta.value = !adesso || inPagina(adesso)
    if (pronta.value) return
    await mettiIcona(adesso).catch(() => {})
    if (adesso === nome.value) pronta.value = inPagina(adesso)
  },
  { immediate: true },
)
</script>
