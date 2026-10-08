<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The next appointment, the first screen's one deep block (area.css), as the
  brand's phone has it: when, in the mint of the logo; what - which session of a
  cycle; with whom and where - an online visit says so, and opens its room from a
  quarter of an hour before (OnlineVisit); the way to move or cancel it, and
  «I'm here» around its time (CheckIn). In the centre's
  preview, one whoever previews does not read shows only when.
-->
<template>
  <HiddenCard v-if="appointment.hidden" :when="when(appointment.starts_on)" />
  <div v-else class="area-deep">
    <span class="dc-crosses" aria-hidden="true" />
    <p class="area-deep__when">
      {{ intestazione(appointment.starts_on, locale) }}
    </p>
    <p class="area-deep__title">
      {{ appointment.service }}
      <template v-if="laSeduta(appointment.session, t)">
        · {{ laSeduta(appointment.session, t) }}
      </template>
    </p>
    <p v-if="who" class="area-deep__sub">{{ who }}</p>
    <p
      v-if="appointment.status === 'Cancelled'"
      class="area-deep__sub font-semibold"
    >
      {{ __('Cancelled') }}
    </p>
    <a
      v-else-if="appointment.manage_url"
      :href="appointment.manage_url"
      class="mt-3 inline-flex min-h-10 items-center gap-1 text-sm"
    >
      {{ __('Move or cancel') }}
      <LucideChevronRight class="size-4" aria-hidden="true" />
    </a>
    <OnlineVisit
      v-if="appointment.online && appointment.status !== 'Cancelled'"
      :appointment="appointment"
      deep
    />
    <CheckIn
      v-else-if="appointment.status !== 'Cancelled'"
      :appointment="appointment"
    />
  </div>
</template>

<script setup>
import { laSeduta } from '@/utils/cicli'
import { computed } from 'vue'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { intestazione } from '../aspetto'
import { when } from '../dates'
import { locale } from '../translation'
import CheckIn from './CheckIn.vue'
import HiddenCard from './HiddenCard.vue'
import OnlineVisit from './OnlineVisit.vue'

const props = defineProps({ appointment: { type: Object, required: true } })

const t = (text, args) => __(text, args)

// with whom, and where
const who = computed(() =>
  [
    props.appointment.staff?.length
      ? __('With {0}', [props.appointment.staff.join(', ')])
      : '',
    props.appointment.online
      ? __('Online visit')
      : props.appointment.location || '',
  ]
    .filter(Boolean)
    .join(' · '),
)
</script>
