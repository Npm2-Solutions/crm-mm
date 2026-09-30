<!-- On the first screen: the plans followed now, and how today is going. -->
<template>
  <section v-if="plans.data?.plans?.length" class="flex flex-col gap-2">
    <h2 class="text-base font-medium text-ink-gray-7">
      {{ __('Your plans') }}
    </h2>
    <router-link
      v-for="plan in plans.data.plans"
      :key="plan.name"
      :to="{ name: 'Plan', params: { plan: plan.name } }"
      class="flex items-center justify-between gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
    >
      <span class="min-w-0 text-base text-ink-gray-9">{{ plan.title }}</span>
      <span v-if="plan.today" class="shrink-0 text-p-sm text-ink-gray-6">
        {{ __('Today {0} of {1}', [plan.done_today, plan.today]) }}
      </span>
    </router-link>
  </section>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { area } from '../store'

const plans = createResource({
  url: 'crm.clinica.area.piani.area_plans',
  params: { person: area.person },
  auto: true,
})
</script>
