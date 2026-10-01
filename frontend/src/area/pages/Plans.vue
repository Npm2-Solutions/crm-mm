<!--
  What the person follows now: their quotes and how they are going, their
  programmes stage by stage, their plans with how today is going on each.
-->
<template>
  <div class="flex flex-col gap-4">
    <template v-if="quotes.data?.quotes?.length">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Your quotes') }}
      </h1>
      <template v-for="quote in quotes.data.quotes" :key="quote.name">
        <HiddenCard v-if="quote.hidden" />
        <QuoteCard v-else :quote="quote" />
      </template>
    </template>
    <template v-if="programmes.data?.programmes?.length">
      <h1 class="text-xl font-semibold text-ink-gray-9">
        {{ __('Your programmes') }}
      </h1>
      <template
        v-for="programme in programmes.data.programmes"
        :key="programme.name"
      >
        <HiddenCard v-if="programme.hidden" />
        <ProgrammeCard v-else :programme="programme" @changed="reload" />
      </template>
    </template>
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Your plans') }}
    </h1>
    <template v-for="plan in plans.data?.plans || []" :key="plan.name">
      <HiddenCard v-if="plan.hidden" />
      <router-link
        v-else
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
    </template>
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
import HiddenCard from '../components/HiddenCard.vue'
import ProgrammeCard from '../components/ProgrammeCard.vue'
import QuoteCard from '../components/QuoteCard.vue'
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
// the quotes proposed to the person and going on, where there are any
const quotes = createResource({
  url: 'crm.preventivi.area.area_quotes',
  params: { person: area.person },
  auto: Boolean(section('quotes')),
})

// a stage finished opens the next, and its plan comes with it
function reload() {
  programmes.reload()
  plans.reload()
}
</script>
