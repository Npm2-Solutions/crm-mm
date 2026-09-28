<template>
  <!-- a page that draws its own header (data import, not found) left this
       border as a stray line across the top -->
  <div class="flex border-b pr-5 has-[#app-header:empty]:border-b-0">
    <div id="app-header" class="min-w-0 flex-1"></div>
    <div class="flex items-center justify-center">
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
</script>
