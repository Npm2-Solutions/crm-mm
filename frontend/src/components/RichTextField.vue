<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  A field of formatted text. Its editor - TipTap, the menus, highlight.js, the
  markdown reader - comes when the field is drawn (editor/RichTextEditor.vue),
  not with every page that could draw one: the agenda's event panel, editing a
  note in a person's activities, the phone's task panel, where it was most of
  the page's first download. Until it arrives, the box keeps its place.
-->
<template>
  <component
    :is="Editore"
    v-if="Editore"
    v-bind="$props"
    @change="(valore) => emit('change', valore)"
  />
  <div v-else aria-busy="true">
    <div :class="['min-h-[3rem]', editorClass]" />
  </div>
</template>

<script setup>
import { onMounted, shallowRef } from 'vue'

defineProps({
  content: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  // what a screen reader calls the box, when its label is not tied to it
  label: { type: String, default: '' },
  editable: { type: Boolean, default: true },
  editorClass: { type: String, default: '' },
  fixedMenu: { type: Boolean, default: false },
  bubbleMenu: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const Editore = shallowRef(null)
onMounted(async () => {
  Editore.value = (
    await import('@/components/editor/RichTextEditor.vue')
  ).default
})
</script>
