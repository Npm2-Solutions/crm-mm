<!--
  A plan on a day, as the brand's phone has it: what kind of plan and whose, its
  title and how far today is; the days - two back to make up what was missed, a
  week ahead to look at (and shop for); each moment a card, each item one tap.
-->
<template>
  <div class="flex flex-col gap-4">
    <router-link :to="{ name: 'Plans' }" class="area-back w-fit">
      <LucideChevronLeft class="size-4" aria-hidden="true" />
      {{ __('Your plans') }}
    </router-link>
    <template v-if="data">
      <div class="flex items-end justify-between gap-3">
        <div class="flex min-w-0 flex-col gap-1">
          <p class="area-label">
            {{ __(data.plan.plan_type) }} · {{ data.plan.practitioner_name }}
          </p>
          <h1 class="area-title break-words">{{ data.plan.title }}</h1>
        </div>
        <!-- how far the day is, in the colour of the plan's kind -->
        <svg
          v-if="progresso.tutte"
          class="shrink-0"
          width="56"
          height="56"
          viewBox="0 0 56 56"
          role="img"
          :aria-label="
            __('Today {0} of {1}', [progresso.fatte, progresso.tutte])
          "
        >
          <circle
            cx="28"
            cy="28"
            r="22"
            fill="none"
            :stroke="anello.traccia"
            stroke-width="7"
          />
          <circle
            cx="28"
            cy="28"
            r="22"
            fill="none"
            :stroke="anello.segno"
            stroke-width="7"
            stroke-linecap="round"
            transform="rotate(-90 28 28)"
            :stroke-dasharray="GIRO"
            :stroke-dashoffset="GIRO * (1 - progresso.fatte / progresso.tutte)"
          />
          <text
            x="28"
            y="33"
            text-anchor="middle"
            font-size="14"
            font-weight="700"
            fill="var(--ink-gray-9)"
          >
            {{ progresso.fatte }}/{{ progresso.tutte }}
          </text>
        </svg>
      </div>

      <div class="-mx-5 flex gap-1.5 overflow-x-auto px-5 pb-1">
        <button
          v-for="d in data.days"
          :key="d"
          type="button"
          class="area-day"
          :aria-pressed="d === data.day"
          :aria-label="d === data.today ? __('Today') : day(d)"
          @click="go(d)"
        >
          {{ d === data.today ? __('Today') : giorno(d, locale).settimana }}
          <b>{{ giorno(d, locale).numero }}</b>
        </button>
      </div>
      <p v-if="data.day > data.today" class="text-p-sm text-ink-gray-5">
        {{ __('A look ahead: you mark it on the day.') }}
      </p>

      <router-link
        v-if="data.plan.features?.includes('shopping')"
        :to="{ name: 'PlanShopping', params: { plan: data.plan.name } }"
        class="area-card area-row"
      >
        <AreaChip colore="amber" icona="shopping-cart" />
        <span class="area-row__title min-w-0 flex-1">
          {{ __('Shopping list') }}
        </span>
        <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
      </router-link>
      <details
        v-if="data.plan.instructions"
        class="area-card text-p-base text-ink-gray-8"
      >
        <summary class="cursor-pointer font-semibold text-ink-gray-9">
          {{ __('What to keep in mind') }}
        </summary>
        <p class="mt-2 whitespace-pre-line">{{ data.plan.instructions }}</p>
      </details>

      <section
        v-for="moment in data.moments"
        :key="moment.key"
        class="area-card"
        :class="{ 'area-card--done': tuttoFatto(moment) }"
      >
        <h2 class="area-label">
          {{ moment.label }}
          <template v-if="ora(moment.time)">
            · {{ ora(moment.time) }}
          </template>
        </h2>
        <p
          v-if="moment.note"
          class="mt-1 whitespace-pre-line text-p-sm text-ink-gray-6"
        >
          {{ moment.note }}
        </p>
        <div class="divide-y divide-outline-gray-1">
          <PlanItem
            v-for="item in moment.items"
            :key="item.key"
            :item="item"
            :can-log="data.can_log"
            :busy="saving === item.key"
            @log="(outcome) => log(item, outcome)"
          />
        </div>
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
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import LucideChevronLeft from '~icons/lucide/chevron-left'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { aspetto, avanzamento, giorno, ora } from '../aspetto'
import AreaChip from '../components/AreaChip.vue'
import PlanItem from '../components/PlanItem.vue'
import { day } from '../dates'
import { area, messageOf } from '../store'
import { locale } from '../translation'

// the ring's length: 2πr with r 22
const GIRO = 138.2

const route = useRoute()
const data = ref(null)
const error = ref('')
const saving = ref(null)

const progresso = computed(() => avanzamento(data.value?.moments))
// the ring in the colour of the plan's kind, else the brand's mark
const anello = computed(() => {
  const { colore } = aspetto(data.value?.plan)
  return colore
    ? { segno: `var(--cat-${colore})`, traccia: `var(--cat-${colore}-subtle)` }
    : { segno: 'var(--brand-segno)', traccia: 'var(--brand-subtle)' }
})

const tuttoFatto = (moment) =>
  moment.items.length > 0 && moment.items.every((i) => i.outcome === 'Done')

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
