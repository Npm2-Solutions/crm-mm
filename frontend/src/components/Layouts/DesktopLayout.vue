<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div class="flex h-screen w-screen">
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
