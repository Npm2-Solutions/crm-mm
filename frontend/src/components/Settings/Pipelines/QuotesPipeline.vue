<template>
  <!--
    The quotes pipeline (crm.preventivi): a quote handed over moves the person's
    deal to "quote delivered", accepted wins it, declined loses it. And how long a
    quote holds, unless whoever writes it says otherwise.
  -->
  <div
    v-if="settings.data"
    class="mt-8 flex flex-col gap-4 border-t border-outline-gray-2 px-2 pt-6"
  >
    <div class="flex flex-col gap-1">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Quotes') }}
      </h3>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'A quote handed over moves the person\'s deal to "quote delivered"; accepted, the deal is won, declined, it is lost. With no pipeline chosen, quotes move no deal.',
          )
        }}
      </p>
    </div>
    <div v-if="!settings.data.quotes_pipeline">
      <Button
        :label="__('Create the quotes pipeline')"
        :loading="busy"
        @click="create"
      />
    </div>
    <div class="grid grid-cols-3 gap-4 max-md:grid-cols-1">
      <FormControl
        v-model="form.quotes_pipeline"
        type="select"
        :label="__('Pipeline')"
        :options="pipelineOptions"
      />
      <FormControl
        v-model="form.valid_days"
        type="number"
        inputmode="numeric"
        :label="__('A quote holds, in days')"
        :placeholder="__('60')"
        :min="1"
      />
    </div>
    <!-- a quote paid in instalments (crm.preventivi.rate): who invoices them -->
    <div class="flex flex-col gap-3">
      <FormControl
        v-model="form.instalment_invoicing"
        type="select"
        :label="__('Quotes paid in instalments')"
        :options="instalmentOptions"
      />
      <p class="text-p-sm text-ink-gray-6">
        {{
          form.instalment_invoicing === 'Track only'
            ? __(
                'The centre invoices the work by itself as it is done; the instalments are only followed, and marked paid by whoever records payments.',
              )
            : __(
                'On the day each payment falls due {brand} makes its invoice, and the appointments of the quote are not invoiced again. Money received before a service is done is invoiced when it is received.',
              )
        }}
      </p>
      <FormControl
        v-if="form.instalment_invoicing !== 'Track only'"
        v-model="form.issue_instalment_invoices"
        type="checkbox"
        :label="
          __(
            'Issue them at once, rather than leaving drafts to check and issue',
          )
        "
      />
    </div>
    <ErrorMessage :message="error" />
    <div class="flex justify-end">
      <Button
        variant="solid"
        class="max-md:w-full"
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
  url: 'crm.preventivi.pipeline.get_settings',
  auto: puo('pipeline.configura'),
})

const form = reactive({
  quotes_pipeline: '',
  valid_days: '',
  instalment_invoicing: 'Each instalment when due',
  issue_instalment_invoices: false,
})
const busy = ref(false)
const error = ref('')

watch(
  () => settings.data,
  (data) => {
    form.quotes_pipeline = data?.quotes_pipeline || ''
    form.valid_days = data?.valid_days || ''
    form.instalment_invoicing =
      data?.instalment_invoicing || 'Each instalment when due'
    form.issue_instalment_invoices = Boolean(data?.issue_instalment_invoices)
  },
  { immediate: true },
)

const changed = computed(
  () =>
    (settings.data?.quotes_pipeline || '') !== form.quotes_pipeline ||
    String(settings.data?.valid_days || '') !== String(form.valid_days || '') ||
    (settings.data?.instalment_invoicing || 'Each instalment when due') !==
      form.instalment_invoicing ||
    Boolean(settings.data?.issue_instalment_invoices) !==
      Boolean(form.issue_instalment_invoices),
)

const instalmentOptions = computed(() => [
  {
    label: __('{brand} invoices each instalment'),
    value: 'Each instalment when due',
  },
  {
    label: __('The centre invoices by itself'),
    value: 'Track only',
  },
])

const pipelineOptions = computed(() => [
  { label: '', value: '' },
  ...(pipelines.data || [])
    .filter((pipeline) => pipeline.name)
    .map((pipeline) => ({ label: __(pipeline.name), value: pipeline.name })),
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

const create = () => run('crm.preventivi.pipeline.create_pipeline')
const save = () =>
  run('crm.preventivi.pipeline.save_settings', {
    quotes_pipeline: form.quotes_pipeline || null,
    valid_days: Number(form.valid_days) || null,
    instalment_invoicing: form.instalment_invoicing,
    issue_instalment_invoices: form.issue_instalment_invoices ? 1 : 0,
  })
</script>
