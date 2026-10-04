<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!-- The hamburger used to live here. What it opened is now the "More" page,
       a tab at the bottom within thumb reach, so the header gives all of its
       width — all 390px of it on a phone — to the page's own breadcrumbs and
       actions. -->
  <!-- gap-3: the phone's ring reaches 8px to its left, and with less room it
       took the last 7px of the page's own last button -->
  <div class="flex items-center gap-3 pl-2 pr-2 pt-safe">
    <div id="app-header" class="min-w-0 flex-1" />
    <!-- the phone at hand: calling is something one does, not a place -->
    <PhoneButton class="shrink-0" />
  </div>
  <CallUI class="mr-3 mt-2" />
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
import PhoneButton from '@/components/Telephony/PhoneButton.vue'
</script>
