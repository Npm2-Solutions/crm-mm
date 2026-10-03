<!--
  A plan: written as a draft by its author, published to the person's area.

  The moments are the plan's rows - a session, a meal of the day - and each holds
  its items. Published, a plan is read here with how the last two weeks went,
  item by item; it is not rewritten: a new version replaces it, or it is closed.

  What a kind holds and what it offers besides comes from the server
  (crm.piani.api): the clinic's diets bring their calories, targets, nutrients,
  recipes and shopping list.
-->
<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ editing ? __(plan.plan_type) : plan.title }}
        </h3>
        <Badge
          v-if="plan.status"
          variant="subtle"
          :theme="statusTheme[plan.status] || 'gray'"
          :label="__(plan.status)"
        />
      </div>
    </template>
    <template #body-content>
      <div v-if="loading" class="py-10 text-center text-p-sm text-ink-gray-5">
        {{ __('Loading…') }}
      </div>

      <!-- writing it -->
      <div v-else-if="editing" class="flex flex-col gap-4">
        <p
          v-if="plan.programme"
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'A stage of the programme “{0}”: the plan is published when its stage opens.',
              [plan.programme_title],
            )
          }}
        </p>
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <FormControl v-model="plan.title" :label="__('Title')" />
          <FormControl
            v-model="plan.starts_on"
            type="date"
            :label="__('From')"
          />
          <FormControl
            v-model="plan.ends_on"
            type="date"
            :label="__('Until')"
          />
        </div>
        <FormControl
          v-model="plan.instructions"
          type="textarea"
          :rows="3"
          :label="__('For the person')"
          :placeholder="
            __(
              'What to keep in mind, in the words the person reads in their area',
            )
          "
        />
        <label v-if="offre(tipo, 'calories')" class="flex items-center gap-2">
          <Checkbox
            v-model="plan.show_calories"
            class="touch-target shrink-0"
          />
          <span class="text-base text-ink-gray-8">
            {{ __('Show the calories to the patient') }}
          </span>
        </label>
        <div v-if="offre(tipo, 'targets')" class="flex flex-col gap-2">
          <span class="text-sm font-medium text-ink-gray-7">
            {{ __('Targets for a day') }}
          </span>
          <div class="grid grid-cols-5 gap-3 max-md:grid-cols-2">
            <FormControl
              v-for="field in nutrientFields"
              :key="field.key"
              v-model="plan.targets[field.key]"
              type="number"
              :label="field.label"
            />
          </div>
        </div>

        <section
          v-for="moment in plan.moments"
          :key="moment.key"
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="flex flex-wrap items-end gap-2">
            <div class="min-w-40 flex-1">
              <FormControl v-model="moment.label" :label="__('Moment')" />
            </div>
            <div class="w-40 max-md:flex-1">
              <FormControl
                v-model="moment.day"
                type="select"
                :label="__('Day')"
                :options="dayOptions"
              />
            </div>
            <div class="w-32 max-md:flex-1">
              <FormControl
                v-model="moment.time"
                type="time"
                :label="__('Time')"
              />
            </div>
            <Button
              variant="ghost"
              icon="trash-2"
              class="touch-target shrink-0"
              :aria-label="__('Remove the moment')"
              @click="removeMoment(moment)"
            />
          </div>
          <FormControl
            v-model="moment.note"
            type="textarea"
            :rows="moment.note ? 4 : 2"
            :placeholder="
              offre(tipo, 'meals')
                ? __('How to prepare it: the patient reads it with the meal')
                : __(
                    'What to keep in mind: the person reads it with the session',
                  )
            "
          />
          <PlanItemEditor
            v-for="item in itemsOf(moment.key)"
            :key="item.key"
            :model-value="item"
            @remove="removeItem(item)"
          />
          <div class="flex flex-wrap items-center gap-2">
            <Dropdown :options="addOptions(moment)" placement="left">
              <Button
                size="sm"
                icon-left="plus"
                class="w-fit"
                :label="__('Add')"
              />
            </Dropdown>
            <Button
              v-if="offre(tipo, 'recipes') && plan.recipes?.on"
              size="sm"
              icon-left="lucide-sparkles"
              :label="__('Propose recipes')"
              :disabled="!plan.recipes.consent"
              :title="
                plan.recipes.consent
                  ? ''
                  : __('The patient has not agreed to the assistant')
              "
              @click="openRecipes(moment)"
            />
            <span
              v-if="offre(tipo, 'nutrients') && momentLine(moment.key)"
              class="text-p-xs text-ink-gray-5"
            >
              {{ momentLine(moment.key) }}
            </span>
          </div>
        </section>
        <Button
          class="w-fit"
          icon-left="plus"
          :label="__('Add a moment')"
          @click="addMoment"
        />
        <PlanNutrientsTable
          v-if="offre(tipo, 'nutrients') && hasFoods"
          :days="days"
          :targets="plan.targets"
          :missing="missing"
        />
        <ErrorMessage :message="error" />
        <!-- inside the plan's dialog: one layer on the other, for the eye and
             for a screen reader -->
        <RecipeDialog
          v-model="recipes.show"
          :plan="plan.name"
          :moment="recipes.moment"
          :suggested-kcal="recipes.kcal"
          @used="onRecipeUsed"
        />
      </div>

      <!-- reading it -->
      <div v-else class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{ __(plan.plan_type) }} · {{ plan.practitioner_name }}
          <template v-if="plan.starts_on || plan.ends_on">
            · {{ period }}
          </template>
        </p>
        <p
          v-if="plan.instructions"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-base text-ink-gray-8"
        >
          {{ plan.instructions }}
        </p>
        <div
          v-if="plan.status !== 'Draft'"
          class="flex flex-wrap items-center gap-3 text-p-xs text-ink-gray-5"
        >
          <span>{{ __('The last two weeks') }}:</span>
          <span
            v-for="outcome in outcomes"
            :key="outcome"
            class="flex items-center gap-1"
          >
            <span class="size-2.5 rounded-sm" :class="dot(outcome)" />
            {{ __(outcome) }}
          </span>
        </div>
        <section
          v-for="moment in plan.moments.filter((m) => itemsOf(m.key).length)"
          :key="moment.key"
          class="flex flex-col gap-2"
        >
          <h4 class="text-base font-medium text-ink-gray-8">
            {{ moment.label }}
            <span class="text-p-sm font-normal text-ink-gray-5">
              · {{ __(moment.day)
              }}{{ moment.time ? ' · ' + hhmm(moment.time) : '' }}
            </span>
          </h4>
          <p
            v-if="moment.note"
            class="whitespace-pre-line text-p-sm text-ink-gray-6"
          >
            {{ moment.note }}
          </p>
          <div
            v-for="item in itemsOf(moment.key)"
            :key="item.key"
            class="flex flex-wrap items-center justify-between gap-2 border-b border-outline-gray-1 pb-2 last:border-0"
          >
            <div class="flex min-w-0 flex-col">
              <span class="text-p-base text-ink-gray-8">
                {{ describe(item) }}
              </span>
              <span
                v-if="item.alternatives || item.note"
                class="text-p-sm text-ink-gray-5"
              >
                {{ [item.alternatives, item.note].filter(Boolean).join(' · ') }}
              </span>
            </div>
            <div v-if="plan.status !== 'Draft'" class="flex shrink-0 gap-0.5">
              <span
                v-for="day in giorniDellaVoce(plan.logs, item.key, plan.days)"
                :key="day.day"
                class="size-2.5 rounded-sm"
                :class="dot(day.outcome)"
                :title="day.day + (day.outcome ? ' · ' + __(day.outcome) : '')"
              />
            </div>
          </div>
        </section>
        <PlanNutrientsTable
          v-if="offre(tipo, 'nutrients') && hasFoods"
          :days="days"
          :targets="plan.targets"
          :missing="missing"
        />
        <p v-if="plan.replaced_by" class="text-p-sm text-ink-gray-5">
          {{ __('Replaced by a new version.') }}
        </p>
        <ErrorMessage :message="error" />
        <!-- inside the plan's dialog, one layer on the other -->
        <ShoppingListDialog v-model="shopping" :plan="plan.name" />
      </div>
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          v-if="plan.name"
          variant="ghost"
          theme="red"
          :label="__('Delete the draft')"
          @click="remove"
        />
        <span v-else />
        <div class="flex gap-2">
          <Button
            :label="__('Save the draft')"
            :variant="plan.programme ? 'solid' : 'subtle'"
            :loading="busy === 'save'"
            @click="save()"
          />
          <!-- a stage's plan opens with its stage, not on its own -->
          <Button
            v-if="!plan.programme"
            variant="solid"
            :label="__('Publish')"
            :loading="busy === 'publish'"
            @click="publish"
          />
        </div>
      </div>
      <div v-else class="dialog-footer flex flex-wrap justify-end gap-2">
        <Button
          v-if="offre(tipo, 'shopping') && hasShopping"
          icon-left="lucide-shopping-cart"
          :label="__('Shopping list')"
          @click="shopping = true"
        />
        <Button
          v-if="plan.can_close"
          :label="__('Close the plan')"
          :loading="busy === 'close'"
          @click="close"
        />
        <Button
          v-if="plan.can_version"
          variant="solid"
          :label="__('New version')"
          :loading="busy === 'version'"
          @click="newVersion"
        />
        <Button v-else :label="__('Done')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import PlanItemEditor from '@/components/Plans/PlanItemEditor.vue'
