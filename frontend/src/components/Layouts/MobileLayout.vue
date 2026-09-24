<template>
  <!-- `h-app` rather than `h-screen`: 100vh on a phone is measured with the
       address bar already hidden, so the shell used to hang the height of that
       bar below the fold. `w-full` rather than `w-screen`, which counts the
       scrollbar gutter and hands the page a horizontal scroll it never wanted. -->
  <div class="flex h-app w-full">
    <MobileSidebar />
    <div
      class="flex h-full min-w-0 flex-1 flex-col overflow-auto bg-surface-base px-safe"
    >
      <MobileAppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
