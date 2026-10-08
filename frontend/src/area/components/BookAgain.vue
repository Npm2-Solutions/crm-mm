<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Booking again on the centre's booking page: the service of the last appointment
  when it is still booked online, else the page's catalogue (`book` from
  `crm.area.api.get_appointments`). The page writes in who books from the session:
  nothing to type again.
-->
<template>
  <a :href="book.url" class="area-card area-row">
    <AreaChip icona="calendar" />
    <span class="min-w-0 flex-1">
      <span class="area-row__title">
        {{ book.service ? __('Book again') : __('Book an appointment') }}
      </span>
      <span v-if="book.service" class="area-row__sub">{{ book.service }}</span>
    </span>
    <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
  </a>
</template>

<script setup>
import LucideChevronRight from '~icons/lucide/chevron-right'
import AreaChip from './AreaChip.vue'

defineProps({ book: { type: Object, required: true } })
</script>
