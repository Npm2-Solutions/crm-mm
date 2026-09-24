<template>
  <!-- The hamburger used to live here. The drawer it opened is now the "More"
       tab at the bottom, within thumb reach, so the header gives all of its
       width — all 390px of it on a phone — to the page's own breadcrumbs and
       actions. -->
  <div class="flex pl-2 pr-3 pt-safe">
    <div id="app-header" class="min-w-0 flex-1" />
  </div>
  <CallUI class="mr-3 mt-2" />
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
</script>
