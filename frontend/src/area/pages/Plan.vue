<!--
  A plan on a day: two days back to make up what was missed, a week ahead to
  look at (and shop for). Each item one tap: done, partly, skipped.
-->
<template>
  <div class="flex flex-col gap-4">
    <router-link
      :to="{ name: 'Plans' }"
      class="w-fit text-p-sm text-ink-gray-6 underline underline-offset-2"
    >
      {{ __('Your plans') }}
    </router-link>
    <template v-if="data">
      <div class="flex flex-col gap-0.5">
        <h1 class="text-xl font-semibold text-ink-gray-9">
          {{ data.plan.title }}
        </h1>
        <p class="text-p-sm text-ink-gray-5">
          {{ __(data.plan.plan_type) }} · {{ data.plan.practitioner_name }}
        </p>
      </div>
      <router-link
        v-if="data.plan.features?.includes('shopping')"
        :to="{ name: 'PlanShopping', params: { plan: data.plan.name } }"
        class="flex min-h-11 items-center justify-between gap-3 rounded-lg bg-surface-elevation-1 px-4 py-3 text-p-base text-ink-gray-9 shadow-sm"
      >
        {{ __('Shopping list') }}
        <span aria-hidden="true" class="text-ink-gray-5">›</span>
      </router-link>
      <details
        v-if="data.plan.instructions"
        class="rounded-lg bg-surface-elevation-1 p-4 text-p-base text-ink-gray-8 shadow-sm"
      >
        <summary class="cursor-pointer text-ink-gray-9">
          {{ __('What to keep in mind') }}
        </summary>
        <p class="mt-2 whitespace-pre-line">{{ data.plan.instructions }}</p>
      </details>

      <div class="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
        <button
          v-for="d in data.days"
          :key="d"
          type="button"
          class="min-h-9 shrink-0 rounded-full px-3 text-p-sm"
          :class="
            d === data.day
              ? 'bg-surface-gray-10 text-ink-base'
              : 'bg-surface-elevation-1 text-ink-gray-7 shadow-sm'
          "
          :aria-pressed="d === data.day"
          @click="go(d)"
        >
          {{ d === data.today ? __('Today') : shortDay(d) }}
        </button>
      </div>
      <p v-if="data.day > data.today" class="text-p-sm text-ink-gray-5">
        {{ __('A look ahead: you mark it on the day.') }}
      </p>

      <section
        v-for="moment in data.moments"
        :key="moment.key"
        class="flex flex-col gap-2"
      >
        <h2 class="text-base font-medium text-ink-gray-7">
          {{ moment.label }}
          <span v-if="moment.time" class="font-normal text-ink-gray-5">
            · {{ String(moment.time).slice(0, 5) }}
          </span>
        </h2>
        <p
          v-if="moment.note"
          class="whitespace-pre-line text-p-sm text-ink-gray-6"
        >
          {{ moment.note }}
        </p>
        <PlanItem
          v-for="item in moment.items"
          :key="item.key"
          :item="item"
          :can-log="data.can_log"
          :busy="saving === item.key"
          @log="(outcome) => log(item, outcome)"
        />
      </section>
      <p v-if="!data.moments.length" class="text-p-base text-ink-gray-5">
        {{ __('Nothing planned for this day.') }}
      </p>
      <ErrorMessage :message="error" />
    </template>
    <ErrorMessage v-else :message="error" />
  </div>
</template>

<script setup>
import { ErrorMessage, call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import PlanItem from '../components/PlanItem.vue'
import { shortDay } from '../dates'
import { area, messageOf } from '../store'

const route = useRoute()
const data = ref(null)
const error = ref('')
const saving = ref(null)

async function go(day) {
  error.value = ''
  try {
    data.value = await call('crm.piani.area.area_plan', {
      person: area.person,
      plan: route.params.plan,
      day: day || null,
    })
  } catch (e) {
    error.value = __(messageOf(e))
  }
}
go(null)

async function log(item, outcome) {
  const before = item.outcome
  item.outcome = outcome
  saving.value = item.key
  error.value = ''
  try {
    await call('crm.piani.area.log_item', {
      person: area.person,
      plan: route.params.plan,
      item: item.key,
      outcome,
      day: data.value.day,
    })
    // how many are left this week follows the answer
    if (item.left_this_week != null) await go(data.value.day)
  } catch (e) {
    item.outcome = before
    error.value = __(messageOf(e))
  } finally {
    saving.value = null
  }
}
</script>
