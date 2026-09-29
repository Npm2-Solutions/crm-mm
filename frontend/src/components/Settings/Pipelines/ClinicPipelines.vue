<template>
  <!--
    The medical centre's two pipelines, where the clinic is on. A booking moves
    an open deal of the new patients pipeline to the stage chosen here, and
    becoming a patient wins it: that is what lets the ads report say what a new
    patient costs.
  -->
  <div
    v-if="settings.data?.clinic_on"
    class="mt-8 flex flex-col gap-4 border-t border-outline-gray-2 px-2 pt-6"
  >
    <div class="flex flex-col gap-1">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Medical centre') }}
      </h3>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'A booking moves an open deal of the new patients pipeline to the stage after a booking, and becoming a patient wins it. So the ads report says what a new patient costs.',
          )
        }}
      </p>
    </div>
    <div v-if="missing">
      <Button
        :label="__('Create the two pipelines')"
        :loading="busy"
        @click="create"
      />
    </div>
    <div class="grid grid-cols-3 gap-4 max-md:grid-cols-1">
      <FormControl
        v-model="form.new_patients_pipeline"
        type="select"
        :label="__('New patients')"
        :options="pipelineOptions"
        @update:modelValue="form.booked_stage = ''"
      />
      <FormControl
        v-model="form.booked_stage"
        type="select"
        :label="__('Stage after a booking')"
        :options="stageOptions"
        :disabled="!form.new_patients_pipeline"
      />
      <FormControl
        v-model="form.quotes_pipeline"
        type="select"
        :label="__('Quotes')"
        :options="pipelineOptions"
      />
    </div>
    <ErrorMessage :message="error" />
    <div class="flex justify-end">
      <Button
        variant="solid"
        :label="__('Save')"
        :disabled="!changed"
        :loading="busy"
        @click="save"
      />
    </div>
  </div>
</template>

<script setup>
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
  url: 'crm.clinica.pipeline.get_settings',
  auto: puo('pipeline.configura'),
})

const FIELDS = ['new_patients_pipeline', 'booked_stage', 'quotes_pipeline']
const form = reactive(Object.fromEntries(FIELDS.map((field) => [field, ''])))
const busy = ref(false)
const error = ref('')

watch(
  () => settings.data,
  (data) => FIELDS.forEach((field) => (form[field] = data?.[field] || '')),
  { immediate: true },
)

const missing = computed(
  () =>
    !settings.data?.new_patients_pipeline || !settings.data?.quotes_pipeline,
)
const changed = computed(() =>
  FIELDS.some((field) => (settings.data?.[field] || '') !== form[field]),
)

const pipelineOptions = computed(() => [
  { label: '', value: '' },
  ...(pipelines.data || [])
    .filter((pipeline) => pipeline.name)
    .map((pipeline) => ({ label: pipeline.name, value: pipeline.name })),
])
const stageOptions = computed(() => [
  { label: '', value: '' },
  ...(
    (pipelines.data || []).find(
      (pipeline) => pipeline.name === form.new_patients_pipeline,
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

const create = () => run('crm.clinica.pipeline.create_pipelines')
const save = () => run('crm.clinica.pipeline.save_settings', { ...form })
</script>
