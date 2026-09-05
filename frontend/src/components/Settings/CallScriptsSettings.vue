<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-1">
        <Button
          v-if="draft"
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="draft.script_name || __('New script')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 active:bg-transparent text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="draft = null"
        />
        <h2 v-else class="text-2xl-semibold leading-none h-5">
          {{ __('Call Scripts') }}
        </h2>
      </div>
    </template>

    <template #description>
      <p v-if="!draft" class="text-p-base text-ink-gray-6">
        {{
          __(
            'The procedure an agent works through while the line is open. Steps keep the call on track; the wording under each one means a new hire has the sentence ready.',
          )
        }}
      </p>
    </template>

    <template #header-actions>
      <div class="flex gap-2">
        <Button
          v-if="!draft"
          variant="solid"
          :label="__('New script')"
          @click="newScript"
        />
        <template v-else>
          <Button
            :label="__('Delete')"
            variant="subtle"
            theme="red"
            :disabled="!draft.name"
            @click="remove"
          />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="save"
          />
        </template>
      </div>
    </template>

    <template #content>
      <!-- the list -->
      <div v-if="!draft">
        <div v-if="scripts.loading" class="flex justify-center py-16">
          <LoadingIndicator class="size-5" />
        </div>
        <div
          v-else-if="!scripts.data?.length"
          class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-12 text-center"
        >
          <p class="text-p-base text-ink-gray-6">
            {{ __('No scripts yet.') }}
          </p>
          <Button
            class="mt-3"
            variant="solid"
            :label="__('Write the first one')"
            @click="newScript"
          />
        </div>
        <div
          v-else
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <button
            v-for="s in scripts.data"
            :key="s.name"
            class="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-surface-gray-1"
            @click="edit(s)"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-base-medium text-ink-gray-8 truncate">
                  {{ s.script_name }}
                </span>
                <Badge
                  v-if="!s.enabled"
                  :label="__('Disabled')"
                  variant="subtle"
                  theme="gray"
                />
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{ s.description || __('No description') }}
              </div>
            </div>
            <div class="shrink-0 text-p-sm text-ink-gray-5">
              {{ __('{0} steps', [s.steps.length]) }}
              <span v-if="s.service"> · {{ s.service }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- the editor -->
      <div v-else class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            v-model="draft.script_name"
            :label="__('Name')"
            :placeholder="__('First call — teeth whitening')"
          />
          <FormControl
            v-model="draft.service"
            type="select"
            :label="__('For service')"
            :options="serviceOptions"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            v-model="draft.description"
            :label="__('When to use it')"
            :placeholder="__('One line, so the agent picks the right one')"
          />
          <div class="flex items-end gap-6">
            <FormControl
              v-model.number="draft.order"
              type="number"
              :label="__('Order')"
              class="w-24"
            />
            <div class="flex items-center gap-2 pb-2">
              <Switch v-model="draft.enabled" size="sm" />
              <span class="text-p-base text-ink-gray-7">{{
                __('Enabled')
              }}</span>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
          <span class="text-base-semibold text-ink-gray-9">
            {{ __('Steps') }}
          </span>
          <Button :label="__('Add step')" @click="addStep" />
        </div>

        <div
          v-for="(step, i) in draft.steps"
          :key="i"
          class="rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="flex items-start gap-2">
            <span class="pt-2 text-p-sm text-ink-gray-4">{{ i + 1 }}</span>
            <FormControl
              v-model="step.title"
              class="flex-1"
              :placeholder="__('What the agent does at this point')"
            />
            <Button
              icon="chevron-up"
              variant="ghost"
              :disabled="i === 0"
              :tooltip="__('Move up')"
              @click="move(i, -1)"
            />
            <Button
              icon="chevron-down"
              variant="ghost"
              :disabled="i === draft.steps.length - 1"
              :tooltip="__('Move down')"
              @click="move(i, 1)"
            />
            <Button
              icon="x"
              variant="ghost"
              :tooltip="__('Remove')"
              @click="draft.steps.splice(i, 1)"
            />
          </div>
          <div class="mt-2 pl-5">
            <RichTextField
              editor-class="prose-sm min-h-[60px] text-ink-base"
              :content="step.body || ''"
              :placeholder="__('The wording to read out (optional)')"
              @change="(value) => (step.body = value)"
            />
            <label class="mt-2 flex items-center gap-2">
              <Checkbox v-model="step.optional" />
              <span class="text-p-sm text-ink-gray-6">
                {{ __('Optional — may be left unticked') }}
              </span>
            </label>
          </div>
        </div>

        <ErrorMessage :message="error" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import RichTextField from '@/components/RichTextField.vue'
import {
  Badge,
  Checkbox,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const draft = ref(null)
const saving = ref(false)
const error = ref('')

const scripts = createResource({
  url: 'crm.api.call_scripts.list_scripts',
  params: { include_disabled: true },
  auto: true,
})

const meta = createResource({
  url: 'crm.api.appointments.get_scheduler_meta',
  cache: 'scheduler-meta',
  auto: true,
})

const serviceOptions = computed(() => [
  { label: __('Any service'), value: '' },
  ...(meta.data?.services || []).map((s) => ({
    label: s.service_name,
    value: s.name,
  })),
])

function newScript() {
  error.value = ''
  draft.value = {
    name: null,
    script_name: '',
    enabled: true,
    service: '',
    description: '',
    order: 0,
    steps: [{ title: '', body: '', optional: false }],
  }
}

function edit(script) {
  error.value = ''
  // a deep copy so abandoning the editor leaves the list untouched
  draft.value = JSON.parse(JSON.stringify(script))
}

function addStep() {
  draft.value.steps.push({ title: '', body: '', optional: false })
}

function move(index, delta) {
  const steps = draft.value.steps
  const [row] = steps.splice(index, 1)
  steps.splice(index + delta, 0, row)
}

function save() {
  saving.value = true
  error.value = ''
  createResource({
    url: 'crm.api.call_scripts.save_script',
    params: { script: draft.value, name: draft.value.name || null },
    auto: true,
    onSuccess: () => {
      saving.value = false
      draft.value = null
      scripts.reload()
      toast.success(__('Script saved'))
    },
    onError: (e) => {
      saving.value = false
      error.value = e.messages?.[0] || __('Could not save the script')
    },
  })
}

function remove() {
  createResource({
    url: 'crm.api.call_scripts.delete_script',
    params: { name: draft.value.name },
    auto: true,
    onSuccess: () => {
      draft.value = null
      scripts.reload()
      toast.success(__('Script deleted'))
    },
    onError: (e) =>
      toast.error(e.messages?.[0] || __('Could not delete the script')),
  })
}
</script>
