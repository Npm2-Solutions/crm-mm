<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!-- `h-app` and `w-full`, as the phone's frame (MobileLayout.vue): a tablet
       draws this one too, and where its browser hides its bar 100vh is
       measured without the bar, so the bottom of a list, the agenda's last
       hours and the sidebar's foot sat under it -->
  <div class="flex h-app w-full">
    <AppSidebar />
    <!-- `main`: where a screen reader jumps to the page -->
    <main class="flex-1 flex flex-col h-full overflow-auto bg-surface-base">
      <AppHeader />
      <SenzaRete />
      <slot />
    </main>
    <GlobalModals />
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import SenzaRete from '@/components/SenzaRete.vue'
</script>
