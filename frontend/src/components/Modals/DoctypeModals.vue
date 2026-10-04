<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <DoctypeModal
    v-if="doctypeModal.show.value"
    v-model="doctypeModal.show.value"
    :doctypeTitle="doctypeModal.title.value"
    :doctype="doctypeModal.doctype.value"
    :docname="doctypeModal.name.value"
    :defaults="doctypeModal.defaults.value"
    @afterInsert="(d) => doctypeModal.triggerCallback('afterInsert', d)"
    @afterUpdate="(d) => doctypeModal.triggerCallback('afterUpdate', d)"
    :eliminabile="doctypeModal.eliminabile.value"
    @afterDelete="(d) => doctypeModal.triggerCallback('afterDelete', d)"
  />
</template>
<script setup>
import DoctypeModal from '@/components/Modals/DoctypeModal.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'

const doctypeModal = useDoctypeModal()
</script>
