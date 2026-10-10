<!-- Appointments: booking again, the cycles of sessions and the subscriptions going on, what
     the centre sells online, what the person waits for, the ones coming, then the last ones. -->
<template>
  <div class="flex flex-col gap-5">
    <h1 class="area-title">
      {{ __('Your appointments') }}
    </h1>
    <!-- back from Stripe's page: said once -->
    <p
      v-if="returned"
      class="rounded-[12px_12px_12px_2px] bg-[var(--brand-subtle)] px-3 py-2 text-p-sm text-[var(--on-brand-subtle)]"
      role="status"
    >
      {{
        returned === 'done'
          ? __(
              'Thank you: the payment went through. Your subscription shows here in a moment, its invoice in your Documents.',
            )
          : __('The payment was not made: nothing was bought.')
      }}
    </p>
    <BookAgain v-if="appointments.data?.book" :book="appointments.data.book" />
    <section
      v-if="appointments.data?.cycles?.length"
      class="flex flex-col gap-2"
    >
      <h2 class="area-label">
        {{ __('Your cycles of sessions') }}
      </h2>
      <CycleCard
        v-for="cycle in appointments.data.cycles"
        :key="cycle.name"
        :cycle="cycle"
      />
    </section>
    <section
      v-if="appointments.data?.subscriptions?.length"
      class="flex flex-col gap-2"
    >
      <h2 class="area-label">
        {{ __('Your subscriptions') }}
      </h2>
      <p
        v-if="saidOfCard"
        class="rounded-[12px_12px_12px_2px] bg-[var(--brand-subtle)] px-3 py-2 text-p-sm text-[var(--on-brand-subtle)]"
        role="status"
      >
        {{ saidOfCard }}
      </p>
      <SubscriptionCard
        v-for="subscription in appointments.data.subscriptions"
        :key="subscription.name"
        :subscription="subscription"
        @changed="cardChanged"
      />
    </section>
    <!-- what the centre sells online (crm/pagamenti/addebiti.py): never in its preview -->
    <section v-if="shop.data?.items?.length" class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Buy online') }}</h2>
      <ShopCard
        v-for="item in shop.data.items"
        :key="item.name"
        :item="item"
        @buy="buying = item"
      />
    </section>
    <section
      v-if="appointments.data?.waiting?.length || appointments.data?.can_wait"
      class="flex flex-col gap-2"
    >
      <div class="flex items-center justify-between gap-2">
        <h2 class="area-label">
          {{ __('Waiting list') }}
        </h2>
        <Button
          v-if="appointments.data?.can_wait && !anteprima"
          size="md"
          :label="__('Join the waiting list')"
          icon-left="plus"
          @click="joining = true"
        />
      </div>
      <p
        v-if="said"
        class="rounded-[12px_12px_12px_2px] bg-[var(--brand-subtle)] px-3 py-2 text-p-sm text-[var(--on-brand-subtle)]"
        role="status"
      >
        {{ said }}
      </p>
      <WaitingCard
        v-for="entry in appointments.data?.waiting || []"
        :key="entry.name"
        :entry="entry"
        @changed="changed"
      />
      <p
        v-if="appointments.data && !appointments.data.waiting.length"
        class="text-p-base text-ink-gray-5"
      >
        {{
          __(
            'No time suits you? Join the waiting list: when a place frees up we write to you.',
          )
        }}
      </p>
    </section>
    <section class="flex flex-col gap-2">
      <h2 class="area-label">
        {{ __('Coming up') }}
      </h2>
      <AppointmentCard
        v-for="appointment in appointments.data?.upcoming || []"
        :key="appointment.name"
        :appointment="appointment"
      />
      <p
        v-if="appointments.data && !appointments.data.upcoming.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('No appointments booked.') }}
      </p>
    </section>
    <section v-if="appointments.data?.past?.length" class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Past') }}</h2>
      <AppointmentCard
        v-for="appointment in appointments.data.past"
        :key="appointment.name"
        :appointment="appointment"
        past
      />
    </section>
    <WaitingJoinDialog v-model="joining" @changed="changed('')" />
    <BuyDialog
      :model-value="Boolean(buying)"
      :item="buying"
      @update:model-value="(open) => !open && (buying = null)"
    />
  </div>
</template>

<script setup>
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { anteprima } from '../anteprima'
import AppointmentCard from '../components/AppointmentCard.vue'
import BookAgain from '../components/BookAgain.vue'
import BuyDialog from '../components/BuyDialog.vue'
import CycleCard from '../components/CycleCard.vue'
import ShopCard from '../components/ShopCard.vue'
import SubscriptionCard from '../components/SubscriptionCard.vue'
import WaitingCard from '../components/WaitingCard.vue'
import WaitingJoinDialog from '../components/WaitingJoinDialog.vue'
import { area } from '../store'

const joining = ref(false)
// how the last answer went: the card of a place booked or a list left is gone
const said = ref('')

const appointments = createResource({
  url: 'crm.area.api.get_appointments',
  params: { person: area.person },
  auto: true,
})

function changed(message) {
  said.value = message || ''
  appointments.reload()
}

// what the centre sells online: nothing asked in its preview
const shop = createResource({
  url: 'crm.area.api.get_shop',
  params: { person: area.person },
  auto: !anteprima,
})
const buying = ref(null)

const saidOfCard = ref('')
function cardChanged(message) {
  saidOfCard.value = message || ''
  appointments.reload()
}

// back from Stripe's page: said once, the address put back; Stripe tells the
// centre a moment after the person comes back
const route = useRoute()
const router = useRouter()
const returned = ref(
  { fatto: 'done', annullato: 'cancelled' }[route.query.pagamento] || '',
)
if (returned.value) {
  router.replace({ query: { ...route.query, pagamento: undefined } })
  if (returned.value === 'done') setTimeout(() => appointments.reload(), 4000)
}
</script>
