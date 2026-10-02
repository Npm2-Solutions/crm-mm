<!--
  What to buy for the days ahead: the diet's foods with how much, rounded up as a
  person buys them; an exchange diet's groups with their portions and the foods
  to choose from. A tick for what is already in the bag, kept on this phone only.
-->
<template>
  <div class="flex flex-col gap-4">
    <router-link
      :to="{ name: 'Plan', params: { plan: route.params.plan } }"
      class="area-back w-fit"
    >
      <LucideChevronLeft class="size-4" aria-hidden="true" />
      {{ data?.plan.title || __('Your plans') }}
    </router-link>
    <h1 class="area-title">
      {{ __('Shopping list') }}
    </h1>
    <div class="flex gap-2">
      <button
        v-for="option in options"
        :key="option.days"
        type="button"
        class="min-h-10 shrink-0 rounded-[12px_12px_12px_2px] px-4 text-p-sm font-semibold"
        :class="
          option.days === days
            ? 'bg-[var(--brand-solid)] text-[var(--on-brand-solid)]'
            : 'bg-surface-elevation-1 text-ink-gray-7 shadow-[inset_0_0_0_1px_var(--outline-gray-2)]'
        "
        :aria-pressed="option.days === days"
        @click="load(option.days)"
      >
        {{ option.label }}
      </button>
    </div>
    <template v-if="data">
      <p class="text-p-sm text-ink-gray-6">
        {{ __('From {0} to {1}', [day(data.from), day(data.until)]) }}
        <template v-if="data.days < data.asked">
          · {{ __('the plan ends before') }}
        </template>
      </p>

      <section
        v-for="group in groups"
        :key="group.group"
        class="flex flex-col gap-2"
      >
        <h2 class="area-label">
          {{ __(group.group) }}
        </h2>
        <label
          v-for="row in group.items"
          :key="row.food"
          class="area-card area-row"
        >
          <Checkbox
            class="touch-target shrink-0"
            :model-value="ticked.has(row.food)"
            @update:model-value="(on) => tick(row.food, on)"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <span
              class="text-p-base"
              :class="
                ticked.has(row.food)
                  ? 'text-ink-gray-5 line-through'
                  : 'text-ink-gray-9'
              "
            >
              {{ row.food_name }}
            </span>
            <span v-if="how(row)" class="text-p-sm text-ink-gray-5">
              {{ how(row) }}
            </span>
          </span>
          <span class="shrink-0 text-p-base text-ink-gray-8">
            {{ quantitaDaComprare(row.grams, locale) }}
          </span>
        </label>
      </section>

      <section v-if="data.groups.length" class="flex flex-col gap-2">
        <h2 class="area-label">
          {{ __('To choose in the group') }}
        </h2>
        <div
          v-for="group in data.groups"
          :key="group.food_group"
          class="area-card flex flex-col gap-2"
        >
          <p class="text-p-base text-ink-gray-9 first-letter:uppercase">
            {{
              __('{0} portions of {1}', [group.portions, __(group.food_group)])
            }}
          </p>
          <details
            v-if="group.choices.length"
            class="text-p-sm text-ink-gray-7"
          >
            <summary class="area-link cursor-pointer">
              {{ __('Choose among') }}
            </summary>
            <ul class="mt-2 flex flex-col gap-1">
              <li v-for="choice in group.choices" :key="choice.food_name">
                {{ choice.food_name }}
                <span v-if="choice.portion_g" class="text-ink-gray-5">
                  · {{ choice.portion_g }} g
                </span>
              </li>
            </ul>
          </details>
        </div>
      </section>

      <p
        v-if="!data.foods.length && !data.groups.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('Nothing to buy in these days.') }}
      </p>
      <button
        v-if="ticked.size"
        type="button"
        class="min-h-11 w-fit area-link"
        @click="untick"
      >
        {{ __('Untick everything') }}
      </button>
    </template>
    <ErrorMessage :message="error" />
  </div>
</template>

<script setup>
import { comeSiArriva, perGruppo, quantitaDaComprare } from '@/utils/piani'
import { Checkbox, ErrorMessage, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import LucideChevronLeft from '~icons/lucide/chevron-left'
import { day } from '../dates'
import { area, messageOf } from '../store'
import { locale } from '../translation'

const route = useRoute()
const data = ref(null)
const error = ref('')
const days = ref(7)
const ticked = ref(new Set())

const options = [
  { days: 7, label: __('A week') },
  { days: 14, label: __('Two weeks') },
]
const groups = computed(() => perGruppo(data.value?.foods))

// the ticks are this phone's: nobody else needs to know what is in the bag
function key() {
  return `crm-area-spesa:${route.params.plan}:${data.value?.from}`
}

function readTicks() {
  try {
    ticked.value = new Set(JSON.parse(localStorage.getItem(key()) || '[]'))
  } catch {
    ticked.value = new Set()
  }
}

function saveTicks() {
  try {
    localStorage.setItem(key(), JSON.stringify([...ticked.value]))
  } catch {
    // a private window keeps nothing: the ticks last as long as the page
  }
}

function tick(food, on) {
  const next = new Set(ticked.value)
  if (on) next.add(food)
  else next.delete(food)
  ticked.value = next
  saveTicks()
}

function untick() {
  ticked.value = new Set()
  saveTicks()
}

async function load(count = days.value) {
  error.value = ''
  try {
    data.value = await call('crm.clinica.area.piani.area_shopping_list', {
      person: area.person,
      plan: route.params.plan,
      days: count,
    })
    days.value = count
    readTicks()
  } catch (e) {
    error.value = __(messageOf(e))
  }
}
load()

function how(row) {
  return comeSiArriva(row, (text, args) => __(text, args))
}
</script>
