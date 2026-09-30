<!--
  A programme the person follows: its stages in order, what the open one says and
  its plan; the stages ahead say when they open. At one's own pace the person says
  when a stage is finished, and the next one opens.
-->
<template>
  <article
    class="flex flex-col gap-3 rounded-lg bg-surface-white p-4 shadow-sm"
  >
    <div class="flex flex-col gap-0.5">
      <h2 class="text-base font-medium text-ink-gray-9">
        {{ programme.title }}
      </h2>
      <p class="text-p-sm text-ink-gray-5">
        {{ progress }} · {{ programme.practitioner_name }}
      </p>
    </div>
    <p
      v-if="programme.instructions"
      class="whitespace-pre-line text-p-sm text-ink-gray-7"
    >
      {{ programme.instructions }}
    </p>
    <ol class="flex flex-col gap-2">
      <li
        v-for="(stage, index) in programme.stages"
        :key="stage.key"
        class="flex gap-3"
      >
        <span
          class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-p-xs"
          :class="dot[stage.state]"
          :aria-label="labels[stage.state]"
        >
          {{ stage.state === 'done' ? '✓' : index + 1 }}
        </span>
        <span class="flex min-w-0 flex-1 flex-col gap-1">
          <span
            class="text-p-base"
            :class="
              stage.state === 'locked' ? 'text-ink-gray-5' : 'text-ink-gray-9'
            "
          >
            {{ stage.title }}
          </span>
          <span
            v-if="stage.state === 'locked'"
            class="text-p-sm text-ink-gray-5"
          >
            {{
              stage.opens_on
                ? __('Opens on {0}', [day(stage.opens_on)])
                : __('Opens when you finish the one before')
            }}
          </span>
          <span
            v-if="stage.state === 'open' && stage.description"
            class="whitespace-pre-line text-p-sm text-ink-gray-7"
          >
            {{ stage.description }}
          </span>
          <router-link
            v-if="stage.state === 'open' && stage.plan"
            :to="{ name: 'Plan', params: { plan: stage.plan } }"
            class="w-fit text-p-sm text-ink-gray-9 underline underline-offset-2"
          >
            {{ __('Open the plan of this stage') }}
          </router-link>
          <template v-if="stage.state === 'open' && programme.can_finish">
            <button
              v-if="!confirming"
              type="button"
              class="mt-1 min-h-11 w-fit rounded-md bg-surface-gray-10 px-4 text-p-sm font-medium text-ink-base"
              @click="confirming = true"
            >
              {{ __('I have finished this stage') }}
            </button>
            <span v-else class="mt-1 flex flex-wrap items-center gap-2">
              <span class="text-p-sm text-ink-gray-7">
                {{
                  index + 1 < programme.stages.length
                    ? __('The next stage opens now.')
                    : __('This is the last stage.')
                }}
              </span>
              <button
                type="button"
                class="min-h-11 rounded-md bg-surface-gray-10 px-4 text-p-sm font-medium text-ink-base"
                :disabled="busy"
                @click="finish(stage)"
              >
                {{ __('Yes, finished') }}
              </button>
              <button
                type="button"
                class="min-h-11 rounded-md px-3 text-p-sm text-ink-gray-7"
                @click="confirming = false"
              >
                {{ __('Not yet') }}
              </button>
            </span>
          </template>
        </span>
      </li>
    </ol>
    <ErrorMessage :message="error" />
  </article>
</template>

<script setup>
import { aCheTappa } from '@/utils/programmi'
import { ErrorMessage, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { day } from '../dates'
import { area, messageOf } from '../store'

const props = defineProps({ programme: { type: Object, required: true } })
const emit = defineEmits(['changed'])

const confirming = ref(false)
const busy = ref(false)
const error = ref('')

const progress = computed(() =>
  aCheTappa(props.programme, (text, args) => __(text, args)),
)
// done, open, locked: no red, only where the person stands
const dot = {
  done: 'bg-surface-green-2 text-ink-green-8',
  open: 'bg-surface-gray-10 text-ink-base',
  locked: 'bg-surface-gray-2 text-ink-gray-6',
}
const labels = {
  done: __('Done'),
  open: __('Open'),
  locked: __('Not open yet'),
}

async function finish(stage) {
  busy.value = true
  error.value = ''
  try {
    await call('crm.clinica.area.piani.finish_stage', {
      person: area.person,
      programme: props.programme.name,
      stage: stage.key,
    })
    confirming.value = false
    emit('changed')
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
