<!-- On the first screen: the plans followed now, each in the cloud of its kind,
     and how today is going. Two or more side by side, as tiles; one, a row. -->
<template>
  <section v-if="plans.data?.plans?.length" class="flex flex-col gap-2">
    <h2 class="area-label">{{ __('Your plans') }}</h2>
    <div
      :class="
        plans.data.plans.length > 1
          ? 'grid grid-cols-2 gap-2.5'
          : 'flex flex-col gap-2'
      "
    >
      <template v-for="plan in plans.data.plans" :key="plan.name">
        <HiddenCard v-if="plan.hidden" />
        <router-link
          v-else
          :to="{ name: 'Plan', params: { plan: plan.name } }"
          class="area-card"
          :class="
            plans.data.plans.length > 1
              ? 'flex min-w-0 flex-col gap-2.5'
              : 'area-row'
          "
        >
          <AreaChip v-bind="chip(plan)" />
          <span class="min-w-0 flex-1">
            <span class="area-row__title break-words">{{ plan.title }}</span>
            <span class="area-row__sub">{{ how(plan) }}</span>
          </span>
          <LucideChevronRight
            v-if="plans.data.plans.length === 1"
            class="area-row__go size-5"
            aria-hidden="true"
          />
        </router-link>
      </template>
    </div>
  </section>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { aspetto } from '../aspetto'
import { area } from '../store'
import AreaChip from './AreaChip.vue'
import HiddenCard from './HiddenCard.vue'

const plans = createResource({
  url: 'crm.piani.area.area_plans',
  params: { person: area.person },
  auto: true,
})

function chip(plan) {
  const { colore, icona } = aspetto(plan)
  return { colore, icona }
}

// today's count where today has something, else what kind of plan it is
function how(plan) {
  return plan.today
    ? __('Today {0} of {1}', [plan.done_today, plan.today])
    : __(plan.plan_type)
}
</script>
