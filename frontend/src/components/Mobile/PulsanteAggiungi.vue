<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The phone's «+» (docs/crm/29): what a list adds - a person, a task,
  a deal - where the thumb is, above the bar at the bottom, in the brand's
  colour like every primary action.

  It steps aside while the list goes down and comes back on the way up, as a
  phone's own apps do: sitting over the rows' right edge, it covered the «Call»
  of whichever person passed under it and the «Emetti la fattura» of the day's
  last appointments, and a tap meant for them added a new one instead.
-->
<template>
  <Button
    variant="solid"
    icon="lucide-plus"
    class="!fixed !bottom-[calc(env(safe-area-inset-bottom)+5rem)] !right-4 z-20 !size-14 !rounded-2xl shadow-lg transition-[transform,opacity] duration-200 motion-reduce:transition-none [&_svg]:!size-6 [&_span]:!size-6"
    :class="
      nascosto && 'pointer-events-none translate-y-[calc(100%+6rem)] opacity-0'
    "
    :aria-label="label"
    @focus="nascosto = false"
    @click="emit('click')"
  />
</template>

<script setup>
import { Button } from 'frappe-ui'
import { onBeforeUnmount, onMounted, ref } from 'vue'

defineProps({ label: { type: String, required: true } })
const emit = defineEmits(['click'])

// Down hides it, up shows it again; a few pixels either way are a finger
// resting, not a direction. Each list scrolls in a box of its own, so the
// scroll is heard on the way down the page (capture), box by box.
const nascosto = ref(false)
const dove = new WeakMap()

function alloScorrere(evento) {
  const box =
    evento.target === document ? document.scrollingElement : evento.target
  if (!(box instanceof Element)) return
  const ora = box.scrollTop
  if (!dove.has(box)) return dove.set(box, ora)
  const prima = dove.get(box)
  if (Math.abs(ora - prima) < 6) return
  dove.set(box, ora)
  nascosto.value = ora > prima && ora > 24
}

onMounted(() =>
  document.addEventListener('scroll', alloScorrere, {
    capture: true,
    passive: true,
  }),
)
onBeforeUnmount(() =>
  document.removeEventListener('scroll', alloScorrere, { capture: true }),
)
</script>
