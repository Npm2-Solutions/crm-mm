<!--
  A subscription the person has: what it is, until when it lasts, and - when its
  entries are counted - how many are left this week or this month. Booking stays
  with the centre and the booking page: an appointment of a comprised service
  uses an entry by itself. Bought online and paid by the month, the card it is
  charged on and the next charge; a charge that did not go through, with «Pay
  now»; «Stop the charges» (crm/pagamenti/addebiti.py).
-->
<template>
  <article class="area-card flex flex-col gap-2">
    <div class="flex items-start justify-between gap-2">
      <h3 class="area-row__title min-w-0">
        {{ subscription.type }}
      </h3>
      <Badge
        v-if="subscription.suspended_until"
        class="shrink-0"
        variant="subtle"
        theme="orange"
        :label="__('Suspended')"
      />
    </div>
    <p v-if="subscription.description" class="text-p-sm text-ink-gray-7">
      {{ subscription.description }}
    </p>
    <template v-if="left !== null">
      <div
        class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2"
        role="progressbar"
        :aria-valuenow="percentuale(subscription)"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="__('Entries used')"
      >
        <div
          class="h-full rounded-full bg-[var(--brand-segno)]"
          :style="{ width: `${percentuale(subscription)}%` }"
        />
      </div>
      <p class="text-p-base text-ink-gray-8">{{ leftLine }}</p>
    </template>
    <p class="text-p-sm text-ink-gray-6">{{ until }}</p>
    <template v-if="carta.riga || carta.problema">
      <p v-if="carta.riga" class="text-p-sm text-ink-gray-7">
        {{ carta.riga }}
      </p>
      <p v-if="carta.problema" class="text-p-sm text-ink-red-7" role="status">
        {{ carta.problema }}
      </p>
      <div
        v-if="
          !anteprima && (subscription.card?.failed || subscription.card?.active)
        "
        class="flex flex-wrap gap-2"
      >
        <Button
          v-if="subscription.card?.failed"
          size="md"
          variant="solid"
          class="touch-target"
          :label="__('Pay now')"
          :loading="busy === 'pay'"
          @click="pay"
        />
        <Button
          v-if="subscription.card?.active"
          size="md"
          variant="subtle"
          class="touch-target"
          :label="__('Stop the charges')"
          @click="asking = true"
        />
      </div>
      <ErrorMessage :message="error" />
    </template>
    <Dialog
      v-model="asking"
      :options="{ title: __('Stop the charges on the card?'), size: 'sm' }"
    >
      <template #body-content>
        <p class="text-p-base text-ink-gray-8">
          {{
            __(
              'The card will not be charged any more. The instalments stay to pay as your subscription says: the centre tells you how.',
            )
          }}
        </p>
      </template>
      <template #actions>
        <div class="flex flex-wrap justify-end gap-2">
          <Button size="md" :label="__('Cancel')" @click="asking = false" />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Stop the charges')"
            :loading="busy === 'stop'"
            @click="stop"
          />
        </div>
      </template>
    </Dialog>
  </article>
</template>

<script setup>
import { A_SETTIMANA, percentuale, rimasti } from '@/utils/abbonamenti'
import { addebitoInParole } from '@/utils/pagamentiOnline'
import { Badge, Button, Dialog, ErrorMessage, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { anteprima } from '../anteprima'
import { day } from '../dates'
import { area } from '../store'

const props = defineProps({ subscription: { type: Object, required: true } })
const emit = defineEmits(['changed'])
const t = (text, args) => __(text, args)

// the monthly charge on the card, in the person's words
const carta = computed(() => addebitoInParole(props.subscription.card, t, day))

const busy = ref('')
const error = ref('')
const asking = ref(false)

async function pay() {
  busy.value = 'pay'
  error.value = ''
  try {
    const link = await call('crm.area.api.pay_instalment', {
      person: area.person,
      subscription: props.subscription.name,
      instalment: props.subscription.card.failed.instalment,
    })
    window.location.href = link.url
  } catch (e) {
    busy.value = ''
    error.value =
      e.messages?.[0] || __('The payment could not start: try again.')
  }
}

async function stop() {
  busy.value = 'stop'
  error.value = ''
  try {
    await call('crm.area.api.stop_card_charges', {
      person: area.person,
      subscription: props.subscription.name,
    })
    asking.value = false
    emit('changed', __('The card will not be charged any more.'))
  } catch (e) {
    error.value =
      e.messages?.[0] || __('Could not stop the charges: try again.')
  } finally {
    busy.value = ''
  }
}

// entries still to use in this week or month; none counted, nothing to say
const left = computed(() =>
  props.subscription.used === null || props.subscription.used === undefined
    ? null
    : rimasti(props.subscription),
)

const leftLine = computed(() => {
  const week = props.subscription.entries === A_SETTIMANA
  if (left.value === 1)
    return week ? __('1 entry left this week') : __('1 entry left this month')
  return week
    ? __('{0} entries left this week', [left.value])
    : __('{0} entries left this month', [left.value])
})

const until = computed(() => {
  const parts = []
  if (props.subscription.suspended_until)
    parts.push(
      __('suspended until {0}', [day(props.subscription.suspended_until)]),
    )
  parts.push(
    props.subscription.auto_renew
      ? __('renews by itself on {0}', [
          day(nextDay(props.subscription.ends_on)),
        ])
      : __('valid until {0}', [day(props.subscription.ends_on)]),
  )
  return parts.join(' · ')
})

function nextDay(value) {
  const giorno = new Date(`${value}T00:00:00Z`)
  giorno.setUTCDate(giorno.getUTCDate() + 1)
  return giorno.toISOString().slice(0, 10)
}
</script>
