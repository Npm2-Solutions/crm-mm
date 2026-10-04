<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <FieldLayoutDialog
    v-for="dialog in fieldLayoutDialogs"
    :key="dialog.key"
    v-bind="dialogProps(dialog)"
    @resolve="dialog.props.onResolve"
  />
</template>

<script setup>
import { fieldLayoutDialogs } from '@/utils/renderFieldLayoutDialog'
import { aRichiesta } from '@/utils/aRichiesta'

// the dialog and its fields come with the first formDialog(): mounted with every
// page, the container had them in the first download
const FieldLayoutDialog = aRichiesta(
  () => import('@/components/Modals/FieldLayoutDialog.vue'),
  { attesa: false },
)

function dialogProps(dialog) {
  // Extract onResolve so it's only attached via @resolve, not doubled via v-bind
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { onResolve: _onResolve, ...rest } = dialog.props
  return rest
}
</script>
