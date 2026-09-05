<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: __('Dialer'), route: { name: 'Dialer' } }]"
      />
    </template>
    <template #right-header>
      <Button
        v-if="session.data"
        variant="ghost"
        :label="__('End session')"
        @click="endSession(false)"
      />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto">
    <div class="mx-auto w-full max-w-xl px-3 py-6 sm:px-5">
      <!-- no active session: build one -->
      <div
        v-if="!session.data && !session.loading"
        class="rounded-lg border border-outline-gray-2 bg-surface-base p-4"
      >
        <div class="mb-3 text-lg font-semibold text-ink-gray-9">
          {{ __('Start a dial session') }}
        </div>

        <div class="flex flex-col gap-3">
          <FormControl
            v-model="form.source"
            type="select"
            :label="__('Build queue from')"
            :options="sourceOptions"
            @update:modelValue="sourceTouched = true"
          />

          <!-- callbacks the answering service promised -->
          <template v-if="isCallbackRound">
            <div
              class="flex items-center justify-between rounded-md bg-surface-gray-2 px-3 py-2"
            >
              <div class="flex flex-col">
                <span class="text-base-medium text-ink-gray-8">
                  {{ __('{0} due now', [summary.data?.due ?? 0]) }}
                </span>
                <span class="text-p-sm text-ink-gray-6">
                  {{ __('{0} waiting in total', [summary.data?.pending ?? 0]) }}
                </span>
              </div>
              <Button
                variant="ghost"
                icon="refresh-cw"
                :loading="summary.loading"
                :tooltip="__('Refresh')"
                @click="summary.reload()"
              />
            </div>

            <FormControl
              v-model="form.includeUpcoming"
              type="checkbox"
              :label="__('Include callbacks that are not due yet')"
            />
          </template>

          <!-- the original lead/deal queue -->
          <template v-else>
            <FormControl
              v-model="form.status"
              type="select"
              :label="__('With status')"
              :options="statusSelectOptions"
            />
          </template>

          <FormControl
            v-model="form.limit"
            type="number"
            :label="__('Max records')"
          />
          <ErrorMessage :message="createError" />
          <Button
            variant="solid"
            :label="__('Build queue')"
            :loading="creating"
            @click="createSession"
          />
        </div>
      </div>

      <!-- active session -->
      <template v-else-if="session.data">
        <div class="mb-4 flex items-center justify-between">
          <span class="text-lg font-semibold text-ink-gray-9">
            {{ session.data.title }}
          </span>
          <span class="text-sm text-ink-gray-5">
            {{ session.data.done }} / {{ session.data.total }}
          </span>
        </div>
        <div
          class="mb-6 h-1.5 w-full overflow-hidden rounded bg-surface-gray-2"
        >
          <div
            class="h-full rounded bg-surface-gray-7 transition-all"
            :style="{
              width: (session.data.done / session.data.total) * 100 + '%',
            }"
          />
        </div>

        <!-- current contact -->
        <div
          v-if="current"
          class="rounded-lg border border-outline-gray-2 bg-surface-base p-4"
        >
          <div class="flex items-center justify-between">
            <div class="min-w-0">
              <router-link
                v-if="recordRoute(current)"
                :to="recordRoute(current)"
                class="text-lg font-medium text-ink-gray-9 hover:underline"
              >
                {{ current.display_name }}
              </router-link>
              <span v-else class="text-lg font-medium text-ink-gray-9">
                {{ current.display_name }}
              </span>
              <div class="text-sm text-ink-gray-5">{{ current.number }}</div>
              <div
                v-if="current.call_log && !current.reference_name"
                class="mt-1 text-p-sm text-ink-gray-5"
              >
                {{ __('No lead or deal matched this number') }}
              </div>
            </div>
            <Button
              variant="solid"
              theme="green"
              :label="__('Call')"
              :disabled="!callEnabled"
              @click="makeCall(current.number)"
            >
              <template #prefix>
                <PhoneIcon class="h-4 w-4" />
              </template>
            </Button>
          </div>

          <div class="mt-4 border-t border-outline-gray-1 pt-3">
            <div class="mb-2 text-xs text-ink-gray-5">{{ __('Outcome') }}</div>
            <div class="flex flex-wrap gap-2">
              <Button
                v-for="d in session.data.dispositions"
                :key="d"
                :variant="disposition == d ? 'solid' : 'outline'"
                :label="__(d)"
                @click="disposition = disposition == d ? '' : d"
              />
            </div>
            <p
              v-if="isCallbackSession && outcomeHint"
              class="mt-2 text-p-sm text-ink-gray-5"
            >
              {{ outcomeHint }}
            </p>
            <FormControl
              v-model="note"
              type="textarea"
              class="mt-3"
              :placeholder="__('Call note (optional)')"
            />
            <div class="mt-3 flex justify-between">
              <Button :label="__('Skip')" @click="completeCurrent(true)" />
              <Button
                variant="solid"
                :label="__('Save & next')"
                :loading="completing"
                @click="completeCurrent(false)"
              />
            </div>
          </div>
        </div>

        <!-- queue done -->
        <div
          v-else
          class="flex flex-col items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-base p-8 text-ink-gray-5"
        >
          <span class="text-lg font-medium text-ink-gray-9">
            {{ __('Queue completed!') }}
          </span>
          <span class="text-sm">{{
            __('Every record has been handled.')
          }}</span>
          <Button
            class="mt-2"
            variant="solid"
            :label="__('Close session')"
            @click="endSession(false)"
          />
        </div>

        <!-- upcoming -->
        <div v-if="upcoming.length" class="mt-6">
          <div class="mb-2 text-sm font-medium text-ink-gray-7">
            {{ __('Up next') }}
          </div>
          <div
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="e in upcoming"
              :key="e.idx"
              class="flex items-center justify-between px-3 py-2 text-sm"
            >
              <span class="truncate text-ink-gray-8">{{ e.display_name }}</span>
              <span class="text-ink-gray-4">{{ e.number }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { answeringEnabled, callEnabled } from '@/composables/telephony'
import { createResource, Breadcrumbs, FormControl, toast } from 'frappe-ui'
import { ref, reactive, computed, watch } from 'vue'

const { makeCall } = globalStore()
const { leadStatuses, dealStatuses } = statusesStore()

const form = reactive({
  source: 'Records',
  doctype: 'CRM Lead',
  status: '',
  limit: 20,
  includeUpcoming: false,
})
const sourceTouched = ref(false)
const creating = ref(false)
const createError = ref('')
const completing = ref(false)
const disposition = ref('')
const note = ref('')

const session = createResource({
  url: 'crm.api.dialer.get_active_session',
  cache: 'crm-dial-session',
  auto: true,
})

const summary = createResource({
  url: 'crm.api.dialer.get_callback_summary',
  cache: 'crm-callback-summary',
  auto: true,
})

// a practice running the answering service works its callbacks far more often
// than it cold-calls a list, so that is the round it lands on — until the agent
// says otherwise, at which point their choice stands. The flag is only ever set
// from the select's own event, so this default never counts as a choice.
function preferCallbacks() {
  if (answeringEnabled.value && !sourceTouched.value) form.source = 'Callbacks'
}
preferCallbacks()
watch(answeringEnabled, preferCallbacks)

const sourceOptions = [
  { label: __('Callbacks'), value: 'Callbacks' },
  { label: __('Leads'), value: 'CRM Lead' },
  { label: __('Deals'), value: 'CRM Deal' },
]

const isCallbackRound = computed(() => form.source === 'Callbacks')
const isCallbackSession = computed(() => session.data?.source === 'Callbacks')

const current = computed(() => session.data?.current)
const upcoming = computed(
  () =>
    session.data?.entries
      ?.filter((e) => e.status == 'Pending' && e.idx != current.value?.idx)
      .slice(0, 5) || [],
)

const outcomeHint = computed(() => {
  const d = disposition.value
  if (['No Answer', 'Voicemail'].includes(d))
    return __('The callback stays queued and comes back around later.')
  if (d === 'Callback') return __('The callback is pushed to a later round.')
  if (d === 'Wrong Number')
    return __('The callback is closed — nobody to call.')
  if (d) return __('The callback is marked as done.')
  return ''
})

const statusSelectOptions = computed(() => {
  const statuses =
    form.source == 'CRM Lead' ? leadStatuses.data : dealStatuses.data
  return [
    { label: __('Any'), value: '' },
    ...(statuses || []).map((s) => ({ label: s.name, value: s.name })),
  ]
})

function recordRoute(entry) {
  // a callback whose number matched nothing has no record to open
  if (!entry.reference_doctype || !entry.reference_name) return null
  const name = entry.reference_doctype == 'CRM Lead' ? 'Lead' : 'Deal'
  const paramKey = name == 'Lead' ? 'leadId' : 'dealId'
  return { name, params: { [paramKey]: entry.reference_name } }
}

function createSession() {
  creating.value = true
  createError.value = ''
  createResource({
    url: 'crm.api.dialer.create_session',
    params: {
      source: isCallbackRound.value ? 'Callbacks' : 'Records',
      doctype: isCallbackRound.value ? undefined : form.source,
      status: isCallbackRound.value ? undefined : form.status || null,
      include_upcoming: isCallbackRound.value ? form.includeUpcoming : false,
      limit: form.limit || 20,
    },
    auto: true,
    onSuccess: (data) => {
      creating.value = false
      session.data = data
    },
    onError: (e) => {
      creating.value = false
      createError.value = e.messages?.[0] || __('Failed to create session')
    },
  })
}

function completeCurrent(skipped) {
  if (!current.value) return
  completing.value = true
  createResource({
    url: 'crm.api.dialer.complete_entry',
    params: {
      session: session.data.name,
      idx: current.value.idx,
      disposition: disposition.value || null,
      note: note.value || null,
      skipped,
    },
    auto: true,
    onSuccess: (data) => {
      completing.value = false
      disposition.value = ''
      note.value = ''
      session.data = data
    },
    onError: (e) => {
      completing.value = false
      toast.error(e.messages?.[0] || __('Failed to save outcome'))
    },
  })
}

function endSession(cancel) {
  createResource({
    url: 'crm.api.dialer.end_session',
    params: { session: session.data.name, cancel },
    auto: true,
    onSuccess: () => {
      session.data = null
      session.reload()
      summary.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to end session')),
  })
}
</script>
