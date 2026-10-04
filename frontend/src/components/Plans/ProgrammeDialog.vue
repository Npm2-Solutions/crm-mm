<!--
  A programme of stages: written as a draft by its author, published to the
  person's area. Each stage says what the person reads and may have its own plan,
  written in the plan's editor. By time, each stage opens on its day; at one's own
  pace, when the one before is finished. Published, the programme is read here
  with its stages - done, open, locked - and goes on, or is closed.
-->
<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-wrap items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ editing ? __('Programme') : programme.title }}
        </h3>
        <Badge
          v-if="programme.status"
          variant="subtle"
          :theme="statusTheme[programme.status] || 'gray'"
          :label="__(programme.status)"
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
          <FormControl v-model="programme.title" :label="__('Title')" />
          <FormControl
            v-model="programme.mode"
            type="select"
            :label="__('The stages open')"
            :options="modeOptions"
          />
          <FormControl
            v-model="programme.starts_on"
            type="date"
            :format="dateFormat()"
            :label="__('From')"
          />
        </div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            programme.mode === TEMPO
              ? __(
                  'Each stage opens after the days of the one before, from the first day. The last one may have no days: it stays open until the programme is closed.',
                )
              : __(
                  'The next stage opens when the person says the one before is finished, in their area, or when you do.',
                )
          }}
        </p>
        <FormControl
          v-model="programme.instructions"
          type="textarea"
          :rows="2"
          :label="__('For the person')"
          :placeholder="
            __('What the programme is for, in the words the person reads')
          "
        />
        <section
          v-for="(stage, index) in programme.stages"
          :key="stage.key"
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="flex flex-wrap items-end gap-2">
            <span
              class="flex size-7 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-p-sm text-ink-gray-7"
            >
              {{ index + 1 }}
            </span>
            <div class="min-w-40 flex-1">
              <FormControl v-model="stage.title" :label="__('Stage name')" />
            </div>
            <div v-if="programme.mode === TEMPO" class="w-28 max-md:flex-1">
              <FormControl
                v-model="stage.days"
                type="number"
                inputmode="numeric"
                :label="__('Days')"
              />
            </div>
            <Button
              variant="ghost"
              icon="arrow-up"
              class="touch-target shrink-0"
              :disabled="index === 0"
              :aria-label="__('Move up')"
              @click="move(index, -1)"
            />
            <Button
              variant="ghost"
              icon="trash-2"
              class="touch-target shrink-0"
              :aria-label="__('Remove the stage')"
              @click="removeStage(stage)"
            />
          </div>
          <FormControl
            v-model="stage.description"
            type="textarea"
            :rows="2"
            :placeholder="
              __(
                'What the person reads when the stage opens: its goal, what to keep in mind',
              )
            "
          />
          <div class="flex flex-wrap items-center gap-2">
            <template v-if="stage.plan">
              <span class="min-w-0 text-p-sm text-ink-gray-7">
                {{ __(stage.plan_type || 'Plan') }} · {{ stage.plan_title }}
              </span>
              <Button
                size="sm"
                :label="__('Write the plan')"
                @click="openPlan(stage.plan)"
              />
            </template>
            <Dropdown
              v-else-if="programme.kinds?.length"
              :options="planOptions(stage)"
              placement="left"
            >
              <Button
                size="sm"
                icon-left="plus"
                :label="__('A plan for this stage')"
              />
            </Dropdown>
            <span v-if="!stage.plan" class="text-p-xs text-ink-gray-5">
              {{ __('Without a plan, the stage is what it says.') }}
            </span>
          </div>
        </section>
        <Button
          class="w-fit"
          icon-left="plus"
          :label="__('Add a stage')"
          @click="addStage"
        />
        <ErrorMessage :message="error" />
      </div>

      <!-- reading it -->
      <div v-else class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{ __(programme.mode) }} · {{ programme.practitioner_name }}
          <template v-if="programme.starts_on">
            ·
            {{
              __('from {0}', [formatDate(programme.starts_on, 'D MMM YYYY')])
            }}
          </template>
        </p>
        <p
          v-if="programme.instructions"
          class="whitespace-pre-line rounded-md bg-surface-gray-2 px-3 py-2 text-p-base text-ink-gray-8"
        >
          {{ programme.instructions }}
        </p>
        <ol class="flex flex-col gap-2">
          <li
            v-for="(stage, index) in programme.stages"
            :key="stage.key"
            class="flex gap-3 rounded-lg border px-3 py-2"
            :class="
              stage.state === 'open'
                ? 'border-outline-gray-4'
                : 'border-outline-gray-2'
            "
          >
            <span
              class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-p-xs"
              :class="dot[stage.state]"
            >
              {{ stage.state === 'done' ? '✓' : index + 1 }}
            </span>
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="text-p-base text-ink-gray-8">{{ stage.title }}</span>
              <span class="text-p-sm text-ink-gray-5">{{ when(stage) }}</span>
              <span
                v-if="stage.description"
                class="whitespace-pre-line text-p-sm text-ink-gray-6"
              >
                {{ stage.description }}
              </span>
              <button
                v-if="stage.plan"
                type="button"
                class="w-fit text-p-sm text-ink-gray-8 underline underline-offset-2"
                @click="openPlan(stage.plan)"
              >
                {{ __(stage.plan_type) }} · {{ stage.plan_title }}
              </button>
            </span>
          </li>
        </ol>
        <ErrorMessage :message="error" />
      </div>
      <!-- inside the programme's dialog, one layer on the other -->
      <PlanDialog
        v-model="plan.show"
        :lead="lead"
        :name="plan.name"
        @changed="reloadQuietly"
      />
    </template>

    <template #actions>
      <div
        v-if="editing"
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          v-if="programme.name"
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
          v-if="programme.can_close"
          :label="__('Close the programme')"
          :loading="busy === 'close'"
          @click="close"
        />
        <Button
          v-if="programme.can_open_next"
          variant="solid"
          :label="
            programme.open_stage === null
              ? __('Open the first stage now')
              : __('Open the next stage now')
          "
          :loading="busy === 'next'"
          @click="next"
        />
        <Button
          v-else-if="programme.can_finish"
          variant="solid"
          :label="__('Finish the last stage')"
          :loading="busy === 'next'"
          @click="next"
        />
        <Button v-else :label="__('Done')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import PlanDialog from '@/components/Plans/PlanDialog.vue'
