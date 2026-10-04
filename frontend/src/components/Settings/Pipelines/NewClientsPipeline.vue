<template>
  <!--
    The new clients pipeline (crm.clienti): a booking moves an open deal of it to
    the stage chosen here, and the first time the person comes wins it. That is
    what lets the ads report say what a new client costs. With the clinic on it is
    the new patients' one, in the clinic's words.
  -->
  <div
    v-if="settings.data"
    class="mt-8 flex flex-col gap-4 border-t border-outline-gray-2 px-2 pt-6"
  >
    <div class="flex flex-col gap-1">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('New clients') }}
      </h3>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'A booking moves an open deal of the new clients pipeline to the stage after a booking, and the first time the person comes wins it. So the ads report says what a new client costs.',
          )
        }}
      </p>
    </div>
    <div v-if="missing">
      <Button
        :label="__('Create the new clients pipeline')"
        :loading="busy"
        @click="create"
      />
    </div>
    <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
      <FormControl
        v-model="form.new_clients_pipeline"
        type="select"
        :label="__('Pipeline')"
        :options="pipelineOptions"
        @update:modelValue="form.booked_stage = ''"
      />
      <FormControl
        v-model="form.booked_stage"
        type="select"
        :label="__('Stage after a booking')"
        :options="stageOptions"
        :disabled="!form.new_clients_pipeline"
      />
    </div>
    <ErrorMessage :message="error" />
    <div class="flex justify-end">
      <AzioneImpostazioni
        :label="__('Save')"
        :disabled="!changed"
        :loading="busy"
        @click="save"
      />
    </div>
  </div>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import { usersStore } from '@/stores/users'
import {
  Button,
  ErrorMessage,
  FormControl,
  call,
  createResource,
} from 'frappe-ui'
import { computed, inject, reactive, ref, watch } from 'vue'

const pipelines = inject('pipelines')
const reloadPipelines = inject('reloadPipelines')
const { puo } = usersStore()

const settings = createResource({
  url: 'crm.clienti.pipeline.get_settings',
  auto: puo('pipeline.configura'),
})

const FIELDS = ['new_clients_pipeline', 'booked_stage']
const form = reactive(Object.fromEntries(FIELDS.map((field) => [field, ''])))
const busy = ref(false)
const error = ref('')

watch(
  () => settings.data,
  (data) => FIELDS.forEach((field) => (form[field] = data?.[field] || '')),
  { immediate: true },
)

const missing = computed(() => !settings.data?.new_clients_pipeline)
const changed = computed(() =>
  FIELDS.some((field) => (settings.data?.[field] || '') !== form[field]),
)

const pipelineOptions = computed(() => [
  { label: '', value: '' },
  ...(pipelines.data || [])
    .filter((pipeline) => pipeline.name)
    .map((pipeline) => ({ label: __(pipeline.name), value: pipeline.name })),
])
const stageOptions = computed(() => [
  { label: '', value: '' },
  ...(
    (pipelines.data || []).find(
      (pipeline) => pipeline.name === form.new_clients_pipeline,
    )?.stages || []
  ).map((stage) => ({ label: stage.name, value: stage.name })),
])

async function run(method, args = {}) {
  busy.value = true
  error.value = ''
  try {
    settings.data = await call(method, args)
    reloadPipelines()
  } catch (e) {
    error.value = e.messages?.[0] || e.message
  } finally {
    busy.value = false
  }
}

const create = () => run('crm.clienti.pipeline.create_pipeline')
const save = () =>
  run('crm.clienti.pipeline.save_settings', {
    new_clients_pipeline: form.new_clients_pipeline || null,
    booked_stage: form.booked_stage || null,
  })
</script>
