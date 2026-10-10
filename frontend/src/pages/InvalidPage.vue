<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  An address that leads nowhere: the design system's EmptyState, as on a
  record that does not open, and the way back to one's own first page (the
  Agenda for a practitioner, never "People" for everybody).
-->
<template>
  <div class="grid h-full place-items-center px-4 py-12">
    <EmptyState
      class="max-w-md"
      :livello="2"
      :title="__('This page is not here')"
      :text="
        __('The address may be wrong, or the page is not one your level opens.')
      "
    >
      <Button
        variant="solid"
        :route="{ name: 'Home' }"
        :label="__('Go to the start')"
      />
    </EmptyState>
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
</script>
