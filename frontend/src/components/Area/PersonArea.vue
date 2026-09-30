<!--
  The person's client area, on their page: who enters it, the board the centre
  writes on, and the plans and programmes they follow there. The area is the
  CRM's; with the clinic on it is the patient area, and says so (crm.verticali),
  and its diets and exercises at home are plans too.
-->
<template>
  <div class="flex flex-col gap-4 px-8 py-6 max-md:px-4 max-md:py-4">
    <AreaAccessCard v-if="puo('area.invita')" :lead="lead" />
    <AreaMessagesCard v-if="puo('area.messaggi')" :lead="lead" />
    <PlansCard v-if="puo('piani.vedi') || puo('piani.scrivi')" :lead="lead" />
  </div>
</template>

<script setup>
import AreaAccessCard from '@/components/Area/AreaAccessCard.vue'
import AreaMessagesCard from '@/components/Area/AreaMessagesCard.vue'
import PlansCard from '@/components/Plans/PlansCard.vue'
import { usersStore } from '@/stores/users'

defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()
</script>
