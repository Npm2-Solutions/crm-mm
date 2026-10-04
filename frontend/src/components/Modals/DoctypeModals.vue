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
import { useDoctypeModal } from '@/composables/doctypeModal'
import { aRichiesta } from '@/utils/aRichiesta'

// a record's dialog, with the fields of every kind, comes when it opens: App.vue
// mounts this on every page
const DoctypeModal = aRichiesta(
  () => import('@/components/Modals/DoctypeModal.vue'),
  { attesa: false },
)

const doctypeModal = useDoctypeModal()
</script>
