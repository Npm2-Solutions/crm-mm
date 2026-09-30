<!--
  The app's icon: the brand's - the vertical's (crm.marchio) - on every screen.
  DottorCloud's is its mark, a cloud with a cross cut out of it, white on the
  teal square. A centre's own logo goes beside it, never in its place.
-->
<template>
  <img :src="brand.icon" :alt="brand.name" class="object-contain" />
</template>

<script setup>
import { marchio } from '@/utils/marchio'

const brand = marchio()
</script>
