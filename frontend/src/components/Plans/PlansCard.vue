<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The person's plans, a tab of their page: a training, habits, and the kinds a
  module brings - the clinic's diets and exercises at home. Each is written by
  whoever's qualification allows its kind, and followed by the person in their
  area; here, how the last week went. What a plan is and how it goes is said
  above it; with none yet, the kinds one may write are the choices, each saying
  what it is. The kinds come from the server (crm.piani.api).
-->
<template>
  <section v-if="plans.data" class="flex flex-col gap-5">
    <div
      class="flex flex-wrap items-start justify-between gap-4 max-md:flex-col max-md:gap-3"
    >
      <!-- the tab's header names it: here, what a plan is -->
      <div class="flex min-w-[15rem] max-w-2xl flex-1 flex-col gap-1">
        <DescrizioneRipiegata>
          {{
            __(
              'What the person follows between one appointment and the next: a training, habits, a diet, exercises at home. You write it here and publish it; they find it in their area and tick off what they do.',
            )
          }}
        </DescrizioneRipiegata>
      </div>
      <Dropdown
        v-if="plans.data.kinds.length && !vuoto"
        :options="newOptions"
        placement="right"
      >
        <Button
          class="shrink-0"
          variant="solid"
          icon-left="plus"
          :label="__('New plan')"
        />
      </Dropdown>
    </div>

    <!-- a published plan reaches the person only through their area -->
    <div
      v-if="avvisoArea"
      class="flex gap-2 rounded-lg bg-surface-amber-1 px-3 py-2.5 text-p-sm text-ink-amber-8"
    >
      <span class="lucide-info mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>{{ avvisoArea }}</span>
    </div>

    <!-- health data one may know of but does not read: their padlock, as in
         the history, never «No plans yet» over plans that are there -->
    <div v-if="nascosti.length" class="flex flex-col gap-1">
      <p
        v-for="riga in nascosti"
        :key="riga"
        class="flex items-start gap-2 text-p-sm text-ink-gray-6"
      >
        <span class="lucide-lock mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <span>{{ riga }}</span>
      </p>
    </div>

    <!-- none yet: how it goes, and what one may write -->
    <template v-if="vuoto">
      <!-- side by side where each has 12rem: three in a record's column on a
           tablet held upright were 70px, a word to a line -->
      <ol class="grid grid-cols-[repeat(auto-fit,minmax(12rem,1fr))] gap-3">
        <li
          v-for="(passo, i) in COME_FUNZIONA"
          :key="passo"
          class="flex gap-3 rounded-lg bg-surface-gray-1 p-3"
        >
          <span
            class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-3 text-p-sm font-medium text-ink-gray-7"
            aria-hidden="true"
          >
            {{ i + 1 }}
          </span>
          <span class="text-p-sm text-ink-gray-7">{{ __(passo) }}</span>
        </li>
      </ol>
      <div v-if="plans.data.kinds.length" class="flex flex-col gap-2">
        <h4 class="text-base-medium text-ink-gray-8">
          {{ __('What do you want to write?') }}
        </h4>
        <!-- two to a row where each has 14rem, one under the other in a
             record's column on a tablet held upright (125px each before) -->
        <ul class="grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-3">
          <li v-for="kind in plans.data.kinds" :key="kind.key">
            <button
              type="button"
              class="flex h-full w-full flex-col gap-1 rounded-lg border border-outline-gray-2 p-4 text-left hover:border-outline-gray-3 hover:bg-surface-gray-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              @click="nuovo(kind)"
            >
              <span class="text-base-medium text-ink-gray-8">
                {{ __(kind.key) }}
              </span>
              <span v-if="kind.description" class="text-p-sm text-ink-gray-6">
                {{ __(kind.description) }}
              </span>
            </button>
          </li>
          <li>
            <button
              type="button"
              class="flex h-full w-full flex-col gap-1 rounded-lg border border-dashed border-outline-gray-3 p-4 text-left hover:bg-surface-gray-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              @click="nuovoProgramma"
            >
              <span class="text-base-medium text-ink-gray-8">
                {{ __('Programme of stages') }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Several plans in a row: opened one after the other, or as the weeks go by.',
                  )
                }}
              </span>
            </button>
          </li>
        </ul>
      </div>
      <p v-else-if="!nascosti.length" class="text-p-sm text-ink-gray-5">
        {{
          __(
            'No plans yet. A practitioner writes them here, and the person follows them in their area.',
          )
        }}
      </p>
    </template>

    <div v-else class="flex flex-col gap-1">
      <!-- the programmes: stages that open with time, or one after the other -->
      <button
        v-for="programme in programmes.data?.programmes || []"
        :key="programme.name"
        type="button"
        class="flex items-center justify-between gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
        @click="openProgramme(programme.name)"
      >
        <span class="flex min-w-0 flex-col">
          <span class="truncate text-base text-ink-gray-8">
            {{ programme.title }}
          </span>
          <span
            class="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-0.5 text-p-sm text-ink-gray-5"
          >
            <span>
              {{ __('Programme') }} ·
              {{
                programme.open_stage === null
                  ? __('{0} stages', [programme.stages])
                  : __('stage {0} of {1}', [
                      programme.open_stage + 1,
                      programme.stages,
                    ])
              }}
              · {{ programme.practitioner_name }}
            </span>
            <!-- read like the clinical record, as a quote or a document is -->
            <CategoryTag
              v-if="programme.clinical"
              color="rose"
              :label="__('Health data')"
            />
          </span>
        </span>
        <Badge
          class="shrink-0"
          variant="subtle"
          :theme="statusTheme[programme.status] || 'gray'"
          :label="__(programme.status)"
        />
      </button>
      <button
        v-for="plan in plans.data.plans"
        :key="plan.name"
        type="button"
        class="flex items-center justify-between gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
        @click="open(plan.name)"
      >
        <span class="flex min-w-0 flex-col">
          <span class="truncate text-base text-ink-gray-8">{{
            plan.title
          }}</span>
          <!-- the line wraps rather than cut the name: a plan with health
               data has two marks before it -->
          <span
            class="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-0.5 text-p-sm text-ink-gray-5"
          >
            <CategoryTag
              :label="__(plan.plan_type)"
              :color="KIND_COLOR[plan.plan_type]"
            />
            <span class="max-w-full shrink-0 truncate">{{
              plan.practitioner_name
            }}</span>
            <CategoryTag
              v-if="plan.clinical"
              color="rose"
              :label="__('Health data')"
            />
          </span>
        </span>
        <span class="flex shrink-0 items-center gap-2">
          <span
            v-if="plan.status === 'Published'"
            class="text-p-xs text-ink-gray-5 max-md:hidden"
          >
            {{ __('{0} done this week', [plan.summary.Done]) }}
          </span>
          <Badge
            variant="subtle"
            :theme="statusTheme[plan.status] || 'gray'"
            :label="__(plan.status)"
          />
        </span>
      </button>
    </div>
    <PlanDialog
      v-model="dialog.show"
      :lead="lead"
      :name="dialog.name"
      :kind="dialog.kind"
      @changed="plans.reload()"
    />
    <ProgrammeDialog
      v-model="programmeDialog.show"
      :lead="lead"
      :name="programmeDialog.name"
      :kinds="plans.data.kinds"
      @changed="reload"
    />
  </section>
