<template>
  <!-- `h-app` rather than `h-screen`: 100vh on a phone is measured with the
       address bar already hidden, so the shell used to hang the height of that
       bar below the fold. `w-full` rather than `w-screen`, which counts the
       scrollbar gutter and hands the page a horizontal scroll it never wanted. -->
  <!-- data-cornice-telefono: while somebody writes, the frame is as tall as
       what the keyboard leaves (utils/tastieraAperta.js, telefono.css) -->
  <div class="flex h-app w-full" data-cornice-telefono>
    <div class="flex h-full min-w-0 flex-1 flex-col px-safe">
      <MobileAppHeader />
      <!-- The scroll box is this wrapper, not the whole column, so the header
           stays put and the tab bar is never scrolled off the bottom. -->
      <div
        ref="scroll"
        class="flex min-h-0 flex-1 flex-col overflow-auto bg-surface-base"
      >
        <slot />
      </div>
      <MobileBottomNav />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import MobileBottomNav from '@/components/Mobile/MobileBottomNav.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { seguiLaTastiera } from '@/utils/tastieraAperta'
import { registerScrollContainer, unregisterScrollContainer } from 'frappe-ui'
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

// frappe-ui's shells publish their scroll element to a shared registry; this
// layout is not one of them, so it registers its own. Without it `MobileNavItem`
// has nothing to scroll and tapping the tab you are already on does nothing.
const scroll = useTemplateRef('scroll')

onMounted(() => scroll.value && registerScrollContainer(scroll.value))
onBeforeUnmount(() => scroll.value && unregisterScrollContainer(scroll.value))

// the keyboard covers the bottom of the screen without making the page any
// shorter: while somebody writes, the frame follows what one sees
let smettiDiSeguire = () => {}
onMounted(() => (smettiDiSeguire = seguiLaTastiera()))
onBeforeUnmount(() => smettiDiSeguire())

// what one taps shows it is pressed (`active:`) in place of the browser's grey
// flash (telefono.css); iPhone shows it only where a touch is listened to
function alTocco() {}
onMounted(() =>
  document.addEventListener('touchstart', alTocco, { passive: true }),
)
onBeforeUnmount(() => document.removeEventListener('touchstart', alTocco))
</script>
