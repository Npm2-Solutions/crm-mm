<!--
  The only screen here that makes the ads better instead of better understood.

  Everything else reads from Meta. This writes back: the stage each lead reached
  in the CRM, so a lead-ads campaign can optimise for the people who buy instead
  of the people who submit. Meta grades the integration on coverage, so the
  coverage is the first thing on the screen — and the requirements are stated
  plainly, because this is a feature that takes weeks to pay off and saying
  otherwise would set the wrong expectation.
-->
<template>
  <div class="flex flex-col gap-4 px-2">
    <p class="text-p-sm text-ink-gray-5">
      {{
        __(
          'Send back to Meta what became of each lead, so the ads look for people who buy instead of people who fill in forms.',
        )
      }}
    </p>

    <div class="flex flex-col gap-4">
      <div
        v-if="status.data && !connected"
        class="flex items-center justify-between gap-3 rounded-lg border border-dashed border-outline-gray-2 p-6"
      >
        <span class="text-p-base text-ink-gray-5">
          {{ __('Connect your Meta account first.') }}
        </span>
        <Button
          :label="__('Go to connection')"
          @click="emit('navigate', 'connection')"
        />
      </div>

      <template v-else-if="connected">
        <div
          class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="min-w-0">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Send lead stages to Meta') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Stages leave every hour, and when a status changes.') }}
              </div>
            </div>
            <Switch
              :modelValue="Boolean(form.enabled)"
              @update:modelValue="(v) => save({ enabled: v })"
            />
          </div>

          <FormControl
            v-model="form.dataset_id"
            type="text"
            :label="__('Dataset (pixel) ID from Events Manager')"
            placeholder="1234567890"
            @change="save({ dataset_id: form.dataset_id })"
          />
          <!-- a verification tool, and a trap: events sent with it do not
               count, so a code left in place silently switches the feature
               off. An administrator's, not something to find in passing. -->
          <FormControl
            v-if="isAdmin || form.test_code"
            v-model="form.test_code"
            type="text"
            :label="__('Test event code (only while verifying)')"
            placeholder="TEST12345"
            :disabled="!isAdmin"
            :description="
              __(
                'Leave this empty in normal use: events sent with a test code do not count.',
              )
            "
            @change="save({ test_code: form.test_code })"
          />

          <div
            v-if="conversions.data?.last_error"
            class="text-p-sm text-ink-red-5"
          >
            {{ conversions.data.last_error }}
          </div>
        </div>

        <!-- coverage: the number Meta actually judges -->
        <div class="rounded-lg border border-outline-gray-2 p-4">
          <div class="flex items-center justify-between gap-3">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Coverage, last 30 days') }}
            </div>
            <Button
              size="sm"
              :label="__('Send now')"
              :loading="sending"
              @click="sendNow"
            />
          </div>

          <div class="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-2">
            <div>
              <span
                class="text-2xl-semibold"
                :class="
                  conversions.data?.enough
                    ? 'text-ink-green-6'
                    : 'text-ink-orange-5'
                "
              >
                {{
                  conversions.data?.percent === null
                    ? '—'
                    : conversions.data?.percent + '%'
                }}
              </span>
              <span class="ml-2 text-p-sm text-ink-gray-5">
                {{
                  __('{0} of {1} leads reported', [
                    conversions.data?.reported ?? 0,
                    conversions.data?.leads ?? 0,
                  ])
                }}
              </span>
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{ __('{0} waiting', [conversions.data?.pending ?? 0]) }}
              <template v-if="conversions.data?.failed">
                ·
                <span class="text-ink-red-5">{{
                  __('{0} failed', [conversions.data.failed])
                }}</span>
              </template>
            </div>
          </div>

          <div v-if="stages.length" class="mt-3 flex flex-col gap-1">
            <div
              v-for="stage in stages"
              :key="stage.event_name"
              class="flex justify-between text-p-sm"
            >
              <span class="text-ink-gray-7">{{ stage.event_name }}</span>
              <span class="text-ink-gray-5">{{ stage.events }}</span>
            </div>
          </div>

          <div
            class="mt-3 rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'Meta needs at least 60% coverage and at least two stages, the raw lead included, before it will optimise on this. It also asks for around 200 leads a month and takes 3 to 4 weeks to learn.',
              )
            }}
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { createResource, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

// the connection, loaded once by the page around the tabs
const props = defineProps({
  status: { type: Object, required: true },
})

const emit = defineEmits(['navigate'])

const connected = computed(() => Boolean(props.status.data?.connected))
const isAdmin = computed(() => Boolean(props.status.data?.is_admin))

const conversions = createResource({
  url: 'crm.integrations.meta.api.get_conversions_status',
  auto: true,
})

const form = reactive({ enabled: false, dataset_id: '', test_code: '' })
watch(
  () => conversions.data,
  (data) => {
    if (!data) return
    form.enabled = Boolean(data.enabled)
    form.dataset_id = data.dataset_id || ''
    form.test_code = data.test_code || ''
  },
  { immediate: true },
)

const stages = computed(() => conversions.data?.stages || [])

function save(changes) {
  createResource({
    url: 'crm.integrations.meta.api.save_conversions_settings',
    params: {
      dataset_id: form.dataset_id,
      test_code: form.test_code,
      enabled: form.enabled,
      ...changes,
    },
    auto: true,
    onSuccess: () => conversions.reload(),
    onError: (e) => {
      conversions.reload()
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

const sending = ref(false)
function sendNow() {
  sending.value = true
  createResource({
    url: 'crm.integrations.meta.api.send_conversions_now',
    auto: true,
    onSuccess: (data) => {
      sending.value = false
      if (data.error) toast.error(data.error)
      else toast.success(__('{0} stages sent', [data.sent || 0]))
      conversions.reload()
    },
    onError: (e) => {
      sending.value = false
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}
</script>
