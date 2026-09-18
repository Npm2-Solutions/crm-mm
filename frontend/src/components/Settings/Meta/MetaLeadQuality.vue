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
  <div
    class="flex h-full flex-col gap-6 overflow-y-auto py-8 px-6 text-ink-gray-8"
  >
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Lead quality') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Send back to Meta what became of each lead, so the ads look for people who buy instead of people who fill in forms.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-col gap-4 px-2">
      <div
        v-if="!status.data?.connected"
        class="flex items-center justify-between gap-3 rounded-lg border border-dashed border-outline-gray-2 p-6"
      >
        <span class="text-p-base text-ink-gray-5">
          {{ __('Connect your Meta account first.') }}
        </span>
        <Button :label="__('Go to connection')" @click="goToConnection" />
      </div>

      <template v-else>
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
          <FormControl
            v-model="form.test_code"
            type="text"
            :label="__('Test event code (only while verifying)')"
            placeholder="TEST12345"
            :description="
              __(
                'Leave this empty in normal use: events sent with a test code do not count.',
              )
            "
            @change="save({ test_code: form.test_code })"
          />

          <div v-if="status.data?.last_error" class="text-p-sm text-ink-red-5">
            {{ status.data.last_error }}
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
                  status.data?.enough ? 'text-ink-green-6' : 'text-ink-orange-5'
                "
              >
                {{
                  status.data?.percent === null
                    ? '—'
                    : status.data?.percent + '%'
                }}
              </span>
              <span class="ml-2 text-p-sm text-ink-gray-5">
                {{
                  __('{0} of {1} leads reported', [
                    status.data?.reported ?? 0,
                    status.data?.leads ?? 0,
                  ])
                }}
              </span>
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{ __('{0} waiting', [status.data?.pending ?? 0]) }}
              <template v-if="status.data?.failed">
                ·
                <span class="text-ink-red-5">{{
                  __('{0} failed', [status.data.failed])
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
import { activeSettingsPage } from '@/composables/settings'
import { createResource, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const status = createResource({
  url: 'crm.integrations.meta.api.get_conversions_status',
  auto: true,
})

const form = reactive({ enabled: false, dataset_id: '', test_code: '' })
watch(
  () => status.data,
  (data) => {
    if (!data) return
    form.enabled = Boolean(data.enabled)
    form.dataset_id = data.dataset_id || ''
    form.test_code = data.test_code || ''
  },
  { immediate: true },
)

const stages = computed(() => status.data?.stages || [])

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
    onSuccess: () => status.reload(),
    onError: (e) => {
      status.reload()
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
      data.error
        ? toast.error(data.error)
        : toast.success(__('{0} stages sent', [data.sent || 0]))
      status.reload()
    },
    onError: (e) => {
      sending.value = false
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

function goToConnection() {
  activeSettingsPage.value = 'Meta connection'
}
</script>
