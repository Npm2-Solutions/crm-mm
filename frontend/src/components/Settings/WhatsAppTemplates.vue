<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-start justify-between gap-3 px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('WhatsApp Templates') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Outside 24 hours from the last customer message, WhatsApp only delivers approved templates.',
            )
          }}
        </p>
      </div>
      <div v-if="data.available" class="flex items-center gap-2">
        <!-- A template made in WhatsApp Manager, or `hello_world` that Meta
             creates by itself, exists there and not here — so it cannot be sent
             until it is brought in. -->
        <Button
          :loading="syncing"
          :label="__('Sync from Meta')"
          @click="sync"
        />
        <Button
          variant="solid"
          iconLeft="plus"
          :label="__('New template')"
          @click="openTemplate()"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="templates.data && !data.available"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('The WhatsApp app is not installed on this site yet.') }}
      </div>

      <div
        v-else-if="data.templates?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="template in data.templates"
          :key="template.name"
          class="flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
        >
          <div class="min-w-0 flex-1 cursor-pointer" @click="openTemplate(template)">
            <div class="truncate text-p-base text-ink-gray-8">
              {{ template.template_name || template.name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">{{ template.template }}</div>
          </div>
          <Badge
            v-if="template.status"
            :label="__(template.status)"
            :theme="statusTheme(template.status)"
            size="sm"
          />
          <Button variant="ghost" icon="lucide-trash-2" @click.stop="remove(template)" />
        </div>
      </div>

      <div
        v-else
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('No templates yet.') }}
      </div>
    </div>
  </div>

  <Dialog
    v-model="showTemplate"
    :options="{ title: form.name ? __('Edit template') : __('New template'), size: 'xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-if="!form.name"
          v-model="form.template_name"
          type="text"
          :label="__('Name')"
          :description="__('Lowercase letters, digits and underscores. It cannot be changed later.')"
        />
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.category"
            type="select"
            :label="__('Category')"
            :options="(data.categories || []).map((c) => ({ label: c, value: c }))"
          />
          <FormControl
            v-model="form.language"
            type="select"
            :label="__('Language')"
            :options="data.languages || []"
          />
        </div>
        <FormControl v-model="form.header" type="text" :label="__('Header (optional)')" />
        <FormControl
          v-model="form.template"
          type="textarea"
          :rows="5"
          :label="__('Message')"
          :placeholder="bodyPlaceholder"
          :description="placeholderHint"
        />
        <!-- Meta wants an example for every {{n}} at creation time, and rejects
             the template the moment it is submitted when one is missing. -->
        <FormControl
          v-if="placeholderCount"
          v-model="form.sample_values"
          type="text"
          :label="__('Example values')"
          :placeholder="samplePlaceholder"
          :description="
            __(
              'One per variable, separated by commas, in order. Meta needs them to review the template — this body has {0}.',
              [placeholderCount],
            )
          "
        />
        <FormControl v-model="form.footer" type="text" :label="__('Footer (optional)')" />
        <div class="rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-5">
          {{
            __(
              'Saving submits the template to Meta for review. It can be used once the status turns Approved, usually within a few hours.',
            )
          }}
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :loading="saving"
        :label="form.name ? __('Save changes') : __('Submit for approval')"
        @click="save"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { createResource, Dialog, FormControl, toast } from 'frappe-ui'
import { ref, reactive, computed } from 'vue'

// a literal {{1}} cannot live in the template markup: Vue would parse it
const bodyPlaceholder = 'Ciao {{1}}, il tuo ordine è pronto.'
const placeholderHint = __('Use {0} for the first variable, {1} for the second, and so on.', [
  '{{1}}',
  '{{2}}',
])

const saving = ref(false)
const showTemplate = ref(false)

const templates = createResource({
  url: 'crm.integrations.whatsapp.templates.get_templates',
  auto: true,
})

const data = computed(() => templates.data || {})

const form = reactive({
  name: null,
  template_name: '',
  category: 'MARKETING',
  language: 'it',
  header: '',
  template: '',
  footer: '',
  sample_values: '',
})

// {{1}}, {{2}}… — how many distinct ones the body uses
const placeholderCount = computed(
  () => new Set(form.template?.match(/\{\{\s*\d+\s*\}\}/g) || []).size,
)

const samplePlaceholder = computed(() =>
  Array.from({ length: placeholderCount.value }, (_, i) =>
    i === 0 ? __('Marco') : __('value {0}', [i + 1]),
  ).join(', '),
)

function statusTheme(status) {
  return (
    {
      APPROVED: 'green',
      Approved: 'green',
      PENDING: 'orange',
      Pending: 'orange',
      REJECTED: 'red',
      Rejected: 'red',
    }[status] || 'gray'
  )
}

function openTemplate(template = null) {
  form.name = template?.name || null
  form.template_name = template?.template_name || ''
  form.category = template?.category || data.value.categories?.[0] || 'MARKETING'
  form.language =
    template?.language || data.value.languages?.[0]?.value || 'it'
  form.header = template?.header || ''
  form.template = template?.template || ''
  form.footer = template?.footer || ''
  form.sample_values = template?.sample_values || ''
  showTemplate.value = true
}

const syncing = ref(false)

function sync() {
  syncing.value = true
  createResource({
    url: 'crm.integrations.whatsapp.templates.sync_templates',
    auto: true,
    onSuccess: (fresh) => {
      syncing.value = false
      templates.data = fresh
      toast.success(__('Templates brought in from Meta'))
    },
    onError: (e) => {
      syncing.value = false
      toast.error(e.messages?.[0] || __('Could not read the templates from Meta'))
    },
  })
}

function save() {
  saving.value = true
  createResource({
    url: 'crm.integrations.whatsapp.templates.save_template',
    params: { name: form.name, template: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showTemplate.value = false
      toast.success(__('Template saved'))
      templates.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save the template'))
    },
  })
}

function remove(template) {
  createResource({
    url: 'crm.integrations.whatsapp.templates.delete_template',
    params: { name: template.name },
    auto: true,
    onSuccess: () => templates.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
