<!--
  A programme the person follows: its stages in order, what the open one says and
  its plan; the stages ahead say when they open. At one's own pace the person says
  when a stage is finished, and the next one opens.
-->
<template>
  <article class="area-card flex flex-col gap-3">
    <div class="flex flex-col gap-0.5">
      <h2 class="area-row__title">
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
        <!-- done, ticked; the stage open now, the brand's cross; the ones ahead,
             their number -->
        <span
          class="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-[50%_50%_50%_22%] text-p-xs font-semibold"
          :class="dot[stage.state]"
          role="img"
          :aria-label="labels[stage.state]"
        >
          <LucideCheck
            v-if="stage.state === 'done'"
            class="size-4"
            aria-hidden="true"
          />
          <span
            v-else-if="stage.state === 'open'"
            class="dc-cross"
            style="--c: var(--mint-300); --s: 10px"
            aria-hidden="true"
          />
          <template v-else>{{ index + 1 }}</template>
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
            class="w-fit area-link"
          >
            {{ __('Open the plan of this stage') }}
          </router-link>
          <template
            v-if="stage.state === 'open' && programme.can_finish && !anteprima"
          >
            <Button
              v-if="!confirming"
              class="mt-1 w-fit"
              variant="solid"
              size="lg"
              :label="__('I have finished this stage')"
              @click="confirming = true"
            />
            <span v-else class="mt-1 flex flex-wrap items-center gap-2">
              <span class="text-p-sm text-ink-gray-7">
                {{
                  index + 1 < programme.stages.length
                    ? __('The next stage opens now.')
                    : __('This is the last stage.')
                }}
              </span>
              <Button
                variant="solid"
                size="lg"
                :label="__('Yes, finished')"
                :loading="busy"
                @click="finish(stage)"
              />
              <Button
                variant="ghost"
                size="lg"
                :label="__('Not yet')"
                @click="confirming = false"
              />
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
import { Button, ErrorMessage, call } from 'frappe-ui'
import LucideCheck from '~icons/lucide/check'
import { computed, ref } from 'vue'
import { anteprima } from '../anteprima'
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
  done: 'bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]',
  open: 'bg-[var(--brand-solid)]',
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
    await call('crm.piani.area.finish_stage', {
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
