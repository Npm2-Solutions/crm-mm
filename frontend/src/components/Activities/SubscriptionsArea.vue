<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What the person has going with the centre beyond one appointment: their
  subscriptions, their cycles of sessions, what they are waiting for. These
  were sections under the person's data - on the side of the page on a
  computer, under the fields of Details on a phone - and the data were a long
  scroll from them, and they from the data. A tab of their own now; the data
  are the person's alone.
-->
<template>
  <div
    class="mx-auto flex w-full max-w-3xl flex-col pb-6 pt-1 sm:px-7 [&>div:first-child>div:first-child]:hidden"
  >
    <SubscriptionsSection :lead="lead" />
    <CyclesSection :lead="lead" />
    <WaitingSection :lead="lead" />
  </div>
</template>

<script setup>
import CyclesSection from '@/components/CyclesSection.vue'
import SubscriptionsSection from '@/components/Subscriptions/SubscriptionsSection.vue'
import WaitingSection from '@/components/Waiting/WaitingSection.vue'

defineProps({
  lead: { type: String, required: true },
})
</script>