import { dateFormat, formatDate } from '@/utils'
import { RITMO, TEMPO, nuovaTappa, perIlServer } from '@/utils/programmi'
import {
  Badge,
  Button,
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
  // the programme to open; none for a new one
  name: { type: String, default: null },
  // the kinds of plan the author writes ({key, items, features}), before the
  // server says them
  kinds: { type: Array, default: () => [] },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const programme = reactive({ stages: [] })
const loading = ref(false)
const busy = ref('')
const error = ref('')
const statusTheme = {
  Draft: 'orange',
  Published: 'green',
  Completed: 'blue',
  Closed: 'gray',
}
const dot = {
  done: 'bg-surface-green-2 text-ink-green-8',
  open: 'bg-[var(--brand-action)] text-ink-base',
  locked: 'bg-surface-gray-2 text-ink-gray-6',
}
const modeOptions = [
  { label: __('At one’s own pace'), value: RITMO },
  { label: __('By time'), value: TEMPO },
]

const editing = computed(() => !programme.name || programme.can_edit)

function fill(data) {
  for (const key of Object.keys(programme)) delete programme[key]
  Object.assign(programme, data, {
    stages: (data.stages || []).map((s) => ({ ...s, days: s.days || '' })),
  })
}

watch(show, async (open) => {
  if (!open) return
  error.value = ''
  busy.value = ''
  if (!props.name) {
    fill({
      title: '',
      mode: RITMO,
      status: 'Draft',
      stages: [nuovaTappa(__('First stage'))],
      kinds: props.kinds,
    })
    return
  }
  loading.value = true
  try {
    fill(await call('crm.piani.programmi.get_programme', { name: props.name }))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    loading.value = false
  }
})

function when(stage) {
  const day = (value) => formatDate(value, 'D MMM')
  if (stage.state === 'done')
    return __('done on {0}', [day(stage.completed_on)])
  if (stage.state === 'open')
    return stage.ends_on
      ? __('open since {0}, until {1}', [
          day(stage.opened_on),
          day(stage.ends_on),
        ])
      : __('open since {0}', [day(stage.opened_on)])
  if (stage.opens_on) return __('opens on {0}', [day(stage.opens_on)])
  return __('opens when the one before is finished')
}

function addStage() {
  programme.stages.push(nuovaTappa(''))
}

function removeStage(stage) {
  programme.stages = programme.stages.filter((s) => s !== stage)
}

function move(index, by) {
  const stages = [...programme.stages]
  const [stage] = stages.splice(index, 1)
  stages.splice(index + by, 0, stage)
  programme.stages = stages
}

async function run(what, method, args) {
  busy.value = what
  error.value = ''
  try {
    const data = await call(`crm.piani.programmi.${method}`, args)
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
  const done = await run('save', 'save_programme', {
    lead: props.lead,
    data: JSON.stringify(perIlServer(programme)),
    name: programme.name || null,
  })
  if (done && !quiet) toast.success(__('Draft saved'))
  return done
}

async function publish() {
  if (!(await save(true))) return
  const done = await run('publish', 'publish_programme', {
    name: programme.name,
  })
  if (done) {
    toast.success(__('Published: the person finds it in their area'))
    show.value = false
  }
}

async function next() {
  await run('next', 'open_next_stage', { name: programme.name })
}

async function close() {
  await run('close', 'close_programme', { name: programme.name })
}

async function remove() {
  const done = await run('delete', 'delete_programme_draft', {
    name: programme.name,
  })
  if (done) show.value = false
}

// ------------------------------------------------------------ a stage's plan

const plan = reactive({ show: false, name: null })

function planOptions(stage) {
  return (programme.kinds || []).map((kind) => ({
    label: __(kind.key),
    onClick: () => newPlan(stage, kind.key),
  }))
}

async function newPlan(stage, kind) {
  // the stage exists on the server before its plan does
  if (!(await save(true))) return
  const saved = programme.stages.find((s) => s.key === stage.key)
  if (!saved) return
  const done = await call('crm.piani.programmi.stage_plan', {
    name: programme.name,
    stage: saved.key,
    plan_type: kind,
  }).catch((e) => {
    error.value = e.messages?.join(' ') || e.message
    return null
  })
  if (!done) return
  await reloadQuietly()
  openPlan(done.plan)
}

function openPlan(name) {
  Object.assign(plan, { show: true, name })
}

async function reloadQuietly() {
  if (!programme.name) return
  const data = await call('crm.piani.programmi.get_programme', {
    name: programme.name,
  }).catch(() => null)
  if (!data) return
  // what is being written stays as it is; the plans come from the server
  if (editing.value) {
    const plans = Object.fromEntries(data.stages.map((s) => [s.key, s]))
    for (const stage of programme.stages) {
      const saved = plans[stage.key]
      if (!saved) continue
      Object.assign(stage, {
        plan: saved.plan,
        plan_title: saved.plan_title,
        plan_type: saved.plan_type,
      })
    }
  } else {
    fill(data)
  }
  emit('changed')
}
</script>
