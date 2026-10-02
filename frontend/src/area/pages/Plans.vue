<!--
  What the person follows now: their plans, each in the cloud of its kind, with
  how today is going; their programmes stage by stage; their quotes and how they
  are going.
-->
<template>
  <div class="flex flex-col gap-5">
    <h1 class="area-title">{{ __('Plans') }}</h1>
    <section class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Your plans') }}</h2>
      <template v-for="plan in plans.data?.plans || []" :key="plan.name">
        <HiddenCard v-if="plan.hidden" />
        <router-link
          v-else
          :to="{ name: 'Plan', params: { plan: plan.name } }"
          class="area-card area-row"
        >
          <AreaChip v-bind="chip(plan)" />
          <span class="min-w-0 flex-1">
            <span class="area-row__title">{{ plan.title }}</span>
            <span class="area-row__sub">
              {{ __(plan.plan_type) }} · {{ plan.practitioner_name }}
            </span>
          </span>
          <span
            v-if="plan.today"
            class="shrink-0 text-p-sm font-semibold tabular-nums text-ink-gray-6"
          >
            {{ plan.done_today }}/{{ plan.today }}
          </span>
          <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
        </router-link>
      </template>
      <p
        v-if="plans.data && !plans.data.plans.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('No plan to follow now.') }}
      </p>
    </section>
    <section
      v-if="programmes.data?.programmes?.length"
      class="flex flex-col gap-2"
    >
      <h2 class="area-label">{{ __('Your programmes') }}</h2>
      <template
        v-for="programme in programmes.data.programmes"
        :key="programme.name"
      >
        <HiddenCard v-if="programme.hidden" />
        <ProgrammeCard v-else :programme="programme" @changed="reload" />
      </template>
    </section>
    <section v-if="quotes.data?.quotes?.length" class="flex flex-col gap-2">
      <h2 class="area-label">{{ __('Your quotes') }}</h2>
      <template v-for="quote in quotes.data.quotes" :key="quote.name">
        <HiddenCard v-if="quote.hidden" />
        <QuoteCard v-else :quote="quote" />
      </template>
    </section>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { aspetto } from '../aspetto'
import AreaChip from '../components/AreaChip.vue'
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

function chip(plan) {
  const { colore, icona } = aspetto(plan)
  return { colore, icona }
}

// a stage finished opens the next, and its plan comes with it
function reload() {
  programmes.reload()
  plans.reload()
}
</script>
