<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  One person of an appointment on the desk's day: who, how they stand, the forms
  they owe, how long they have been waiting, and the next outcomes to give. On a
  phone the name has its own line and the outcomes the next, as wide as the
  screen and as tall as a thumb: 40px, with no ring of their own, which reached
  over the name and left it 29px to be tapped on.
-->
<template>
  <div class="flex items-center gap-3 py-2 max-md:flex-wrap max-md:py-3">
    <!-- a phone gives the name its own line, and the buttons the next; the
         name is read whole, the chips beside it go under it when it is long
         («Alice Fab…» beside «In attesa» and «1 modulo da firmare») -->
    <div
      class="flex min-w-0 flex-1 items-center gap-2 max-md:basis-full max-md:flex-wrap max-md:gap-y-1"
    >
      <RouterLink
        v-if="participant.party_type === 'CRM Lead' && participant.party"
        :to="{ name: 'Lead', params: { leadId: participant.party } }"
        class="truncate text-base-medium text-ink-gray-8 hover:underline max-md:-my-3 max-md:max-w-full max-md:shrink-0 max-md:py-3"
      >
        {{ participant.participant_name || participant.party }}
      </RouterLink>
      <span
        v-else
        class="truncate text-base-medium text-ink-gray-8 max-md:max-w-full max-md:shrink-0"
      >
        {{ participant.participant_name }}
      </span>
      <!-- a day gone by asks with its buttons: «In arrivo» there is not true -->
      <Badge
        v-if="!(past && participant.status === 'Booked')"
        :label="
          __(
            STATUS[participant.status]?.label || participant.status,
            null,
            'One person',
          )
        "
        :theme="STATUS[participant.status]?.theme || 'gray'"
        variant="subtle"
        class="shrink-0"
      />
      <!-- forms they owe for this appointment: to sign while they wait -->
      <RouterLink
        v-if="participant.due_forms?.length"
        :to="{
          name: 'Lead',
          params: { leadId: participant.party },
          hash: '#forms',
        }"
        class="touch-target shrink-0"
        :title="participant.due_forms.map((form) => form.title).join(', ')"
      >
        <Badge
          :label="
            participant.due_forms.length === 1
              ? __('1 form to sign')
              : __('{0} forms to sign', [participant.due_forms.length])
          "
          theme="blue"
          variant="subtle"
        />
      </RouterLink>
      <span
        v-if="participant.status === 'Arrived'"
        class="shrink-0 text-p-sm tabular-nums text-ink-gray-5"
        :title="
          __('In the waiting room since {0}', [timeOf(participant.arrived_at)])
        "
      >
        {{ waitingLabel(minutesWaiting(participant.arrived_at, now)) }}
      </span>
    </div>
    <div
      v-if="canMark"
      class="flex shrink-0 items-center gap-1.5 max-md:w-full max-md:gap-2"
    >
      <Button
        v-for="(outcome, i) in prossimiEsiti(participant.status, past)"
        :key="outcome"
        :label="etichetta(outcome)"
        :variant="i === 0 && outcome !== 'Booked' ? 'solid' : 'subtle'"
        :theme="outcome === 'No Show' ? 'red' : 'gray'"
        :size="isMobileView ? 'lg' : 'sm'"
        :loading="busy === outcome"
        :class="isMobileView ? 'flex-1' : 'touch-target'"
        @click="mark(outcome)"
      />
    </div>
  </div>
</template>

<script setup>
import { isMobileView } from '@/composables/breakpoints'
import {
  minutesWaiting,
  prossimiEsiti,
  timeOf,
  waitingLabel,
} from '@/utils/oggi'
import { Badge, Button, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  appointment: { type: Object, required: true },
  participant: { type: Object, required: true },
  canMark: { type: Boolean, default: false },
  // a day gone by: whether they came, not checking them in
  past: { type: Boolean, default: false },
  now: { type: Date, default: () => new Date() },
})

const emit = defineEmits(['changed'])

// what each outcome is called on its button, and on the badge once given: for
// one person («Assente»), where the day's tiles count them all («Non venuti»)
const ACTIONS = {
  Arrived: 'Check in',
  Attended: 'Came',
  'No Show': 'Did not come',
}
// going back says what it takes back: a bare «Annulla» beside «Presente», at a
// reception desk, read as cancelling the appointment
function etichetta(outcome) {
  if (outcome !== 'Booked') return __(ACTIONS[outcome], null, 'One person')
  return props.participant.status === 'Arrived'
    ? __('Undo the check-in')
    : __('Undo the outcome')
}

const STATUS = {
  Booked: { label: 'Expected', theme: 'gray' },
  Arrived: { label: 'Waiting', theme: 'orange' },
  Attended: { label: 'Came', theme: 'green' },
  'No Show': { label: 'Did not come', theme: 'red' },
}

const busy = ref('')

async function mark(outcome) {
  busy.value = outcome
  try {
    await call('crm.api.oggi.set_outcome', {
      appointment: props.appointment.name,
      participant: props.participant.name,
      outcome,
    })
    emit('changed')
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save'))
  } finally {
    busy.value = ''
  }
}
</script>