</template>

<script setup>
import DescrizioneRipiegata from '@/components/Mobile/DescrizioneRipiegata.vue'
import PlanDialog from '@/components/Plans/PlanDialog.vue'
import ProgrammeDialog from '@/components/Plans/ProgrammeDialog.vue'
import CategoryTag from '@/components/Espresso/CategoryTag.vue'
import { Badge, Button, Dropdown, createResource } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

// the kind is a category, the design system's Tag: exercises in violet, what
// the centre writes otherwise in its own colour
const KIND_COLOR = {
  Training: 'violet',
  'Home exercises': 'violet',
}

const statusTheme = {
  Draft: 'orange',
  Published: 'green',
  Completed: 'blue',
  Closed: 'gray',
}

const plans = createResource({
  url: 'crm.piani.api.get_plans',
  makeParams: () => ({ lead: props.lead }),
})
const programmes = createResource({
  url: 'crm.piani.programmi.get_programmes',
  makeParams: () => ({ lead: props.lead }),
})

function reload() {
  plans.reload()
  programmes.reload()
}

watch(
  () => props.lead,
  (lead) => lead && reload(),
  { immediate: true },
)

const dialog = reactive({ show: false, name: null, kind: null })

// how a plan goes, for whoever writes the first one
const COME_FUNZIONA = [
  'Choose what to write: a training, habits, a diet, exercises at home.',
  'Write the moments - breakfast, Monday morning - and what to do in each; exercises and foods come from the libraries.',
  'Publish it: the person finds it in their area and ticks off what they do. Here you see how their week went.',
]

// the plans and programmes with health data one may know of but does not read
const nascosti = computed(() => {
  const piani = plans.data?.hidden || 0
  const programmi = programmes.data?.hidden || 0
  return [
    piani === 1 && __('One plan with health data you cannot read'),
    piani > 1 && __('{0} plans with health data you cannot read', [piani]),
    programmi === 1 && __('One programme with health data you cannot read'),
    programmi > 1 &&
      __('{0} programmes with health data you cannot read', [programmi]),
  ].filter(Boolean)
})

// none yet, of plans or programmes
const vuoto = computed(
  () => !plans.data?.plans?.length && !programmes.data?.programmes?.length,
)

// what keeps a published plan from the person
const avvisoArea = computed(() => {
  const area = plans.data?.area
  if (!area || !plans.data.kinds.length) return ''
  if (!area.on)
    return __(
      'The client area is not on: the person will not see the plans. It is added in Settings, The centre, Features.',
    )
  if (!area.open)
    return __(
      'The person does not enter their area yet: invite them from the Client area tab, so that they see the plans you publish.',
    )
  return ''
})

function nuovo(kind) {
  Object.assign(dialog, { show: true, name: null, kind })
}

function nuovoProgramma() {
  Object.assign(programmeDialog, { show: true, name: null })
}

// the kinds the author's qualification writes, and a programme of them
const newOptions = computed(() => [
  ...(plans.data?.kinds || []).map((kind) => ({
    label: __(kind.key),
    onClick: () => nuovo(kind),
  })),
  {
    label: __('Programme of stages'),
    onClick: nuovoProgramma,
  },
])

const programmeDialog = reactive({ show: false, name: null })

function openProgramme(name) {
  Object.assign(programmeDialog, { show: true, name })
}

function open(name) {
  Object.assign(dialog, { show: true, name, kind: null })
}

defineExpose({ reload })
</script>
