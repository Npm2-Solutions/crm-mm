<!--
  The app's icon: the brand's - the vertical's (crm.marchio). DottorCloud's is
  its mark, a cloud with a cross cut out of it, white on the teal square: the
  collapsed sidebar, the signature at the foot of the pages people open, the
  tile of a centre with neither a logo nor a name (CentreTile).
-->
<template>
  <img :src="brand.icon" :alt="brand.name" class="object-contain" />
</template>

<script setup>
import { marchio } from '@/utils/marchio'

const brand = marchio()
</script>
