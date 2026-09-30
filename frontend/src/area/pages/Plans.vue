<!--
  What the person follows now: their programmes, stage by stage, their plans with
  how today is going on each, and their dental care plans.
-->
<template>
  <div class="flex flex-col gap-4">
    <template v-if="carePlans.data?.plans?.length">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Your care plans') }}
      </h1>
      <CarePlanCard
        v-for="plan in carePlans.data.plans"
        :key="plan.name"
        :plan="plan"
      />
    </template>
    <template v-if="programmes.data?.programmes?.length">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Your programmes') }}
      </h1>
      <ProgrammeCard
        v-for="programme in programmes.data.programmes"
        :key="programme.name"
        :programme="programme"
        @changed="reload"
      />
    </template>
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Your plans') }}
    </h1>
    <router-link
      v-for="plan in plans.data?.plans || []"
      :key="plan.name"
      :to="{ name: 'Plan', params: { plan: plan.name } }"
      class="flex items-center justify-between gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
    >
      <span class="flex min-w-0 flex-col">
        <span class="text-base text-ink-gray-9">{{ plan.title }}</span>
        <span class="text-p-sm text-ink-gray-5">
          {{ __(plan.plan_type) }} · {{ plan.practitioner_name }}
        </span>
      </span>
      <span v-if="plan.today" class="shrink-0 text-p-sm text-ink-gray-6">
        {{ __('Today {0} of {1}', [plan.done_today, plan.today]) }}
      </span>
    </router-link>
    <p
      v-if="plans.data && !plans.data.plans.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('No plan to follow now.') }}
    </p>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import CarePlanCard from '../components/CarePlanCard.vue'
import ProgrammeCard from '../components/ProgrammeCard.vue'
import { area, section } from '../store'

const plans = createResource({
  url: 'crm.piani.area.area_plans',
  params: { person: area.person },
  auto: true,
})
const programmes = createResource({
  url: 'crm.piani.area.area_programmes',
  params: { person: area.person },
  auto: true,
})
// the clinic's dental care plans, where it has any for the person
const carePlans = createResource({
  url: 'crm.clinica.area.piani.area_care_plans',
  params: { person: area.person },
  auto: Boolean(section('care_plans')),
})

// a stage finished opens the next, and its plan comes with it
function reload() {
  programmes.reload()
  plans.reload()
}
</script>
