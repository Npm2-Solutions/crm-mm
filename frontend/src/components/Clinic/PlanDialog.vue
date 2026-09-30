<!--
  A plan: written as a draft by its author, published to the person's area.

  The moments are the plan's rows - a meal of the day, a session - and each holds
  its items. Published, a plan is read here with how the last two weeks went,
  item by item; it is not rewritten: a new version replaces it, or it is closed.
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
          :label="__('For the patient')"
          :placeholder="
            __(
              'What to keep in mind, in the words the patient reads in their area',
            )
          "
        />
        <label v-if="isDieta(plan.plan_type)" class="flex items-center gap-2">
          <Checkbox
            v-model="plan.show_calories"
            class="touch-target shrink-0"
          />
          <span class="text-base text-ink-gray-8">
            {{ __('Show the calories to the patient') }}
          </span>
        </label>

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
          <PlanItemEditor
            v-for="item in itemsOf(moment.key)"
            :key="item.key"
            :model-value="item"
            @remove="removeItem(item)"
          />
          <Dropdown :options="addOptions(moment)" placement="left">
            <Button
              size="sm"
              icon-left="plus"
              class="w-fit"
              :label="__('Add')"
            />
          </Dropdown>
        </section>
        <Button
          class="w-fit"
          icon-left="plus"
          :label="__('Add a moment')"
          @click="addMoment"
        />
        <ErrorMessage :message="error" />
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
        <p v-if="plan.replaced_by" class="text-p-sm text-ink-gray-5">
          {{ __('Replaced by a new version.') }}
        </p>
        <ErrorMessage :message="error" />
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
            :loading="busy === 'save'"
            @click="save()"
          />
          <Button
            variant="solid"
            :label="__('Publish')"
            :loading="busy === 'publish'"
            @click="publish"
          />
        </div>
      </div>
      <div v-else class="dialog-footer flex flex-wrap justify-end gap-2">
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
import PlanItemEditor from '@/components/Clinic/PlanItemEditor.vue'
import { formatDate } from '@/utils'
import {
  ESITI,
  GIORNI,
  OGNI_GIORNO,
  descrivi,
  generiPer,
  giorniDellaVoce,
  isDieta,
  momentiIniziali,
  nuovaVoce,
  nuovoMomento,
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
  // the plan to open; none for a new one of ``kind``
  name: { type: String, default: null },
  kind: { type: String, default: null },
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
const dayOptions = [OGNI_GIORNO, ...GIORNI].map((day) => ({
  label: __(day),
  value: day,
}))

// what the server gives, as the editor holds it
function fill(data) {
  for (const key of Object.keys(plan)) delete plan[key]
  Object.assign(plan, data, {
    show_calories: Boolean(data.show_calories),
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
      plan_type: props.kind,
      title: __(props.kind),
      status: 'Draft',
      moments: momentiIniziali(props.kind, {
        pasti: [
          __('Breakfast'),
          __('Morning snack'),
          __('Lunch'),
          __('Afternoon snack'),
          __('Dinner'),
        ],
        seduta: __('Session'),
        giorno: __('Every day'),
      }),
      items: [],
    })
    return
  }
  loading.value = true
  try {
    fill(await call('crm.clinica.piani.get_plan', { name: props.name }))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    loading.value = false
  }
})

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
  return generiPer(plan.plan_type).map((kind) => ({
    label: __(kind),
    onClick: () => plan.items.push(nuovaVoce(kind, moment.key)),
  }))
}

function describe(item) {
  return descrivi(item, (text, args) => __(text, args))
}

function hhmm(time) {
  return String(time).slice(0, 5)
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
    moments: plan.moments,
    items: plan.items,
  })
}

async function run(what, method, args) {
  busy.value = what
  error.value = ''
  try {
    const data = await call(`crm.clinica.piani.${method}`, args)
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
</script>
