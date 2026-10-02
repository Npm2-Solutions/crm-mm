<template>
  <!-- a page that draws its own header (data import, not found) left this
       border as a stray line across the top -->
  <div class="flex border-b pr-5 has-[#app-header:empty]:border-b-0">
    <div id="app-header" class="min-w-0 flex-1"></div>
    <div class="flex items-center justify-center gap-2">
      <CallUI />
      <!-- the phone at hand, at the top right of every page (doc 34) -->
      <PhoneButton class="ml-1" />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
import PhoneButton from '@/components/Telephony/PhoneButton.vue'
</script>
