<template>
  <!-- `h-app` rather than `h-screen`: 100vh on a phone is measured with the
       address bar already hidden, so the shell used to hang the height of that
       bar below the fold. `w-full` rather than `w-screen`, which counts the
       scrollbar gutter and hands the page a horizontal scroll it never wanted. -->
  <div class="flex h-app w-full">
    <MobileMenu />
    <!-- The surface belongs to the whole column, not just the scroll box: with
         it only on the box, the header and the strip around it fell through to
         the page background, which in dark mode is white — white text on white. -->
    <div class="flex h-full min-w-0 flex-1 flex-col bg-surface-base px-safe">
      <MobileAppHeader />
      <!-- The scroll box is this wrapper, not the whole column, so the header
           stays put and the tab bar is never scrolled off the bottom. -->
      <div ref="scroll" class="flex min-h-0 flex-1 flex-col overflow-auto">
        <slot />
      </div>
      <MobileBottomNav v-if="!mobileNavHidden" />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileMenu from '@/components/Mobile/MobileMenu.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import MobileBottomNav from '@/components/Mobile/MobileBottomNav.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { mobileNavHidden } from '@/composables/mobileChrome'
import { registerScrollContainer, unregisterScrollContainer } from 'frappe-ui'
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

// frappe-ui's shells publish their scroll element to a shared registry; this
// layout is not one of them, so it registers its own. Without it `MobileNavItem`
// has nothing to scroll and tapping the tab you are already on does nothing.
const scroll = useTemplateRef('scroll')

onMounted(() => scroll.value && registerScrollContainer(scroll.value))
onBeforeUnmount(() => scroll.value && unregisterScrollContainer(scroll.value))
</script>