import PlanNutrientsTable from '@/components/Clinic/PlanNutrientsTable.vue'
import RecipeDialog from '@/components/Clinic/RecipeDialog.vue'
import ShoppingListDialog from '@/components/Clinic/ShoppingListDialog.vue'
import { formatDate } from '@/utils'
import { hhmm } from '@/utils/scheduler'
import {
  CIBO,
  ESITI,
  GIORNI,
  GRUPPO,
  NUTRIENTI,
  OGNI_GIORNO,
  descrivi,
  giorniDellaVoce,
  momentiIniziali,
  nuovaVoce,
  nuovoMomento,
  nutrienti,
  offre,
  perGiorno,
  rigaNutrienti,
} from '@/utils/piani'
import {
  Badge,
  Button,
  Checkbox,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
  // the plan to open; none for a new one of ``kind``, as the server describes
  // it: {key, items, features}
  name: { type: String, default: null },
  kind: { type: Object, default: null },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const plan = reactive({ moments: [], items: [] })
const loading = ref(false)
const busy = ref('')
const error = ref('')
const outcomes = ESITI
const statusTheme = { Draft: 'orange', Published: 'green', Closed: 'gray' }

const editing = computed(() => !plan.name || plan.can_edit)
// the plan's kind as the server describes it: what it holds, what it offers
const tipo = computed(() => ({
  key: plan.plan_type,
  items: plan.item_kinds || [],
  features: plan.features || [],
}))
const dayOptions = [OGNI_GIORNO, ...GIORNI].map((day) => ({
  label: __(day),
  value: day,
}))

// what the server gives, as the editor holds it
function fill(data) {
  for (const key of Object.keys(plan)) delete plan[key]
  Object.assign(plan, data, {
    show_calories: Boolean(data.show_calories),
    targets: Object.fromEntries(
      NUTRIENTI.map((n) => [n, data.targets?.[n] ?? '']),
    ),
    moments: (data.moments || []).map((m) => ({ ...m, time: m.time || null })),
    items: (data.items || []).map((i) => ({
      ...i,
      times_per_week: i.times_per_week ? String(i.times_per_week) : '0',
    })),
  })
}

watch(show, async (open) => {
  if (!open) return
  error.value = ''
  busy.value = ''
  if (!props.name) {
    fill({
      plan_type: props.kind?.key,
      item_kinds: props.kind?.items || [],
      features: props.kind?.features || [],
      title: __(props.kind?.key || ''),
      status: 'Draft',
      moments: firstMoments(props.kind),
      items: [],
    })
    if (offre(props.kind, 'recipes')) {
      plan.recipes = await call('crm.clinica.menu.recipes_available', {
        lead: props.lead,
      }).catch(() => ({}))
    }
    return
  }
  loading.value = true
  try {
    fill(await call('crm.piani.api.get_plan', { name: props.name }))
    // a stage's plan starts empty on the server: the same first moments as a new one
    if (plan.can_edit && !plan.moments.length && !plan.items.length)
      plan.moments = firstMoments(tipo.value)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    loading.value = false
  }
})

// where a plan starts: the day's meals, a session, or every day
function firstMoments(kind) {
  return momentiIniziali(kind, {
    pasti: [
      __('Breakfast'),
      __('Morning snack'),
      __('Lunch'),
      __('Afternoon snack'),
      __('Dinner'),
    ],
    seduta: __('Session'),
    giorno: __('Every day'),
  })
}

function itemsOf(key) {
  return plan.items.filter((item) => item.moment === key)
}

function addMoment() {
  plan.moments.push(nuovoMomento(''))
}

function removeMoment(moment) {
  plan.items = plan.items.filter((item) => item.moment !== moment.key)
  plan.moments = plan.moments.filter((m) => m.key !== moment.key)
}

function removeItem(item) {
  plan.items = plan.items.filter((i) => i !== item)
}

function addOptions(moment) {
  return (plan.item_kinds || []).map((kind) => ({
    label: __(kind),
    onClick: () => plan.items.push(nuovaVoce(kind, moment.key)),
  }))
}

function describe(item) {
  return descrivi(item, (text, args) => __(text, args))
}

const period = computed(() => {
  const from = plan.starts_on ? formatDate(plan.starts_on, 'D MMM YYYY') : ''
  const until = plan.ends_on ? formatDate(plan.ends_on, 'D MMM YYYY') : ''
  if (from && until) return __('from {0} to {1}', [from, until])
  return from ? __('from {0}', [from]) : __('until {0}', [until])
})

// done, partly, skipped: no red - the plan is followed, not judged
function dot(outcome) {
  return (
    {
      Done: 'bg-surface-green-3',
      Partly: 'bg-surface-amber-3',
      Skipped: 'bg-surface-gray-4',
    }[outcome] || 'border border-outline-gray-2'
  )
}

function payload() {
  return JSON.stringify({
    plan_type: plan.plan_type,
    title: plan.title,
    starts_on: plan.starts_on || null,
    ends_on: plan.ends_on || null,
    instructions: plan.instructions || null,
    show_calories: plan.show_calories ? 1 : 0,
    targets: plan.targets,
    moments: plan.moments,
    items: plan.items,
  })
}

async function run(what, method, args) {
  busy.value = what
  error.value = ''
  try {
    const data = await call(`crm.piani.api.${method}`, args)
    if (data) fill(data)
    emit('changed')
    return data || true
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
    return null
  } finally {
    busy.value = ''
  }
}

async function save(quiet = false) {
  const done = await run('save', 'save_plan', {
    lead: props.lead,
    data: payload(),
    name: plan.name || null,
  })
  if (done && !quiet) toast.success(__('Draft saved'))
  return done
}

async function publish() {
  // what is on screen is saved first: the draft published is the one shown
  if (!(await save(true))) return
  const done = await run('publish', 'publish_plan', { name: plan.name })
  if (done) {
    toast.success(__('Published: the person finds it in their area'))
    show.value = false
  }
}

async function close() {
  await run('close', 'close_plan', { name: plan.name })
}

async function newVersion() {
  await run('version', 'new_version', { name: plan.name })
}

async function remove() {
  const done = await run('delete', 'delete_draft', { name: plan.name })
  if (done) show.value = false
}

// ------------------------------------------------------------ the nutrients
// counted from the tables' values for 100 g, as the server counts them

const nutrientFields = [
  { key: 'kcal', label: __('Energy (kcal)') },
  { key: 'protein_g', label: __('Proteins (g)') },
  { key: 'carbs_g', label: __('Carbohydrates (g)') },
  { key: 'fat_g', label: __('Fats (g)') },
  { key: 'fibre_g', label: __('Fibre (g)') },
]

const foods = computed(() =>
  Object.fromEntries(
    (plan.items || [])
      .filter((item) => item.food && item.food_detail)
      .map((item) => [item.food, item.food_detail]),
  ),
)
const hasFoods = computed(() =>
  (plan.items || []).some((item) => item.kind === CIBO && item.food),
)
// a diet with something to buy: its foods, or an exchange diet's portions
const shopping = ref(false)
const hasShopping = computed(() =>
  (plan.items || []).some(
    (item) => (item.kind === CIBO && item.food) || item.kind === GRUPPO,
  ),
)
const days = computed(() => perGiorno(plan.moments, plan.items, foods.value))
const missing = computed(
  () => nutrienti(plan.items, foods.value).missing.length,
)

function momentLine(key) {
  const items = itemsOf(key)
  if (!items.some((item) => item.kind === CIBO && item.food)) return ''
  return rigaNutrienti(nutrienti(items, foods.value), (text, args) =>
    __(text, args),
  )
}

// ------------------------------------------------------------ the recipes

const recipes = reactive({ show: false, moment: null, kcal: '' })

// what the day's target leaves to this meal, shared with the empty ones
function suggestedKcal(moment) {
  const target = Number(plan.targets?.kcal)
  if (!target) return ''
  const day = moment.day === OGNI_GIORNO ? days.value[0]?.day : moment.day
  const ofTheDay = plan.moments.filter(
    (m) => m.day === OGNI_GIORNO || m.day === day,
  )
  const empty = ofTheDay.filter(
    (m) =>
      m.key !== moment.key &&
      !itemsOf(m.key).some((item) => item.kind === CIBO && item.food),
  )
  const total = days.value.find((row) => row.day === day)?.kcal || 0
  const own = nutrienti(itemsOf(moment.key), foods.value).kcal
  const left = target - (total - own)
  return left > 0 ? Math.round(left / (empty.length + 1)) : ''
}

async function openRecipes(moment) {
  // the proposal is the saved draft's: what is on screen is saved first
  if (!(await save(true))) return
  const saved = plan.moments.find((m) => m.key === moment.key) || moment
  Object.assign(recipes, {
    show: true,
    moment: { key: saved.key, label: saved.label },
    kcal: suggestedKcal(saved),
  })
}

function onRecipeUsed(data) {
  fill(data)
  emit('changed')
  toast.success(__('The recipe is in the meal: read it, then save or publish'))
}
</script>
