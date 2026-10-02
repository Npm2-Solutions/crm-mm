<!-- An appointment as the patient reads it: when, heading the card - in the
     brand's colour while it is to come; what - which session of a cycle - with
     whom, where; the way to move or cancel it. In the centre's preview, one
     whoever previews does not read shows only when. -->
<template>
  <HiddenCard v-if="appointment.hidden" :when="when(appointment.starts_on)" />
  <div
    v-else
    class="area-card flex flex-col gap-1"
    :class="{ 'opacity-70': appointment.status === 'Cancelled' }"
  >
    <div class="flex items-start justify-between gap-2">
      <span
        class="area-label"
        :class="past ? '' : 'text-[var(--brand-strong)]'"
      >
        {{ intestazione(appointment.starts_on, locale) }}
      </span>
      <Badge
        v-if="appointment.status === 'Cancelled'"
        theme="red"
        variant="subtle"
        :label="__('Cancelled')"
      />
    </div>
    <span
      class="area-row__title"
      :class="{ 'line-through': appointment.status === 'Cancelled' }"
    >
      {{ appointment.service }}
      <template v-if="laSeduta(appointment.session, t)">
        · {{ laSeduta(appointment.session, t) }}
      </template>
    </span>
    <span v-if="appointment.staff?.length" class="area-row__sub">
      {{ __('With {0}', [appointment.staff.join(', ')]) }}
    </span>
    <span v-if="appointment.location" class="area-row__sub">
      {{ appointment.location }}
    </span>
    <a
      v-if="appointment.manage_url"
      :href="appointment.manage_url"
      class="area-link mt-1 inline-flex min-h-10 w-fit items-center gap-1"
    >
      {{ __('Move or cancel') }}
      <LucideChevronRight class="size-4" aria-hidden="true" />
    </a>
  </div>
</template>

<script setup>
import { laSeduta } from '@/utils/cicli'
import { Badge } from 'frappe-ui'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { intestazione } from '../aspetto'
import { when } from '../dates'
import { locale } from '../translation'
import HiddenCard from './HiddenCard.vue'

defineProps({
  appointment: { type: Object, required: true },
  // one gone by: its date in grey
  past: { type: Boolean, default: false },
})

const t = (text, args) => __(text, args)
</script>
